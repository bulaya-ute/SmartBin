#!/usr/bin/env python3
"""
SmartBin Image Monitor
Receives and processes ESP32 transmissions using the working Bluetooth approach
Displays captured images and can be extended for classification feedback
"""

import subprocess
import threading
import queue
import time
import re
import base64
import os
from PIL import Image
import io
from datetime import datetime

class ESP32ImageMonitor:
    def __init__(self, esp32_mac="EC:E3:34:15:F2:62"):
        self.esp32_mac = esp32_mac
        self.running = False
        self.rfcomm_process = None
        self.output_queue = queue.Queue()
        self.current_image_data = {}
        self.image_counter = 0
        
        print(f"🤖 ESP32 Image Monitor")
        print(f"Target ESP32: {esp32_mac}")
        print(f"Using rfcomm + subprocess approach (same as working bash script)")
        
    def start_monitoring(self):
        """Start monitoring ESP32 transmissions"""
        self.running = True
        
        # Start the rfcomm connection (same approach as bash script)
        try:
            print(f"🔗 Connecting to ESP32 via rfcomm...")
            
            # First, bind rfcomm device (same as bash script)
            bind_cmd = ["sudo", "rfcomm", "bind", "0", self.esp32_mac, "1"]
            bind_result = subprocess.run(bind_cmd, capture_output=True, text=True)
            
            if bind_result.returncode != 0:
                print(f"❌ Failed to bind rfcomm: {bind_result.stderr}")
                return False
                
            print("✅ rfcomm device bound to /dev/rfcomm0")
            
            # Now read from the device
            read_cmd = ["sudo", "cat", "/dev/rfcomm0"]
            self.rfcomm_process = subprocess.Popen(
                read_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            print("✅ Connected - monitoring ESP32 output...")
            print("📡 Waiting for transmissions...")
            print("💡 Make sure ESP32 is powered on and running")
            print("💡 Try triggering image capture on ESP32")
            print("=" * 60)
            
            # Start output processing thread
            monitor_thread = threading.Thread(target=self._monitor_output, daemon=True)
            monitor_thread.start()
            
            # Start image processing thread
            image_thread = threading.Thread(target=self._process_images, daemon=True)
            image_thread.start()
            
            return True
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def _monitor_output(self):
        """Monitor rfcomm output (same as what bash script sees)"""
        buffer = ""
        line_count = 0
        
        try:
            while self.running and self.rfcomm_process:
                # Read character by character to avoid blocking
                char = self.rfcomm_process.stdout.read(1)
                if not char:
                    # Check if process is still alive
                    if self.rfcomm_process.poll() is not None:
                        print("❌ rfcomm process ended")
                        break
                    continue
                    
                buffer += char
                
                # Process complete lines
                if char == '\n':
                    line = buffer.strip()
                    buffer = ""
                    line_count += 1
                    
                    if line:
                        # Add timestamp and display
                        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                        print(f"[{timestamp}] {line}")
                        
                        # Queue for image processing
                        self.output_queue.put(line)
                    
                    # Show we're receiving data
                    if line_count % 10 == 1:  # Every 10 lines
                        print(f"📊 Received {line_count} lines so far...")
                        
        except Exception as e:
            print(f"❌ Monitor error: {e}")
        finally:
            print(f"📊 Total lines received: {line_count}")
            self._cleanup()
    
    def _process_images(self):
        """Process queued lines to extract and decode images"""
        image_buffer = []
        in_image = False
        
        while self.running:
            try:
                # Get line from queue with timeout
                line = self.output_queue.get(timeout=1)
                
                # Look for image data markers
                if "==IMAGE_START==" in line:
                    print("\n📸 Image transmission started")
                    in_image = True
                    image_buffer = []
                    self.current_image_data = {}
                    
                elif "==IMAGE_END==" in line:
                    if in_image:
                        print("📸 Image transmission complete - processing...")
                        self._decode_image(image_buffer)
                    in_image = False
                    image_buffer = []
                    
                elif in_image:
                    # Collect image data
                    image_buffer.append(line)
                    
                    # Extract metadata
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
                            
            except queue.Empty:
                continue
            except Exception as e:
                print(f"❌ Image processing error: {e}")
    
    def _decode_image(self, image_lines):
        """Decode Base64 image from collected lines"""
        try:
            print(f"🔍 Processing image data...")
            
            # Extract Base64 data from chunked format
            base64_data = ""
            collecting = False
            
            for line in image_lines:
                if "BASE64_DATA:" in line:
                    collecting = True
                    continue
                elif "[IMG_B64]" in line:
                    # Handle chunked format: [IMG_B64] [1/86] base64data...
                    parts = line.split("] ")
                    if len(parts) >= 2:
                        base64_part = parts[-1].strip()  # Get the actual Base64 data
                        # Remove any non-Base64 characters
                        cleaned = re.sub(r'[^A-Za-z0-9+/=]', '', base64_part)
                        if cleaned and len(cleaned) > 10:  # Only substantial chunks
                            base64_data += cleaned
                elif collecting and line and not line.startswith('['):
                    # Remove any non-Base64 characters
                    cleaned = re.sub(r'[^A-Za-z0-9+/=]', '', line)
                    if cleaned:
                        base64_data += cleaned
            
            if not base64_data:
                print("❌ No Base64 data found")
                print("🔍 Debug: Sample lines received:")
                for i, line in enumerate(image_lines[:10]):  # Show first 10 lines
                    print(f"  [{i}]: {line}")
                return
                
            print(f"📊 Base64 length: {len(base64_data)} characters")
            
            # Fix padding if needed
            missing_padding = len(base64_data) % 4
            if missing_padding:
                base64_data += '=' * (4 - missing_padding)
                print(f"🔧 Fixed Base64 padding")
            
            # Decode image
            image_bytes = base64.b64decode(base64_data)
            print(f"✅ Decoded {len(image_bytes)} bytes")
            
            # Verify size if available
            if 'size' in self.current_image_data:
                expected_size = self.current_image_data['size']
                if len(image_bytes) == expected_size:
                    print("✅ Size matches metadata")
                else:
                    print(f"⚠️ Size mismatch: got {len(image_bytes)}, expected {expected_size}")
            
            # Save image
            self.image_counter += 1
            timestamp = int(time.time())
            filename = f"esp32_capture_{timestamp}_{self.image_counter:03d}.jpg"
            
            with open(filename, 'wb') as f:
                f.write(image_bytes)
            print(f"💾 Saved: {filename}")
            
            # Verify and display image info
            try:
                with Image.open(filename) as img:
                    print(f"🖼️ Image: {img.format} {img.size} {img.mode}")
                    
                    # Show dimensions comparison
                    if 'width' in self.current_image_data and 'height' in self.current_image_data:
                        expected_dims = (self.current_image_data['width'], self.current_image_data['height'])
                        if img.size == expected_dims:
                            print("✅ Dimensions match metadata")
                        else:
                            print(f"⚠️ Dimension mismatch: got {img.size}, expected {expected_dims}")
                    
                    # Analyze image for lighting/quality
                    self._analyze_image_quality(img, filename)
                    
                    # Try to display (optional)
                    try:
                        img.show()
                        print("🖼️ Image opened in viewer")
                    except:
                        print("ℹ️ Could not auto-open image")
                        
            except Exception as e:
                print(f"⚠️ PIL verification failed: {e}")
            
            print("=" * 60)
            
        except Exception as e:
            print(f"❌ Image decode failed: {e}")
    
    def _analyze_image_quality(self, img, filename):
        """Analyze image quality for classification feedback"""
        try:
            import numpy as np
            
            # Convert to numpy array for analysis
            img_array = np.array(img)
            
            # Basic statistics
            if len(img_array.shape) == 3:  # Color image
                # Convert to grayscale for brightness analysis
                gray = np.dot(img_array[...,:3], [0.2989, 0.5870, 0.1140])
            else:
                gray = img_array
            
            # Calculate image statistics
            mean_brightness = np.mean(gray)
            std_brightness = np.std(gray)
            min_brightness = np.min(gray)
            max_brightness = np.max(gray)
            
            print(f"📊 Image Quality Analysis:")
            print(f"   • Average brightness: {mean_brightness:.1f}/255")
            print(f"   • Brightness range: {min_brightness}-{max_brightness}")
            print(f"   • Contrast (std): {std_brightness:.1f}")
            
            # Quality assessment
            if mean_brightness < 50:
                print("   ⚠️ Image appears DARK - consider better lighting")
            elif mean_brightness > 200:
                print("   ⚠️ Image appears BRIGHT - might be overexposed")
            else:
                print("   ✅ Brightness looks good")
                
            if std_brightness < 20:
                print("   ⚠️ Low contrast - image might be blurry or flat")
            else:
                print("   ✅ Good contrast")
                
        except ImportError:
            print("📊 Install numpy for image quality analysis")
        except Exception as e:
            print(f"📊 Quality analysis error: {e}")
    
    def _cleanup(self):
        """Clean up resources"""
        print("\n🔌 Cleaning up...")
        
        if self.rfcomm_process:
            try:
                self.rfcomm_process.terminate()
                self.rfcomm_process.wait(timeout=5)
            except:
                try:
                    self.rfcomm_process.kill()
                except:
                    pass
        
        # Unbind rfcomm device
        try:
            subprocess.run(["sudo", "rfcomm", "release", "0"], 
                         capture_output=True, timeout=5)
        except:
            pass
    
    def stop(self):
        """Stop monitoring"""
        self.running = False
        self._cleanup()

def main():
    """Main function"""
    monitor = ESP32ImageMonitor()
    
    try:
        if monitor.start_monitoring():
            print("\n💡 Tips:")
            print("   - Images will be saved automatically")
            print("   - Quality analysis helps adjust ESP32 lighting")
            print("   - Press Ctrl+C to stop")
            print("\n🔄 Monitoring active...")
            
            # Keep running until interrupted
            while monitor.running:
                time.sleep(1)
        else:
            print("❌ Failed to start monitoring")
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping monitor...")
    finally:
        monitor.stop()
        print("👋 Monitor stopped")

if __name__ == "__main__":
    main()
