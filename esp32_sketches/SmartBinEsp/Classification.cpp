#include "Classification.h"
#include <Arduino.h>

// Classification confidence thresholds
const float CONFIDENCE_THRESHOLD = 0.60f;  // 60% minimum confidence
const float MINIMUM_CONFIDENCE = 0.30f;    // 30% absolute minimum

static bool classificationInitialized = false;

bool initClassification() {
    Serial.println("[Classification] Initializing mock classification system...");
    yield(); // Prevent watchdog timeout
    
    // TODO: Replace with actual Edge Impulse model initialization
    // For now, just simulate initialization
    delay(100);
    
    Serial.println("[Classification] ✅ Mock classification system initialized");
    classificationInitialized = true;
    return true;
}

ClassificationResult classifyImage(const CapturedImage& image) {
    ClassificationResult result = {"unknown", 0.0f, false, ""};
    
    if (!classificationInitialized) {
        result.errorMessage = "Classification system not initialized";
        Serial.println("[Classification] ERROR: " + result.errorMessage);
        return result;
    }
    
    if (!image.isValid) {
        result.errorMessage = "Invalid input image";
        Serial.println("[Classification] ERROR: " + result.errorMessage);
        return result;
    }
    
    Serial.println("[Classification] Processing image...");
    Serial.printf("[Classification] Image details: %d bytes, %dx%d pixels\n", 
                  image.imageSize, 
                  image.frameBuffer->width, 
                  image.frameBuffer->height);
    
    yield(); // Prevent watchdog timeout
    
    // TODO: Replace this mock classification with actual Edge Impulse inference
    // For now, simulate realistic classification behavior
    
    // Array of possible classifications from your Edge Impulse model
    String classifications[] = {"metal", "misc", "paper", "plastic"};
    float confidences[] = {0.0f, 0.0f, 0.0f, 0.0f};
    
    // Generate random classification with realistic confidence distribution
    int randomIndex = random(0, 4);  // 0-3 for the 4 classes
    float baseConfidence = random(30, 95) / 100.0f;  // 30-95% confidence
    
    // Set the selected class confidence
    confidences[randomIndex] = baseConfidence;
    
    // Distribute remaining confidence among other classes
    float remainingConfidence = 1.0f - baseConfidence;
    for (int i = 0; i < 4; i++) {
        if (i != randomIndex) {
            float maxRemaining = remainingConfidence / (4 - 1); // Distribute evenly among remaining classes
            confidences[i] = random(0, (int)(maxRemaining * 1000)) / 1000.0f;
            remainingConfidence -= confidences[i];
        }
    }
    
    // Ensure confidences sum to approximately 1.0
    confidences[randomIndex] += remainingConfidence;
    
    // Log all predictions like the real model would
    Serial.println("[Classification] Mock classification results:");
    for (int i = 0; i < 4; i++) {
        Serial.printf("[Classification] %s: %.1f%%\n", 
                     classifications[i].c_str(), 
                     confidences[i] * 100.0f);
    }
    
    String topClass = classifications[randomIndex];
    float topConfidence = confidences[randomIndex];
    
    // Simulate processing delay (real Edge Impulse inference takes time)
    delay(200);
    yield(); // Prevent watchdog timeout
    
    // Fill result structure
    result.detectedClass = topClass;
    result.confidence = topConfidence;
    result.isValid = true;
    
    Serial.printf("[Classification] ✅ Top prediction: %s (%.1f%% confidence)\n", 
                 topClass.c_str(), 
                 topConfidence * 100.0f);
    
    // Check if confidence meets threshold
    if (topConfidence < CONFIDENCE_THRESHOLD) {
        Serial.printf("[Classification] ⚠️ Low confidence (%.1f%% < %.1f%% threshold)\n", 
                     topConfidence * 100.0f, 
                     CONFIDENCE_THRESHOLD * 100.0f);
    }
    
    return result;
}

String getTopClass(const ClassificationResult& result) {
    if (!result.isValid) {
        return "unknown";
    }
    return result.detectedClass;
}

bool isConfidentResult(const ClassificationResult& result) {
    if (!result.isValid) {
        return false;
    }
    return result.confidence >= CONFIDENCE_THRESHOLD;
}

void printClassificationDetails(const ClassificationResult& result) {
    if (!result.isValid) {
        Serial.println("[Classification] Invalid result: " + result.errorMessage);
        return;
    }
    
    Serial.println("[Classification] === CLASSIFICATION DETAILS ===");
    Serial.printf("[Classification] Class: %s\n", result.detectedClass.c_str());
    Serial.printf("[Classification] Confidence: %.1f%% (%s)\n", 
                  result.confidence * 100.0f,
                  confidenceToString(result.confidence).c_str());
    Serial.printf("[Classification] Meets Threshold: %s (%.1f%% required)\n", 
                  isConfidentResult(result) ? "✅ YES" : "❌ NO",
                  CONFIDENCE_THRESHOLD * 100.0f);
    Serial.println("[Classification] ============================");
}

String confidenceToString(float confidence) {
    if (confidence >= 0.90f) return "Very High";
    if (confidence >= 0.75f) return "High";
    if (confidence >= 0.60f) return "Good";
    if (confidence >= 0.40f) return "Low";
    return "Very Low";
}
