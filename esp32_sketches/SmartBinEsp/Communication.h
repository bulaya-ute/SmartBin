#ifndef COMMUNICATION_H
#define COMMUNICATION_H

#include <Arduino.h>
#include <ArduinoJson.h>
#include <BluetoothSerial.h>
#include "mbedtls/base64.h"
#include "Logger.h"

// Communication states
enum CommunicationState {
    COMM_INIT,
    COMM_WAITING_LAPTOP,
    COMM_CONNECTED,
    COMM_CAPTURING,
    COMM_SENDING_IMAGE,
    COMM_WAITING_RESULT,
    COMM_PROCESSING_RESULT,
    COMM_ERROR
};

// Message types
#define MSG_WAITING_LAPTOP "WAITING_LAPTOP"
#define MSG_LAPTOP_READY "LAPTOP_READY"
#define MSG_IMAGE_DATA "IMAGE_DATA"
#define MSG_CLASSIFICATION_RESULT "CLASSIFICATION_RESULT"
#define MSG_CLASSIFICATION_ERROR "CLASSIFICATION_ERROR"
#define MSG_STATUS_UPDATE "STATUS_UPDATE"
#define MSG_HEARTBEAT "HEARTBEAT"

// Error codes
#define ERR_DECODE_FAILED "DECODE_FAILED"
#define ERR_INVALID_FORMAT "INVALID_FORMAT"
#define ERR_CLASSIFICATION_FAILED "CLASSIFICATION_FAILED"
#define ERR_TIMEOUT "TIMEOUT"
#define ERR_DISCONNECTED "DISCONNECTED"

// Timing constants
#define LAPTOP_RESPONSE_TIMEOUT_MS 10000  // 10 seconds
#define HEARTBEAT_INTERVAL_MS 30000       // 30 seconds
#define WAITING_BROADCAST_INTERVAL_MS 3000 // 3 seconds
#define MAX_CONSECUTIVE_TIMEOUTS 3

// Communication class
class Communication {
private:
    BluetoothSerial* bluetooth;
    CommunicationState currentState;
    unsigned long lastMessageTime;
    unsigned long lastHeartbeatTime;
    unsigned long lastBroadcastTime;
    int consecutiveTimeouts;
    String currentImageId;
    bool laptopConnected;
    
    // Message handling
    bool sendMessage(const String& messageType, const JsonDocument& data);
    bool receiveMessage(String& messageType, JsonDocument& data);
    String generateImageId();
    
    // State machine functions
    void handleWaitingLaptopState();
    void handleConnectedState();
    void handleWaitingResultState();
    void handleErrorState();
    
public:
    Communication(BluetoothSerial* bt);
    
    // Initialization and main loop
    void begin();
    void update();
    
    // State management
    CommunicationState getState() const { return currentState; }
    bool isLaptopConnected() const { return laptopConnected; }
    void setState(CommunicationState newState);
    
    // Communication functions
    bool waitForLaptopConnection();
    bool sendImageForClassification(const uint8_t* imageData, size_t imageSize, 
                                   int width, int height, String& result);
    bool sendStatusUpdate(const String& status);
    
    // Error handling
    void handleTimeout();
    void handleDisconnection();
    void reset();
};

// Global communication instance
extern Communication comm;

// Helper functions
String stateToString(CommunicationState state);
void logCommunicationEvent(const String& event, const String& details = "");

#endif // COMMUNICATION_H
