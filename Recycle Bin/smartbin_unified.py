#!/usr/bin/env python3
"""
SmartBin Laptop Communication System - Unified Solution
Handles RFCOMM connection, image reception, and classification responses
"""

import re
import base64
import time
import threading
import signal
import sys
import subprocess
import os
import queue
import random
from datetime import datetime
from PIL import Image
import io

# Configuration
ESP32_MAC = "EC:E3:34:15:F2:62"
ESP32_NAME = "SmartBin_ESP32"
RFCOMM_DEVICE = "/dev/rfcomm0"

class SmartBinCommunicationSystem:
    def __init__(self):
        self.running = False
        self.connected = False
        self.rfcomm_process = None
        self.rfcomm_file = None
        
        # Image processing
        self.output_queue = queue.Queue()
        self.current_image_data = {}
        self.image_counter = 0
        
        # Threading
        self.reader_thread = None
        self.processor_thread = None
        
        print("🤖 SmartBin Communication System v2.0")
        print(f"Target ESP32: {ESP32_NAME} ({ESP32_MAC})")
        print("📡 Unified image processing & communication")
    
    def start(self):
        """Start the unified communication system"""
        print("🚀 Starting SmartBin Communication System...")
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.running = True
        
        try:
            # Connect to ESP32
            if self._connect_rfcomm():
                # Start processing threads
                self._start_threads()
                # Main loop
                self._main_loop()
            else:
                print("❌ Failed to establish connection")
                
        except KeyboardInterrupt:
            self._shutdown()
        except Exception as e:
            print(f"❌ Fatal error: {e}")
            self._shutdown()
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\n🛑 Received signal {signum}, shutting down...")
        self._shutdown()
    
    def _connect_rfcomm(self):
        """Establish RFCOMM connection to ESP32 (same approach as working image monitor)"""
        try:
            print(f"🔗 Connecting to ESP32 via RFCOMM...")
            
            # First, bind rfcomm device (same as image monitor)
            bind_cmd = ["sudo", "rfcomm", "bind", "0", ESP32_MAC, "1"]
            bind_result = subprocess.run(bind_cmd, capture_output=True, text=True)
            
            if bind_result.returncode != 0:
                print(f"❌ Failed to bind rfcomm: {bind_result.stderr}")
                return False
                
            print("✅ RFCOMM device bound to /dev/rfcomm0")
            
            # Use subprocess approach like image monitor (sudo cat for reading)
            read_cmd = ["sudo", "cat", RFCOMM_DEVICE]
            self.rfcomm_process = subprocess.Popen(
                read_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=False,  # Handle bytes like image monitor
                bufsize=0    # Unbuffered like image monitor
            )
            
            # For writing, we'll need a separate approach
            # We'll open a write-only subprocess when needed
            
            print("✅ RFCOMM connection established")
            print("📡 Ready for bidirectional communication")
            self.connected = True
            
            # Send initial ready signal in proper JSON format for ESP32 protocol
            self._send_laptop_ready_message()
            
            return True
            
        except Exception as e:
            print(f"❌ RFCOMM connection failed: {e}")
            self._cleanup_rfcomm()
            return False
    
    def _start_threads(self):
        """Start processing threads"""
        # Reader thread - reads from ESP32
        self.reader_thread = threading.Thread(target=self._reader_loop, daemon=True)
        self.reader_thread.start()
        
        # Processor thread - handles images and messages
        self.processor_thread = threading.Thread(target=self._processor_loop, daemon=True)
        self.processor_thread.start()
        
        print("🧵 Processing threads started")
    
    def _main_loop(self):
        """Main daemon loop"""
        print("👂 Listening for ESP32 communication...")
        print("💡 Features:")
        print("   - ✅ Images received and saved automatically")
        print("   - ✅ Classification requests answered (mock results)")
        print("   - ✅ Handshake and heartbeat handling")
        print("   - ✅ Bidirectional communication")
        print("   - Press Ctrl+C to stop")
        print("=" * 60)
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
    
    def _reader_loop(self):
        """Read data from ESP32 subprocess and queue for processing (same as image monitor)"""
        buffer = ""
        
        while self.running and self.connected:
            try:
                if not self.rfcomm_process:
                    break
                
                # Read character by character like image monitor
                char_bytes = self.rfcomm_process.stdout.read(1)
                if not char_bytes:
                    continue
                
                char = char_bytes.decode('utf-8', errors='ignore')
                buffer += char
                
                # Process complete lines
                if char == '\n':
                    line = buffer.strip()
                    if line:
                        self.output_queue.put(line)
                    buffer = ""
                    
            except Exception as e:
                if self.running:
                    print(f"❌ Reader error: {e}")
                break
    
    def _processor_loop(self):
        """Process queued messages and images"""
        image_buffer = []
        in_image = False
        
        while self.running:
            try:
                # Get message from queue
                line = self.output_queue.get(timeout=1)
                
                # Handle image data
                if "==IMAGE_START==" in line:
                    print("\n📸 Image transmission started")
                    in_image = True
                    image_buffer = []
                    self.current_image_data = {}
                    
                elif "==IMAGE_END==" in line:
                    if in_image:
                        print("📸 Image transmission complete - processing...")
                        self._process_image(image_buffer)
                    in_image = False
                    image_buffer = []
                    
                elif in_image:
                    # Collect image data
                    image_buffer.append(line)
                    self._extract_image_metadata(line)
                    
                else:
                    # Handle communication messages
                    self._handle_communication(line)
                    
            except queue.Empty:
                continue
            except Exception as e:
                print(f"❌ Processor error: {e}")
    
    def _extract_image_metadata(self, line):
        """Extract image metadata from transmission"""
        if line.startswith("FORMAT:"):
            self.current_image_data['format'] = line.split(":", 1)[1].strip()
        elif line.startswith("SIZE:"):
            size_match = re.search(r'(\d+)', line)
            if size_match:
                self.current_image_data['size'] = int(size_match.group(1))
        elif line.startswith("DIMENSIONS:"):
            dim_match = re.search(r'(\d+)x(\d+)', line)
            if dim_match:
                self.current_image_data['width'] = int(dim_match.group(1))
                self.current_image_data['height'] = int(dim_match.group(2))
        elif line.startswith("TIMESTAMP:"):
            time_match = re.search(r'(\d+)', line)
            if time_match:
                self.current_image_data['timestamp'] = int(time_match.group(1))
    
    def _process_image(self, image_lines):
        """Process and decode received image"""
        try:
            print(f"🔍 Processing image data...")
            
            # Extract Base64 data from chunked format
            base64_data = ""
            
            for line in image_lines:
                if "BASE64_DATA:" in line:
                    continue
                elif "[IMG_B64]" in line:
                    # Handle chunked format: [IMG_B64] [1/86] base64data...
                    parts = line.split("] ")
                    if len(parts) >= 2:
                        base64_part = parts[-1].strip()
                        cleaned = re.sub(r'[^A-Za-z0-9+/=]', '', base64_part)
                        if cleaned and len(cleaned) > 10:
                            base64_data += cleaned
            
            if not base64_data:
                print("❌ No Base64 data found")
                return
                
            print(f"📊 Base64 length: {len(base64_data)} characters")
            
            # Fix padding if needed
            missing_padding = len(base64_data) % 4
            if missing_padding:
                base64_data += '=' * (4 - missing_padding)
            
            # Decode image
            image_bytes = base64.b64decode(base64_data)
            print(f"✅ Decoded {len(image_bytes)} bytes")
            
            # Save image
            self.image_counter += 1
            timestamp = int(time.time())
            filename = f"esp32_capture_{timestamp}_{self.image_counter:03d}.jpg"
            
            with open(filename, 'wb') as f:
                f.write(image_bytes)
            
            print(f"💾 Image saved: {filename}")
            
            # Perform mock classification
            classification = self._mock_classify_image(image_bytes)
            print(f"🧠 Mock Classification: {classification['class']} ({classification['confidence']*100:.1f}% confidence)")
            
            # Send classification result to ESP32
            self._send_classification_result(classification)
            
        except Exception as e:
            print(f"❌ Image processing error: {e}")
    
    def _mock_classify_image(self, image_bytes):
        """Perform mock classification (random result)"""
        waste_types = ["plastic", "paper", "metal", "misc"]
        result = random.choice(waste_types)
        confidence = round(random.uniform(0.6, 0.95), 2)
        
        return {
            "class": result,
            "confidence": confidence
        }
    
    def _handle_communication(self, message):
        """Handle communication messages from ESP32"""
        print(f"📨 ESP32: {message}")
        
        # Handle different message types
        if "WAITING_LAPTOP" in message or "waiting for laptop" in message.lower():
            print("🔔 ESP32 waiting for laptop - sending ready signal")
            self._send_message("LAPTOP_READY")
            
        elif "CLASSIFICATION" in message and "REQUEST" in message:
            print("🧠 ESP32 requesting classification")
            # Classification will be sent after image processing
            
        elif "HEARTBEAT" in message:
            print("💓 Heartbeat from ESP32")
            self._send_message("HEARTBEAT_ACK")
            
        elif "CYCLE_COMPLETE" in message:
            print("✅ ESP32 completed sorting cycle")
    
    def _send_message(self, message):
        """Send message to ESP32 using subprocess (since we need sudo for write access)"""
        try:
            if self.connected:
                msg = f"{message}\n"
                # Use echo with sudo to write to the device
                write_cmd = ["sudo", "bash", "-c", f"echo '{message}' > {RFCOMM_DEVICE}"]
                result = subprocess.run(write_cmd, capture_output=True, text=True, timeout=5)
                
                if result.returncode == 0:
                    print(f"📤 Sent: {message}")
                    return True
                else:
                    print(f"❌ Send failed: {result.stderr}")
                    return False
        except Exception as e:
            print(f"❌ Send error: {e}")
            return False
    
    def _send_laptop_ready_message(self):
        """Send proper MSG_LAPTOP_READY message in JSON format expected by ESP32"""
        try:
            import json
            import time
            
            # Create JSON message matching ESP32 protocol
            message_data = {
                "type": "LAPTOP_READY",
                "timestamp": int(time.time() * 1000),  # milliseconds like ESP32
                "data": {
                    "protocol_version": "1.0",
                    "device_id": "SmartBin_Laptop",
                    "capabilities": ["image_processing", "classification", "yolo"],
                    "status": "ready_for_communication"
                }
            }
            
            # Convert to JSON string
            json_message = json.dumps(message_data)
            
            # Send with ESP32 message delimiters
            delimiter_start = "===MSG_START==="
            delimiter_end = "===MSG_END==="
            
            # Send the complete message
            if self.connected:
                for line in [delimiter_start, json_message, delimiter_end]:
                    write_cmd = ["sudo", "bash", "-c", f"echo '{line}' > {RFCOMM_DEVICE}"]
                    result = subprocess.run(write_cmd, capture_output=True, text=True, timeout=5)
                    
                    if result.returncode != 0:
                        print(f"❌ Failed to send laptop ready message: {result.stderr}")
                        return False
                
                print("✅ MSG_LAPTOP_READY sent to ESP32 with proper protocol")
                return True
            else:
                print("❌ Cannot send laptop ready - not connected")
                return False
                
        except Exception as e:
            print(f"❌ Error sending laptop ready message: {e}")
            return False
    
    def _send_classification_result(self, classification):
        """Send classification result to ESP32"""
        try:
            result_msg = f"CLASSIFICATION_RESULT:{classification['class']}:{classification['confidence']}"
            self._send_message(result_msg)
            print(f"🎯 Classification sent to ESP32: {classification['class']}")
        except Exception as e:
            print(f"❌ Failed to send classification: {e}")
    
    def _cleanup_rfcomm(self):
        """Clean up RFCOMM resources"""
        if self.rfcomm_process:
            try:
                self.rfcomm_process.terminate()
            except:
                pass
            self.rfcomm_process = None
        
        try:
            subprocess.run(['sudo', 'rfcomm', 'release', '0'], 
                         capture_output=True, timeout=5)
            print("🔌 RFCOMM device released")
        except:
            pass
    
    def _shutdown(self):
        """Graceful shutdown"""
        print("\n🛑 Shutting down SmartBin Communication System...")
        self.running = False
        self.connected = False
        
        self._cleanup_rfcomm()
        
        print("👋 SmartBin system stopped")
        sys.exit(0)

def main():
    print("=" * 70)
    print("🗑️  SmartBin Laptop Communication System v2.0")
    print("=" * 70)
    print("🔧 Unified Solution:")
    print("   ✅ RFCOMM Bluetooth connection management")
    print("   ✅ Image reception and Base64 decoding")
    print("   ✅ Mock waste classification (random results)")
    print("   ✅ Bidirectional ESP32 communication")
    print("   ✅ Handshake and heartbeat protocols")
    print("=" * 70)
    
    system = SmartBinCommunicationSystem()
    system.start()

if __name__ == "__main__":
    main()
