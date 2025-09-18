/*
  SmartBin ESP32 Buzzer Test - With Servo Control
  
  Features:
  - Basic command protocol (buzzer + servo)
  - PCF8575 I2C I/O expander integration
  - Buzzer control on PCF8575 P3
  - Servo motor control on GPIO16
  - Classification-based servo positioning
  - Simple Bluetooth communication
  
  Hardware:
  - ESP32-CAM or ESP32 dev board
  - PCF8575 I2C I/O expander
  - Buzzer on PCF8575 P3
  - Servo motor on GPIO16
*/

#include "BluetoothSerial.h"
#include <Wire.h>
#include <ArduinoJson.h>
#include <ESP32Servo.h>

// PCF8575 I2C address
#define PCF8575_ADDRESS 0x20

// Buzzer pin on PCF8575 (P3)
#define BUZZER_PIN 3

// Servo pin
#define SERVO_PIN 16

// Hardware components
BluetoothSerial SerialBT;
Servo sortingServo;

// System variables
uint16_t pcfState = 0xFFFF;  // All pins high initially

// Function prototypes
void initPCF8575();
void writePCF8575(uint16_t data);
void setBuzzer(bool state);
void playTone(int frequency, int duration);
void performStartupSequence();
void sendResponse(String id, String status);
void parseAndExecuteCommand(String command);
void initServo();
void moveServoForClassification(String classification);

void setup() {
  Serial.begin(115200);
  Serial.println("🚀 SmartBin ESP32 Buzzer + Servo Test Starting...");
  
  // Initialize I2C
  Wire.begin();
  
  // Initialize PCF8575
  initPCF8575();
  
  // Initialize servo
  initServo();
  
  // Initialize Bluetooth
  SerialBT.begin("SmartBin_Servo_Test");
  Serial.println("📶 Bluetooth initialized: SmartBin_Servo_Test");
  
  // Startup sequence
  performStartupSequence();
  
  Serial.println("✅ System initialization complete");
  Serial.println("💡 Ready for buzzer and servo commands...");
  Serial.println("💡 Send buzzer commands: control:buzzer:1");
  Serial.println("💡 Send classification: classify:paper");
  Serial.println("💡 Send classification: classify:plastic");
}
}

void loop() {
  // Handle Bluetooth communication
  if (SerialBT.available()) {
    String input = SerialBT.readStringUntil('\n');
    input.trim();
    
    if (input.length() > 0) {
      Serial.println("📨 Received: " + input);
      parseAndExecuteCommand(input);
    }
  }
  
  // Handle Serial communication (for debugging)
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    input.trim();
    
    if (input.length() > 0) {
      Serial.println("🔧 Debug command: " + input);
      parseAndExecuteCommand(input);
    }
  }
  
  delay(10);
}

// PCF8575 initialization
void initPCF8575() {
  Wire.beginTransmission(PCF8575_ADDRESS);
  if (Wire.endTransmission() == 0) {
    Serial.println("✅ PCF8575 found at address 0x20");
    writePCF8575(0xFFFF); // All pins high
  } else {
    Serial.println("❌ PCF8575 not found! Check I2C connections.");
  }
}

// Write to PCF8575
void writePCF8575(uint16_t data) {
  Wire.beginTransmission(PCF8575_ADDRESS);
  Wire.write(data & 0xFF);         // Low byte
  Wire.write((data >> 8) & 0xFF);  // High byte
  Wire.endTransmission();
  pcfState = data;
}

// Control buzzer on PCF8575
void setBuzzer(bool state) {
  if (state) {
    pcfState &= ~(1 << BUZZER_PIN);  // Clear bit (active low)
  } else {
    pcfState |= (1 << BUZZER_PIN);   // Set bit (inactive high)
  }
  writePCF8575(pcfState);
}

// Play tone with specific frequency and duration
void playTone(int frequency, int duration) {
  if (frequency <= 0) {
    setBuzzer(false);
    delay(duration);
    return;
  }
  
  int period = 1000000 / frequency;  // Period in microseconds
  int halfPeriod = period / 2;
  int cycles = (duration * 1000) / period;
  
  for (int i = 0; i < cycles; i++) {
    setBuzzer(true);
    delayMicroseconds(halfPeriod);
    setBuzzer(false);
    delayMicroseconds(halfPeriod);
  }
}

// Startup sequence with multiple tones
void performStartupSequence() {
  Serial.println("🎵 Playing startup sequence...");
  
  // Musical startup sequence
  playTone(523, 200);  // C5
  delay(50);
  playTone(659, 200);  // E5
  delay(50);
  playTone(784, 300);  // G5
  delay(100);
  playTone(1047, 400); // C6
  delay(200);
  
  setBuzzer(false);    // Ensure buzzer is off
  Serial.println("✅ Startup sequence complete");
}

// Parse and execute commands
void parseAndExecuteCommand(String command) {
  // Parse command format: action:target:value
  int firstColon = command.indexOf(':');
  int secondColon = command.indexOf(':', firstColon + 1);
  
  if (firstColon > 0) {
    String action = command.substring(0, firstColon);
    String target = "";
    String valueStr = "";
    int value = 0;
    
    if (secondColon > firstColon) {
      target = command.substring(firstColon + 1, secondColon);
      valueStr = command.substring(secondColon + 1);
      value = valueStr.toInt();
    } else {
      target = command.substring(firstColon + 1);
    }
    
    Serial.println("🔧 Parsing command:");
    Serial.println("  Action: " + action);
    Serial.println("  Target: " + target);
    Serial.println("  Value: " + String(value));
    
    if (action.equalsIgnoreCase("control") && target.equalsIgnoreCase("buzzer")) {
      // Handle buzzer commands
      if (value == 0) {
        // Silence
        setBuzzer(false);
        sendResponse("buzzer", "off");
        Serial.println("🔕 Buzzer: OFF");
      } else if (value == 1) {
        // Single beep
        playTone(1000, 200);
        sendResponse("buzzer", "single_beep");
        Serial.println("🔔 Buzzer: Single beep");
      } else if (value == 2) {
        // Double beep
        playTone(1000, 150);
        delay(100);
        playTone(1000, 150);
        sendResponse("buzzer", "double_beep");
        Serial.println("🔔 Buzzer: Double beep");
      } else if (value == 3) {
        // Triple beep
        playTone(1000, 100);
        delay(80);
        playTone(1000, 100);
        delay(80);
        playTone(1000, 100);
        sendResponse("buzzer", "triple_beep");
        Serial.println("🔔 Buzzer: Triple beep");
      } else {
        // Custom sequence
        for (int i = 0; i < value && i < 10; i++) {
          playTone(800 + (i * 100), 150);
          delay(100);
        }
        sendResponse("buzzer", "custom_sequence");
        Serial.println("🔔 Buzzer: Custom sequence (" + String(value) + " tones)");
      }
    } else if (action.equalsIgnoreCase("classify")) {
      // Handle classification commands for servo sorting
      String classification = target;
      if (secondColon > firstColon) {
        classification = valueStr; // In case classification is after second colon
      }
      
      moveServoForClassification(classification);
    } else {
      sendResponse("error", "unknown_command");
      Serial.println("❌ Unknown command: " + command);
    }
  } else {
    sendResponse("error", "invalid_format");
    Serial.println("❌ Invalid command format: " + command);
  }
}

// Send response back to client
void sendResponse(String command, String status) {
  DynamicJsonDocument response(256);
  response["command"] = command;
  response["status"] = status;
  response["timestamp"] = millis();
  
  String responseStr;
  serializeJson(response, responseStr);
  
  SerialBT.println(responseStr);
  Serial.println("📤 Response: " + responseStr);
}

// Initialize servo motor
void initServo() {
  // Allocate timer for servo
  ESP32PWM::allocateTimer(0);
  
  // Set servo frequency and attach to pin
  sortingServo.setPeriodHertz(50);    // Standard 50 Hz servo
  sortingServo.attach(SERVO_PIN, 1000, 2000); // 1ms-2ms pulse width
  
  // Set default position (90 degrees)
  sortingServo.write(90);
  delay(500); // Wait for servo to reach position
  
  Serial.println("🤖 Servo initialized on GPIO16, default position: 90°");
}

// Move servo based on classification result
void moveServoForClassification(String classification) {
  classification.toLowerCase();
  
  Serial.println("🎯 Classification received: " + classification);
  
  int targetPosition;
  String binType;
  
  if (classification == "paper" || classification == "misc") {
    targetPosition = 180;
    binType = "paper/misc bin";
  } else {
    // plastic, metal, or any other classification
    targetPosition = 0;
    binType = "plastic/metal bin";
  }
  
  Serial.println("🤖 Moving servo to " + String(targetPosition) + "° (" + binType + ")");
  
  // Move to target position
  sortingServo.write(targetPosition);
  
  // Play confirmation sound
  playTone(1200, 200);
  
  // Hold position for 2 seconds
  delay(2000);
  
  // Return to default position (90 degrees)
  Serial.println("🤖 Returning servo to default position (90°)");
  sortingServo.write(90);
  
  // Play return sound
  playTone(800, 200);
  
  // Send response
  sendResponse("servo", "sorted_to_" + String(targetPosition) + "_degrees");
}
