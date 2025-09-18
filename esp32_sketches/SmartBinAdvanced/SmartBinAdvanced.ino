/*
  SmartBin ESP32 Advanced Control System
  
  Features:
  - Command protocol implementation (lid, coin, buzzer)
  - PCF8575 I2C I/O expander integration
  - Buzzer control on PCF8575 P3
  - Servo control for lid and coin dispenser
  - Multi-tone startup sequence
  - Sound feedback for different states
  
  Hardware:
  - ESP32-CAM
  - PCF8575 I2C I/O expander
  - Buzzer on PCF8575 P3
  - Servo motors for lid and coin dispenser
  - LEDs for status indication
*/

#include "BluetoothSerial.h"
#include <Wire.h>
// #include <ESP32Servo.h>  // Commented out - no servos connected
#include <ArduinoJson.h>

// PCF8575 I2C address
#define PCF8575_ADDRESS 0x20

// Buzzer pin on PCF8575 (P3)
#define BUZZER_PIN 3

// Servo pins (commented out - no servos connected)
// #define LID_SERVO_PIN 12
// #define COIN_SERVO_PIN 13

// LED pins on PCF8575
#define LED_RED_PIN 0
#define LED_GREEN_PIN 1
#define LED_BLUE_PIN 2

// System states
enum SystemState {
  STATE_STARTUP,
  STATE_READY,
  STATE_ITEM_DETECTED,
  STATE_PROCESSING,
  STATE_SORTING,
  STATE_COMPLETE,
  STATE_ERROR
};

// Buzzer tone definitions
struct BuzzerTone {
  int frequency;
  int duration;
};

// Function prototypes
void initPCF8575();
void writePCF8575(uint16_t data);
uint16_t readPCF8575();
void setBuzzer(bool state);
void playTone(int frequency, int duration);
void playToneSequence(BuzzerTone* tones, int count);
void performStartupSequence();
void changeState(SystemState newState);
void handleSystemStates();
void handleImageRequest();
void sendResponse(String id, String status);
void handleLidCommand(String params);
void handleCoinCommand(String params);
void handleBuzzerCommand(String params);
void openLid();
void closeLid();
void dispenseCoin(int count);
void testCoinDispenser();
void sendCoinStatus();

// Hardware components
BluetoothSerial SerialBT;
// Servo lidServo;    // Commented out - no servos connected
// Servo coinServo;   // Commented out - no servos connected

// System variables
SystemState currentState = STATE_STARTUP;
bool lidOpen = false;
bool autoLidMode = true;
int coinCount = 10;  // Initial coin count
unsigned long lastHeartbeat = 0;
unsigned long stateChangeTime = 0;

// PCF8575 state
uint16_t pcfState = 0xFFFF;  // All pins high initially

// Tone sequences
BuzzerTone startupTones[] = {
  {440, 200},   // A4 - Low tone
  {523, 200},   // C5 - Medium tone  
  {659, 200}    // E5 - High tone
};

BuzzerTone detectedTone[] = {
  {1000, 100},  // Quick beep
  {0, 50},      // Pause
  {1000, 100}   // Quick beep
};

BuzzerTone completeTone[] = {
  {523, 150},   // C5
  {659, 150},   // E5
  {784, 300}    // G5 - Success melody
};

BuzzerTone errorTone[] = {
  {200, 200},   // Low error tone
  {0, 100},     // Pause
  {200, 200},   // Repeat
  {0, 100},
  {200, 200}
};

void setup() {
  Serial.begin(115200);
  Serial.println("🚀 SmartBin ESP32 Advanced Control System Starting...");
  
  // Initialize I2C
  Wire.begin();
  
  // Initialize ESP32Servo library (commented out - no servos connected)
  // ESP32PWM::allocateTimer(0);
  // ESP32PWM::allocateTimer(1);
  // ESP32PWM::allocateTimer(2);
  // ESP32PWM::allocateTimer(3);
  
  // Initialize servos (commented out - no servos connected)
  // lidServo.setPeriodHertz(50);    // standard 50 hz servo
  // coinServo.setPeriodHertz(50);   // standard 50 hz servo
  // lidServo.attach(LID_SERVO_PIN, 1000, 2000);   // 1ms-2ms pulse width
  // coinServo.attach(COIN_SERVO_PIN, 1000, 2000); // 1ms-2ms pulse width
  
  // Set initial servo positions (commented out - no servos connected)
  // lidServo.write(0);    // Lid closed
  // coinServo.write(90);  // Coin dispenser ready
  
  // Initialize PCF8575
  initPCF8575();
  
  // Initialize Bluetooth
  SerialBT.begin("SmartBin_Advanced");
  Serial.println("📶 Bluetooth initialized: SmartBin_Advanced");
  
  // Startup sequence
  performStartupSequence();
  
  // Set ready state
  changeState(STATE_READY);
  
  Serial.println("✅ System initialization complete");
  Serial.println("💡 Waiting for commands...");
}

void loop() {
  // Handle Bluetooth commands
  handleBluetoothCommands();
  
  // System state management
  handleSystemStates();
  
  // Periodic heartbeat
  if (millis() - lastHeartbeat > 30000) {  // 30 seconds
    sendHeartbeat();
    lastHeartbeat = millis();
  }
  
  delay(50);  // Small delay for stability
}

void initPCF8575() {
  // Set all pins high initially (PCF8575 is active low for most operations)
  writePCF8575(pcfState);
  Serial.println("🔧 PCF8575 initialized");
}

void writePCF8575(uint16_t data) {
  Wire.beginTransmission(PCF8575_ADDRESS);
  Wire.write(data & 0xFF);        // Low byte
  Wire.write((data >> 8) & 0xFF); // High byte
  Wire.endTransmission();
  pcfState = data;
}

void setBuzzer(bool state) {
  if (state) {
    pcfState &= ~(1 << BUZZER_PIN);  // Clear bit (active low)
  } else {
    pcfState |= (1 << BUZZER_PIN);   // Set bit (inactive high)
  }
  writePCF8575(pcfState);
}

void setLED(int pin, bool state) {
  if (state) {
    pcfState &= ~(1 << pin);  // Clear bit (LED on)
  } else {
    pcfState |= (1 << pin);   // Set bit (LED off)
  }
  writePCF8575(pcfState);
}

void playTone(int frequency, int duration) {
  if (frequency > 0) {
    // Generate tone using buzzer
    int period = 1000000 / frequency;  // Period in microseconds
    int cycles = (duration * 1000) / period;
    
    for (int i = 0; i < cycles; i++) {
      setBuzzer(true);
      delayMicroseconds(period / 2);
      setBuzzer(false);
      delayMicroseconds(period / 2);
    }
  } else {
    // Silence
    setBuzzer(false);
    delay(duration);
  }
}

void playToneSequence(BuzzerTone* tones, int count) {
  for (int i = 0; i < count; i++) {
    playTone(tones[i].frequency, tones[i].duration);
    if (i < count - 1) {
      delay(50);  // Small gap between tones
    }
  }
}

void performStartupSequence() {
  Serial.println("🎵 Playing startup sequence...");
  
  // Synchronized LED and buzzer startup
  for (int i = 0; i < 3; i++) {
    // Turn on LED based on sequence
    setLED(LED_RED_PIN, i == 0);
    setLED(LED_GREEN_PIN, i == 1);
    setLED(LED_BLUE_PIN, i == 2);
    
    // Play corresponding tone
    playTone(startupTones[i].frequency, startupTones[i].duration);
    
    delay(100);  // Brief pause between steps
  }
  
  // All LEDs off after startup
  setLED(LED_RED_PIN, false);
  setLED(LED_GREEN_PIN, false);
  setLED(LED_BLUE_PIN, false);
}

void changeState(SystemState newState) {
  if (currentState != newState) {
    Serial.printf("🔄 State change: %d -> %d\n", currentState, newState);
    currentState = newState;
    stateChangeTime = millis();
    
    // Handle state-specific actions
    switch (newState) {
      case STATE_READY:
        setLED(LED_GREEN_PIN, true);
        setLED(LED_RED_PIN, false);
        setLED(LED_BLUE_PIN, false);
        break;
        
      case STATE_ITEM_DETECTED:
        setLED(LED_BLUE_PIN, true);
        setLED(LED_GREEN_PIN, false);
        playToneSequence(detectedTone, 2);
        break;
        
      case STATE_PROCESSING:
        // Blinking blue during processing
        setLED(LED_BLUE_PIN, true);
        break;
        
      case STATE_COMPLETE:
        setLED(LED_GREEN_PIN, true);
        setLED(LED_BLUE_PIN, false);
        playToneSequence(completeTone, 3);
        break;
        
      case STATE_ERROR:
        setLED(LED_RED_PIN, true);
        setLED(LED_GREEN_PIN, false);
        setLED(LED_BLUE_PIN, false);
        playToneSequence(errorTone, 5);
        break;
    }
  }
}

void handleBluetoothCommands() {
  if (SerialBT.available()) {
    String command = SerialBT.readStringUntil('\n');
    command.trim();
    
    Serial.printf("📨 Received command: %s\n", command.c_str());
    
    // Parse and execute command
    executeCommand(command);
  }
}

void executeCommand(String command) {
  // Parse command components
  int spaceIndex = command.indexOf(' ');
  String cmdCode = command.substring(0, spaceIndex > 0 ? spaceIndex : command.length());
  String cmdData = spaceIndex > 0 ? command.substring(spaceIndex + 1) : "";
  
  // Execute based on command code
  if (cmdCode == "LID00") {
    handleLidCommand(cmdData);
  } else if (cmdCode == "COIN0") {
    handleCoinCommand(cmdData);
  } else if (cmdCode == "BUZZ0") {
    handleBuzzerCommand(cmdData);
  } else if (cmdCode == "RTC00") {
    handleHeartbeat();
  } else if (cmdCode == "STA01") {
    sendSystemStatus();
  } else if (cmdCode == "IMG01") {
    handleImageRequest();
  } else {
    sendResponse("ERROR", "Unknown command: " + cmdCode);
  }
}

void handleLidCommand(String params) {
  if (params == "open") {
    openLid();
    sendResponse("LID00", "opened");
  } else if (params == "close") {
    closeLid();
    sendResponse("LID00", "closed");
  } else if (params == "status") {
    sendResponse("LID00", lidOpen ? "open" : "closed");
  } else if (params == "auto") {
    autoLidMode = true;
    sendResponse("LID00", "auto_mode_enabled");
  } else if (params == "manual") {
    autoLidMode = false;
    sendResponse("LID00", "manual_mode_enabled");
  } else {
    sendResponse("ERROR", "Invalid lid command: " + params);
  }
}

void handleCoinCommand(String params) {
  if (params == "dispense") {
    dispenseCoin(1);
  } else if (params.startsWith("dispense --count ")) {
    int count = params.substring(17).toInt();
    dispenseCoin(count);
  } else if (params == "status") {
    sendCoinStatus();
  } else if (params == "test") {
    testCoinDispenser();
  } else if (params.startsWith("refill --count ")) {
    int count = params.substring(15).toInt();
    coinCount = count;
    sendResponse("COIN0", "refilled to " + String(count));
  } else {
    sendResponse("ERROR", "Invalid coin command: " + params);
  }
}

void handleBuzzerCommand(String params) {
  if (params == "startup") {
    playToneSequence(startupTones, 3);
    sendResponse("BUZZ0", "startup_sound_played");
  } else if (params == "detected") {
    playToneSequence(detectedTone, 2);
    sendResponse("BUZZ0", "detection_sound_played");
  } else if (params == "complete") {
    playToneSequence(completeTone, 3);
    sendResponse("BUZZ0", "completion_sound_played");
  } else if (params == "error") {
    playToneSequence(errorTone, 5);
    sendResponse("BUZZ0", "error_sound_played");
  } else if (params == "off") {
    setBuzzer(false);
    sendResponse("BUZZ0", "buzzer_off");
  } else {
    sendResponse("ERROR", "Invalid buzzer command: " + params);
  }
}

void openLid() {
  Serial.println("🔓 [SIMULATED] Opening lid... (no servo connected)");
  // lidServo.write(90);  // Open position - commented out, no servo connected
  lidOpen = true;
  delay(100);  // Reduced delay since no actual servo movement
}

void closeLid() {
  Serial.println("🔒 [SIMULATED] Closing lid... (no servo connected)");
  // lidServo.write(0);   // Closed position - commented out, no servo connected
  lidOpen = false;
  delay(100);  // Reduced delay since no actual servo movement
}

void dispenseCoin(int count) {
  if (coinCount >= count) {
    Serial.printf("🪙 [SIMULATED] Dispensing %d coin(s)... (no servo connected)\n", count);
    
    for (int i = 0; i < count; i++) {
      // Coin dispenser mechanism (simulated)
      // coinServo.write(45);   // Dispense position - commented out, no servo connected
      delay(100);  // Reduced delay
      // coinServo.write(90);   // Return position - commented out, no servo connected
      delay(100);  // Reduced delay
      
      coinCount--;
    }
    
    sendResponse("COIN0", "dispensed " + String(count) + " coins, remaining: " + String(coinCount));
    
    // Play completion sound
    playToneSequence(completeTone, 3);
  } else {
    sendResponse("ERROR", "Insufficient coins: " + String(coinCount) + " available, " + String(count) + " requested");
    playToneSequence(errorTone, 5);
  }
}

void testCoinDispenser() {
  Serial.println("🔧 [SIMULATED] Testing coin dispenser... (no servo connected)");
  
  // Test movement without dispensing (simulated)
  // coinServo.write(45);  // commented out, no servo connected
  delay(100);  // Reduced delay
  // coinServo.write(90);  // commented out, no servo connected
  delay(100);  // Reduced delay
  
  sendResponse("COIN0", "dispenser_test_complete");
}

void sendCoinStatus() {
  DynamicJsonDocument doc(200);
  doc["command"] = "COIN0";
  doc["status"] = "ok";
  doc["remaining_coins"] = coinCount;
  doc["dispenser_ready"] = true;
  
  String response;
  serializeJson(doc, response);
  SerialBT.println(response);
}

void handleSystemStates() {
  // Automatic state transitions and behaviors
  switch (currentState) {
    case STATE_PROCESSING:
      // Blink blue LED during processing
      if ((millis() - stateChangeTime) % 500 < 250) {
        setLED(LED_BLUE_PIN, true);
      } else {
        setLED(LED_BLUE_PIN, false);
      }
      break;
      
    case STATE_COMPLETE:
      // Auto-return to ready after 3 seconds
      if (millis() - stateChangeTime > 3000) {
        changeState(STATE_READY);
      }
      break;
      
    case STATE_ERROR:
      // Blink red LED during error
      if ((millis() - stateChangeTime) % 1000 < 500) {
        setLED(LED_RED_PIN, true);
      } else {
        setLED(LED_RED_PIN, false);
      }
      break;
  }
}

void handleHeartbeat() {
  sendResponse("RTC00", "heartbeat_ok");
  lastHeartbeat = millis();
}

void handleImageRequest() {
  // Trigger item detection state
  changeState(STATE_ITEM_DETECTED);
  
  // Auto-open lid if in auto mode
  if (autoLidMode && !lidOpen) {
    openLid();
  }
  
  // Simulate image capture (actual implementation would capture from camera)
  delay(100);
  changeState(STATE_PROCESSING);
  
  sendResponse("IMG01", "image_capture_initiated");
}

void sendSystemStatus() {
  DynamicJsonDocument doc(400);
  doc["command"] = "STA01";
  doc["state"] = currentState;
  doc["lid_open"] = lidOpen;
  doc["auto_lid_mode"] = autoLidMode;
  doc["coin_count"] = coinCount;
  doc["uptime"] = millis();
  doc["free_memory"] = ESP.getFreeHeap();
  
  String response;
  serializeJson(doc, response);
  SerialBT.println(response);
}

void sendHeartbeat() {
  DynamicJsonDocument doc(150);
  doc["command"] = "HEARTBEAT";
  doc["uptime"] = millis();
  doc["state"] = currentState;
  doc["timestamp"] = millis();
  
  String response;
  serializeJson(doc, response);
  SerialBT.println(response);
}

void sendResponse(String command, String message) {
  DynamicJsonDocument doc(200);
  doc["command"] = command;
  doc["response"] = message;
  doc["timestamp"] = millis();
  
  String response;
  serializeJson(doc, response);
  SerialBT.println(response);
  
  Serial.printf("📤 Sent: %s\n", response.c_str());
}
