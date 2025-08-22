#ifndef SERVOS_H
#define SERVOS_H

#include <ESP32Servo.h>

// Define pins for servos
extern int COIN_DISPENSER_PIN;
extern int LID_MOTOR_PIN;
extern int SLIDING_MOTOR_PIN;
extern int DROPPING_MOTOR_PIN;

void initServos();
void rotateCoinDispenser(int angle);
void rotateLid(int angle);
void rotateSlidingMotor(int angle);
void rotateDroppingMotor(int angle);

#endif
