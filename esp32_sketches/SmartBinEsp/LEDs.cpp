#include "LEDs.h"
#include "Logger.h"
#include <Arduino.h>

// PCF8575 instance (I2C address 0x20) - following test_pcf8575 pattern
PCF8575 pcf8575(0x20);

void initLEDs() {
  LOG_LEDS("Initializing LEDs via PCF8575 - Starting LED system");
  
  yield(); // Prevent watchdog timeout
  
  // Initialize I2C with SDA=14, SCL=15 (following test_pcf8575 pattern)
  Wire.begin(14, 15);
  
  // Initialize PCF8575
  if (!pcf8575.begin()) {
    LOG_ERROR("PCF8575 Init Failed - Could not initialize I2C expander");
    return;
  }
  
  delay(10); // Allow PCF8575 to stabilize
  
  // Initialize all pins LOW (following test_pcf8575 pattern)
  pcf8575.write16(0x0000);
  
  yield(); // Prevent watchdog timeout
  delay(5);
  
  // Brief startup sequence to test LEDs
  LOG_LEDS("LED Test Sequence - Testing all LEDs");
  
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
  
  LOG_LEDS("LEDs Initialized - LED system ready");
  yield(); // Final yield
}

void setSystemState(SystemState state) {
  // Clear all LEDs first
  clearAllLEDs();
  
  switch (state) {
    case SYSTEM_READY:
      setGreenLED(true);
      LOG_LEDS("System Ready - Green LED: Waiting for item");
      break;
      
    case SYSTEM_BUSY:
      setOrangeLED(true);
      LOG_LEDS("System Busy - Orange LED: Performing sorting");
      break;
      
    case SYSTEM_STATUS:
      setRedLED(true);
      LOG_LEDS("System Status - Red LED: Initialization complete");
      break;
  }
}

void setRedLED(bool state) {
  pcf8575.write(RED_LED_PIN, state ? HIGH : LOW);
}

void setOrangeLED(bool state) {
  pcf8575.write(ORANGE_LED_PIN, state ? HIGH : LOW);
}

void setGreenLED(bool state) {
  pcf8575.write(GREEN_LED_PIN, state ? HIGH : LOW);
}

void clearAllLEDs() {
  setRedLED(false);
  setOrangeLED(false);
  setGreenLED(false);
}
