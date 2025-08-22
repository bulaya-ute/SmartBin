#ifndef CLASSIFICATION_H
#define CLASSIFICATION_H

#include <Arduino.h>
#include "Camera.h"

// Classification result structure
typedef struct {
    String detectedClass;
    float confidence;
    bool isValid;
    String errorMessage;
} ClassificationResult;

// Classification confidence thresholds
extern const float CONFIDENCE_THRESHOLD;
extern const float MINIMUM_CONFIDENCE;

// Classification functions
bool initClassification();
ClassificationResult classifyImage(const CapturedImage& image);
String getTopClass(const ClassificationResult& result);
bool isConfidentResult(const ClassificationResult& result);

// Utility functions for debugging
void printClassificationDetails(const ClassificationResult& result);
String confidenceToString(float confidence);

#endif
