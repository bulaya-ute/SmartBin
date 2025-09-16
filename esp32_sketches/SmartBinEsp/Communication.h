#ifndef COMMUNICATION_H
#define COMMUNICATION_H

#include <Arduino.h>
#include <BluetoothSerial.h>
#include "mbedtls/base64.h"
#include "Logger.h"

// Communication states
enum CommunicationState {
    COMM_INIT,
    COMM_WAITING_LAPTOP,
    COMM_CONNECTED,
    COMM_SENDING_IMAGE,
    COMM_WAITING_RESULT,
    COMM_ERROR
};

// Protocol message codes (5 characters + space + content)
#define CODE_RTC00 "RTC00"  // ESP32 ready to connect
#define CODE_RTC01 "RTC01"  // Laptop ready to connect
#define CODE_RTC02 "RTC02"  // Connection established
#define CODE_PA000 "PA000"  // Image metadata header
#define CODE_PA_PREFIX "PA"  // Prefix for PA001, PA002, etc.
#define CODE_PX_PREFIX "PX"  // Prefix for PX### (final chunk)
#define CODE_CLS01 "CLS01"  // Classification result
#define CODE_ERR_PREFIX "ERR" // Error codes

// Error codes
#define ERR_TIMEOUT "01"
#define ERR_DECODE_FAILED "02"
#define ERR_INVALID_FORMAT "03"
#define ERR_CLASSIFICATION_FAILED "04"
#define ERR_IMAGE_CAPTURE_FAILED "05"
#define ERR_DISCONNECTED "06"

// Timing constants
#define LAPTOP_RESPONSE_TIMEOUT_MS 10000  // 10 seconds
#define WAITING_BROADCAST_INTERVAL_MS 3000 // 3 seconds
#define MAX_CONSECUTIVE_TIMEOUTS 3
#define MAX_IMAGE_PARTS 999

// Communication class
class Communication {
private:
    BluetoothSerial* bluetooth;
    CommunicationState currentState;
    unsigned long lastMessageTime;
    unsigned long lastBroadcastTime;
    int consecutiveTimeouts;
    bool laptopConnected;
    
    // Image transmission state
    String currentImageId;
    int totalImageParts;
    String* imageParts;
    bool imageTransmissionComplete;
    
    // Message handling
    bool sendProtocolMessage(const String& code, const String& content = "");
    bool receiveProtocolMessage(String& code, String& content);
    bool isProtocolMessage(const String& line);
    String extractCode(const String& line);
    String extractContent(const String& line);
    
    // State machine functions
    void handleWaitingLaptopState();
    void handleConnectedState();
    void handleWaitingResultState();
    void handleErrorState();
    
    // Image transmission helpers
    bool prepareImageTransmission(const uint8_t* imageData, size_t imageSize, 
                                int width, int height);
    void cleanupImageTransmission();
    
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
