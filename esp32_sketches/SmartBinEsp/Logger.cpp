#include "Logger.h"
#include <Arduino.h>
#include "BluetoothSerial.h"

// External reference to the Bluetooth Serial object from main file
extern BluetoothSerial SerialBT;

// Logger state variables
static bool loggerInitialized = false;
static bool bluetoothLoggingEnabled = false;
static bool serialLoggingEnabled = true;  // Serial always available
static String deviceName = "SmartBin_ESP32";

// Logger statistics
static unsigned long totalMessagesLogged = 0;
static unsigned long bluetoothMessagesLogged = 0;
static unsigned long serialMessagesLogged = 0;

// Message chunking configuration
static const size_t MAX_BLUETOOTH_CHUNK_SIZE = 240;  // Safe size for Bluetooth Serial (ESP32 limit ~250)
static const size_t MAX_SERIAL_CHUNK_SIZE = 512;     // Serial can handle larger chunks

bool initLogger(const String& btDeviceName) {
    // Use Serial directly during initialization to avoid recursion
    Serial.println("[System] Initializing Logger module...");
    
    // Store device name
    deviceName = btDeviceName;
    
    // Serial is always available
    serialLoggingEnabled = true;
    
    // Initialize Bluetooth Serial
    bluetoothLoggingEnabled = SerialBT.begin(deviceName);
    
    if (bluetoothLoggingEnabled) {
        loggerInitialized = true;
        LOG_SYSTEM("✅ Logger initialized successfully");
        LOG_SYSTEM("Serial logging: ENABLED");
        LOG_SYSTEM("Bluetooth logging: ENABLED (Device: " + deviceName + ")");
        return true;
    } else {
        loggerInitialized = true;  // Still functional with Serial only
        LOG_WARNING("Logger initialized with Serial only - Bluetooth failed");
        LOG_SYSTEM("Serial logging: ENABLED");
        LOG_SYSTEM("Bluetooth logging: DISABLED");
        return false;  // Indicate partial failure
    }
}

void deinitLogger() {
    if (!loggerInitialized) {
        return;
    }
    
    LOG_SYSTEM("Deinitializing Logger module...");
    printLoggerStats();
    
    if (bluetoothLoggingEnabled) {
        SerialBT.end();
        bluetoothLoggingEnabled = false;
    }
    
    loggerInitialized = false;
    LOG_SYSTEM("Logger deinitialized");
}

void logMessage(const String& message) {
    if (!loggerInitialized) {
        // Fallback to Serial only if logger not initialized
        Serial.println(message);
        return;
    }
    
    // Check if message needs chunking
    if (message.length() > MAX_BLUETOOTH_CHUNK_SIZE && bluetoothLoggingEnabled) {
        logLongMessage(message);
        return;
    }
    
    // Always log to Serial (primary output)
    if (serialLoggingEnabled) {
        Serial.println(message);
        serialMessagesLogged++;
    }
    
    // Log to Bluetooth if available and enabled
    if (bluetoothLoggingEnabled && SerialBT.hasClient()) {
        SerialBT.println(message);
        bluetoothMessagesLogged++;
    }
    
    totalMessagesLogged++;
}

void logLongMessage(const String& message, const String& prefix) {
    if (!loggerInitialized) {
        Serial.println(message);
        return;
    }
    
    // Always send full message to Serial (can handle large messages)
    if (serialLoggingEnabled) {
        Serial.println(message);
        serialMessagesLogged++;
    }
    
    // Chunk message for Bluetooth transmission
    if (bluetoothLoggingEnabled && SerialBT.hasClient()) {
        size_t messageLength = message.length();
        size_t chunkSize = MAX_BLUETOOTH_CHUNK_SIZE;
        size_t totalChunks = (messageLength + chunkSize - 1) / chunkSize;  // Ceiling division
        
        for (size_t i = 0; i < totalChunks; i++) {
            size_t startPos = i * chunkSize;
            size_t endPos = min(startPos + chunkSize, messageLength);
            
            String chunk = message.substring(startPos, endPos);
            String chunkMessage = prefix + "[" + String(i + 1) + "/" + String(totalChunks) + "] " + chunk;
            
            SerialBT.println(chunkMessage);
            bluetoothMessagesLogged++;
            
            // Small delay between chunks to prevent Bluetooth buffer overflow
            delay(10);
        }
    }
    
    totalMessagesLogged++;
}

void logMessageNoNewline(const String& message) {
    if (!loggerInitialized) {
        Serial.print(message);
        return;
    }
    
    if (serialLoggingEnabled) {
        Serial.print(message);
    }
    
    if (bluetoothLoggingEnabled && SerialBT.hasClient()) {
        SerialBT.print(message);
    }
}

bool isLoggerInitialized() {
    return loggerInitialized;
}

bool isBluetoothLoggingEnabled() {
    return bluetoothLoggingEnabled && SerialBT.hasClient();
}

bool isSerialLoggingEnabled() {
    return serialLoggingEnabled;
}

void setBluetoothLogging(bool enabled) {
    if (loggerInitialized && SerialBT.hasClient()) {
        bluetoothLoggingEnabled = enabled;
        LOG_SYSTEM("Bluetooth logging " + String(enabled ? "ENABLED" : "DISABLED"));
    }
}

void setSerialLogging(bool enabled) {
    serialLoggingEnabled = enabled;
    // Note: We can't use LOG_SYSTEM here as it might cause recursion
    if (serialLoggingEnabled) {
        Serial.println("[Logger] Serial logging ENABLED");
    }
}

String getDeviceName() {
    return deviceName;
}

void printLoggerStatus() {
    LOG_SYSTEM("=== LOGGER STATUS ===");
    logMessage("[Logger] Initialized: " + String(loggerInitialized ? "YES" : "NO"));
    logMessage("[Logger] Device Name: " + deviceName);
    logMessage("[Logger] Serial Logging: " + String(serialLoggingEnabled ? "ENABLED" : "DISABLED"));
    logMessage("[Logger] Bluetooth Logging: " + String(bluetoothLoggingEnabled ? "ENABLED" : "DISABLED"));
    logMessage("[Logger] Bluetooth Client Connected: " + String(SerialBT.hasClient() ? "YES" : "NO"));
    LOG_SYSTEM("====================");
}

void printLoggerStats() {
    LOG_SYSTEM("=== LOGGER STATISTICS ===");
    logMessage("[Logger] Total messages logged: " + String(totalMessagesLogged));
    logMessage("[Logger] Serial messages: " + String(serialMessagesLogged));
    logMessage("[Logger] Bluetooth messages: " + String(bluetoothMessagesLogged));
    LOG_SYSTEM("=========================");
}

void resetLoggerStats() {
    totalMessagesLogged = 0;
    bluetoothMessagesLogged = 0;
    serialMessagesLogged = 0;
    LOG_SYSTEM("Logger statistics reset");
}
