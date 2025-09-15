#!/usr/bin/env python3
"""
SmartBin Laptop Communication Daemon
Handles communication protocol with ESP32-CAM for image classification
"""

import json
import time
import base64
import threading
import signal
import sys
from datetime import datetime
from queue import Queue, Empty
import bluetooth
from PIL import Image
import io
import tempfile
import os
import numpy as np

# Import YOLO for classification
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    print("⚠️  Warning: ultralytics not installed. Using dummy classification.")
    YOLO_AVAILABLE = False

# Configuration
ESP32_MAC = "EC:E3:34:15:F2:62"  # Update with your ESP32 MAC
ESP32_NAME = "SmartBin_ESP32"
RFCOMM_PORT = 1
HEARTBEAT_INTERVAL = 30  # seconds
RECONNECT_DELAY = 5  # seconds

class SmartBinDaemon:
    def __init__(self):
        self.running = False
        self.connected = False
        self.sock = None
        self.message_queue = Queue()
        self.last_heartbeat = time.time()
        
        # Threading
        self.comm_thread = None
        self.processing_thread = None
        
        # State
        self.device_id = "SmartBin_Laptop"
        self.version = "1.0"
        
        # Classification model
        self.model = None
        self._load_model()
        
        print(f"🤖 SmartBin Laptop Daemon v{self.version}")
        print(f"Target ESP32: {ESP32_NAME} ({ESP32_MAC})")
    
    def _load_model(self):
        """Load YOLO classification model"""
        if not YOLO_AVAILABLE:
            print("⚠️  YOLO not available - using dummy classification")
            return
        
        model_path = "best.pt"  # Your trained model
        
        try:
            if os.path.exists(model_path):
                print(f"🧠 Loading YOLO model: {model_path}")
                self.model = YOLO(model_path)
                print("✅ YOLO model loaded successfully")
            else:
                print(f"❌ Model file not found: {model_path}")
                print("📁 Available models:")
                for file in os.listdir("."):
                    if file.endswith('.pt'):
                        print(f"   - {file}")
        except Exception as e:
            print(f"❌ Failed to load YOLO model: {e}")
            self.model = None
    
    def start(self):
        """Start the communication daemon"""
        self.running = True
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        print("🚀 Starting communication daemon...")
        
        # Start communication thread
        self.comm_thread = threading.Thread(target=self._communication_loop, daemon=True)
        self.comm_thread.start()
        
        # Start message processing thread
        self.processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
        self.processing_thread.start()
        
        # Main loop
        try:
            self._main_loop()
        except KeyboardInterrupt:
            self._shutdown()
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\n🛑 Received signal {signum}, shutting down...")
        self._shutdown()
    
    def _shutdown(self):
        """Graceful shutdown"""
        self.running = False
        
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
        
        print("👋 SmartBin daemon stopped")
        sys.exit(0)
    
    def _main_loop(self):
        """Main daemon loop"""
        while self.running:
            try:
                # Send heartbeat if connected
                if self.connected and (time.time() - self.last_heartbeat) > HEARTBEAT_INTERVAL:
                    self._send_heartbeat()
                
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ Error in main loop: {e}")
                time.sleep(1)
    
    def _communication_loop(self):
        """Communication thread - handles connection and message receiving"""
        while self.running:
            try:
                if not self.connected:
                    self._connect_to_esp32()
                else:
                    self._receive_messages()
                    
            except Exception as e:
                print(f"❌ Communication error: {e}")
                self._handle_disconnection()
                time.sleep(RECONNECT_DELAY)
    
    def _connect_to_esp32(self):
        """Connect to ESP32 via Bluetooth"""
        try:
            print(f"🔗 Attempting to connect to {ESP32_MAC}...")
            
            self.sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            self.sock.settimeout(10)  # 10 second timeout
            self.sock.connect((ESP32_MAC, RFCOMM_PORT))
            
            print("✅ Bluetooth connection established")
            self.connected = True
            self.last_heartbeat = time.time()
            
            # Remove timeout for message receiving
            self.sock.settimeout(None)
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            if self.sock:
                try:
                    self.sock.close()
                except:
                    pass
                self.sock = None
            self.connected = False
            raise
    
    def _receive_messages(self):
        """Receive and parse messages from ESP32"""
        if not self.sock:
            return
        
        try:
            # Read data from Bluetooth
            data = self.sock.recv(4096)
            if not data:
                raise bluetooth.BluetoothError("No data received")
            
            # Decode and process messages
            text = data.decode('utf-8', errors='ignore')
            self._process_incoming_data(text)
            
        except bluetooth.BluetoothError as e:
            print(f"❌ Bluetooth receive error: {e}")
            raise
        except Exception as e:
            print(f"❌ Message receive error: {e}")
    
    def _process_incoming_data(self, data):
        """Process incoming data and extract messages"""
        # Look for complete messages
        lines = data.split('\\n')
        
        message_buffer = ""
        in_message = False
        
        for line in lines:
            line = line.strip()
            
            if line == "===MSG_START===":
                in_message = True
                message_buffer = ""
            elif line == "===MSG_END===":
                if in_message and message_buffer:
                    try:
                        message = json.loads(message_buffer)
                        self.message_queue.put(message)
                        print(f"📨 Received: {message.get('type', 'unknown')}")
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON decode error: {e}")
                in_message = False
            elif in_message:
                message_buffer += line + "\\n"
            else:
                # Handle non-JSON messages (like waiting messages)
                if "WAITING_LAPTOP" in line or "waiting" in line.lower():
                    print(f"📢 ESP32: {line}")
                    self._send_ready_signal()
    
    def _processing_loop(self):
        """Message processing thread"""
        while self.running:
            try:
                # Get message from queue (blocks with timeout)
                message = self.message_queue.get(timeout=1)
                self._handle_message(message)
                
            except Empty:
                continue
            except Exception as e:
                print(f"❌ Message processing error: {e}")
    
    def _handle_message(self, message):
        """Handle received messages based on type"""
        msg_type = message.get('type', '')
        data = message.get('data', {})
        
        if msg_type == "WAITING_LAPTOP":
            print("🔔 ESP32 is waiting for laptop connection")
            self._send_ready_signal()
            
        elif msg_type == "IMAGE_DATA":
            print("📸 Received image for classification")
            self._process_image_classification(data)
            
        elif msg_type == "STATUS_UPDATE":
            status = data.get('status', 'unknown')
            print(f"📊 ESP32 Status: {status}")
            
        else:
            print(f"❓ Unknown message type: {msg_type}")
    
    def _send_ready_signal(self):
        """Send ready signal to ESP32"""
        ready_data = {
            "device_id": self.device_id,
            "version": self.version,
            "ready": True
        }
        
        if self._send_message("LAPTOP_READY", ready_data):
            print("✅ Sent ready signal to ESP32")
    
    def _send_heartbeat(self):
        """Send heartbeat to ESP32"""
        heartbeat_data = {
            "status": "online"
        }
        
        if self._send_message("HEARTBEAT", heartbeat_data):
            self.last_heartbeat = time.time()
    
    def _process_image_classification(self, image_data):
        """Process image classification request"""
        try:
            image_id = image_data.get('image_id', 'unknown')
            base64_data = image_data.get('base64_data', '')
            image_format = image_data.get('format', 'JPEG')
            
            print(f"🔍 Processing image {image_id} ({image_format})")
            
            if not base64_data:
                self._send_classification_error(image_id, "INVALID_FORMAT", 
                                              "No Base64 data received", False)
                return
            
            # Decode Base64 image
            try:
                image_bytes = base64.b64decode(base64_data)
                print(f"✅ Decoded {len(image_bytes)} bytes")
            except Exception as e:
                self._send_classification_error(image_id, "DECODE_FAILED", 
                                              f"Base64 decode failed: {str(e)}", True)
                return
            
            # Save image temporarily for verification
            timestamp = int(time.time())
            temp_filename = f"received_image_{timestamp}.jpg"
            
            try:
                with open(temp_filename, 'wb') as f:
                    f.write(image_bytes)
                print(f"💾 Saved image: {temp_filename}")
                
                # Verify image with PIL
                with Image.open(temp_filename) as img:
                    print(f"🖼️  Image: {img.format} {img.size} {img.mode}")
                
                # TODO: Replace with actual classification model
                classification_result, confidence = self._classify_image(img)
                
                # Send result back to ESP32
                self._send_classification_result(image_id, classification_result, confidence, 250)
                
            except Exception as e:
                print(f"❌ Image processing failed: {e}")
                self._send_classification_error(image_id, "CLASSIFICATION_FAILED", 
                                              str(e), False)
            finally:
                # Clean up temp file
                try:
                    os.remove(temp_filename)
                except:
                    pass
                    
        except Exception as e:
            print(f"❌ Classification processing error: {e}")
            self._send_classification_error("unknown", "PROCESSING_ERROR", str(e), False)
    
    def _classify_image(self, image):
        """Classify image using YOLO model or fallback to dummy"""
        try:
            if self.model is not None and YOLO_AVAILABLE:
                print("🎯 Running YOLO classification...")
                
                # Convert PIL image to format suitable for YOLO
                img_array = np.array(image)
                
                # Run YOLO prediction
                results = self.model(img_array, verbose=False)
                
                if results and len(results) > 0:
                    result = results[0]
                    
                    # Check if any objects were detected
                    if result.boxes is not None and len(result.boxes) > 0:
                        # Get the highest confidence detection
                        confidences = result.boxes.conf.cpu().numpy()
                        classes = result.boxes.cls.cpu().numpy()
                        
                        max_conf_idx = np.argmax(confidences)
                        max_confidence = float(confidences[max_conf_idx])
                        predicted_class = int(classes[max_conf_idx])
                        
                        # Map class ID to waste category
                        class_names = result.names if hasattr(result, 'names') else {}
                        predicted_name = class_names.get(predicted_class, f"class_{predicted_class}")
                        
                        # Map to standard waste categories
                        waste_category = self._map_to_waste_category(predicted_name)
                        
                        print(f"✅ YOLO result: {predicted_name} -> {waste_category} ({max_confidence:.3f})")
                        return waste_category, max_confidence
                    else:
                        print("🔍 No objects detected by YOLO")
                        return "general", 0.1  # Low confidence general waste
                else:
                    print("❌ YOLO returned no results")
                    return "general", 0.1
                    
            else:
                # Fallback to dummy classification
                return self._classify_image_dummy(image)
                
        except Exception as e:
            print(f"❌ YOLO classification failed: {e}")
            return self._classify_image_dummy(image)
    
    def _map_to_waste_category(self, predicted_class):
        """Map YOLO prediction to waste categories"""
        # This mapping depends on your trained model's classes
        # Update this based on your actual class names
        recyclable_items = ["plastic", "bottle", "can", "paper", "cardboard", "metal"]
        organic_items = ["food", "organic", "fruit", "vegetable", "apple", "banana"]
        
        predicted_lower = predicted_class.lower()
        
        for item in recyclable_items:
            if item in predicted_lower:
                return "recyclable"
        
        for item in organic_items:
            if item in predicted_lower:
                return "organic"
        
        # Default to general waste
        return "general"
    
    def _classify_image_dummy(self, image):
        """Dummy classification - replace with actual model"""
        print("🎯 Running dummy classification...")
        
        # Simple dummy logic based on image properties
        width, height = image.size
        
        if width > 600 or height > 600:
            return "recyclable", 0.85
        elif width < 300 and height < 300:
            return "organic", 0.75
        else:
            return "general", 0.65
    
    def _send_classification_result(self, image_id, classification, confidence, processing_time):
        """Send classification result to ESP32"""
        result_data = {
            "image_id": image_id,
            "classification": classification,
            "confidence": confidence,
            "processing_time_ms": processing_time
        }
        
        if self._send_message("CLASSIFICATION_RESULT", result_data):
            print(f"✅ Sent classification result: {classification} ({confidence:.2f})")
    
    def _send_classification_error(self, image_id, error_code, error_message, retry_suggested):
        """Send classification error to ESP32"""
        error_data = {
            "image_id": image_id,
            "error_code": error_code,
            "error_message": error_message,
            "retry_suggested": retry_suggested
        }
        
        if self._send_message("CLASSIFICATION_ERROR", error_data):
            print(f"❌ Sent classification error: {error_code}")
    
    def _send_message(self, message_type, data):
        """Send message to ESP32"""
        if not self.connected or not self.sock:
            return False
        
        try:
            message = {
                "type": message_type,
                "timestamp": int(time.time() * 1000),  # milliseconds
                "data": data
            }
            
            message_str = json.dumps(message)
            
            # Send with delimiters
            self.sock.send("===MSG_START===\\n".encode())
            self.sock.send(message_str.encode())
            self.sock.send("\\n===MSG_END===\\n".encode())
            
            return True
            
        except Exception as e:
            print(f"❌ Send message error: {e}")
            self._handle_disconnection()
            return False
    
    def _handle_disconnection(self):
        """Handle disconnection"""
        print("🔌 Connection lost - will attempt to reconnect")
        self.connected = False
        
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
            self.sock = None

def main():
    """Main function"""
    daemon = SmartBinDaemon()
    daemon.start()

if __name__ == "__main__":
    main()
