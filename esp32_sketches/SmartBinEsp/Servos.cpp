#include "ESP32Servo.h"

Servo coinServo, lidServo, slidingServo, droppingServo;

// Pin assignments (update to match your wiring)
int COIN_DISPENSER_PIN = 12;
int LID_MOTOR_PIN      = 13;
int SLIDING_MOTOR_PIN  = 14;
int DROPPING_MOTOR_PIN = 15;

void initServos() {
  yield(); // Prevent watchdog timeout
  coinServo.attach(COIN_DISPENSER_PIN);
  delay(10); // Allow servo to attach
  
  yield(); // Prevent watchdog timeout
  lidServo.attach(LID_MOTOR_PIN);
  delay(10); // Allow servo to attach
  
  yield(); // Prevent watchdog timeout
  slidingServo.attach(SLIDING_MOTOR_PIN);
  delay(10); // Allow servo to attach
  
  yield(); // Prevent watchdog timeout
  droppingServo.attach(DROPPING_MOTOR_PIN);
  delay(10); // Allow servo to attach
  
  yield(); // Final yield after all servos attached
}

void rotateCoinDispenser(int angle) {
  coinServo.write(angle);
}

void rotateLid(int angle) {
  lidServo.write(angle);
}

void rotateSlidingMotor(int angle) {
  slidingServo.write(angle);
}

void rotateDroppingMotor(int angle) {
  droppingServo.write(angle);
}
