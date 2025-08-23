#ifndef CLASSIFICATION_H
#define CLASSIFICATION_H

#include <Arduino.h>
#include "Camera.h"

// Model data (will be replaced with your trained model)
extern const unsigned char waste_classification_model[];
extern const int waste_classification_model_len;

// Classification result structure
struct ClassificationResult {
    String detectedClass;
    float confidence;
    bool isValid;
    String errorMessage;
    float classConfidences[4]; // metal, misc, paper, plastic
    
    // Legacy compatibility fields for old SmartBinClassifier
    String topClass;
    float topConfidence;
    bool success;
    String error;
    String classes[4];
    
    // Constructor for easy initialization
    ClassificationResult() : confidence(0.0f), isValid(false), topConfidence(0.0f), success(false) {
        for(int i = 0; i < 4; i++) {
            classConfidences[i] = 0.0f;
        }
        classes[0] = "metal";
        classes[1] = "misc"; 
        classes[2] = "paper";
        classes[3] = "plastic";
    }
};

// Classification confidence thresholds
extern const float CONFIDENCE_THRESHOLD;
extern const float MINIMUM_CONFIDENCE;

// Model configuration
extern const int MODEL_INPUT_WIDTH;
extern const int MODEL_INPUT_HEIGHT;
extern const int MODEL_INPUT_CHANNELS;
extern const int MODEL_OUTPUT_CLASSES;

// Model configuration
extern const int MODEL_INPUT_WIDTH;
extern const int MODEL_INPUT_HEIGHT;
extern const int MODEL_INPUT_CHANNELS;
extern const int MODEL_OUTPUT_CLASSES;

// Classification functions
bool initClassification();
ClassificationResult classifyImage(const CapturedImage& image);
String getTopClass(const ClassificationResult& result);
bool isConfidentResult(const ClassificationResult& result);

// Image preprocessing functions
bool preprocessImage(const CapturedImage& image, float* input_data);
void resizeImage(uint8_t* src, int src_width, int src_height, 
                 float* dst, int dst_width, int dst_height);
void normalizePixels(float* image_data, int pixel_count);

// Utility functions for debugging
void printClassificationDetails(const ClassificationResult& result);
String confidenceToString(float confidence);
void printModelInfo();

#endif
