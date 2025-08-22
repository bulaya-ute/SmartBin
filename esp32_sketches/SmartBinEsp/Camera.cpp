#include "Camera.h"
#include <Arduino.h>

// Camera configuration for ESP32-CAM (ESP_EYE model)
static camera_config_t camera_config = {
    .pin_pwdn = -1,        // Power down pin (not used on ESP_EYE)
    .pin_reset = -1,       // Reset pin (not used on ESP_EYE)
    .pin_xclk = 4,         // XCLK pin
    .pin_sscb_sda = 18,    // SIOD pin
    .pin_sscb_scl = 23,    // SIOC pin
    .pin_d7 = 36,          // D7 pin
    .pin_d6 = 37,          // D6 pin
    .pin_d5 = 38,          // D5 pin
    .pin_d4 = 39,          // D4 pin
    .pin_d3 = 35,          // D3 pin
    .pin_d2 = 14,          // D2 pin
    .pin_d1 = 13,          // D1 pin
    .pin_d0 = 34,          // D0 pin
    .pin_vsync = 5,        // VSYNC pin
    .pin_href = 27,        // HREF pin
    .pin_pclk = 25,        // PCLK pin

    .xclk_freq_hz = 20000000, // XCLK frequency
    .ledc_timer = LEDC_TIMER_0,
    .ledc_channel = LEDC_CHANNEL_0,

    .pixel_format = PIXFORMAT_RGB565, // Use RGB565 for compatibility
    .frame_size = FRAMESIZE_QQVGA,    // 160x120 for fast processing
    .jpeg_quality = 12,               // JPEG quality (0-63, lower = better)
    .fb_count = 1,                    // Number of frame buffers
    .fb_location = CAMERA_FB_IN_PSRAM, // Use PSRAM for frame buffer
    .grab_mode = CAMERA_GRAB_WHEN_EMPTY
};

static bool cameraInitialized = false;

bool initCamera() {
    Serial.println("[Camera] Initializing ESP32-CAM...");
    yield(); // Prevent watchdog timeout
    
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
        // Optional: Configure sensor settings
        sensor->set_brightness(sensor, 0);     // Brightness (-2 to 2)
        sensor->set_contrast(sensor, 0);       // Contrast (-2 to 2)
        sensor->set_saturation(sensor, 0);     // Saturation (-2 to 2)
        sensor->set_special_effect(sensor, 0); // No special effects
        sensor->set_whitebal(sensor, 1);       // Enable white balance
        sensor->set_awb_gain(sensor, 1);       // Enable AWB gain
        sensor->set_wb_mode(sensor, 0);        // Auto white balance mode
        sensor->set_exposure_ctrl(sensor, 1);  // Enable exposure control
        sensor->set_aec2(sensor, 0);           // Disable AEC2
        sensor->set_ae_level(sensor, 0);       // AE level (-2 to 2)
        sensor->set_aec_value(sensor, 300);    // AEC value (0 to 1200)
        sensor->set_gain_ctrl(sensor, 1);      // Enable gain control
        sensor->set_agc_gain(sensor, 0);       // AGC gain (0 to 30)
        sensor->set_gainceiling(sensor, (gainceiling_t)0); // Gain ceiling
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
    
    delay(100); // Allow camera to stabilize
    yield(); // Prevent watchdog timeout
    
    Serial.println("[Camera] ✅ ESP32-CAM initialized successfully");
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
    
    Serial.println("[Camera] Capturing image...");
    yield(); // Prevent watchdog timeout
    
    // Capture frame
    camera_fb_t* frameBuffer = esp_camera_fb_get();
    
    if (!frameBuffer) {
        Serial.println("[Camera] ERROR: Failed to capture image");
        return result;
    }
    
    // Check if frame buffer is valid
    if (frameBuffer->len == 0 || frameBuffer->buf == nullptr) {
        Serial.println("[Camera] ERROR: Invalid frame buffer");
        esp_camera_fb_return(frameBuffer);
        return result;
    }
    
    Serial.printf("[Camera] ✅ Image captured successfully: %dx%d, %d bytes, format: %d\n", 
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
