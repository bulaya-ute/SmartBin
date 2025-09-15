#include "Classification.h"
#include <Arduino.h>
#include "Logger.h"  // For centralized logging

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
    LOG_CLASSIFICATION("Initializing classification system...");
    
    // For now, just simulate initialization
    // TODO: Add TensorFlow Lite initialization once library issues are resolved
    logMessage("[Classification] Model size: " + String(waste_classification_model_len) + " bytes");
    logMessage("[Classification] Expected input: " + String(MODEL_INPUT_WIDTH) + "x" + String(MODEL_INPUT_HEIGHT) + "x" + String(MODEL_INPUT_CHANNELS));
    logMessage("[Classification] Output classes: " + String(MODEL_OUTPUT_CLASSES));
    
    delay(100);
    yield(); // Prevent watchdog timeout
    
    LOG_CLASSIFICATION("✅ Classification initialized successfully (mock mode)");
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
        LOG_ERROR(result.errorMessage);
        return result;
    }
    
    if (!image.isValid) {
        result.errorMessage = "Invalid input image";
        LOG_ERROR(result.errorMessage);
        return result;
    }
    
    LOG_CLASSIFICATION("Processing image (mock classification)...");
    logMessage("[Classification] Image details: " + String(image.imageSize) + " bytes, " + String(image.frameBuffer->width) + "x" + String(image.frameBuffer->height) + " pixels");
    
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
    
    logMessage("[Classification] ✅ Mock classification: " + result.detectedClass + " (" + String(result.confidence * 100.0f, 1) + "% confidence)");
    
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
        LOG_WARNING("Invalid result: " + result.errorMessage);
        return;
    }
    
    LOG_CLASSIFICATION("=== CLASSIFICATION DETAILS ===");
    logMessage("[Classification] Class: " + result.detectedClass);
    logMessage("[Classification] Confidence: " + String(result.confidence * 100.0f, 1) + "% (" + confidenceToString(result.confidence) + ")");
    logMessage("[Classification] Meets Threshold: " + String(isConfidentResult(result) ? "✅ YES" : "❌ NO") + " (" + String(CONFIDENCE_THRESHOLD * 100.0f, 1) + "% required)");
    
    LOG_CLASSIFICATION("All class confidences:");
    for (int i = 0; i < MODEL_OUTPUT_CLASSES; i++) {
        logMessage("[Classification] " + String(class_names[i]) + ": " + String(result.classConfidences[i] * 100.0f, 1) + "%");
    }
    LOG_CLASSIFICATION("============================");
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
        LOG_WARNING("Model not initialized");
        return;
    }
    
    LOG_CLASSIFICATION("=== MODEL INFO (MOCK) ===");
    logMessage("[Classification] Model size: " + String(waste_classification_model_len) + " bytes");
    logMessage("[Classification] Input shape: [1, " + String(MODEL_INPUT_HEIGHT) + ", " + String(MODEL_INPUT_WIDTH) + ", " + String(MODEL_INPUT_CHANNELS) + "]");
    logMessage("[Classification] Output classes: " + String(MODEL_OUTPUT_CLASSES));
    logMessage("[Classification] Classes: metal, misc, paper, plastic");
    LOG_CLASSIFICATION("Mode: MOCK (for testing compilation)");
    LOG_CLASSIFICATION("==================");
}
