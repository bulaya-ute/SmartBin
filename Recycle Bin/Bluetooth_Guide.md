# SmartBin Bluetooth Connection Guide

## Overview
Your SmartBin ESP32 now broadcasts as **"SmartBin_ESP32"** and sends all log messages via Bluetooth Serial, allowing wireless monitoring without USB connection.

## Connection Options

### 1. Android - Serial Bluetooth Terminal
1. Install "Serial Bluetooth Terminal" from Google Play Store
2. Enable Bluetooth on your phone
3. Pair with "SmartBin_ESP32" (PIN: 1234 if prompted)
4. Open the app and connect to SmartBin_ESP32
5. View real-time logs from your Smart Bin

### 2. PC/Windows - Bluetooth Serial
1. Go to Settings > Bluetooth & devices
2. Add device > Bluetooth
3. Select "SmartBin_ESP32" and pair
4. Note the assigned COM port (e.g., COM7)
5. Use Arduino Serial Monitor or PuTTY:
   - Port: Your assigned COM port
   - Baud rate: 115200

### 3. PC/Linux - bluetoothctl
```bash
# Scan and pair
sudo bluetoothctl
scan on
# Wait for SmartBin_ESP32 to appear
pair XX:XX:XX:XX:XX:XX
connect XX:XX:XX:XX:XX:XX

# Create serial connection
sudo rfcomm bind 0 XX:XX:XX:XX:XX:XX
screen /dev/rfcomm0 115200
```

### 4. macOS - Screen Command
```bash
# Pair via System Preferences > Bluetooth first
# Then connect via terminal
screen /dev/cu.SmartBin_ESP32-SPPDev 115200
```

## Log Messages You'll See

### System Startup
```
Bluetooth Serial Started - Device Name: SmartBin_ESP32
[Camera] Initializing Edge Impulse camera...
[Camera] Edge Impulse camera initialized successfully
[System] SmartBin Ready and Initialized
```

### Sorting Cycle
```
[Ultrasonic] Distance: 8.5 cm
[Detection] Item detected! Starting sorting cycle...
[Lid] Closing bin lid...
[AI] Detected class: plastic
[Motor] Moving to position: 0
[Release] Opening...
[Release] Closing...
[Motor] Moving to position: 90
[Lid] Opening bin lid...
[Cycle Complete] Sorted 'plastic' into respective bin.
```

### Classification Details
```
[Inference] Capturing image and running classification...
[Inference] metal: 15.2%
[Inference] misc: 8.7%
[Inference] paper: 12.1%
[Inference] plastic: 64.0%
[Inference] Top prediction: plastic (64.0% confidence)
```

## Benefits

✅ **Wireless Monitoring** - No USB cable needed  
✅ **Remote Debugging** - Monitor from phone/laptop up to ~10m away  
✅ **Real-time Logs** - See classification results and system status  
✅ **No WiFi Interference** - Uses different frequency band  
✅ **Dual Output** - Still works with USB Serial as backup  

## Troubleshooting

### Connection Issues
- Ensure Bluetooth is enabled on your device
- Try unpairing and re-pairing if connection fails
- Check that no other device is connected to SmartBin_ESP32

### No Data Received
- Verify baud rate is set to 115200
- Check that you're connected to the correct device/port
- Try restarting the ESP32 if logs stop flowing

### Range Issues
- Bluetooth Classic range is typically 10 meters
- Obstacles and interference can reduce range
- Move closer to the ESP32 for better signal

## Code Changes Made

1. **Added BluetoothSerial library**
2. **Created logMessage() function** that sends to both Serial and Bluetooth
3. **Replaced all Serial.println() calls** with logMessage() calls
4. **Device name**: "SmartBin_ESP32" for easy identification

The system maintains full compatibility with USB Serial while adding wireless monitoring capability!
