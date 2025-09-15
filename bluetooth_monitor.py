#!/usr/bin/env python3
"""
ESP32 Bluetooth Serial Monitor
A simple Python script to connect to ESP32 Bluetooth and monitor serial output
"""

import bluetooth
import sys
import time
from datetime import datetime

def scan_for_esp32():
    """Scan for ESP32 devices"""
    print("🔍 Scanning for Bluetooth devices...")
    devices = bluetooth.discover_devices(duration=8, lookup_names=True)
    
    esp32_devices = []
    for addr, name in devices:
        if name and ('esp32' in name.lower() or 'smart' in name.lower() or 'smartbin' in name.lower()):
            esp32_devices.append((addr, name))
            print(f"📱 Found ESP32: {name} ({addr})")
    
    return esp32_devices

def connect_to_esp32(address, port=1):
    """Connect to ESP32 via Bluetooth"""
    try:
        print(f"🔗 Connecting to {address}...")
        sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        sock.connect((address, port))
        print("✅ Connected successfully!")
        return sock
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None

def monitor_serial(sock):
    """Monitor serial output from ESP32"""
    print("📱 Monitoring ESP32 serial output...")
    print("💡 Press Ctrl+C to exit")
    print("-" * 50)
    
    try:
        while True:
            try:
                data = sock.recv(1024)
                if data:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    message = data.decode('utf-8', errors='ignore').strip()
                    if message:
                        print(f"[{timestamp}] {message}")
            except bluetooth.BluetoothError:
                print("❌ Bluetooth connection lost")
                break
            except KeyboardInterrupt:
                print("\n👋 Disconnecting...")
                break
    finally:
        sock.close()

def main():
    print("🤖 ESP32 Bluetooth Serial Monitor")
    print("=" * 40)
    
    # Check if address provided as argument
    if len(sys.argv) > 1:
        address = sys.argv[1]
        print(f"📱 Using provided address: {address}")
    else:
        # Scan for devices
        esp32_devices = scan_for_esp32()
        
        if not esp32_devices:
            print("❌ No ESP32 devices found")
            print("💡 Make sure your ESP32 is powered on and discoverable")
            print("💡 You can also provide the MAC address as an argument:")
            print(f"   python3 {sys.argv[0]} XX:XX:XX:XX:XX:XX")
            return
        
        if len(esp32_devices) == 1:
            address = esp32_devices[0][0]
        else:
            print("\n📋 Multiple ESP32 devices found:")
            for i, (addr, name) in enumerate(esp32_devices):
                print(f"  {i+1}. {name} ({addr})")
            
            try:
                choice = int(input("Select device (1-{}): ".format(len(esp32_devices)))) - 1
                address = esp32_devices[choice][0]
            except (ValueError, IndexError):
                print("❌ Invalid selection")
                return
    
    # Connect and monitor
    sock = connect_to_esp32(address)
    if sock:
        monitor_serial(sock)

if __name__ == "__main__":
    main()
