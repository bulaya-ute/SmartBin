#!/usr/bin/env python3
"""
SmartBin Laptop Communication Daemon (RFCOMM version)
Uses the working rfcomm approach instead of PyBluez
"""

import json
import time
import base64
import threading
import signal
import sys
import subprocess
import os
from datetime import datetime
from queue import Queue, Empty
from PIL import Image
import io
import tempfile
import numpy as np

# Import YOLO for classification
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    print("⚠️  Warning: ultralytics not installed. Using dummy classification.")
    YOLO_AVAILABLE = False

# Configuration
ESP32_MAC = "EC:E3:34:15:F2:62"
ESP32_NAME = "SmartBin_ESP32"
RFCOMM_DEVICE = "/dev/rfcomm0"
HEARTBEAT_INTERVAL = 30
RECONNECT_DELAY = 5

class SmartBinDaemonRFCOMM:
    def __init__(self):
        self.running = False
        self.connected = False
        self.rfcomm_process = None
        self.rfcomm_file = None
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
        
        print(f"🤖 SmartBin Laptop Daemon v{self.version} (RFCOMM)")
        print(f"Target ESP32: {ESP32_NAME} ({ESP32_MAC})")
    
    def _load_model(self):
        """Load YOLO classification model"""
        if not YOLO_AVAILABLE:
            print("⚠️  YOLO not available - using dummy classification")
            return
        
        model_files = [f for f in os.listdir(".") if f.endswith('.pt')]
        if model_files:
            model_path = model_files[0]  # Use first .pt file found
            try:
                print(f"🧠 Loading YOLO model: {model_path}")
                self.model = YOLO(model_path)
                print("✅ YOLO model loaded successfully")
            except Exception as e:
                print(f"❌ Failed to load YOLO model: {e}")
                self.model = None
        else:
            print("📁 No .pt model files found")
    
    def start(self):
        """Start the communication daemon"""
        self.running = True
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        print("🚀 Starting RFCOMM communication daemon...")
        
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
        
        if self.rfcomm_file:
            try:
                self.rfcomm_file.close()
            except:
                pass
        
        if self.rfcomm_process:
            try:
                self.rfcomm_process.terminate()
            except:
                pass
        
        # Release rfcomm
        try:
            subprocess.run(['sudo', 'rfcomm', 'release', '0'], 
                         capture_output=True, timeout=5)
        except:
            pass
        
        print("👋 SmartBin daemon stopped")
        sys.exit(0)
    
    def _main_loop(self):
        """Main daemon loop"""
        while self.running:
            try:
                if self.connected and (time.time() - self.last_heartbeat) > HEARTBEAT_INTERVAL:
                    self._send_heartbeat()
                
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ Error in main loop: {e}")
                time.sleep(1)
    
    def _communication_loop(self):
        """Communication thread"""
        while self.running:
            try:
                if not self.connected:
                    self._connect_rfcomm()
                else:
                    self._receive_messages()
                    
            except Exception as e:
                print(f"❌ Communication error: {e}")
                self._handle_disconnection()
                time.sleep(RECONNECT_DELAY)
    
    def _connect_rfcomm(self):
        """Connect via RFCOMM"""
        try:
            print(f"🔗 Connecting to {ESP32_MAC} via RFCOMM...")
            
            # Bind RFCOMM
            result = subprocess.run([
                'sudo', 'rfcomm', 'bind', '0', ESP32_MAC, '1'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                print(f"❌ RFCOMM bind failed: {result.stderr}")
                raise Exception("RFCOMM bind failed")
            
            # Open device for read/write
            self.rfcomm_file = open(RFCOMM_DEVICE, 'r+b', buffering=0)
            
            print("✅ RFCOMM connection established")
            self.connected = True
            self.last_heartbeat = time.time()
            
        except Exception as e:
            print(f"❌ RFCOMM connection failed: {e}")
            self._cleanup_rfcomm()
            raise
    
    def _receive_messages(self):
        """Receive messages from ESP32"""
        if not self.rfcomm_file:
            return
        
        try:
            # Read line from RFCOMM device
            line = self.rfcomm_file.readline()
            if not line:
                raise Exception("No data received")
            
            text = line.decode('utf-8', errors='ignore').strip()
            if text:
                self._process_incoming_data(text)
                
        except Exception as e:
            print(f"❌ Receive error: {e}")
            raise
    
    def _process_incoming_data(self, data):
        """Process incoming data and extract messages"""
        print(f"📨 Received: {data}")
        
        # Handle different message types
        if "WAITING_LAPTOP" in data or "waiting" in data.lower():
            print("🔔 ESP32 is waiting for laptop connection")
            self._send_ready_signal()
        elif data.startswith("===MSG_START==="):
            # JSON message format
            # TODO: Implement JSON message parsing
            pass
        elif "IMAGE_DATA" in data:
            print("📸 Received image data signal")
            # TODO: Implement image data handling
            pass
    
    def _processing_loop(self):
        """Message processing thread"""
        while self.running:
            try:
                message = self.message_queue.get(timeout=1)
                self._handle_message(message)
            except Empty:
                continue
            except Exception as e:
                print(f"❌ Processing error: {e}")
    
    def _handle_message(self, message):
        """Handle received messages"""
        # TODO: Implement message handling
        pass
    
    def _send_ready_signal(self):
        """Send ready signal to ESP32"""
        try:
            if self.rfcomm_file:
                ready_msg = "LAPTOP_READY\n"
                self.rfcomm_file.write(ready_msg.encode())
                self.rfcomm_file.flush()
                print("✅ Sent ready signal to ESP32")
                return True
        except Exception as e:
            print(f"❌ Failed to send ready signal: {e}")
            return False
    
    def _send_heartbeat(self):
        """Send heartbeat"""
        try:
            if self.rfcomm_file:
                heartbeat_msg = "HEARTBEAT\n"
                self.rfcomm_file.write(heartbeat_msg.encode())
                self.rfcomm_file.flush()
                self.last_heartbeat = time.time()
                return True
        except Exception as e:
            print(f"❌ Heartbeat failed: {e}")
            return False
    
    def _handle_disconnection(self):
        """Handle disconnection"""
        print("🔌 Connection lost - will attempt to reconnect")
        self.connected = False
        self._cleanup_rfcomm()
    
    def _cleanup_rfcomm(self):
        """Clean up RFCOMM resources"""
        if self.rfcomm_file:
            try:
                self.rfcomm_file.close()
            except:
                pass
            self.rfcomm_file = None
        
        try:
            subprocess.run(['sudo', 'rfcomm', 'release', '0'], 
                         capture_output=True, timeout=5)
        except:
            pass

def main():
    daemon = SmartBinDaemonRFCOMM()
    daemon.start()

if __name__ == "__main__":
    main()