#include "SmartBinClassifier.h"
#include "Logger.h"  // For centralized logging

SmartBinClassifier::SmartBinClassifier() {
    cameraInitialized = false;
}

SmartBinClassifier::~SmartBinClassifier() {
    deinitCamera();
}

bool SmartBinClassifier::initCamera() {
    if (cameraInitialized) {
        return true;
    }

    // Initialize camera using the Camera module
    if (!::initCamera()) {
        LOG_ERROR("Failed to initialize camera via Camera module");
        return false;
    }

    // Initialize classification system
    if (!initClassification()) {
        LOG_ERROR("Failed to initialize classification system");
        return false;
    }

    cameraInitialized = true;
    LOG_CLASSIFIER("SmartBinClassifier initialized successfully");
    return true;
}

void SmartBinClassifier::deinitCamera() {
    if (!cameraInitialized) {
        return;
    }

    cameraInitialized = false;
    LOG_CLASSIFIER("SmartBinClassifier deinitialized");
}

ClassificationResult SmartBinClassifier::captureAndClassify() {
    ClassificationResult result;
    
    if (!cameraInitialized) {
        result.success = false;
        result.isValid = false;
        result.error = "Camera not initialized";
        result.errorMessage = "Camera not initialized";
        return result;
    }

    // Capture image using Camera module
    CapturedImage image = captureImage();
    if (!image.isValid) {
        result.success = false;
        result.isValid = false;
        result.error = "Failed to capture image";
        result.errorMessage = "Failed to capture image";
        return result;
    }

    // Print captured image data for verification
    LOG_CLASSIFIER("Printing captured image data...");
    printImageAsBase64(image);

    // Classify using Classification module
    result = classifyImage(image);
    
    // Release the captured image
    releaseImage(image);
    
    // Update legacy compatibility fields
    if (result.isValid) {
        result.success = true;
        result.topClass = result.detectedClass;
        result.topConfidence = result.confidence;
        result.error = "";
        
        // Copy class confidence values to legacy format
        for (int i = 0; i < 4; i++) {
            if (result.classes[i] == result.detectedClass) {
                result.topConfidence = result.classConfidences[i];
            }
        }
    } else {
        result.success = false;
        result.error = result.errorMessage;
    }

    return result;
}

bool SmartBinClassifier::isCameraReady() {
    return cameraInitialized;
}
