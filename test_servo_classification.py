#!/usr/bin/env python3
"""
ESP32 Servo Test Script
Tests the servo motor control with classification commands
"""

import time
import json
import serial
import sys

class ServoTestProtocol:
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
            time.sleep(1)  # Wait for processing
            
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

def test_servo_classification():
    """Test ESP32 servo motor classification movements"""
    print("🤖 ESP32 Servo Classification Test")
    print("=" * 50)
    
    # Initialize protocol
    protocol = ServoTestProtocol()
    
    try:
        # Connect to ESP32
        print("📡 Connecting to ESP32...")
        if not protocol.connect():
            print("❌ Failed to connect to ESP32")
            print("💡 Make sure:")
            print("   - ESP32 is running SmartBinBuzzerTest.ino (with servo)")
            print("   - Servo motor connected to GPIO16")
            print("   - Bluetooth is paired")
            print("   - RFCOMM is set up: sudo rfcomm bind /dev/rfcomm0 <MAC_ADDRESS>")
            return False
        
        print("✅ Connected to ESP32")
        time.sleep(2)
        
        # Test servo classification commands
        print(f"\n🎯 === SERVO CLASSIFICATION TESTS ===")
        print("Expected behavior:")
        print("- Paper/Misc → 180° for 2 seconds, then back to 90°")
        print("- Plastic/Metal → 0° for 2 seconds, then back to 90°")
        print()
        
        servo_tests = [
            ("Paper classification", "classify:paper", "Should move to 180° (paper bin)"),
            ("Plastic classification", "classify:plastic", "Should move to 0° (plastic bin)"),
            ("Metal classification", "classify:metal", "Should move to 0° (metal bin)"),
            ("Misc classification", "classify:misc", "Should move to 180° (misc bin)")
        ]
        
        for test_name, command, description in servo_tests:
            print(f"\n🎯 Testing: {test_name}")
            print(f"📤 Sending: {command}")
            print(f"🔍 Expected: {description}")
            print("⏱️  Watch servo movement (should take ~3 seconds)...")
            
            response = protocol.send_command(command)
            if response:
                print(f"📥 Response: {response}")
                try:
                    resp_data = json.loads(response)
                    print(f"   ✅ Status: {resp_data.get('status')}")
                    print(f"   ✅ Command: {resp_data.get('command')}")
                except:
                    print(f"   📝 Raw: {response}")
            else:
                print("❌ No response received")
            
            print("⏸️  Waiting 5 seconds before next test...")
            time.sleep(5)
        
        # Test buzzer commands too
        print(f"\n🔔 === BUZZER TESTS ===")
        buzzer_tests = [
            ("Single beep", "control:buzzer:1"),
            ("Double beep", "control:buzzer:2"),
            ("Buzzer off", "control:buzzer:0")
        ]
        
        for test_name, command in buzzer_tests:
            print(f"\n🔔 Testing: {test_name}")
            print(f"📤 Sending: {command}")
            
            response = protocol.send_command(command)
            if response:
                print(f"📥 Response: {response}")
            
            time.sleep(2)
        
        print(f"\n✅ All tests completed!")
        return True
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False
        
    finally:
        protocol.disconnect()
        print("📡 Disconnected from ESP32")

def main():
    print("🔧 SmartBin ESP32 Servo Classification Test")
    print("=" * 50)
    print("Requirements:")
    print("1. ESP32 running SmartBinBuzzerTest.ino (updated version with servo)")
    print("2. Servo motor connected to GPIO16")
    print("3. PCF8575 I2C I/O expander with buzzer")
    print("4. Bluetooth paired and RFCOMM set up")
    print()
    print("Servo Logic:")
    print("- Default position: 90°")
    print("- Paper/Misc items: Move to 180°, hold 2s, return to 90°")
    print("- Plastic/Metal items: Move to 0°, hold 2s, return to 90°")
    print()
    
    # Check if RFCOMM device exists
    import os
    if not os.path.exists("/dev/rfcomm0"):
        print("⚠️  /dev/rfcomm0 not found!")
        print("   Run: sudo rfcomm bind /dev/rfcomm0 <ESP32_MAC_ADDRESS>")
        return
    
    input("Press Enter to start servo test...")
    
    success = test_servo_classification()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Servo classification test completed!")
        print("🔊 You should have seen servo movements and heard buzzer sounds")
    else:
        print("💥 Servo test failed!")
        print("🔧 Check connections and ESP32 code")

if __name__ == "__main__":
    main()
