#include "Servos.h"
#include "LEDs.h"
#include "Ultrasonic.h"
#include "CameraInference.h"

unsigned long lastTrigger = 0;
const unsigned long triggerInterval = 10000; // 10 seconds

void setup() {
  Serial.begin(115200);

  initServos();
  initLEDs();
  initUltrasonic();
  initCamera();

  Serial.println("[System] SmartBin Ready");
}

void loop() {
  unsigned long currentMillis = millis();

  if (currentMillis - lastTrigger >= triggerInterval) {
    lastTrigger = currentMillis;

    Serial.println("[Trigger] Starting capture + classification sequence");

    // Turn on flash LED (example)
    setLED1(true);
    delay(250); // simulate flash ON before capture

    String detectedClass = runInference();

    // Turn off flash LED
    setLED1(false);

    // Placeholder for action based on detection
    if (detectedClass == "Plastic Bottle") {
      rotateSlidingMotor(90);
      delay(1000);
      rotateDroppingMotor(45);
    }
  }
}
