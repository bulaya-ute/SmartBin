# Smart Bin Classification System

This module provides modular functions for capturing images from ESP32-CAM and performing waste classification using Edge Impulse machine learning.

## Features

- **Modular Design**: Separate functions for camera initialization, image capture, and classification
- **Edge Impulse Integration**: Uses your trained model to classify waste into 4 categories:
  - Metal
  - Paper  
  - Plastic
  - Miscellaneous
- **Confidence Thresholding**: Only acts on high-confidence predictions
- **Error Handling**: Comprehensive error reporting and recovery

## Files

- `SmartBinClassifier.h/.cpp` - Main classifier class with modular functions
- `SmartBinClassifier_Example.ino` - Standalone example showing how to use the classifier
- `CameraInference.h/.cpp` - Updated to integrate with your existing SmartBin system

## Usage

### Option 1: Using the Classifier Class Directly

```cpp
#include "SmartBinClassifier.h"

SmartBinClassifier classifier;

void setup() {
    Serial.begin(115200);
    classifier.initCamera();
}

void loop() {
    // Capture and classify in one call
    ClassificationResult result = classifier.captureAndClassify();
    
    if (result.success && result.topConfidence > 0.7) {
        Serial.printf("Detected: %s (%.1f%% confidence)\n", 
                     result.topClass.c_str(), 
                     result.topConfidence * 100.0);
        
        // Take action based on classification
        if (result.topClass == "plastic") {
            // Open plastic bin
        } else if (result.topClass == "metal") {
            // Open metal bin
        }
        // etc.
    }
    
    delay(5000);
}
```

### Option 2: Using with Existing SmartBin System

Your existing code in `SmartBinEsp.ino` will now use the Edge Impulse classifier through the updated `CameraInference` module. No changes needed to your main loop!

### Option 3: Separate Capture and Classification

```cpp
// Capture image
if (classifier.captureImage()) {
    // Classify the captured image
    ClassificationResult result = classifier.classifyImage();
    
    if (result.success) {
        // Process results...
    }
}
```

## Hardware Requirements

- ESP32-CAM (ESP-EYE model recommended)
- PSRAM enabled
- Your Edge Impulse library (`smart-bin_inferencing`)

## Installation

1. Copy `SmartBinClassifier.h` and `SmartBinClassifier.cpp` to your Arduino sketch folder
2. Make sure your Edge Impulse library is installed and accessible
3. Include the header file: `#include "SmartBinClassifier.h"`
4. Update your existing `CameraInference.h/.cpp` files with the new versions provided

## Configuration

The classifier is configured for ESP-EYE camera model. If using AI-Thinker or other models, update the pin definitions in `SmartBinClassifier.h`:

```cpp
// For AI-Thinker model, uncomment and modify:
// #define CAMERA_MODEL_AI_THINKER
```

## Edge Impulse Model Details

- **Input Size**: 48x48 pixels
- **Categories**: metal, misc, paper, plastic  
- **Confidence Threshold**: 0.6 (adjustable)
- **Model Type**: Classification (not object detection)

## API Reference

### SmartBinClassifier Class

#### Methods

- `bool initCamera()` - Initialize ESP32-CAM
- `void deinitCamera()` - Clean up camera resources  
- `bool captureImage()` - Capture image from camera
- `ClassificationResult classifyImage()` - Classify captured image
- `ClassificationResult captureAndClassify()` - Capture and classify in one call
- `bool isCameraReady()` - Check if camera is initialized
- `uint8_t* getImageBuffer()` - Get raw image buffer (for debugging)

#### ClassificationResult Structure

```cpp
struct ClassificationResult {
    String topClass;          // Most likely class
    float topConfidence;      // Confidence of top class (0.0 - 1.0)
    float confidence[4];      // Confidence for all classes
    String classes[4];        // Class names
    bool success;             // Whether classification succeeded
    String error;             // Error message if failed
};
```

## Troubleshooting

1. **Camera init failed**: Check pin connections and camera model configuration
2. **Low confidence**: Improve lighting conditions or retrain model with more data
3. **Classification failed**: Ensure Edge Impulse library is properly installed
4. **Memory issues**: Make sure PSRAM is enabled on ESP32-CAM

## Performance Tips

- Ensure good lighting for better classification accuracy
- Keep objects centered in camera view
- Consider adding a confidence threshold appropriate for your use case
- Monitor memory usage - the system allocates ~230KB for image processing
