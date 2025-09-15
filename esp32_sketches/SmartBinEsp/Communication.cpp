#include "Communication.h"
#include <Arduino.h>

Communication::Communication(BluetoothSerial* bt) : 
    bluetooth(bt),
    currentState(COMM_INIT),
    lastMessageTime(0),
    lastHeartbeatTime(0),
    lastBroadcastTime(0),
    consecutiveTimeouts(0),
    currentImageId(""),
    laptopConnected(false) {
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
    
    // Check for incoming messages
    String messageType;
    DynamicJsonDocument data(1024);
    
    if (receiveMessage(messageType, data)) {
        if (messageType == MSG_LAPTOP_READY) {
            logCommunicationEvent("Laptop ready signal received");
            laptopConnected = true;
            setState(COMM_CONNECTED);
            
            // Send confirmation
            DynamicJsonDocument response(512);
            response["device_id"] = "SmartBin_ESP32";
            response["status"] = "connected";
            sendMessage("CONNECTION_CONFIRMED", response);
            return;
        }
    }
    
    // Broadcast waiting message periodically
    if (now - lastBroadcastTime > WAITING_BROADCAST_INTERVAL_MS) {
        DynamicJsonDocument waitingData(512);
        waitingData["device_id"] = "SmartBin_ESP32";
        waitingData["version"] = "1.0";
        JsonArray capabilities = waitingData.createNestedArray("capabilities");
        capabilities.add("image_capture");
        capabilities.add("classification");
        
        if (sendMessage(MSG_WAITING_LAPTOP, waitingData)) {
            logCommunicationEvent("Broadcasting laptop connection request");
            lastBroadcastTime = now;
        }
    }
}

void Communication::handleConnectedState() {
    // Check for heartbeats or disconnection
    String messageType;
    DynamicJsonDocument data(512);
    
    if (receiveMessage(messageType, data)) {
        if (messageType == MSG_HEARTBEAT) {
            lastHeartbeatTime = millis();
            logCommunicationEvent("Heartbeat received from laptop");
        }
    }
    
    // Check for heartbeat timeout
    unsigned long now = millis();
    if (laptopConnected && (now - lastHeartbeatTime) > (HEARTBEAT_INTERVAL_MS * 2)) {
        logCommunicationEvent("Heartbeat timeout - laptop may be disconnected");
        handleDisconnection();
    }
}

void Communication::handleWaitingResultState() {
    String messageType;
    DynamicJsonDocument data(1024);
    
    if (receiveMessage(messageType, data)) {
        if (messageType == MSG_CLASSIFICATION_RESULT) {
            logCommunicationEvent("Classification result received", 
                                data["classification"].as<String>());
            setState(COMM_CONNECTED);
            consecutiveTimeouts = 0;
            
        } else if (messageType == MSG_CLASSIFICATION_ERROR) {
            String errorCode = data["error_code"];
            logCommunicationEvent("Classification error received", errorCode);
            
            if (data["retry_suggested"].as<bool>()) {
                setState(COMM_CONNECTED); // Will retry
            } else {
                setState(COMM_ERROR);
            }
            consecutiveTimeouts = 0;
        }
    }
}

void Communication::handleErrorState() {
    logCommunicationEvent("In error state - attempting recovery");
    delay(5000); // Wait before retry
    reset();
}

bool Communication::sendMessage(const String& messageType, const JsonDocument& data) {
    if (!bluetooth || !bluetooth->connected()) {
        return false;
    }
    
    DynamicJsonDocument message(2048);
    message["type"] = messageType;
    message["timestamp"] = millis();
    message["data"] = data;
    
    String messageStr;
    serializeJson(message, messageStr);
    
    // Send with delimiters for parsing
    bluetooth->println("===MSG_START===");
    bluetooth->println(messageStr);
    bluetooth->println("===MSG_END===");
    
    lastMessageTime = millis();
    return true;
}

bool Communication::receiveMessage(String& messageType, JsonDocument& data) {
    if (!bluetooth || !bluetooth->available()) {
        return false;
    }
    
    String line;
    bool inMessage = false;
    String messageBuffer = "";
    
    while (bluetooth->available()) {
        char c = bluetooth->read();
        if (c == '\n') {
            line.trim();
            
            if (line == "===MSG_START===") {
                inMessage = true;
                messageBuffer = "";
            } else if (line == "===MSG_END===") {
                if (inMessage) {
                    // Parse the message
                    DynamicJsonDocument message(2048);
                    DeserializationError error = deserializeJson(message, messageBuffer);
                    
                    if (!error) {
                        messageType = message["type"].as<String>();
                        data = message["data"];
                        return true;
                    }
                }
                inMessage = false;
            } else if (inMessage) {
                messageBuffer += line + "\n";
            }
            line = "";
        } else {
            line += c;
        }
    }
    
    return false;
}

bool Communication::sendImageForClassification(const uint8_t* imageData, size_t imageSize, 
                                             int width, int height, String& result) {
    if (currentState != COMM_CONNECTED) {
        return false;
    }
    
    setState(COMM_SENDING_IMAGE);
    currentImageId = generateImageId();
    
    // Convert image to Base64
    logCommunicationEvent("Converting image to Base64", 
                         "Size: " + String(imageSize) + " bytes");
    
    // Calculate Base64 size
    size_t base64_len = 0;
    int ret = mbedtls_base64_encode(NULL, 0, &base64_len, imageData, imageSize);
    if (ret != MBEDTLS_ERR_BASE64_BUFFER_TOO_SMALL) {
        logCommunicationEvent("Failed to calculate Base64 size");
        setState(COMM_ERROR);
        return false;
    }
    
    // Encode to Base64
    char* base64_buffer = (char*)malloc(base64_len + 1);
    if (!base64_buffer) {
        logCommunicationEvent("Failed to allocate Base64 buffer");
        setState(COMM_ERROR);
        return false;
    }
    
    ret = mbedtls_base64_encode((unsigned char*)base64_buffer, base64_len, 
                               &base64_len, imageData, imageSize);
    if (ret != 0) {
        free(base64_buffer);
        logCommunicationEvent("Base64 encoding failed");
        setState(COMM_ERROR);
        return false;
    }
    
    base64_buffer[base64_len] = '\0';
    
    // Create image data message
    DynamicJsonDocument imageMsg(base64_len + 1024);
    imageMsg["image_id"] = currentImageId;
    imageMsg["format"] = "JPEG";
    imageMsg["size"] = imageSize;
    imageMsg["width"] = width;
    imageMsg["height"] = height;
    imageMsg["base64_data"] = String(base64_buffer);
    
    free(base64_buffer);
    
    logCommunicationEvent("Sending image for classification", currentImageId);
    
    if (sendMessage(MSG_IMAGE_DATA, imageMsg)) {
        setState(COMM_WAITING_RESULT);
        return true;
    } else {
        setState(COMM_ERROR);
        return false;
    }
}

bool Communication::waitForLaptopConnection() {
    setState(COMM_WAITING_LAPTOP);
    
    unsigned long startTime = millis();
    const unsigned long maxWaitTime = 60000; // 1 minute max wait
    
    while (currentState == COMM_WAITING_LAPTOP && 
           (millis() - startTime) < maxWaitTime) {
        update();
        delay(100);
        yield();
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
    currentImageId = "";
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

String Communication::generateImageId() {
    return "img_" + String(millis());
}

bool Communication::sendStatusUpdate(const String& status) {
    DynamicJsonDocument statusData(512);
    statusData["status"] = status;
    statusData["last_image_id"] = currentImageId;
    statusData["uptime_ms"] = millis();
    
    return sendMessage(MSG_STATUS_UPDATE, statusData);
}

// Helper functions
String stateToString(CommunicationState state) {
    switch (state) {
        case COMM_INIT: return "INIT";
        case COMM_WAITING_LAPTOP: return "WAITING_LAPTOP";
        case COMM_CONNECTED: return "CONNECTED";
        case COMM_CAPTURING: return "CAPTURING";
        case COMM_SENDING_IMAGE: return "SENDING_IMAGE";
        case COMM_WAITING_RESULT: return "WAITING_RESULT";
        case COMM_PROCESSING_RESULT: return "PROCESSING_RESULT";
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
