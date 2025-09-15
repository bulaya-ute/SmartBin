# SmartBin ESP32-Laptop Communication Protocol

## Overview
This protocol enables reliable communication between the ESP32-CAM and laptop for image classification.

## Message Format
All messages use JSON format with the following structure:
```json
{
  "type": "MESSAGE_TYPE",
  "timestamp": 123456789,
  "data": {...}
}
```

## Message Types

### 1. Handshake Messages
**ESP32 → Laptop:**
```json
{
  "type": "WAITING_LAPTOP",
  "timestamp": 123456789,
  "data": {
    "device_id": "SmartBin_ESP32",
    "version": "1.0",
    "capabilities": ["image_capture", "classification"]
  }
}
```

**Laptop → ESP32:**
```json
{
  "type": "LAPTOP_READY",
  "timestamp": 123456789,
  "data": {
    "device_id": "SmartBin_Laptop",
    "version": "1.0",
    "ready": true
  }
}
```

### 2. Image Classification Messages
**ESP32 → Laptop:**
```json
{
  "type": "IMAGE_DATA",
  "timestamp": 123456789,
  "data": {
    "image_id": "img_001",
    "format": "JPEG",
    "size": 12345,
    "width": 640,
    "height": 480,
    "base64_data": "/9j/4AAQSkZJRgAB..."
  }
}
```

**Laptop → ESP32 (Success):**
```json
{
  "type": "CLASSIFICATION_RESULT",
  "timestamp": 123456789,
  "data": {
    "image_id": "img_001",
    "classification": "recyclable",
    "confidence": 0.85,
    "processing_time_ms": 234
  }
}
```

**Laptop → ESP32 (Error):**
```json
{
  "type": "CLASSIFICATION_ERROR",
  "timestamp": 123456789,
  "data": {
    "image_id": "img_001",
    "error_code": "DECODE_FAILED",
    "error_message": "Could not decode Base64 image data",
    "retry_suggested": true
  }
}
```

### 3. Status Messages
**ESP32 → Laptop:**
```json
{
  "type": "STATUS_UPDATE",
  "timestamp": 123456789,
  "data": {
    "status": "waiting_classification",
    "last_image_id": "img_001",
    "uptime_ms": 567890
  }
}
```

**Laptop → ESP32:**
```json
{
  "type": "HEARTBEAT",
  "timestamp": 123456789,
  "data": {
    "status": "online"
  }
}
```

## Error Codes
- `DECODE_FAILED`: Base64 decoding failed (retry suggested)
- `INVALID_FORMAT`: Image format not supported
- `CLASSIFICATION_FAILED`: Model inference failed
- `TIMEOUT`: Processing took too long
- `DISCONNECTED`: Connection lost

## Timeout Handling
- **ESP32 waits 10 seconds** for laptop responses
- **Laptop sends heartbeat** every 30 seconds when idle
- **Connection assumed lost** after 3 consecutive timeouts
- **Automatic reconnection** triggered on connection loss

## State Machine

### ESP32 States:
1. `INIT` - Starting up
2. `WAITING_LAPTOP` - Broadcasting connection request
3. `CONNECTED` - Handshake completed
4. `CAPTURING` - Taking photo
5. `SENDING_IMAGE` - Transmitting image data
6. `WAITING_RESULT` - Waiting for classification
7. `PROCESSING_RESULT` - Handling response
8. `ERROR` - Error state, will retry

### Laptop States:
1. `SCANNING` - Looking for ESP32
2. `CONNECTING` - Establishing connection
3. `HANDSHAKE` - Exchanging ready messages
4. `READY` - Waiting for images
5. `PROCESSING` - Classifying image
6. `RESPONDING` - Sending result
7. `ERROR` - Error state, will retry
