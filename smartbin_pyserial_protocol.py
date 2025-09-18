#!/usr/bin/env python3
"""
SmartBin PySerial Protocol Implementation
Uses PySerial for cleaner Bluetooth communication without subprocess issues
"""

import serial
import subprocess
import threading
import time
import base64
import io
import random
from PIL import Image
from typing import Optional, Tuple

class SmartBinPySerialProtocol:
    def __init__(self, esp32_mac: str = "EC:E3:34:15:F2:62", rfcomm_device: str = "/dev/rfcomm0", baudrate: int = 115200):
        self.esp32_mac = esp32_mac
        self.rfcomm_device = rfcomm_device
        self.baudrate = baudrate
        self.ser = None
        self.running = False
        self.connected = False
        self.rfcomm_bound = False
        
        # Protocol state
        self.waiting_for_image = False
        self.image_metadata = {}
        self.image_parts = {}
        self.expected_parts = 0
        
        # Threading
        self.reader_thread = None
        
    def start(self):
        """Start the communication system"""
        print("🚀 Starting SmartBin PySerial Protocol Communication")
        
        if not self._setup_rfcomm_binding():
            return False
            
        if not self._setup_serial():
            return False
            
        self.running = True
        self._start_reader_thread()
        
        # Start main communication loop
        self._main_loop()
        
        return True
    
    def stop(self):
        """Stop the communication system"""
        print("🛑 Stopping SmartBin communication")
        self.running = False
        self.connected = False
        
        if self.reader_thread:
            self.reader_thread.join(timeout=2)
            
        self._cleanup_serial()
        self._cleanup_rfcomm_binding()
    
    def _setup_rfcomm_binding(self) -> bool:
        """Setup RFCOMM binding automatically"""
        try:
            print(f"🔗 Automatically binding RFCOMM device to ESP32 {self.esp32_mac}...")
            
            # First, try to release any existing binding (in case it's already bound)
            try:
                release_cmd = ["sudo", "rfcomm", "release", "0"]
                subprocess.run(release_cmd, capture_output=True, text=True, timeout=5)
                print("🔓 Released any existing RFCOMM binding")
            except:
                pass  # It's okay if there was nothing to release
            
            # Now bind the device
            bind_cmd = ["sudo", "rfcomm", "bind", "0", self.esp32_mac, "1"]
            bind_result = subprocess.run(bind_cmd, capture_output=True, text=True, timeout=10)
            
            if bind_result.returncode != 0:
                print(f"❌ Failed to bind RFCOMM: {bind_result.stderr}")
                print(f"💡 Make sure ESP32 {self.esp32_mac} is discoverable and paired")
                return False
            
            self.rfcomm_bound = True
            print(f"✅ RFCOMM device bound to {self.rfcomm_device}")
            
            # Wait a moment for the binding to stabilize
            time.sleep(1)
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to setup RFCOMM binding: {e}")
            return False
    
    def _cleanup_rfcomm_binding(self):
        """Cleanup RFCOMM binding"""
        if self.rfcomm_bound:
            try:
                print("🔓 Releasing RFCOMM device...")
                release_cmd = ["sudo", "rfcomm", "release", "0"]
                subprocess.run(release_cmd, capture_output=True, text=True, timeout=5)
                print("✅ RFCOMM device released")
                self.rfcomm_bound = False
            except Exception as e:
                print(f"⚠️ Warning: Failed to release RFCOMM: {e}")
    
    def _setup_serial(self) -> bool:
        """Setup PySerial connection"""
        try:
            print(f"📡 Setting up PySerial connection to {self.rfcomm_device}...")
            
            self.ser = serial.Serial(
                port=self.rfcomm_device,
                baudrate=self.baudrate,
                timeout=1,  # 1 second timeout for read operations
                write_timeout=1,  # 1 second timeout for write operations
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            
            # Clear any existing data in buffers
            self.ser.flushInput()
            self.ser.flushOutput()
            
            print(f"✅ PySerial connection established")
            print(f"📊 Port: {self.ser.port}, Baudrate: {self.ser.baudrate}")
            print(f"🔧 Timeout: {self.ser.timeout}s, Write timeout: {self.ser.write_timeout}s")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to setup PySerial: {e}")
            return False
    
    def _cleanup_serial(self):
        """Cleanup PySerial connection"""
        if self.ser and self.ser.is_open:
            try:
                print("🔓 Closing PySerial connection...")
                self.ser.close()
                print("✅ PySerial connection closed")
            except Exception as e:
                print(f"⚠️ Warning: Failed to close PySerial: {e}")
    
    def _start_reader_thread(self):
        """Start the reader thread"""
        self.reader_thread = threading.Thread(target=self._reader_loop, daemon=True)
        self.reader_thread.start()
        print("📖 Reader thread started")
    
    def _reader_loop(self):
        """Read messages from ESP32 using PySerial"""
        print("📖 PySerial reader thread active")
        
        while self.running and self.ser and self.ser.is_open:
            try:
                # Check if data is available
                if self.ser.in_waiting > 0:
                    # Read a complete line
                    line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    
                    if line:
                        # print(f"📥 Raw line: '{line}'")
                        self._process_line(line)
                else:
                    # Small sleep to prevent busy waiting
                    time.sleep(0.01)
                
            except Exception as e:
                if self.running:
                    print(f"❌ Reader error: {e}")
                break
        
        print("📖 PySerial reader thread stopped")
    
    def _process_line(self, line: str):
        """Process a received line"""
        # Check if it's a protocol message
        if self._is_protocol_message(line):
            code, content = self._extract_code_content(line)
            self._handle_protocol_message(code, content)
        else:
            # Non-protocol message (verbose/debug)
            print(f"📝 ESP32: {line}")
    
    def _send_message(self, code: str, content: str = "") -> bool:
        """Send a protocol message to ESP32"""
        try:
            if not self.ser or not self.ser.is_open:
                print("❌ Serial port not open")
                return False
            
            message = f"{code} {content}".strip()
            
            # Send message with newline
            self.ser.write((message + '\n').encode('utf-8'))
            self.ser.flush()  # Ensure data is sent immediately
            
            print(f"📤 Sent: {message}")
            return True
            
        except Exception as e:
            print(f"❌ Send error: {e}")
            return False
    
    def _is_protocol_message(self, line: str) -> bool:
        """Check if line is a protocol message"""
        if len(line) < 6:
            return False
        
        code = line[:5]
        if line[5] != ' ':
            return False
        
        # Check valid protocol codes
        return (code in ['RTC00', 'RTC01', 'RTC02', 'CLS01'] or
                code.startswith('PA') or code.startswith('PX') or 
                code.startswith('ERR'))
    
    def _extract_code_content(self, line: str) -> Tuple[str, str]:
        """Extract code and content from protocol message"""
        if len(line) >= 6:
            code = line[:5]
            content = line[6:] if len(line) > 6 else ""
            return code, content
        return "", ""
    
    def _handle_protocol_message(self, code: str, content: str):
        """Handle incoming protocol messages"""
        print(f"📥 Protocol: {code} {content}")
        
        if code == "RTC00":
            # ESP32 ready to connect
            print("🤝 ESP32 requesting connection")
            if self._send_message("RTC01", "Laptop ready"):
                print("✅ Sent connection response")
            
        elif code == "RTC02":
            # Connection confirmed
            print("🎉 Connection established with ESP32!")
            self.connected = True
            
        elif code == "PA000":
            # Image metadata
            self._handle_image_metadata(content)
            
        elif code.startswith("PA"):
            # Image part
            part_num = int(code[2:])
            self._handle_image_part(part_num, content)
            
        elif code.startswith("PX"):
            # Final image part
            part_num = int(code[2:])
            self._handle_final_image_part(part_num, content)
            
        elif code.startswith("ERR"):
            # Error message
            print(f"⚠️ ESP32 Error: {content}")
    
    def _handle_image_metadata(self, content: str):
        """Handle PA000 image metadata"""
        print(f"📷 Image metadata: {content}")
        
        # Parse metadata: "type:image, size:12345, format:JPEG, width:640, height:480, id:img_123, parts:5"
        self.image_metadata = {}
        self.image_parts = {}
        
        for item in content.split(','):
            item = item.strip()
            if ':' in item:
                key, value = item.split(':', 1)
                self.image_metadata[key.strip()] = value.strip()
        
        self.expected_parts = int(self.image_metadata.get('parts', '0'))
        self.waiting_for_image = True
        
        print(f"📊 Expecting {self.expected_parts} image parts")
    
    def _handle_image_part(self, part_num: int, content: str):
        """Handle PA### image parts"""
        if not self.waiting_for_image:
            print("⚠️ Received image part but not expecting image")
            return
        
        self.image_parts[part_num] = content
        print(f"📦 Received image part {part_num}/{self.expected_parts}")
    
    def _handle_final_image_part(self, part_num: int, content: str):
        """Handle PX### final image part"""
        if not self.waiting_for_image:
            print("⚠️ Received final image part but not expecting image")
            return
        
        # Add final part
        self.image_parts[part_num] = content
        print(f"🏁 Received final image part {part_num}/{self.expected_parts}")
        
        # Process complete image
        self._process_complete_image()
    
    def _process_complete_image(self):
        """Process the complete received image"""
        try:
            print("🔄 Processing complete image...")
            
            # Reconstruct Base64 string from parts
            base64_data = ""
            for i in range(1, self.expected_parts + 1):
                if i in self.image_parts:
                    base64_data += self.image_parts[i]
                else:
                    print(f"❌ Missing image part {i}")
                    self._send_error("ERR02", "missing_image_parts")
                    return
            
            print(f"📏 Reconstructed Base64 length: {len(base64_data)}")
            
            # Decode Base64 to image
            try:
                image_data = base64.b64decode(base64_data)
                image = Image.open(io.BytesIO(image_data))
                
                print(f"🖼️ Image decoded successfully: {image.size}, {image.format}")
                
                # Note: Classification is now handled by GUI protocol integration
                # The base protocol no longer performs classification directly
                print("📸 Image processed successfully - classification handled by GUI")
                
            except Exception as e:
                print(f"❌ Base64 decode error: {e}")
                self._send_error("ERR03", "base64_decode_failed")
            
        except Exception as e:
            print(f"❌ Image processing error: {e}")
            self._send_error("ERR04", "image_processing_failed")
        
        finally:
            # Reset image state
            self.waiting_for_image = False
            self.image_metadata = {}
            self.image_parts = {}
            self.expected_parts = 0
    
    def _send_error(self, error_code: str, message: str):
        """Send error message to ESP32"""
        self._send_message(error_code, message)
    
    def _main_loop(self):
        """Main communication loop"""
        print("🔄 Starting main communication loop")
        print("💡 Waiting for ESP32 messages...")
        print("💡 Send RTC00 from ESP32 to establish connection")
        print("=" * 60)
        
        try:
            while self.running:
                # Just sleep and let the reader thread handle everything
                time.sleep(0.1)
                
                # Show connection status periodically
                if not self.connected:
                    # Check if we should show waiting message
                    pass
                
        except KeyboardInterrupt:
            print("\n🛑 Interrupted by user")
        except Exception as e:
            print(f"❌ Main loop error: {e}")
        
        print("🔄 Main communication loop ended")

def main():
    """Main function"""
    print("🎯 SmartBin PySerial Protocol - Automatic Setup")
    print("📱 ESP32 MAC Address: EC:E3:34:15:F2:62")
    print("🔧 RFCOMM Device: /dev/rfcomm0")
    print("⚡ Baudrate: 115200")
    print("=" * 50)
    
    # Automatic setup - no manual RFCOMM binding needed!
    protocol = SmartBinPySerialProtocol(
        esp32_mac="EC:E3:34:15:F2:62",  # Copied from simple protocol script
        rfcomm_device="/dev/rfcomm0",
        baudrate=115200  # Match ESP32 baudrate
    )
    
    try:
        protocol.start()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    finally:
        protocol.stop()

if __name__ == "__main__":
    main()
