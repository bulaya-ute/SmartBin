#include "LEDs.h"
#include "Logger.h"
#include <Arduino.h>

// PCF8575 instance (I2C address 0x20)
PCF8575 pcf8575(0x20);

void initLEDs() {
  logSystemEvent("Initializing LEDs via PCF8575", "Starting LED system");
  
  yield(); // Prevent watchdog timeout
  
  // Initialize PCF8575
  if (!pcf8575.begin()) {
    logSystemEvent("PCF8575 Init Failed", "ERROR: Could not initialize I2C expander");
    return;
  }
  
  delay(10); // Allow PCF8575 to stabilize
  
  // Set all LED pins as outputs
  pcf8575.pinMode(RED_LED_PIN, OUTPUT);
  pcf8575.pinMode(ORANGE_LED_PIN, OUTPUT);  
  pcf8575.pinMode(GREEN_LED_PIN, OUTPUT);
  
  yield(); // Prevent watchdog timeout
  delay(5);
  
  // Turn off all LEDs initially
  clearAllLEDs();
  
  // Brief startup sequence to test LEDs
  logSystemEvent("LED Test Sequence", "Testing all LEDs");
  
  // Test sequence: Red -> Orange -> Green -> All off
  setRedLED(true);
  delay(200);
  setRedLED(false);
  
  setOrangeLED(true);
  delay(200);
  setOrangeLED(false);
  
  setGreenLED(true);
  delay(200);
  setGreenLED(false);
  
  delay(100);
  
  logSystemEvent("LEDs Initialized", "LED system ready");
  yield(); // Final yield
}

void setSystemState(SystemState state) {
  // Clear all LEDs first
  clearAllLEDs();
  
  switch (state) {
    case SYSTEM_READY:
      setGreenLED(true);
      logSystemEvent("System Ready", "Green LED: Waiting for item");
      break;
      
    case SYSTEM_BUSY:
      setOrangeLED(true);
      logSystemEvent("System Busy", "Orange LED: Performing sorting");
      break;
      
    case SYSTEM_STATUS:
      setRedLED(true);
      logSystemEvent("System Status", "Red LED: Initialization complete");
      break;
  }
}

void setRedLED(bool state) {
  pcf8575.digitalWrite(RED_LED_PIN, state ? HIGH : LOW);
}

void setOrangeLED(bool state) {
  pcf8575.digitalWrite(ORANGE_LED_PIN, state ? HIGH : LOW);
}

void setGreenLED(bool state) {
  pcf8575.digitalWrite(GREEN_LED_PIN, state ? HIGH : LOW);
}

void clearAllLEDs() {
  setRedLED(false);
  setOrangeLED(false);
  setGreenLED(false);
}
