#include "Classification.h"
#include <Arduino.h>

// Include model data
extern const unsigned char waste_classification_model[];
extern const int waste_classification_model_len;

// Classification confidence thresholds
const float CONFIDENCE_THRESHOLD = 0.60f;  // 60% minimum confidence
const float MINIMUM_CONFIDENCE = 0.30f;    // 30% absolute minimum

// Model configuration (adjust based on your trained model)
const int MODEL_INPUT_WIDTH = 48;    // Width your model expects
const int MODEL_INPUT_HEIGHT = 48;   // Height your model expects  
const int MODEL_INPUT_CHANNELS = 3;  // RGB channels
const int MODEL_OUTPUT_CLASSES = 4;  // metal, misc, paper, plastic

// Class names corresponding to model output indices
const char* class_names[MODEL_OUTPUT_CLASSES] = {"metal", "misc", "paper", "plastic"};

static bool classificationInitialized = false;

bool initClassification() {
    Serial.println("[Classification] Initializing classification system...");
    
    // For now, just simulate initialization
    // TODO: Add TensorFlow Lite initialization once library issues are resolved
    Serial.printf("[Classification] Model size: %d bytes\n", waste_classification_model_len);
    Serial.printf("[Classification] Expected input: %dx%dx%d\n", MODEL_INPUT_WIDTH, MODEL_INPUT_HEIGHT, MODEL_INPUT_CHANNELS);
    Serial.printf("[Classification] Output classes: %d\n", MODEL_OUTPUT_CLASSES);
    
    delay(100);
    yield(); // Prevent watchdog timeout
    
    Serial.println("[Classification] ✅ Classification initialized successfully (mock mode)");
    classificationInitialized = true;
    return true;
}

ClassificationResult classifyImage(const CapturedImage& image) {
    ClassificationResult result; // Use default constructor
    result.detectedClass = "unknown";
    result.confidence = 0.0f;
    result.isValid = false;
    result.errorMessage = "";
    for(int i = 0; i < 4; i++) {
        result.classConfidences[i] = 0.0f;
    }
    
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
    
    Serial.println("[Classification] Processing image (mock classification)...");
    Serial.printf("[Classification] Image details: %d bytes, %dx%d pixels\n", 
                  image.imageSize, 
                  image.frameBuffer->width, 
                  image.frameBuffer->height);
    
    yield(); // Prevent watchdog timeout
    
    // TODO: Replace this mock classification with real TensorFlow Lite inference
    // For now, simulate classification results for testing
    
    // Mock classification - randomly assign a class for testing
    int mockClassIndex = random(0, MODEL_OUTPUT_CLASSES);
    float mockConfidence = random(60, 95) / 100.0f; // 60-95% confidence
    
    result.detectedClass = String(class_names[mockClassIndex]);
    result.confidence = mockConfidence;
    result.isValid = true;
    result.errorMessage = "";
    
    // Fill class confidences (mock values)
    for(int i = 0; i < MODEL_OUTPUT_CLASSES; i++) {
        if (i == mockClassIndex) {
            result.classConfidences[i] = mockConfidence;
        } else {
            result.classConfidences[i] = random(5, 25) / 100.0f; // Low confidence for other classes
        }
    }
    
    // Update legacy compatibility fields
    result.topClass = result.detectedClass;
    result.topConfidence = result.confidence;
    result.success = result.isValid;
    result.error = result.errorMessage;
    
    Serial.printf("[Classification] ✅ Mock classification: %s (%.1f%% confidence)\n", 
                  result.detectedClass.c_str(), result.confidence * 100.0f);
    
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
    
    Serial.println("[Classification] All class confidences:");
    for (int i = 0; i < MODEL_OUTPUT_CLASSES; i++) {
        Serial.printf("[Classification] %s: %.1f%%\n", 
                     class_names[i], 
                     result.classConfidences[i] * 100.0f);
    }
    Serial.println("[Classification] ============================");
}

String confidenceToString(float confidence) {
    if (confidence >= 0.90f) return "Very High";
    if (confidence >= 0.75f) return "High";
    if (confidence >= 0.60f) return "Good";
    if (confidence >= 0.40f) return "Low";
    return "Very Low";
}

// Mock image preprocessing functions (placeholders for now)
bool preprocessImage(const CapturedImage& image, float* input_data) {
    // Mock preprocessing - just return true for now
    return true;
}

void resizeImage(uint8_t* src, int src_width, int src_height, 
                 float* dst, int dst_width, int dst_height) {
    // Mock resize - placeholder
}

void normalizePixels(float* image_data, int pixel_count) {
    // Mock normalization - placeholder
}

void printModelInfo() {
    if (!classificationInitialized) {
        Serial.println("[Classification] Model not initialized");
        return;
    }
    
    Serial.println("[Classification] === MODEL INFO (MOCK) ===");
    Serial.printf("[Classification] Model size: %d bytes\n", waste_classification_model_len);
    Serial.printf("[Classification] Input shape: [1, %d, %d, %d]\n",
                 MODEL_INPUT_HEIGHT, MODEL_INPUT_WIDTH, MODEL_INPUT_CHANNELS);
    Serial.printf("[Classification] Output classes: %d\n", MODEL_OUTPUT_CLASSES);
    Serial.println("[Classification] Classes: metal, misc, paper, plastic");
    Serial.println("[Classification] Mode: MOCK (for testing compilation)");
    Serial.println("[Classification] ==================");
}
