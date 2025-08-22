#include "CameraInference.h"
#include <Arduino.h>

// Simplified for testing - removed Edge Impulse dependencies
static bool cameraInitialized = false;

void initCamera() {
    // Add yield to prevent watchdog timeout
    yield();
    
    Serial.println("[Camera] Mock camera initialized for testing");
    
    // Add small delay and another yield
    delay(10);
    yield();
    
    cameraInitialized = true;
}

String runInference() {
    Serial.println("[Inference] Running mock classification for testing...");
    
    // Array of possible classifications from your Edge Impulse model
    String classifications[] = {"metal", "misc", "paper", "plastic"};
    float confidences[] = {0.0, 0.0, 0.0, 0.0};
    
    // Generate random classification with realistic confidence
    int randomIndex = random(0, 4);  // 0-3 for the 4 classes
    float baseConfidence = random(60, 95) / 100.0;  // 60-95% confidence
    
    // Set the selected class confidence
    confidences[randomIndex] = baseConfidence;
    
    // Distribute remaining confidence among other classes
    float remainingConfidence = 1.0 - baseConfidence;
    for (int i = 0; i < 4; i++) {
        if (i != randomIndex) {
            confidences[i] = random(0, (int)(remainingConfidence * 1000)) / 1000.0;
            remainingConfidence -= confidences[i];
        }
    }
    
    // Log all predictions like the real model would
    Serial.println("[Inference] Mock classification results:");
    for (int i = 0; i < 4; i++) {
        Serial.printf("[Inference] %s: %.1f%%\n", 
                     classifications[i].c_str(), 
                     confidences[i] * 100.0);
    }
    
    String topClass = classifications[randomIndex];
    float topConfidence = confidences[randomIndex];
    
    Serial.printf("[Inference] Top prediction: %s (%.1f%% confidence)\n", 
                 topClass.c_str(), 
                 topConfidence * 100.0);

    // Simulate processing delay
    delay(500);
    
    return topClass;
}
