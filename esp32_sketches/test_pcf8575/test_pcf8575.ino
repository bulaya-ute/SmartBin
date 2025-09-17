#include <Wire.h>
#include <PCF8575.h>
#include "BluetoothSerial.h"

BluetoothSerial SerialBT;
PCF8575 expander(0x20);  // Rob Tillaart library

// Unified logging function
void log(const String &msg) {
  Serial.println(msg);
  SerialBT.println(msg);
}

void setup() {
  Serial.begin(115200);
  SerialBT.begin("SmartBin_ESP32"); // Bluetooth device name

  log("Waiting for start command '00' over Bluetooth...");

  // Block until "00" is received
  while (true) {
    if (SerialBT.available()) {
      String msg = SerialBT.readStringUntil('\n');
      msg.trim();
      if (msg == "00") {
        log("Start command received!");
        break;
      }
    }
  }

  // Now proceed with I2C and expander initialization
  log("Initializing I2C expander...");
  Wire.begin(14, 15); // SDA, SCL
  if (!expander.begin()) {
    log("PCF8575 not detected!");
    while (1); // halt if expander not found
  }

  // Initialize all pins LOW (0)
  expander.write16(0x0000);
  log("PCF8575 initialized. All pins set to LOW. Ready to receive pin commands.");
}

void loop() {
  if (SerialBT.available()) {
    String cmd = SerialBT.readStringUntil('\n');
    cmd.trim();
    if (cmd.length() == 0) return;

    int spaceIndex = cmd.indexOf(' ');
    if (spaceIndex == -1) {
      log("Invalid command (no space).");
      return; // ignore invalid commands
    }

    String pinStr = cmd.substring(0, spaceIndex);
    String valStr = cmd.substring(spaceIndex + 1);

    int pin = pinStr.toInt();
    int val = valStr.toInt();

    // Validate pin and value
    if (pin < 0 || pin > 15 || (val != 0 && val != 1)) {
      log("Invalid command values.");
      return;
    }

    // Write pin state
    expander.write(pin, val == 1 ? HIGH : LOW);
    log("Pin " + String(pin) + " set to " + String(val));
  }
}
