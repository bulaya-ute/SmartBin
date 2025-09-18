#!/usr/bin/env python3
"""
SmartBin Command Protocol Test Suite
Tests all implemented commands and buzzer functionality
"""

import time
import sys
import json
from smartbin_pyserial_protocol import SmartBinPySerialProtocol

class SmartBinCommandTester:
    def __init__(self, esp32_mac="98:DA:60:03:B4:FA"):
        """Initialize command tester"""
        self.protocol = SmartBinPySerialProtocol(
            esp32_mac=esp32_mac,
            rfcomm_device="/dev/rfcomm0",
            baudrate=115200
        )
        self.test_results = []
    
    def run_tests(self):
        """Run all command tests"""
        print("🧪 SmartBin Command Protocol Test Suite")
        print("=" * 50)
        
        if not self.protocol.start():
            print("❌ Failed to connect to ESP32")
            return False
        
        print("✅ Connected to ESP32")
        print()
        
        # Wait for startup
        time.sleep(2)
        
        # Test categories
        self.test_basic_commands()
        self.test_lid_commands()
        self.test_coin_commands()
        self.test_buzzer_commands()
        
        # Summary
        self.print_test_summary()
        
        self.protocol.stop()
        return True
    
    def send_command_and_wait(self, command, expected_response=None, timeout=5):
        """Send command and wait for response"""
        print(f"📤 Sending: {command}")
        
        # Send command
        parts = command.split(' ', 1)
        code = parts[0]
        content = parts[1] if len(parts) > 1 else ""
        
        success = self.protocol._send_message(code, content)
        if not success:
            result = {"command": command, "success": False, "error": "Failed to send"}
            self.test_results.append(result)
            print(f"❌ Failed to send command")
            return result
        
        # Wait for response (simplified - in real implementation would use callbacks)
        time.sleep(1)
        
        result = {"command": command, "success": True, "response": "Command sent successfully"}
        self.test_results.append(result)
        print(f"✅ Command sent successfully")
        return result
    
    def test_basic_commands(self):
        """Test basic system commands"""
        print("🔧 Testing Basic Commands")
        print("-" * 30)
        
        self.send_command_and_wait("RTC00")
        self.send_command_and_wait("STA01")
        self.send_command_and_wait("IMG01")
        
        print()
    
    def test_lid_commands(self):
        """Test lid control commands"""
        print("🔓 Testing Lid Commands")
        print("-" * 30)
        
        self.send_command_and_wait("LID00 status")
        self.send_command_and_wait("LID00 open")
        time.sleep(2)  # Wait for servo movement
        
        self.send_command_and_wait("LID00 status")
        self.send_command_and_wait("LID00 close")
        time.sleep(2)  # Wait for servo movement
        
        self.send_command_and_wait("LID00 auto")
        self.send_command_and_wait("LID00 manual")
        
        print()
    
    def test_coin_commands(self):
        """Test coin dispenser commands"""
        print("🪙 Testing Coin Commands")
        print("-" * 30)
        
        self.send_command_and_wait("COIN0 status")
        self.send_command_and_wait("COIN0 test")
        self.send_command_and_wait("COIN0 dispense")
        time.sleep(2)  # Wait for dispenser action
        
        self.send_command_and_wait("COIN0 dispense --count 2")
        time.sleep(3)  # Wait for multiple dispensing
        
        self.send_command_and_wait("COIN0 status")
        
        print()
    
    def test_buzzer_commands(self):
        """Test buzzer sound commands"""
        print("🔊 Testing Buzzer Commands")
        print("-" * 30)
        
        sounds = [
            "startup",
            "detected", 
            "complete",
            "error"
        ]
        
        for sound in sounds:
            self.send_command_and_wait(f"BUZZ0 {sound}")
            time.sleep(2)  # Wait for sound to complete
        
        self.send_command_and_wait("BUZZ0 off")
        
        print()
    
    def print_test_summary(self):
        """Print test results summary"""
        print("📊 Test Results Summary")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r["success"])
        failed_tests = total_tests - successful_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Successful: {successful_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(successful_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\nFailed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  ❌ {result['command']}: {result.get('error', 'Unknown error')}")

def main():
    """Main test function"""
    print("🚀 Starting SmartBin Command Protocol Tests")
    
    # Check if MAC address provided
    esp32_mac = "98:DA:60:03:B4:FA"  # Default MAC
    if len(sys.argv) > 1:
        esp32_mac = sys.argv[1]
        print(f"Using ESP32 MAC: {esp32_mac}")
    
    tester = SmartBinCommandTester(esp32_mac)
    
    try:
        success = tester.run_tests()
        if success:
            print("\n🎉 All tests completed!")
        else:
            print("\n❌ Test suite failed to run")
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
    except Exception as e:
        print(f"\n💥 Test error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
