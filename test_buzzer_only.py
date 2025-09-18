#!/usr/bin/env python3
"""
ESP32 Buzzer Test Script
Tests the PCF8575 buzzer functionality without servos
"""

import time
import json
import serial
import sys

class SimpleBuzzerProtocol:
    def __init__(self, port="/dev/rfcomm0", baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.connection = None
    
    def connect(self):
        try:
            self.connection = serial.Serial(self.port, self.baudrate, timeout=2)
            time.sleep(2)  # Wait for connection to stabilize
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def send_command(self, command):
        if not self.connection:
            return None
        
        try:
            self.connection.write(f"{command}\n".encode())
            time.sleep(0.5)  # Wait for processing
            
            # Read response
            if self.connection.in_waiting > 0:
                response = self.connection.readline().decode().strip()
                return response
        except Exception as e:
            print(f"❌ Send error: {e}")
        
        return None
    
    def disconnect(self):
        if self.connection:
            self.connection.close()

def test_esp32_buzzer():
    """Test ESP32 buzzer and servo commands via Bluetooth"""
    print("🧪 ESP32 Buzzer + Servo Test")
    print("=" * 50)
    
    # Initialize protocol
    protocol = SimpleBuzzerProtocol()
    
    try:
        # Connect to ESP32
        print("📡 Connecting to ESP32...")
        if not protocol.connect():
            print("❌ Failed to connect to ESP32")
            print("💡 Make sure:")
            print("   - ESP32 is running SmartBinBuzzerTest.ino (with servo)")
            print("   - Bluetooth is paired")
            print("   - RFCOMM is set up: sudo rfcomm bind /dev/rfcomm0 <MAC_ADDRESS>")
            return False
        
        print("✅ Connected to ESP32")
        time.sleep(2)
        
        # Test buzzer commands
        buzzer_tests = [
            ("Single beep", "control:buzzer:1"),
            ("Double beep", "control:buzzer:2"), 
            ("Triple beep", "control:buzzer:3"),
            ("Custom sequence (5 tones)", "control:buzzer:5"),
            ("Buzzer off", "control:buzzer:0"),
            ("Long sequence (8 tones)", "control:buzzer:8")
        ]
        
        for test_name, command in buzzer_tests:
            print(f"\n🔔 Testing: {test_name}")
            print(f"📤 Sending: {command}")
            
            response = protocol.send_command(command)
            if response:
                print(f"📥 Response: {response}")
                # Try to parse JSON response
                try:
                    resp_data = json.loads(response)
                    print(f"   ✅ Command: {resp_data.get('command')}")
                    print(f"   ✅ Status: {resp_data.get('status')}")
                except:
                    print(f"   � Raw response: {response}")
            else:
                print("❌ No response received")
            
            time.sleep(3)  # Wait between tests to hear the sounds
        
        print(f"\n✅ All buzzer tests completed!")
        return True
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False
        
    finally:
        protocol.disconnect()
        print("📡 Disconnected from ESP32")

def main():
    print("🔧 SmartBin ESP32 Buzzer Test")
    print("=" * 50)
    print("Requirements:")
    print("1. ESP32 running SmartBinBuzzerTest.ino")
    print("2. PCF8575 I2C I/O expander connected")
    print("3. Buzzer connected to PCF8575 P3")
    print("4. Bluetooth paired and RFCOMM set up")
    print("5. No servos required for this test")
    print()
    
    # Check if RFCOMM device exists
    import os
    if not os.path.exists("/dev/rfcomm0"):
        print("⚠️  /dev/rfcomm0 not found!")
        print("   Run: sudo rfcomm bind /dev/rfcomm0 <ESP32_MAC_ADDRESS>")
        print("   Example: sudo rfcomm bind /dev/rfcomm0 24:0A:C4:XX:XX:XX")
        return
    
    input("Press Enter to start buzzer test...")
    
    success = test_esp32_buzzer()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Buzzer test completed successfully!")
        print("🔊 You should have heard various buzzer patterns")
    else:
        print("💥 Buzzer test failed!")
        print("🔧 Check connections and ESP32 code")

if __name__ == "__main__":
    main()
