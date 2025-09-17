#ifndef LEDS_H
#define LEDS_H

#include "PCF8575.h"

// PCF8575 pin assignments (use library constants)
#define RED_LED_PIN    P0   // P0 - Status LED (ready after init)
#define ORANGE_LED_PIN P1   // P1 - Busy LED (sorting sequence)  
#define GREEN_LED_PIN  P2   // P2 - Ready LED (waiting for item)

// LED states
enum LEDState {
  LED_OFF = 0,
  LED_ON = 1
};

// System states
enum SystemState {
  SYSTEM_READY,      // Green LED only
  SYSTEM_BUSY,       // Orange LED only  
  SYSTEM_STATUS      // Red LED only (after init)
};

extern PCF8575 pcf8575;

void initLEDs();
void setSystemState(SystemState state);

// Individual LED controls (for advanced use)
void setRedLED(bool state);
void setOrangeLED(bool state);
void setGreenLED(bool state);

// Turn off all LEDs
void clearAllLEDs();

#endif
