#include "Camera.h"
#include <Arduino.h>
#include "mbedtls/base64.h"  // For Base64 encoding
#include "Logger.h"  // For centralized logging

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
    LOG_CAMERA("Initializing ESP32-CAM (AI Thinker)...");
    yield(); // Prevent watchdog timeout
    
    // Initialize flash LED
    initFlash();
    
    // Configure camera based on PSRAM availability - using lower resolutions for better Bluetooth transmission
    if (psramFound()) {
        LOG_CAMERA("PSRAM found - using medium resolution for classification");
        camera_config.frame_size = FRAMESIZE_VGA;  // 640x480 - good for classification
        camera_config.jpeg_quality = 15;           // Moderate compression
        camera_config.fb_count = 2;
    } else {
        LOG_CAMERA("PSRAM not found - using lower resolution");
        camera_config.frame_size = FRAMESIZE_QVGA; // 320x240 - minimum for classification
        camera_config.jpeg_quality = 20;           // Higher compression
        camera_config.fb_count = 1;
    }
    
    // Initialize camera
    esp_err_t err = esp_camera_init(&camera_config);
    
    if (err != ESP_OK) {
        logMessage("[Camera] ERROR: Camera init failed with error 0x" + String(err, HEX));
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
        
        LOG_CAMERA("Sensor configured successfully");
    }
    
    delay(500); // Longer delay for AI Thinker stabilization
    yield(); // Prevent watchdog timeout
    
    // Clear any residual frames from automatic capture to prevent DMA overflow
    LOG_CAMERA("Clearing DMA buffers...");
    for (int i = 0; i < 3; i++) {
        camera_fb_t* temp_fb = esp_camera_fb_get();
        if (temp_fb) {
            esp_camera_fb_return(temp_fb);
            logMessage("[Camera] Cleared buffer " + String(i + 1));
        }
        delay(50);
        yield();
    }
    
    // Test capture to ensure DMA is working properly
    LOG_CAMERA("Testing initial capture...");
    camera_fb_t* test_fb = esp_camera_fb_get();
    if (test_fb) {
        logMessage("[Camera] Test capture successful: " + String(test_fb->width) + "x" + String(test_fb->height) + ", " + String(test_fb->len) + " bytes");
        esp_camera_fb_return(test_fb);
    } else {
        LOG_WARNING("Camera test capture failed, but continuing...");
    }
    
    LOG_CAMERA("✅ ESP32-CAM (AI Thinker) initialized successfully");
    cameraInitialized = true;
    return true;
}

bool isCameraReady() {
    return cameraInitialized;
}

CapturedImage captureImage() {
    CapturedImage result = {nullptr, 0, nullptr, false};
    
    if (!cameraInitialized) {
        LOG_ERROR("Camera not initialized");
        return result;
    }
    
    LOG_CAMERA("Starting image capture...");
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
        LOG_ERROR("Failed to capture image");
        return result;
    }
    
    // Check if frame buffer is valid
    if (frameBuffer->len == 0 || frameBuffer->buf == nullptr) {
        LOG_ERROR("Invalid frame buffer - zero length or null data");
        logMessage("[Camera] Buffer details: len=" + String(frameBuffer->len) + ", buf=" + String((unsigned long)frameBuffer->buf, HEX));
        esp_camera_fb_return(frameBuffer);
        return result;
    }
    
    logMessage("[Camera] ✅ Image captured successfully with flash: " + String(frameBuffer->width) + "x" + String(frameBuffer->height) + ", " + String(frameBuffer->len) + " bytes, format: " + String(frameBuffer->format));
    
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
        LOG_CAMERA("Image memory released");
    }
    
    // Reset the structure
    image.frameBuffer = nullptr;
    image.imageSize = 0;
    image.imageData = nullptr;
    image.isValid = false;
}

void clearDMABuffers() {
    if (!cameraInitialized) {
        LOG_WARNING("Cannot clear DMA - camera not initialized");
        return;
    }
    
    LOG_CAMERA("Aggressively clearing DMA buffers...");
    int cleared = 0;
    
    // Clear up to 10 pending frames (increased from 5)
    for (int i = 0; i < 10; i++) {
        camera_fb_t* temp_fb = esp_camera_fb_get();
        if (temp_fb) {
            esp_camera_fb_return(temp_fb);
            cleared++;
            logMessage("[Camera] Cleared DMA buffer " + String(cleared) + " (size: " + String(temp_fb->len) + " bytes)");
            delay(20); // Slightly longer delay between clears
        } else {
            break; // No more frames to clear
        }
        yield();
    }
    
    if (cleared > 0) {
        logMessage("[Camera] ✅ Cleared " + String(cleared) + " DMA buffers");
    } else {
        LOG_CAMERA("No DMA buffers to clear");
    }
    
    // Add a brief pause after clearing
    delay(50);
}

void initFlash() {
    pinMode(FLASH_LED_PIN, OUTPUT);
    digitalWrite(FLASH_LED_PIN, LOW); // Ensure flash starts OFF
    LOG_CAMERA("Flash LED initialized (GPIO 4)");
}

void flashOn() {
    digitalWrite(FLASH_LED_PIN, HIGH);
    LOG_DEBUG("Flash ON");
}

void flashOff() {
    digitalWrite(FLASH_LED_PIN, LOW);
    LOG_DEBUG("Flash OFF");
}

void checkCameraStatus() {
    LOG_CAMERA("=== CAMERA STATUS CHECK ===");
    logMessage("[Camera] Initialized: " + String(cameraInitialized ? "YES" : "NO"));
    
    if (!cameraInitialized) {
        LOG_WARNING("Camera not initialized - run initCamera() first");
        return;
    }
    
    // Check sensor status
    sensor_t* sensor = esp_camera_sensor_get();
    if (sensor) {
        LOG_CAMERA("Sensor: DETECTED");
        logMessage("[Camera] Sensor ID: 0x" + String(sensor->id.PID, HEX));
    } else {
        LOG_ERROR("Sensor: NOT DETECTED - CRITICAL ERROR");
    }
    
    // Try a quick test capture to check DMA status
    LOG_CAMERA("Testing DMA with quick capture...");
    camera_fb_t* test_fb = esp_camera_fb_get();
    if (test_fb) {
        logMessage("[Camera] DMA Status: OK (captured " + String(test_fb->width) + "x" + String(test_fb->height) + ", " + String(test_fb->len) + " bytes)");
        esp_camera_fb_return(test_fb);
    } else {
        LOG_ERROR("DMA Status: FAILED - DMA overflow likely");
    }
    
    LOG_CAMERA("========================");
}

void printImageAsBase64(const CapturedImage& image) {
    if (!image.isValid) {
        LOG_ERROR("Cannot print invalid image");
        return;
    }
    
    if (!image.frameBuffer || !image.imageData || image.imageSize == 0) {
        LOG_ERROR("Invalid image data");
        return;
    }
    
    LOG_CAMERA("=== IMAGE DATA OUTPUT ===");
    
    // Send image metadata to Bluetooth for monitoring
    logMessage("==IMAGE_START==");
    logMessage("FORMAT: JPEG");
    logMessage("SIZE: " + String(image.imageSize) + " bytes");
    logMessage("DIMENSIONS: " + String(image.frameBuffer->width) + "x" + String(image.frameBuffer->height));
    logMessage("TIMESTAMP: " + String(millis()));
    logMessage("BASE64_DATA: [Starting transmission...]");
    
    // Keep structured output for Python decoder - these must stay as Serial.println()
    Serial.println("==IMAGE_START==");
    Serial.printf("FORMAT: JPEG\n");
    Serial.printf("SIZE: %d bytes\n", image.imageSize);
    Serial.printf("DIMENSIONS: %dx%d\n", image.frameBuffer->width, image.frameBuffer->height);
    Serial.printf("TIMESTAMP: %lu\n", millis());
    Serial.println("BASE64_DATA:");
    
    // Calculate required buffer size for Base64 encoding
    // Base64 encoded size is approximately 4/3 of original size
    size_t base64_len = 0;
    
    // First call to get required buffer size
    int ret = mbedtls_base64_encode(NULL, 0, &base64_len, image.imageData, image.imageSize);
    if (ret != MBEDTLS_ERR_BASE64_BUFFER_TOO_SMALL) {
        LOG_ERROR("Failed to calculate Base64 buffer size");
        return;
    }
    
    // Print image data in chunks to avoid memory issues
    const size_t CHUNK_SIZE = 3000; // Process 3KB at a time (4KB Base64 output)
    const size_t LINE_LENGTH = 80;  // 80 characters per line for readability
    
    size_t processed = 0;
    char base64_chunk[4096]; // Buffer for Base64 output
    String bluetoothBase64Data = ""; // Accumulate Base64 for Bluetooth transmission
    
    while (processed < image.imageSize) {
        // Calculate chunk size for this iteration
        size_t current_chunk = min(CHUNK_SIZE, image.imageSize - processed);
        
        // Encode this chunk
        size_t chunk_b64_len = 0;
        ret = mbedtls_base64_encode((unsigned char*)base64_chunk, sizeof(base64_chunk), 
                                   &chunk_b64_len, 
                                   image.imageData + processed, 
                                   current_chunk);
        
        if (ret != 0) {
            logMessage("[Camera] ERROR: Base64 encoding failed at offset " + String(processed) + ", error: " + String(ret));
            break;
        }
        
        // Add to Bluetooth data string (will be chunked automatically by logger)
        bluetoothBase64Data += String(base64_chunk).substring(0, chunk_b64_len);
        
        // Print the Base64 data to Serial in lines of specified length (for Python decoder)
        for (size_t i = 0; i < chunk_b64_len; i += LINE_LENGTH) {
            size_t line_len = min(LINE_LENGTH, chunk_b64_len - i);
            
            // Print line with null termination
            for (size_t j = 0; j < line_len; j++) {
                Serial.print((char)base64_chunk[i + j]);
            }
            Serial.println(); // New line after each chunk
            
            // Small delay to prevent overwhelming the serial buffer
            if (i % (LINE_LENGTH * 10) == 0) {
                delay(10);
                yield();
            }
        }
        
        processed += current_chunk;
        
        // Progress indicator
        float progress = (float)processed / image.imageSize * 100.0f;
        if ((int)progress % 20 == 0) {
            logMessage("[Camera] Progress: " + String((int)progress) + "%");
        }
        
        yield(); // Prevent watchdog timeout
    }
    
    // Send complete Base64 data to Bluetooth (will be automatically chunked)
    if (bluetoothBase64Data.length() > 0) {
        logLongMessage(bluetoothBase64Data, "[IMG_B64] ");
    }
    
    // Keep structured output for Python decoder
    Serial.println("==IMAGE_END==");
    logMessage("==IMAGE_END==");
    LOG_CAMERA("=== IMAGE DATA OUTPUT COMPLETE ===");
    logMessage("[Camera] Total bytes processed: " + String(processed));
}
