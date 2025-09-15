# SmartBin Communication Protocol - User Guide

## Overview
The SmartBin now uses a sophisticated communication protocol between the ESP32-CAM and your laptop for intelligent image classification. This replaces the simple Base64 output with a robust, two-way communication system.

## How It Works

### 1. **Startup Sequence**
1. ESP32 boots up and initializes all modules
2. ESP32 waits for laptop connection via Bluetooth
3. ESP32 broadcasts "WAITING_LAPTOP" messages every 3 seconds
4. Laptop daemon automatically connects and sends "LAPTOP_READY"
5. Handshake completed - system ready for operation

### 2. **Image Classification Flow**
1. ESP32 detects item with ultrasonic sensor
2. ESP32 captures image with camera
3. ESP32 sends image data to laptop via Bluetooth (JSON format)
4. Laptop processes image with YOLO model
5. Laptop sends classification result back to ESP32
6. ESP32 operates bin mechanism based on result

### 3. **Error Handling & Recovery**
- **10-second timeouts** for laptop responses
- **Automatic reconnection** if connection lost
- **Retry logic** for failed classifications
- **Fallback to local** classification if laptop unavailable

## Setup Instructions

### Prerequisites
1. **ESP32 Requirements:**
   - ArduinoJson library installed
   - Communication.h and Communication.cpp in project
   - Updated SmartBinEsp.ino with communication protocol

2. **Laptop Requirements:**
   - Python 3.7+
   - PyBluez: `sudo apt install python3-bluez`
   - ultralytics: `pip install ultralytics`
   - PIL: `pip install Pillow`

### Installation Steps

#### 1. **Compile and Upload ESP32 Code**
```bash
# Make sure ArduinoJson library is installed in Arduino IDE
# Upload the updated SmartBinEsp.ino to your ESP32
```

#### 2. **Test Laptop Daemon**
```bash
# Install dependencies
pip install ultralytics Pillow

# Test the daemon
python3 smartbin_laptop_daemon.py
```

#### 3. **Run the Complete System**
```bash
# Terminal 1: Start the laptop daemon
python3 smartbin_laptop_daemon.py

# Terminal 2: Monitor Bluetooth output (optional)
python3 bluetooth_monitor.py
```

## Usage

### **Normal Operation**
1. **Start laptop daemon first:**
   ```bash
   python3 smartbin_laptop_daemon.py
   ```
   
2. **Power on ESP32** - it will automatically:
   - Initialize all modules
   - Search for laptop connection
   - Complete handshake when laptop is ready
   - Begin normal operation

3. **Monitor the process:**
   - Laptop daemon shows connection status
   - ESP32 broadcasts waiting messages until connected
   - Both devices log classification requests/responses

### **Expected Output**

#### **Laptop Daemon:**
```
🤖 SmartBin Laptop Daemon v1.0
Target ESP32: SmartBin_ESP32 (EC:E3:34:15:F2:62)
🧠 Loading YOLO model: best.pt
✅ YOLO model loaded successfully
🚀 Starting communication daemon...
🔗 Attempting to connect to EC:E3:34:15:F2:62...
✅ Bluetooth connection established
📢 ESP32: [COMM] Broadcasting laptop connection request
✅ Sent ready signal to ESP32
📸 Received image for classification
🎯 Running YOLO classification...
✅ YOLO result: plastic_bottle -> recyclable (0.874)
✅ Sent classification result: recyclable (0.87)
```

#### **ESP32 (via Bluetooth monitor):**
```
[COMM] Initializing communication system
[COMM] Broadcasting laptop connection request
[COMM] Laptop ready signal received
[COMM] State change WAITING_LAPTOP -> CONNECTED
[Camera] Starting image capture...
[Camera] ✅ Image captured successfully
[COMM] Converting image to Base64 - Size: 15432 bytes
[COMM] Sending image for classification - img_123456
[COMM] State change SENDING_IMAGE -> WAITING_RESULT
[COMM] Classification result received - recyclable
[COMM] State change WAITING_RESULT -> CONNECTED
[Servo] Moving to recyclable bin position
```

## Troubleshooting

### **Connection Issues**
- **ESP32 shows "waiting for laptop":** Start the laptop daemon
- **Laptop can't connect:** Check ESP32 MAC address in daemon
- **Frequent disconnections:** Check Bluetooth range and interference

### **Classification Issues**
- **"YOLO not available":** Install ultralytics: `pip install ultralytics`
- **"Model file not found":** Ensure `best.pt` is in the same directory
- **Poor accuracy:** Check if your model is trained for waste classification

### **Performance Issues**
- **Slow classification:** YOLO processing takes 2-5 seconds normally
- **Memory warnings:** ESP32 handles large images, monitor heap usage
- **Timeout errors:** Increase `LAPTOP_RESPONSE_TIMEOUT_MS` if needed

## Configuration

### **ESP32 Settings** (Communication.h):
```cpp
#define LAPTOP_RESPONSE_TIMEOUT_MS 10000  // 10 seconds
#define HEARTBEAT_INTERVAL_MS 30000       // 30 seconds  
#define MAX_CONSECUTIVE_TIMEOUTS 3        // Disconnect after 3 timeouts
```

### **Laptop Settings** (smartbin_laptop_daemon.py):
```python
ESP32_MAC = "EC:E3:34:15:F2:62"  # Your ESP32 MAC address
HEARTBEAT_INTERVAL = 30          # seconds
RECONNECT_DELAY = 5              # seconds
```

## Advanced Features

### **Model Replacement**
To use a different YOLO model:
1. Replace `best.pt` with your model file
2. Update `model_path` in daemon if needed
3. Modify `_map_to_waste_category()` for your classes

### **Monitoring Multiple Devices**
- Run multiple daemon instances for multiple ESP32s
- Use different MAC addresses and device names
- Each daemon handles one ESP32 independently

### **Classification Customization**
- Edit `_map_to_waste_category()` for your waste categories
- Adjust confidence thresholds
- Add preprocessing for better accuracy

## Protocol Details
See `COMMUNICATION_PROTOCOL.md` for technical details about:
- Message formats (JSON)
- State machines
- Error codes
- Timing specifications
