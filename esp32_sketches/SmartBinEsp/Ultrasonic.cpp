#include "Ultrasonic.h"
#include <Arduino.h>

// Pin assignments (update to match your wiring)
int ULTRASONIC_TRIG_PIN = 5;
int ULTRASONIC_ECHO_PIN = 18;

void initUltrasonic() {
  pinMode(ULTRASONIC_TRIG_PIN, OUTPUT);
  pinMode(ULTRASONIC_ECHO_PIN, INPUT);
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
