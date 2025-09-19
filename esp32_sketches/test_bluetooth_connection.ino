/*
 * Simple Bluetooth connection test for ESP32-CAM
 * Tests Bluetooth connection stability without the full SmartBin complexity
 * Use this to verify Bluetooth works before running full code
 */

#include "BluetoothSerial.h"

BluetoothSerial SerialBT;

void setup() {
  Serial.begin(115200);
  delay(2000);
  
  Serial.println("=== ESP32-CAM Bluetooth Connection Test ===");
  
  // Initialize Bluetooth
  if (!SerialBT.begin("SmartBin_Test")) {
    Serial.println("❌ Bluetooth initialization failed!");
    while(1); // Stop execution
  }
  
  Serial.println("✅ Bluetooth initialized successfully!");
  Serial.println("📱 Device name: SmartBin_Test");
  Serial.println("💡 Ready for connections - please connect from your device");
  
  SerialBT.println("🚀 ESP32-CAM Bluetooth Test Active!");
  SerialBT.println("📡 Connection test mode");
}

void loop() {
  // Check connection status
  static unsigned long lastStatusCheck = 0;
  if (millis() - lastStatusCheck > 5000) { // Every 5 seconds
    bool connected = SerialBT.hasClient();
    Serial.println("🔵 Bluetooth Status: " + String(connected ? "CONNECTED" : "DISCONNECTED"));
    
    if (connected) {
      SerialBT.println("📊 Status: Connected - Time: " + String(millis()/1000) + "s");
    }
    
    lastStatusCheck = millis();
  }
  
  // Echo any received data
  if (SerialBT.available()) {
    String received = SerialBT.readStringUntil('\n');
    received.trim();
    
    Serial.println("📨 Received: " + received);
    SerialBT.println("📤 Echo: " + received);
    
    // Special commands for testing
    if (received == "test") {
      SerialBT.println("✅ Bluetooth communication working!");
    } else if (received == "status") {
      SerialBT.println("📊 ESP32 Status: Running normally");
      SerialBT.println("🕐 Uptime: " + String(millis()/1000) + " seconds");
    } else if (received == "reboot") {
      SerialBT.println("🔄 Rebooting ESP32...");
      delay(1000);
      ESP.restart();
    }
  }
  
  // Send data from Serial to Bluetooth
  if (Serial.available()) {
    String serialData = Serial.readStringUntil('\n');
    SerialBT.println("💻 From Serial: " + serialData);
  }
  
  delay(100); // Small delay to prevent overwhelming
}
