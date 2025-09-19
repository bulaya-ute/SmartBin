#ifndef SERVOS_H
#define SERVOS_H

#include <ESP32Servo.h>

// Define pins for servos
extern int COIN_DISPENSER_PIN;
// extern int LID_MOTOR_PIN;  // Removed - hardware no longer present
extern int SLIDING_MOTOR_PIN;
// extern int DROPPING_MOTOR_PIN;  // Removed - only using two motors now

// Movement speed configuration
extern const int MOVEMENT_SPEED_MS_PER_DEGREE;

// Servo control functions
void initServos();
void rotateCoinDispenser(int angle);
// void rotateLid(int angle);  // Removed - hardware no longer present
void rotateSlidingMotor(int angle);
// void rotateDroppingMotor(int angle);  // Removed - only using two motors now

// Position tracking functions
int getCurrentCoinPosition();
// int getCurrentLidPosition();  // Removed - hardware no longer present
int getCurrentSlidingPosition();
// int getCurrentDroppingPosition();  // Removed - only using two motors now

#endif
