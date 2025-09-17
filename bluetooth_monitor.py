#!/usr/bin/env python3
"""
SmartBin Bluetooth Monitor
Connects to ESP32-CAM via Bluetooth and displays real-time output
"""

import bluetooth
import threading
import time
import sys

class SmartBinBluetoothMonitor:
    def __init__(self, device_name="SmartBin_PCF8575_Test"):
        self.device_name = device_name
        self.socket = None
        self.running = False
        self.connected = False
        
    def find_device(self):
        """Find the ESP32 device by name"""
        print(f"🔍 Searching for device: {self.device_name}")
        
        try:
            devices = bluetooth.discover_devices(duration=10, lookup_names=True)
            
            for addr, name in devices:
                print(f"📱 Found device: {name} ({addr})")
                if self.device_name in name:
                    print(f"✅ Target device found: {addr}")
                    return addr
            
            print(f"❌ Device '{self.device_name}' not found")
            return None
            
        except Exception as e:
            print(f"❌ Error during device discovery: {e}")
            return None
    
    def connect(self, address):
        """Connect to the ESP32 device"""
        try:
            print(f"🔗 Connecting to {address}...")
            
            self.socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            self.socket.connect((address, 1))  # ESP32 usually uses channel 1
            
            print("✅ Connected successfully!")
            self.connected = True
            return True
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def listen(self):
        """Listen for incoming messages"""
        print("📡 Starting message listener...")
        print("=" * 60)
        
        buffer = ""
        
        while self.running and self.connected:
            try:
                data = self.socket.recv(1024).decode('utf-8')
                if data:
                    buffer += data
                    
                    # Process complete lines
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        if line.strip():
                            timestamp = time.strftime("%H:%M:%S")
                            print(f"[{timestamp}] {line}")
                else:
                    time.sleep(0.1)
                    
            except bluetooth.BluetoothError as e:
                if self.running:
                    print(f"❌ Bluetooth error: {e}")
                break
            except Exception as e:
                if self.running:
                    print(f"❌ Unexpected error: {e}")
                break
        
        print("📡 Message listener stopped")
    
    def start_monitoring(self):
        """Start the monitoring process"""
        print("🚀 SmartBin Bluetooth Monitor")
        print("=" * 40)
        
        # Find device
        address = self.find_device()
        if not address:
            print("💡 Make sure your ESP32 is powered on and Bluetooth is active")
            return False
        
        # Connect to device
        if not self.connect(address):
            print("💡 Make sure the ESP32 is not connected to another device")
            return False
        
        # Start listening
        self.running = True
        listener_thread = threading.Thread(target=self.listen, daemon=True)
        listener_thread.start()
        
        print("💡 Press Ctrl+C to stop monitoring")
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping monitor...")
            self.stop_monitoring()
        
        return True
    
    def stop_monitoring(self):
        """Stop monitoring and cleanup"""
        self.running = False
        self.connected = False
        
        if self.socket:
            try:
                self.socket.close()
                print("✅ Bluetooth connection closed")
            except:
                pass
    
    def send_command(self, command):
        """Send command to ESP32 (for future use)"""
        if self.connected and self.socket:
            try:
                self.socket.send((command + '\n').encode('utf-8'))
                print(f"📤 Sent: {command}")
                return True
            except Exception as e:
                print(f"❌ Send failed: {e}")
                return False
        return False

def main():
    """Main function"""
    # Check if device name provided
    device_name = "SmartBin_PCF8575_Test"
    if len(sys.argv) > 1:
        device_name = sys.argv[1]
    
    print(f"🎯 Target device: {device_name}")
    
    # Create and start monitor
    monitor = SmartBinBluetoothMonitor(device_name)
    
    try:
        monitor.start_monitoring()
    except Exception as e:
        print(f"❌ Monitor failed: {e}")
    finally:
        monitor.stop_monitoring()

if __name__ == "__main__":
    main()
