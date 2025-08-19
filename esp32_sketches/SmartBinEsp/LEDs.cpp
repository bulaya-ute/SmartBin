#include "LEDs.h"
#include <Arduino.h>

// Pin assignments (update as needed)
int LED1_PIN = 2;
int LED2_PIN = 4;
int LED3_PIN = 16;

void initLEDs() {
  pinMode(LED1_PIN, OUTPUT);
  pinMode(LED2_PIN, OUTPUT);
  pinMode(LED3_PIN, OUTPUT);
}

void setLED1(bool state) { digitalWrite(LED1_PIN, state); }
void setLED2(bool state) { digitalWrite(LED2_PIN, state); }
void setLED3(bool state) { digitalWrite(LED3_PIN, state); }
