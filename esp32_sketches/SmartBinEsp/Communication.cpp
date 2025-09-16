#include "Communication.h"
#include <Arduino.h>

Communication::Communication(BluetoothSerial* bt) : 
    bluetooth(bt),
    currentState(COMM_INIT),
    lastMessageTime(0),
    lastBroadcastTime(0),
    consecutiveTimeouts(0),
    laptopConnected(false),
    currentImageId(""),
    totalImageParts(0),
    imageParts(nullptr),
    imageTransmissionComplete(false) {
}

void Communication::begin() {
    logCommunicationEvent("Initializing communication system");
    currentState = COMM_WAITING_LAPTOP;
    lastBroadcastTime = 0; // Force immediate broadcast
    consecutiveTimeouts = 0;
    laptopConnected = false;
}

void Communication::update() {
    unsigned long now = millis();
    
    // Handle timeouts
    if (currentState == COMM_WAITING_RESULT && 
        (now - lastMessageTime) > LAPTOP_RESPONSE_TIMEOUT_MS) {
        handleTimeout();
        return;
    }
    
    // State machine
    switch (currentState) {
        case COMM_WAITING_LAPTOP:
            handleWaitingLaptopState();
            break;
            
        case COMM_CONNECTED:
            handleConnectedState();
            break;
            
        case COMM_WAITING_RESULT:
            handleWaitingResultState();
            break;
            
        case COMM_ERROR:
            handleErrorState();
            break;
            
        default:
            break;
    }
}

void Communication::handleWaitingLaptopState() {
    unsigned long now = millis();
    
    // Only proceed if Bluetooth is actually connected
    if (!bluetooth || !bluetooth->connected()) {
        lastBroadcastTime = 0;
        return;
    }

    // String receivedLine = bluetooth.read();

    
    // Check for incoming protocol messages
    String code, content;
    bool receivedProtocolMessage = receiveProtocolMessage(code, content);
    // Serial.println("--->  Code: " + code + "Content: " + content);
    if (receivedProtocolMessage) {
        logCommunicationEvent("Received protocol message", "Code: " + code);
        
        // FILTER: Ignore our own RTC00 messages while waiting for laptop
        if (code == CODE_RTC00) {
            logCommunicationEvent("Ignoring own RTC00 echo", "Filtering out self-sent message");
            return; // Ignore and continue waiting
        }
        
        if (code == CODE_RTC01) {
            logCommunicationEvent("Valid RTC01 received from laptop", content);
            
            // Send connection confirmation
            if (sendProtocolMessage(CODE_RTC02, "ESP32 connection confirmed")) {
                laptopConnected = true;
                setState(COMM_CONNECTED);
                logCommunicationEvent("✅ Laptop connection established");
                return;
            } else {
                logCommunicationEvent("❌ Failed to send RTC02 confirmation");
            }
        } else {
            logCommunicationEvent("❌ Unexpected protocol message during laptop wait", 
                                "Expected: RTC01, Got: " + code);
        }
    }
    
    // Broadcast ready message periodically (only when bluetooth connected)
    if (now - lastBroadcastTime > WAITING_BROADCAST_INTERVAL_MS) {
        if (sendProtocolMessage(CODE_RTC00, "ESP32 ready to connect")) {
            logCommunicationEvent("📡 Broadcasting RTC00 ready message");
            lastBroadcastTime = now;
        } else {
            logCommunicationEvent("❌ Failed to send RTC00 message");
        }
    }
}

void Communication::handleConnectedState() {
    // In connected state, just listen for incoming messages
    // Main communication happens through sendImageForClassification
    String code, content;
    if (receiveProtocolMessage(code, content)) {
        if (code.startsWith(CODE_ERR_PREFIX)) {
            logCommunicationEvent("Error received from laptop", content);
            // Could handle specific errors here
        } else {
            logCommunicationEvent("Unexpected message in connected state", code + " " + content);
        }
    }
}

void Communication::handleWaitingResultState() {
    String code, content;
    
    if (receiveProtocolMessage(code, content)) {
        if (code == CODE_CLS01) {
            logCommunicationEvent("Classification result received", content);
            setState(COMM_CONNECTED);
            consecutiveTimeouts = 0;
            
        } else if (code.startsWith(CODE_ERR_PREFIX)) {
            logCommunicationEvent("Classification error received", content);
            setState(COMM_CONNECTED); // Will retry
            consecutiveTimeouts = 0;
        }
    }
}

void Communication::handleErrorState() {
    logCommunicationEvent("In error state - attempting recovery");
    delay(5000); // Wait before retry
    reset();
}

bool Communication::sendProtocolMessage(const String& code, const String& content) {
    if (!bluetooth || !bluetooth->connected()) {
        return false;
    }
    
    String message = code + " " + content;
    bluetooth->println(message);
    
    lastMessageTime = millis();
    return true;
}

bool Communication::receiveProtocolMessage(String& code, String& content) {
    if (!bluetooth || !bluetooth->available()) {
        return false;
    }
    
    while (bluetooth->available()) {
        String line = bluetooth->readStringUntil('\n');
        line.trim();
        Serial.print("Received line: ");
        Serial.println(line);

        if (isProtocolMessage(line)) {
            code = extractCode(line);
            content = extractContent(line);
            Serial.println("Code: " + code + ", Content: " + content);
            return true;
        }
        // Non-protocol messages are ignored during protocol communication
        // but could be logged for debugging
    }
    
    return false;
}

bool Communication::isProtocolMessage(const String& line) {
    if (line.length() < 5) return false; // Need at least "CODE"
    
    String code = line.substring(0, 5);
    if (line.charAt(5) != ' ' && line.length() > 5) return false; // Must have space after code
    
    // Check if it's a valid protocol code
    return (code == CODE_RTC00 || code == CODE_RTC01 || code == CODE_RTC02 ||
            code == CODE_PA000 || code.startsWith(CODE_PA_PREFIX) ||
            code.startsWith(CODE_PX_PREFIX) || code == CODE_CLS01 ||
            code.startsWith(CODE_ERR_PREFIX));
}

String Communication::extractCode(const String& line) {
    if (line.length() >= 5) {
        return line.substring(0, 5);
    }
    return "";
}

String Communication::extractContent(const String& line) {
    if (line.length() > 6) {
        return line.substring(6); // Skip "CODE "
    }
    return "";
}

bool Communication::sendImageForClassification(const uint8_t* imageData, size_t imageSize, 
                                             int width, int height, String& result) {
    if (currentState != COMM_CONNECTED) {
        return false;
    }
    
    setState(COMM_SENDING_IMAGE);
    currentImageId = "img_" + String(millis());
    
    logCommunicationEvent("Starting image transmission", 
                         "Size: " + String(imageSize) + " bytes, ID: " + currentImageId);
    
    // Step 1: Prepare image transmission (convert to Base64 and split into parts)
    if (!prepareImageTransmission(imageData, imageSize, width, height)) {
        setState(COMM_ERROR);
        return false;
    }
    
    // Step 2: Send metadata header (PA000)
    String metadata = "type:image, size:" + String(imageSize) + 
                     ", format:JPEG, width:" + String(width) + 
                     ", height:" + String(height) + 
                     ", id:" + currentImageId +
                     ", parts:" + String(totalImageParts);
    
    if (!sendProtocolMessage(CODE_PA000, metadata)) {
        logCommunicationEvent("Failed to send PA000 metadata");
        cleanupImageTransmission();
        setState(COMM_ERROR);
        return false;
    }
    
    logCommunicationEvent("Sent PA000 metadata", "Parts: " + String(totalImageParts));
    
    // Step 3: Send image parts (PA001, PA002, ..., PX###)
    for (int i = 0; i < totalImageParts; i++) {
        String partCode;
        if (i == totalImageParts - 1) {
            // Last part uses PX code
            String partNumber = String(i + 1);
            while (partNumber.length() < 3) {
                partNumber = "0" + partNumber;
            }
            partCode = CODE_PX_PREFIX + partNumber;
        } else {
            // Regular parts use PA code
            String partNumber = String(i + 1);
            while (partNumber.length() < 3) {
                partNumber = "0" + partNumber;
            }
            partCode = CODE_PA_PREFIX + partNumber;
        }
        
        if (!sendProtocolMessage(partCode, imageParts[i])) {
            logCommunicationEvent("Failed to send image part", String(i + 1));
            cleanupImageTransmission();
            setState(COMM_ERROR);
            return false;
        }
        
        // Small delay to prevent overwhelming the connection
        delay(10);
    }
    
    logCommunicationEvent("Image transmission complete", "Sent " + String(totalImageParts) + " parts");
    cleanupImageTransmission();
    
    // Step 4: Wait for classification result
    setState(COMM_WAITING_RESULT);
    
    // Wait for CLS01 response
    unsigned long startTime = millis();
    while (currentState == COMM_WAITING_RESULT && 
           (millis() - startTime) < LAPTOP_RESPONSE_TIMEOUT_MS) {
        
        String code, content;
        if (receiveProtocolMessage(code, content)) {
            if (code == CODE_CLS01) {
                result = content; // e.g. "plastic 0.85"
                setState(COMM_CONNECTED);
                logCommunicationEvent("✅ Classification received", result);
                return true;
            } else if (code.startsWith(CODE_ERR_PREFIX)) {
                logCommunicationEvent("❌ Classification error", content);
                setState(COMM_CONNECTED);
                return false;
            }
        }
        
        delay(100);
        yield();
    }
    
    // Timeout
    logCommunicationEvent("❌ Classification timeout");
    handleTimeout();
    return false;
}

bool Communication::prepareImageTransmission(const uint8_t* imageData, size_t imageSize, 
                                           int width, int height) {
    // Convert image to Base64
    size_t base64_len = 0;
    int ret = mbedtls_base64_encode(NULL, 0, &base64_len, imageData, imageSize);
    if (ret != MBEDTLS_ERR_BASE64_BUFFER_TOO_SMALL) {
        logCommunicationEvent("Failed to calculate Base64 size");
        return false;
    }
    
    // Encode to Base64
    char* base64_buffer = (char*)malloc(base64_len + 1);
    if (!base64_buffer) {
        logCommunicationEvent("Failed to allocate Base64 buffer");
        return false;
    }
    
    ret = mbedtls_base64_encode((unsigned char*)base64_buffer, base64_len, 
                               &base64_len, imageData, imageSize);
    if (ret != 0) {
        free(base64_buffer);
        logCommunicationEvent("Base64 encoding failed");
        return false;
    }
    
    base64_buffer[base64_len] = '\0';
    String base64String = String(base64_buffer);
    free(base64_buffer);
    
    // Split into parts (max ~200 chars per part to avoid Bluetooth buffer issues)
    const int maxPartSize = 200;
    totalImageParts = (base64String.length() + maxPartSize - 1) / maxPartSize;
    
    if (totalImageParts > MAX_IMAGE_PARTS) {
        logCommunicationEvent("Image too large", "Parts: " + String(totalImageParts));
        return false;
    }
    
    // Allocate parts array
    imageParts = new String[totalImageParts];
    if (!imageParts) {
        logCommunicationEvent("Failed to allocate parts array");
        return false;
    }
    
    // Split the Base64 string into parts
    for (int i = 0; i < totalImageParts; i++) {
        int startPos = i * maxPartSize;
        int endPos = min(startPos + maxPartSize, (int)base64String.length());
        imageParts[i] = base64String.substring(startPos, endPos);
    }
    
    logCommunicationEvent("Image prepared for transmission", 
                         "Base64 length: " + String(base64String.length()) + 
                         ", Parts: " + String(totalImageParts));
    
    return true;
}

void Communication::cleanupImageTransmission() {
    if (imageParts) {
        delete[] imageParts;
        imageParts = nullptr;
    }
    totalImageParts = 0;
    currentImageId = "";
}
bool Communication::waitForLaptopConnection() {
    setState(COMM_WAITING_LAPTOP);
    logCommunicationEvent("Starting laptop connection wait - waiting for RTC01");
    
    unsigned long startTime = millis();
    const unsigned long maxWaitTime = 60000; // 1 minute max wait
    
    while (currentState == COMM_WAITING_LAPTOP && 
           (millis() - startTime) < maxWaitTime) {
        
        // Check if bluetooth is connected first
        if (!bluetooth || !bluetooth->connected()) {
            static unsigned long lastConnectionLog = 0;
            if (millis() - lastConnectionLog > 5000) { // Log every 5 seconds
                logCommunicationEvent("Waiting for Bluetooth device connection...");
                lastConnectionLog = millis();
            }
        } else {
            // Bluetooth is connected, but we need the laptop protocol message
            static unsigned long lastProtocolLog = 0;
            if (millis() - lastProtocolLog > 3000) { // Log every 3 seconds
                logCommunicationEvent("Bluetooth connected - waiting for RTC01 message");
                lastProtocolLog = millis();
            }
        }
        
        update(); // This will handle incoming RTC01
        delay(100);
        yield();
    }
    
    if (laptopConnected) {
        logCommunicationEvent("✅ Laptop connection established successfully");
    } else {
        logCommunicationEvent("⚠️ Laptop connection timeout - no RTC01 received");
    }
    
    return laptopConnected;
}

void Communication::handleTimeout() {
    consecutiveTimeouts++;
    logCommunicationEvent("Timeout occurred", 
                         "Count: " + String(consecutiveTimeouts));
    
    if (consecutiveTimeouts >= MAX_CONSECUTIVE_TIMEOUTS) {
        logCommunicationEvent("Max timeouts reached - disconnecting");
        handleDisconnection();
    } else {
        setState(COMM_CONNECTED); // Retry
    }
}

void Communication::handleDisconnection() {
    logCommunicationEvent("Handling disconnection");
    laptopConnected = false;
    consecutiveTimeouts = 0;
    setState(COMM_WAITING_LAPTOP);
}

void Communication::reset() {
    logCommunicationEvent("Resetting communication system");
    laptopConnected = false;
    consecutiveTimeouts = 0;
    cleanupImageTransmission();
    setState(COMM_WAITING_LAPTOP);
}

void Communication::setState(CommunicationState newState) {
    if (currentState != newState) {
        logCommunicationEvent("State change", 
                             stateToString(currentState) + " -> " + stateToString(newState));
        currentState = newState;
        lastMessageTime = millis();
    }
}

// Helper functions
String stateToString(CommunicationState state) {
    switch (state) {
        case COMM_INIT: return "INIT";
        case COMM_WAITING_LAPTOP: return "WAITING_LAPTOP";
        case COMM_CONNECTED: return "CONNECTED";
        case COMM_SENDING_IMAGE: return "SENDING_IMAGE";
        case COMM_WAITING_RESULT: return "WAITING_RESULT";
        case COMM_ERROR: return "ERROR";
        default: return "UNKNOWN";
    }
}

void logCommunicationEvent(const String& event, const String& details) {
    String message = "[COMM] " + event;
    if (details.length() > 0) {
        message += " - " + details;
    }
    logMessage(message);
}
