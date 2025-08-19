#include "Servos.h"

Servo coinServo, lidServo, slidingServo, droppingServo;

// Pin assignments (update to match your wiring)
int COIN_DISPENSER_PIN = 12;
int LID_MOTOR_PIN      = 13;
int SLIDING_MOTOR_PIN  = 14;
int DROPPING_MOTOR_PIN = 15;

void initServos() {
  coinServo.attach(COIN_DISPENSER_PIN);
  lidServo.attach(LID_MOTOR_PIN);
  slidingServo.attach(SLIDING_MOTOR_PIN);
  droppingServo.attach(DROPPING_MOTOR_PIN);
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
