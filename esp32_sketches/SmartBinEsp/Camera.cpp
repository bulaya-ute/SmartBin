#include "Camera.h"
#include <Arduino.h>

// Flash LED pin for AI Thinker ESP32-CAM
#define FLASH_LED_PIN 4  // GPIO 4 is the flash LED on AI Thinker

// Camera configuration for ESP32-CAM (AI Thinker model)
static camera_config_t camera_config = {
    .pin_pwdn = 32,        // Power down pin
    .pin_reset = -1,       // Reset pin (not connected on AI Thinker)
    .pin_xclk = 0,         // XCLK pin
    .pin_sscb_sda = 26,    // SIOD pin (I2C SDA)
    .pin_sscb_scl = 27,    // SIOC pin (I2C SCL)
    .pin_d7 = 35,          // D7 pin
    .pin_d6 = 34,          // D6 pin
    .pin_d5 = 39,          // D5 pin
    .pin_d4 = 36,          // D4 pin
    .pin_d3 = 21,          // D3 pin
    .pin_d2 = 19,          // D2 pin
    .pin_d1 = 18,          // D1 pin
    .pin_d0 = 5,           // D0 pin
    .pin_vsync = 25,       // VSYNC pin
    .pin_href = 23,        // HREF pin
    .pin_pclk = 22,        // PCLK pin

    .xclk_freq_hz = 20000000, // Back to 20MHz like working guide
    .ledc_timer = LEDC_TIMER_0,
    .ledc_channel = LEDC_CHANNEL_0,

    .pixel_format = PIXFORMAT_JPEG,   // JPEG format like working guide
    .frame_size = FRAMESIZE_UXGA,     // High resolution when PSRAM available
    .jpeg_quality = 10,               // Lower number = better quality
    .fb_count = 2,                    // 2 frame buffers like working guide
    .fb_location = CAMERA_FB_IN_PSRAM, // Use PSRAM for frame buffer
    .grab_mode = CAMERA_GRAB_WHEN_EMPTY
};

static bool cameraInitialized = false;

bool initCamera() {
    Serial.println("[Camera] Initializing ESP32-CAM (AI Thinker)...");
    yield(); // Prevent watchdog timeout
    
    // Initialize flash LED
    initFlash();
    
    // Configure camera based on PSRAM availability (like working guide)
    if (psramFound()) {
        Serial.println("[Camera] PSRAM found - using high resolution");
        camera_config.frame_size = FRAMESIZE_UXGA;
        camera_config.jpeg_quality = 10;
        camera_config.fb_count = 2;
    } else {
        Serial.println("[Camera] PSRAM not found - using lower resolution");
        camera_config.frame_size = FRAMESIZE_SVGA;
        camera_config.jpeg_quality = 12;
        camera_config.fb_count = 1;
    }
    
    // Initialize camera
    esp_err_t err = esp_camera_init(&camera_config);
    
    if (err != ESP_OK) {
        Serial.printf("[Camera] ERROR: Camera init failed with error 0x%x\n", err);
        cameraInitialized = false;
        return false;
    }
    
    // Get camera sensor for configuration
    sensor_t* sensor = esp_camera_sensor_get();
    if (sensor != NULL) {
        // Configure sensor settings for AI Thinker stability
        sensor->set_brightness(sensor, 0);     // Brightness (-2 to 2)
        sensor->set_contrast(sensor, 0);       // Contrast (-2 to 2)
        sensor->set_saturation(sensor, -1);    // Reduce saturation to prevent overflow
        sensor->set_special_effect(sensor, 0); // No special effects
        sensor->set_whitebal(sensor, 1);       // Enable white balance
        sensor->set_awb_gain(sensor, 1);       // Enable AWB gain
        sensor->set_wb_mode(sensor, 0);        // Auto white balance mode
        sensor->set_exposure_ctrl(sensor, 1);  // Enable exposure control
        sensor->set_aec2(sensor, 0);           // Disable AEC2
        sensor->set_ae_level(sensor, -1);      // Lower AE level to prevent overflow
        sensor->set_aec_value(sensor, 200);    // Lower AEC value for stability
        sensor->set_gain_ctrl(sensor, 1);      // Enable gain control
        sensor->set_agc_gain(sensor, 0);       // Lower AGC gain
        sensor->set_gainceiling(sensor, (gainceiling_t)2); // Lower gain ceiling
        sensor->set_bpc(sensor, 0);            // Black pixel correction
        sensor->set_wpc(sensor, 1);            // White pixel correction
        sensor->set_raw_gma(sensor, 1);        // Enable raw gamma
        sensor->set_lenc(sensor, 1);           // Enable lens correction
        sensor->set_hmirror(sensor, 0);        // Horizontal mirror
        sensor->set_vflip(sensor, 0);          // Vertical flip
        sensor->set_dcw(sensor, 1);            // DCW (downsize enable)
        sensor->set_colorbar(sensor, 0);       // Disable color bar test pattern
        
        Serial.println("[Camera] Sensor configured successfully");
    }
    
    delay(500); // Longer delay for AI Thinker stabilization
    yield(); // Prevent watchdog timeout
    
    // Clear any residual frames from automatic capture to prevent DMA overflow
    Serial.println("[Camera] Clearing DMA buffers...");
    for (int i = 0; i < 3; i++) {
        camera_fb_t* temp_fb = esp_camera_fb_get();
        if (temp_fb) {
            esp_camera_fb_return(temp_fb);
            Serial.printf("[Camera] Cleared buffer %d\n", i + 1);
        }
        delay(50);
        yield();
    }
    
    // Test capture to ensure DMA is working properly
    Serial.println("[Camera] Testing initial capture...");
    camera_fb_t* test_fb = esp_camera_fb_get();
    if (test_fb) {
        Serial.printf("[Camera] Test capture successful: %dx%d, %d bytes\n", 
                      test_fb->width, test_fb->height, test_fb->len);
        esp_camera_fb_return(test_fb);
    } else {
        Serial.println("[Camera] WARNING: Test capture failed, but continuing...");
    }
    
    Serial.println("[Camera] ✅ ESP32-CAM (AI Thinker) initialized successfully");
    cameraInitialized = true;
    return true;
}

bool isCameraReady() {
    return cameraInitialized;
}

CapturedImage captureImage() {
    CapturedImage result = {nullptr, 0, nullptr, false};
    
    if (!cameraInitialized) {
        Serial.println("[Camera] ERROR: Camera not initialized");
        return result;
    }
    
    Serial.println("[Camera] Starting image capture...");
    yield(); // Prevent watchdog timeout
    
    // Turn on flash before capture
    flashOn();
    
    // Add delay to allow flash to illuminate properly
    delay(150);
    
    // Simple capture approach like working guide
    camera_fb_t* frameBuffer = esp_camera_fb_get();
    
    // Turn off flash immediately after capture attempt
    flashOff();
    
    if (!frameBuffer) {
        Serial.println("[Camera] Error: Failed to capture image");
        return result;
    }
    
    // Check if frame buffer is valid
    if (frameBuffer->len == 0 || frameBuffer->buf == nullptr) {
        Serial.println("[Camera] ERROR: Invalid frame buffer - zero length or null data");
        Serial.printf("[Camera] Buffer details: len=%d, buf=%p\n", frameBuffer->len, frameBuffer->buf);
        esp_camera_fb_return(frameBuffer);
        return result;
    }
    
    Serial.printf("[Camera] ✅ Image captured successfully with flash: %dx%d, %d bytes, format: %d\n", 
                  frameBuffer->width, 
                  frameBuffer->height, 
                  frameBuffer->len,
                  frameBuffer->format);
    
    // Fill result structure
    result.frameBuffer = frameBuffer;
    result.imageSize = frameBuffer->len;
    result.imageData = frameBuffer->buf;
    result.isValid = true;
    
    return result;
}

void releaseImage(CapturedImage& image) {
    if (image.isValid && image.frameBuffer != nullptr) {
        esp_camera_fb_return(image.frameBuffer);
        Serial.println("[Camera] Image memory released");
    }
    
    // Reset the structure
    image.frameBuffer = nullptr;
    image.imageSize = 0;
    image.imageData = nullptr;
    image.isValid = false;
}

void clearDMABuffers() {
    if (!cameraInitialized) {
        Serial.println("[Camera] Cannot clear DMA - camera not initialized");
        return;
    }
    
    Serial.println("[Camera] Aggressively clearing DMA buffers...");
    int cleared = 0;
    
    // Clear up to 10 pending frames (increased from 5)
    for (int i = 0; i < 10; i++) {
        camera_fb_t* temp_fb = esp_camera_fb_get();
        if (temp_fb) {
            esp_camera_fb_return(temp_fb);
            cleared++;
            Serial.printf("[Camera] Cleared DMA buffer %d (size: %d bytes)\n", cleared, temp_fb->len);
            delay(20); // Slightly longer delay between clears
        } else {
            break; // No more frames to clear
        }
        yield();
    }
    
    if (cleared > 0) {
        Serial.printf("[Camera] ✅ Cleared %d DMA buffers\n", cleared);
    } else {
        Serial.println("[Camera] No DMA buffers to clear");
    }
    
    // Add a brief pause after clearing
    delay(50);
}

void initFlash() {
    pinMode(FLASH_LED_PIN, OUTPUT);
    digitalWrite(FLASH_LED_PIN, LOW); // Ensure flash starts OFF
    Serial.println("[Camera] Flash LED initialized (GPIO 4)");
}

void flashOn() {
    digitalWrite(FLASH_LED_PIN, HIGH);
    Serial.println("[Camera] Flash ON");
}

void flashOff() {
    digitalWrite(FLASH_LED_PIN, LOW);
    Serial.println("[Camera] Flash OFF");
}

void checkCameraStatus() {
    Serial.println("[Camera] === CAMERA STATUS CHECK ===");
    Serial.printf("[Camera] Initialized: %s\n", cameraInitialized ? "YES" : "NO");
    
    if (!cameraInitialized) {
        Serial.println("[Camera] Camera not initialized - run initCamera() first");
        return;
    }
    
    // Check sensor status
    sensor_t* sensor = esp_camera_sensor_get();
    if (sensor) {
        Serial.println("[Camera] Sensor: DETECTED");
        Serial.printf("[Camera] Sensor ID: 0x%02X\n", sensor->id.PID);
    } else {
        Serial.println("[Camera] Sensor: NOT DETECTED - CRITICAL ERROR");
    }
    
    // Try a quick test capture to check DMA status
    Serial.println("[Camera] Testing DMA with quick capture...");
    camera_fb_t* test_fb = esp_camera_fb_get();
    if (test_fb) {
        Serial.printf("[Camera] DMA Status: OK (captured %dx%d, %d bytes)\n", 
                      test_fb->width, test_fb->height, test_fb->len);
        esp_camera_fb_return(test_fb);
    } else {
        Serial.println("[Camera] DMA Status: FAILED - DMA overflow likely");
    }
    
    Serial.println("[Camera] ========================");
}
