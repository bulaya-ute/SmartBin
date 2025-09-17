#include "Ultrasonic.h"
#include <Arduino.h>

// Pin assignments (update to match your wiring)
int ULTRASONIC_TRIG_PIN = 4;
int ULTRASONIC_ECHO_PIN = 13;

void initUltrasonic() {
  yield(); // Prevent watchdog timeout
  pinMode(ULTRASONIC_TRIG_PIN, OUTPUT);
  delay(5); // Brief delay
  
  yield(); // Prevent watchdog timeout
  pinMode(ULTRASONIC_ECHO_PIN, INPUT);
  delay(5); // Brief delay
  
  yield(); // Final yield
}

float readUltrasonicDistance() {
  digitalWrite(ULTRASONIC_TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(ULTRASONIC_TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(ULTRASONIC_TRIG_PIN, LOW);

  long duration = pulseIn(ULTRASONIC_ECHO_PIN, HIGH);
  return (duration * 0.0343) / 2; // distance in cm
}
