#include <ESP32Servo.h>

// === Pin Definitions ===
#define SLIDING_MOTOR_PIN   14  // Connected to sliding compartment servo
#define DROPPING_MOTOR_PIN  15  // Connected to release/dropping mechanism servo

// === Servo Objects ===
Servo slidingServo;
Servo droppingServo;

// === Test Parameters ===
const int ANGLE_MIN = 0;
const int ANGLE_MAX = 180;
const int STEP_DELAY = 15;     // ms between steps (smooth movement)
const int PAUSE_BETWEEN = 2000; // ms to wait between motor tests

void setup() {
  Serial.begin(115200);
  while (!Serial); // Wait for serial monitor (optional)

  // Initialize ESP32 PWM settings
  ESP32PWM::allocateTimer(0);
  ESP32PWM::allocateTimer(1);

  // Attach servos
  slidingServo.setPeriodHertz(50);    // Standard servo frequency
  droppingServo.setPeriodHertz(50);

  slidingServo.attach(SLIDING_MOTOR_PIN, 1000, 2000); // Adjust micros if needed
  droppingServo.attach(DROPPING_MOTOR_PIN, 1000, 2000);

  Serial.println("[Motor Test] Started");
  Serial.println("Testing Sliding Motor (Pin 14) first...");
}

void loop() {
  // === Test Sliding Motor (Pin 14) ===
  Serial.println("→ Sliding Motor: 0° → 180°");
  for (int pos = ANGLE_MIN; pos <= ANGLE_MAX; pos++) {
    slidingServo.write(pos);
    delay(STEP_DELAY);
  }

  Serial.println("→ Sliding Motor: 180° → 0°");
  for (int pos = ANGLE_MAX; pos >= ANGLE_MIN; pos--) {
    slidingServo.write(pos);
    delay(STEP_DELAY);
  }

  Serial.println("✅ Sliding Motor test complete");
  delay(PAUSE_BETWEEN);

  // === Test Dropping Motor (Pin 15) ===
  Serial.println("→ Dropping Motor: 0° → 180°");
  for (int pos = ANGLE_MIN; pos <= ANGLE_MAX; pos++) {
    droppingServo.write(pos);
    delay(STEP_DELAY);
  }

  Serial.println("→ Dropping Motor: 180° → 0°");
  for (int pos = ANGLE_MAX; pos >= ANGLE_MIN; pos--) {
    droppingServo.write(pos);
    delay(STEP_DELAY);
  }

  Serial.println("✅ Dropping Motor test complete");
  delay(PAUSE_BETWEEN);

  // Optional: Add longer delay if you want to observe
  Serial.println("🔁 Restarting test in 3 seconds...");
  delay(3000);
}