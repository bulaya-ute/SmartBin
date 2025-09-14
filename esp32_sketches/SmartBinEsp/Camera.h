#ifndef CAMERA_H
#define CAMERA_H

#include <Arduino.h>
#include "esp_camera.h"

// Camera configuration structure
typedef struct {
    camera_fb_t* frameBuffer;
    size_t imageSize;
    uint8_t* imageData;
    bool isValid;
} CapturedImage;

// Camera initialization and control
bool initCamera();
bool isCameraReady();
CapturedImage captureImage();
void releaseImage(CapturedImage& image);
void clearDMABuffers(); // New function to manually clear DMA buffers
void checkCameraStatus(); // Diagnostic function to check camera health

// Flash control functions
void initFlash();
void flashOn();
void flashOff();

// Camera configuration for ESP32-CAM (ESP_EYE model)
void setupCameraConfig();

#endif
