#include "ESP32Servo.h"

Servo coinServo, lidServo, slidingServo, droppingServo;

// Pin assignments (update to match your wiring)
int COIN_DISPENSER_PIN = 12;
int LID_MOTOR_PIN      = 13;
int SLIDING_MOTOR_PIN  = 14;
int DROPPING_MOTOR_PIN = 15;

// Current position tracking for each servo
int currentCoinPosition = 90;     // Default center position
int currentLidPosition = 0;       // Default closed position
int currentSlidingPosition = 90;  // Default center position
int currentDroppingPosition = 0;  // Default closed position

// Movement speed configuration (milliseconds per degree)
const int MOVEMENT_SPEED_MS_PER_DEGREE = 10; // Adjust this value based on your servo speed

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
  
  // Move all servos to their initial positions
  coinServo.write(currentCoinPosition);
  lidServo.write(currentLidPosition);
  slidingServo.write(currentSlidingPosition);
  droppingServo.write(currentDroppingPosition);
  
  delay(500); // Allow all servos to reach initial positions
  yield(); // Prevent watchdog timeout
}

void rotateCoinDispenser(int angle) {
  // Constrain angle to valid servo range
  angle = constrain(angle, 0, 180);
  
  // Calculate displacement from current position
  int displacement = abs(angle - currentCoinPosition);
  
  // Calculate proportional delay (minimum 50ms, maximum 2000ms)
  int movementDelay = constrain(displacement * MOVEMENT_SPEED_MS_PER_DEGREE, 50, 2000);
  
  // Send command to servo
  coinServo.write(angle);
  
  // Wait for movement to complete with watchdog-safe delay
  unsigned long startTime = millis();
  while (millis() - startTime < movementDelay) {
    yield(); // Prevent watchdog timeout
    delay(10); // Small delay chunks
  }
  
  // Update current position
  currentCoinPosition = angle;
}

void rotateLid(int angle) {
  // Constrain angle to valid servo range
  angle = constrain(angle, 0, 180);
  
  // Calculate displacement from current position
  int displacement = abs(angle - currentLidPosition);
  
  // Calculate proportional delay (minimum 50ms, maximum 2000ms)
  int movementDelay = constrain(displacement * MOVEMENT_SPEED_MS_PER_DEGREE, 50, 2000);
  
  // Send command to servo
  lidServo.write(angle);
  
  // Wait for movement to complete with watchdog-safe delay
  unsigned long startTime = millis();
  while (millis() - startTime < movementDelay) {
    yield(); // Prevent watchdog timeout
    delay(10); // Small delay chunks
  }
  
  // Update current position
  currentLidPosition = angle;
}

void rotateSlidingMotor(int angle) {
  // Constrain angle to valid servo range
  angle = constrain(angle, 0, 180);
  
  // Calculate displacement from current position
  int displacement = abs(angle - currentSlidingPosition);
  
  // Calculate proportional delay (minimum 50ms, maximum 2000ms)
  int movementDelay = constrain(displacement * MOVEMENT_SPEED_MS_PER_DEGREE, 50, 2000);
  
  // Send command to servo
  slidingServo.write(angle);
  
  // Wait for movement to complete with watchdog-safe delay
  unsigned long startTime = millis();
  while (millis() - startTime < movementDelay) {
    yield(); // Prevent watchdog timeout
    delay(10); // Small delay chunks
  }
  
  // Update current position
  currentSlidingPosition = angle;
}

void rotateDroppingMotor(int angle) {
  // Constrain angle to valid servo range
  angle = constrain(angle, 0, 180);
  
  // Calculate displacement from current position
  int displacement = abs(angle - currentDroppingPosition);
  
  // Calculate proportional delay (minimum 50ms, maximum 2000ms)
  int movementDelay = constrain(displacement * MOVEMENT_SPEED_MS_PER_DEGREE, 50, 2000);
  
  // Send command to servo
  droppingServo.write(angle);
  
  // Wait for movement to complete with watchdog-safe delay
  unsigned long startTime = millis();
  while (millis() - startTime < movementDelay) {
    yield(); // Prevent watchdog timeout
    delay(10); // Small delay chunks
  }
  
  // Update current position
  currentDroppingPosition = angle;
}

// Position getter functions
int getCurrentCoinPosition() {
  return currentCoinPosition;
}

int getCurrentLidPosition() {
  return currentLidPosition;
}

int getCurrentSlidingPosition() {
  return currentSlidingPosition;
}

int getCurrentDroppingPosition() {
  return currentDroppingPosition;
}
