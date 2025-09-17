#include "Bluetooth.h"
#include "Logger.h"
#include <Arduino.h>

// Bluetooth Serial instance
BluetoothSerial SerialBT;

void initBluetooth() {
  Serial.println("🔵 Initializing Bluetooth...");
  
  // Initialize Bluetooth Serial
  if (!SerialBT.begin(BT_DEVICE_NAME)) {
    Serial.println("❌ Bluetooth initialization failed!");
    return;
  }
  
  Serial.println("✅ Bluetooth initialized successfully!");
  Serial.print("📱 Device name: ");
  Serial.println(BT_DEVICE_NAME);
  Serial.println("💡 Ready for Bluetooth connections");
  
  // Send initial message over Bluetooth
  SerialBT.println("🚀 SmartBin ESP32-CAM Connected!");
  SerialBT.println("📡 Bluetooth communication active");
  SerialBT.println("================================");
  
  delay(100); // Allow Bluetooth to stabilize
}

void bluetoothPrint(const String& message) {
  if (SerialBT.hasClient()) {
    SerialBT.print(message);
  }
}

void bluetoothPrintln(const String& message) {
  if (SerialBT.hasClient()) {
    SerialBT.println(message);
  }
}

void bluetoothPrintf(const char* format, ...) {
  if (SerialBT.hasClient()) {
    va_list args;
    va_start(args, format);
    SerialBT.printf(format, args);
    va_end(args);
  }
}

void dualPrint(const String& message) {
  Serial.print(message);
  bluetoothPrint(message);
}

void dualPrintln(const String& message) {
  Serial.println(message);
  bluetoothPrintln(message);
}

void dualPrintf(const char* format, ...) {
  va_list args;
  
  // Print to Serial
  va_start(args, format);
  Serial.printf(format, args);
  va_end(args);
  
  // Print to Bluetooth
  if (SerialBT.hasClient()) {
    va_start(args, format);
    SerialBT.printf(format, args);
    va_end(args);
  }
}
