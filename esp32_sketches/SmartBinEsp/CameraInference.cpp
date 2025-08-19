#include "CameraInference.h"
#include <Arduino.h>

// TODO: Include actual camera + inference libraries later

void initCamera() {
  // Placeholder — later add real camera initialization code
  Serial.println("[Camera] Initialized");
}

String runInference() {
  // Placeholder — simulate class prediction
  String predictedClass = "Plastic Bottle";
  Serial.println("[Inference] Predicted class: " + predictedClass);
  return predictedClass;
}
