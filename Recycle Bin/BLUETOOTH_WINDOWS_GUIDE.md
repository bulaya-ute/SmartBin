# ESP32-CAM Bluetooth Monitor for Windows

## Option 1: PuTTY (Recommended)
1. Download PuTTY from: https://putty.org/
2. Install PuTTY
3. Pair your ESP32 with Windows Bluetooth
4. Go to Windows Settings > Devices > Bluetooth > More Bluetooth options
5. Find the ESP32 in COM ports tab (note the COM port number)
6. Open PuTTY:
   - Connection type: Serial
   - Serial line: COM3 (or whatever port your ESP32 is on)
   - Speed: 115200
   - Click "Open"

## Option 2: Windows Terminal/PowerShell
```powershell
# First, pair the ESP32 device
# Then find the COM port in Device Manager
# Use built-in PowerShell to connect:
[System.IO.Ports.SerialPort]::getportnames()
# This will show available COM ports

# Connect using PowerShell (replace COM3 with your port):
mode COM3 BAUD=115200 PARITY=N data=8 stop=1
type COM3
```

## Option 3: Tera Term
1. Download Tera Term: https://ttssh2.osdn.jp/
2. Install and run
3. Connect to your ESP32's COM port at 115200 baud

## Option 4: Arduino IDE Serial Monitor
1. Install Arduino IDE
2. Go to Tools > Port and select your ESP32's COM port
3. Open Serial Monitor (Ctrl+Shift+M)
4. Set baud rate to 115200

## Finding ESP32 COM Port:
1. Windows Settings > Devices > Bluetooth & other devices
2. Pair with ESP32
3. Control Panel > Device Manager > Ports (COM & LPT)
4. Look for "Standard Serial over Bluetooth link (COM#)"
