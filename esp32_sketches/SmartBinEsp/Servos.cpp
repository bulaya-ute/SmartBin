#include "ESP32Servo.h"

Servo coinServo, slidingServo; // lidServo and droppingServo removed

// Pin assignments (update to match your wiring)
int COIN_DISPENSER_PIN = 14;
// int LID_MOTOR_PIN      = 13;  // Removed - hardware no longer present
int SLIDING_MOTOR_PIN  = 15;
// int DROPPING_MOTOR_PIN = 16;  // Removed - only using two motors now

// Current position tracking for each servo
int currentCoinPosition = 0;      // Home position: 0 degrees
// int currentLidPosition = 0;       // Removed - hardware no longer present
int currentSlidingPosition = 90;  // Home position: 90 degrees
// int currentDroppingPosition = 0;  // Removed - only using two motors now

// Movement speed configuration (milliseconds per degree)
const int MOVEMENT_SPEED_MS_PER_DEGREE = 10; // Adjust this value based on your servo speed

void initServos() {
  Serial.println("[Servo] Initializing servo motors...");
  
  yield(); // Prevent watchdog timeout
  coinServo.attach(COIN_DISPENSER_PIN);
  Serial.println("[Servo] Coin dispenser attached to GPIO " + String(COIN_DISPENSER_PIN));
  delay(10); // Allow servo to attach
  
  // Lid servo removed - hardware no longer present
  // lidServo.attach(LID_MOTOR_PIN);
  // delay(10); // Allow servo to attach
  
  yield(); // Prevent watchdog timeout
  slidingServo.attach(SLIDING_MOTOR_PIN);
  Serial.println("[Servo] Sliding motor attached to GPIO " + String(SLIDING_MOTOR_PIN));
  delay(10); // Allow servo to attach
  
  // Dropping servo removed - only using two motors now
  // droppingServo.attach(DROPPING_MOTOR_PIN);
  // delay(10); // Allow servo to attach
  
  yield(); // Final yield after all servos attached
  
  // Move all servos to their home positions
  Serial.println("[Servo] Moving to home positions: Coin=" + String(currentCoinPosition) + "°, Sliding=" + String(currentSlidingPosition) + "°");
  coinServo.write(currentCoinPosition);        // Coin dispenser home: 0°
  // lidServo.write(currentLidPosition);       // Removed - hardware no longer present
  slidingServo.write(currentSlidingPosition);  // Sliding motor home: 90°
  // droppingServo.write(currentDroppingPosition); // Removed - only using two motors now
  
  delay(500); // Allow all servos to reach initial positions
  Serial.println("[Servo] Initialization complete!");
  yield(); // Prevent watchdog timeout
}

void rotateCoinDispenser(int angle) {
  // Constrain angle to valid servo range
  angle = constrain(angle, 0, 180);
  
  // Debug logging
  Serial.println("[Servo] CoinDispenser: Moving from " + String(currentCoinPosition) + "° to " + String(angle) + "°");
  
  // Calculate displacement from current position
  int displacement = abs(angle - currentCoinPosition);
  
  // Calculate proportional delay (minimum 50ms, maximum 2000ms)
  int movementDelay = constrain(displacement * MOVEMENT_SPEED_MS_PER_DEGREE, 50, 2000);
  
  Serial.println("[Servo] CoinDispenser: Movement delay = " + String(movementDelay) + "ms");
  
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

// rotateLid function removed - hardware no longer present

void rotateSlidingMotor(int angle) {
  // Constrain angle to valid servo range
  angle = constrain(angle, 0, 180);
  
  // Debug logging
  Serial.println("[Servo] SlidingMotor: Moving from " + String(currentSlidingPosition) + "° to " + String(angle) + "°");
  
  // Calculate displacement from current position
  int displacement = abs(angle - currentSlidingPosition);
  
  // Calculate proportional delay (minimum 50ms, maximum 2000ms)
  int movementDelay = constrain(displacement * MOVEMENT_SPEED_MS_PER_DEGREE, 50, 2000);
  
  Serial.println("[Servo] SlidingMotor: Movement delay = " + String(movementDelay) + "ms");
  
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

// rotateDroppingMotor function removed - only using two motors now
/*
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
*/

// Position getter functions
int getCurrentCoinPosition() {
  return currentCoinPosition;
}

// getCurrentLidPosition function removed - hardware no longer present

int getCurrentSlidingPosition() {
  return currentSlidingPosition;
}

// getCurrentDroppingPosition function removed - only using two motors now
/*
int getCurrentDroppingPosition() {
  return currentDroppingPosition;
}
*/
