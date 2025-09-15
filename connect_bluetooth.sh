#!/bin/bash

# ESP32 Bluetooth Serial Connection Script
# This script helps connect to your ESP32's Bluetooth serial output

ESP32_NAME="ESP32-SmartBin"  # Change this to match your ESP32's Bluetooth name
DEVICE_MAC=""  # Will be auto-discovered

echo "🔍 Scanning for ESP32 Bluetooth devices..."

# Enable Bluetooth and start scanning
sudo systemctl start bluetooth
sudo rfkill unblock bluetooth

echo "📡 Scanning for devices (this may take a moment)..."
echo "Make sure your ESP32 is powered on and Bluetooth is enabled."

# Scan for devices
bluetoothctl power on
timeout 10s bluetoothctl scan on > /dev/null 2>&1 &

# Wait for scan
sleep 12

echo "📋 Available Bluetooth devices:"
bluetoothctl devices

echo ""
echo "🔗 Looking for ESP32 device..."

# Try to find ESP32 device
DEVICE_MAC=$(bluetoothctl devices | grep -i "esp32\|smart.*bin" | awk '{print $2}' | head -n1)

if [ -z "$DEVICE_MAC" ]; then
    echo "❌ No ESP32 device found automatically."
    echo "📝 Please manually enter the MAC address from the list above:"
    read -p "Enter MAC address (format: XX:XX:XX:XX:XX:XX): " DEVICE_MAC
fi

if [ -z "$DEVICE_MAC" ]; then
    echo "❌ No MAC address provided. Exiting."
    exit 1
fi

echo "🎯 Attempting to connect to: $DEVICE_MAC"

# Pair and trust the device
echo "🔐 Pairing with device..."
bluetoothctl pair $DEVICE_MAC
bluetoothctl trust $DEVICE_MAC

# Create RFCOMM connection
echo "🔗 Creating serial connection..."
#!/bin/bash

# Enhanced ESP32 Bluetooth Connection Script
# This script helps you connect to your ESP32-CAM via Bluetooth on Linux

ESP32_MAC="EC:E3:34:15:F2:62"
ESP32_NAME="SmartBin_ESP32"

echo "=== ESP32-CAM Bluetooth Connection Helper ==="
echo "ESP32 MAC Address: $ESP32_MAC"
echo "ESP32 Device Name: $ESP32_NAME"
echo ""

# Function to check if Bluetooth is enabled
check_bluetooth() {
    if ! systemctl is-active --quiet bluetooth; then
        echo "❌ Bluetooth service is not running. Starting it..."
        sudo systemctl start bluetooth
        sleep 2
    fi
    
    if bluetoothctl show | grep -q "Powered: yes"; then
        echo "✅ Bluetooth is powered on"
    else
        echo "🔧 Enabling Bluetooth..."
        bluetoothctl power on
        sleep 2
    fi
}

# Function to pair with ESP32
pair_esp32() {
    echo "🔗 Attempting to pair with ESP32..."
    bluetoothctl <<EOF
agent on
default-agent
scan on
EOF
    sleep 5
    bluetoothctl <<EOF
scan off
pair $ESP32_MAC
trust $ESP32_MAC
EOF
}

# Function to connect using rfcomm
connect_rfcomm() {
    echo "📡 Connecting via rfcomm..."
    echo "Note: This will create /dev/rfcomm0 device"
    sudo rfcomm bind 0 $ESP32_MAC 1
    
    if [ -e /dev/rfcomm0 ]; then
        echo "✅ rfcomm device created: /dev/rfcomm0"
        echo "🔧 Starting minicom serial terminal..."
        echo "   - Press Ctrl+A then X to exit minicom"
        echo "   - Press Ctrl+A then Z for help menu"
        sleep 2
        sudo minicom -D /dev/rfcomm0 -b 115200
    else
        echo "❌ Failed to create rfcomm device"
    fi
}

# Function to connect using Python
connect_python() {
    echo "🐍 Using Python Bluetooth connection..."
    python3 << 'EOF'
import bluetooth
import sys
import time

MAC_ADDRESS = "EC:E3:34:15:F2:62"
PORT = 1

try:
    print(f"Connecting to {MAC_ADDRESS}...")
    sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    sock.connect((MAC_ADDRESS, PORT))
    print("✅ Connected! Listening for data...")
    print("Press Ctrl+C to disconnect")
    
    while True:
        try:
            data = sock.recv(1024)
            if data:
                print(data.decode('utf-8'), end='')
        except bluetooth.BluetoothError as e:
            print(f"\\n❌ Bluetooth error: {e}")
            break
        except KeyboardInterrupt:
            print("\\n🔌 Disconnecting...")
            break
            
except bluetooth.BluetoothError as e:
    print(f"❌ Connection failed: {e}")
    print("Make sure ESP32 is powered on and paired")
except Exception as e:
    print(f"❌ Error: {e}")
finally:
    try:
        sock.close()
    except:
        pass
EOF
}

# Main menu
show_menu() {
    echo ""
    echo "Choose connection method:"
    echo "1) Check Bluetooth status"
    echo "2) Pair with ESP32 (do this first)"
    echo "3) Connect using rfcomm + minicom"
    echo "4) Connect using Python"
    echo "5) List paired devices"
    echo "6) Scan for nearby devices"
    echo "q) Quit"
    echo ""
    read -p "Enter your choice: " choice
}

# Main execution
check_bluetooth

while true; do
    show_menu
    case $choice in
        1)
            echo "🔍 Checking Bluetooth status..."
            bluetoothctl show
            ;;
        2)
            pair_esp32
            ;;
        3)
            connect_rfcomm
            ;;
        4)
            connect_python
            ;;
        5)
            echo "📱 Paired devices:"
            bluetoothctl paired-devices
            ;;
        6)
            echo "🔍 Scanning for devices (10 seconds)..."
            bluetoothctl scan on &
            sleep 10
            bluetoothctl scan off
            bluetoothctl devices
            ;;
        q|Q)
            echo "👋 Goodbye!"
            exit 0
            ;;
        *)
            echo "❌ Invalid choice. Please try again."
            ;;
    esac
    echo ""
    read -p "Press Enter to continue..."
done

# Check if connection was successful
if [ $? -eq 0 ]; then
    echo "✅ Connection established!"
    echo "📱 Opening serial terminal..."
    echo "💡 Use Ctrl+A then X to exit minicom"
    echo ""
    
    # Open minicom to the RFCOMM device
    sudo minicom -D /dev/rfcomm0 -b 115200
    
    # Clean up after exit
    echo "🧹 Cleaning up connection..."
    sudo rfcomm release 0
else
    echo "❌ Failed to create RFCOMM connection"
    echo "🔧 Try the following:"
    echo "   1. Make sure ESP32 is powered on"
    echo "   2. Restart ESP32 and try again"
    echo "   3. Check if the MAC address is correct"
fi
