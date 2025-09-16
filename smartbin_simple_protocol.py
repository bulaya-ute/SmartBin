#!/usr/bin/env python3
"""
SmartBin Unified Communication Script - Simple Protocol
Uses the new 5-character code protocol: RTC, PA, PX, CLS, ERR
"""

import subprocess
import threading
import queue
import time
import base64
import io
import re
from PIL import Image
from typing import Optional, Tuple

class SmartBinSimpleProtocol:
    def __init__(self, rfcomm_device: str = "/dev/rfcomm0"):
        self.rfcomm_device = rfcomm_device
        self.running = False
        self.connected = False
        
        # Protocol state
        self.waiting_for_image = False
        self.image_metadata = {}
        self.image_parts = {}
        self.expected_parts = 0
        
        # Threading
        self.read_process = None
        self.message_queue = queue.Queue()
        self.reader_thread = None
        
    def start(self):
        """Start the communication system"""
        print("🚀 Starting SmartBin Simple Protocol Communication")
        
        if not self._setup_rfcomm():
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
            
        self._cleanup_rfcomm()
    
    def _setup_rfcomm(self) -> bool:
        """Setup RFCOMM connection using subprocess"""
        try:
            print("📡 Setting up RFCOMM connection...")
            
            # Use subprocess to handle RFCOMM with sudo
            cmd = ["sudo", "cat", self.rfcomm_device]
            self.read_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            print(f"✅ RFCOMM connection established to {self.rfcomm_device}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to setup RFCOMM: {e}")
            return False
    
    def _cleanup_rfcomm(self):
        """Cleanup RFCOMM connection"""
        if self.read_process:
            try:
                self.read_process.terminate()
                self.read_process.wait(timeout=2)
            except:
                self.read_process.kill()
            self.read_process = None
    
    def _start_reader_thread(self):
        """Start the reader thread"""
        self.reader_thread = threading.Thread(target=self._reader_loop, daemon=True)
        self.reader_thread.start()
    
    def _reader_loop(self):
        """Read messages from ESP32"""
        print("📖 Reader thread started")
        
        while self.running and self.read_process:
            try:
                # Read line from ESP32
                line = self.read_process.stdout.readline()
                if not line:
                    continue
                    
                line = line.strip()
                if not line:
                    continue
                
                # Put message in queue for processing
                self.message_queue.put(line)
                
            except Exception as e:
                if self.running:
                    print(f"❌ Reader error: {e}")
                break
        
        print("📖 Reader thread stopped")
    
    def _send_message(self, code: str, content: str = "") -> bool:
        """Send a protocol message to ESP32"""
        try:
            message = f"{code} {content}".strip()
            
            # Use subprocess to send message with sudo
            cmd = ["sudo", "bash", "-c", f'echo "{message}" > {self.rfcomm_device}']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                print(f"📤 Sent: {message}")
                return True
            else:
                print(f"❌ Send failed: {result.stderr}")
                return False
                
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
                
                # Perform mock classification
                classification, confidence = self._mock_classify(image)
                
                # Send classification result
                result = f"{classification} {confidence:.2f}"
                if self._send_message("CLS01", result):
                    print(f"✅ Sent classification: {result}")
                else:
                    print("❌ Failed to send classification")
                
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
    
    def _mock_classify(self, image: Image.Image) -> Tuple[str, float]:
        """Mock classification function"""
        import random
        
        classes = ["plastic", "metal", "paper", "misc"]
        classification = random.choice(classes)
        confidence = random.uniform(0.7, 0.95)
        
        print(f"🎯 Mock classification: {classification} (confidence: {confidence:.2f})")
        return classification, confidence
    
    def _send_error(self, error_code: str, message: str):
        """Send error message to ESP32"""
        self._send_message(error_code, message)
    
    def _main_loop(self):
        """Main communication loop"""
        print("🔄 Starting main communication loop")
        
        while self.running:
            try:
                # Process incoming messages
                try:
                    message = self.message_queue.get(timeout=0.1)
                    
                    # Check if it's a protocol message
                    if self._is_protocol_message(message):
                        code, content = self._extract_code_content(message)
                        self._handle_protocol_message(code, content)
                    else:
                        # Non-protocol message (verbose/debug)
                        print(f"📝 ESP32: {message}")
                        
                except queue.Empty:
                    continue
                    
            except KeyboardInterrupt:
                print("\n🛑 Interrupted by user")
                break
            except Exception as e:
                print(f"❌ Main loop error: {e}")
                time.sleep(1)
        
        print("🔄 Main communication loop ended")

def main():
    """Main function"""
    protocol = SmartBinSimpleProtocol()
    
    try:
        protocol.start()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    finally:
        protocol.stop()

if __name__ == "__main__":
    main()
