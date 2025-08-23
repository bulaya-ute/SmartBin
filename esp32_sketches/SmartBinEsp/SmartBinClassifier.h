#ifndef SMARTBIN_CLASSIFIER_H
#define SMARTBIN_CLASSIFIER_H

// Use the new TensorFlow Lite classification system
#include "Classification.h"
#include "Camera.h"

// Legacy wrapper class for backward compatibility
class SmartBinClassifier {
private:
    bool cameraInitialized;
    
public:
    SmartBinClassifier();
    ~SmartBinClassifier();
    
    // Initialize the camera (delegates to Camera module)
    bool initCamera();
    
    // Deinitialize the camera
    void deinitCamera();
    
    // Capture image and classify using new modular system
    ClassificationResult captureAndClassify();
    
    // Check if camera is initialized
    bool isCameraReady();
};

#endif // SMARTBIN_CLASSIFIER_H
