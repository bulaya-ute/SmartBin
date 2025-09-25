#!/usr/bin/env python3

import subprocess
import threading
import time
import base64
from typing import Tuple


class BluetoothModule:
    """Bluetooth communication module with static methods and fields"""

    # Static fields
    _initialized = False
    _ser = None
    _running = False
    _connected = False
    _rfcomm_bound = False
    _reader_thread = None
    _buffer = []

    # Configuration
    _esp32_mac = "EC:E3:34:15:F2:62"
    _rfcomm_device = "/dev/rfcomm0"
    _baudrate = 115200

    # Image processing state
    _waiting_for_image = False
    _image_metadata = {}
    _image_parts = {}
    _expected_parts = 0

    @staticmethod
    def is_initialized() -> bool:
        """Check if bluetooth module is initialized"""
        return BluetoothModule._initialized

    @staticmethod
    def init() -> bool:
        """Initialize bluetooth module"""
        if BluetoothModule._initialized:
            print("Bluetooth module already initialized")
            return True

        try:
            # Lazy import serial only when needed
            global serial
            import serial

            print("Initializing bluetooth module...")

            # Setup RFCOMM binding
            if not BluetoothModule._setup_rfcomm_binding():
                print("Error: Failed to setup RFCOMM binding")
                return False

            # Setup serial connection
            if not BluetoothModule._setup_serial():
                print("Error: Failed to setup serial connection")
                BluetoothModule._cleanup_rfcomm_binding()
                return False

            # Start the communication
            BluetoothModule._running = True
            BluetoothModule._start_reader_thread()

            BluetoothModule._initialized = True
            return True

        except Exception as e:
            print(f"Error initializing bluetooth: {e}")
            BluetoothModule._cleanup()
            return False

    @staticmethod
    def send_message(message: str) -> bool:
        """Send message via bluetooth"""
        if not BluetoothModule._initialized:
            print("Error: Bluetooth not initialized")
            return False

        try:
            # Send the message directly (not as protocol message)
            if BluetoothModule._ser and BluetoothModule._ser.is_open:
                BluetoothModule._ser.write((message + "\n").encode("utf-8"))
                BluetoothModule._ser.flush()
                print(f"📤 Sent: {message}")
                return True
            else:
                print("Error: Serial connection not available")
                return False

        except Exception as e:
            print(f"Error sending bluetooth message: {e}")
            return False

    @staticmethod
    def get_buffer() -> str:
        """Get bluetooth buffer contents and clear the buffer"""
        if not BluetoothModule._initialized:
            print("Error: Bluetooth not initialized")
            return ""

        try:
            if BluetoothModule._buffer:
                # Return all buffered lines and clear the buffer
                buffer_content = "\n".join(BluetoothModule._buffer)
                BluetoothModule._buffer.clear()
                return buffer_content
            else:
                return ""  # Empty buffer

        except Exception as e:
            print(f"Error reading bluetooth buffer: {e}")
            return ""

    @staticmethod
    def stop():
        """Stop the bluetooth module and free resources"""
        if BluetoothModule._initialized:
            BluetoothModule._cleanup()

    @staticmethod
    def _cleanup():
        """Clean up bluetooth resources"""
        BluetoothModule._running = False
        BluetoothModule._connected = False

        # Wait for reader thread to finish
        if BluetoothModule._reader_thread and BluetoothModule._reader_thread.is_alive():
            BluetoothModule._reader_thread.join(timeout=2)
            print("✅ Reader thread stopped")

        # Close serial connection
        BluetoothModule._cleanup_serial()

        # Release RFCOMM binding
        BluetoothModule._cleanup_rfcomm_binding()

        BluetoothModule._initialized = False

    @staticmethod
    def _setup_rfcomm_binding() -> bool:
        """Setup RFCOMM binding to ESP32"""
        try:
            print(f"🔗 Binding RFCOMM to {BluetoothModule._esp32_mac}...")
            # First try to release any existing binding
            try:
                subprocess.run(["sudo", "rfcomm", "release", "0"], capture_output=True, text=True, timeout=5)
            except Exception:
                pass

            # Bind to the ESP32
            res = subprocess.run(["sudo", "rfcomm", "bind", "0", BluetoothModule._esp32_mac, "1"],
                               capture_output=True, text=True, timeout=10)
            if res.returncode != 0:
                print(f"❌ Failed to bind RFCOMM: {res.stderr}")
                return False

            BluetoothModule._rfcomm_bound = True
            print(f"✅ RFCOMM bound to {BluetoothModule._rfcomm_device}")
            time.sleep(1)  # Give it time to establish
            return True

        except Exception as e:
            print(f"❌ RFCOMM setup error: {e}")
            return False

    @staticmethod
    def _cleanup_rfcomm_binding():
        """Release RFCOMM binding"""
        if BluetoothModule._rfcomm_bound:
            try:
                subprocess.run(["sudo", "rfcomm", "release", "0"], capture_output=True, text=True, timeout=5)
                print("✅ RFCOMM released")
            except Exception as e:
                print(f"⚠️ RFCOMM release warning: {e}")
            BluetoothModule._rfcomm_bound = False

    @staticmethod
    def _setup_serial() -> bool:
        """Setup serial connection"""
        try:
            print(f"📡 Opening serial {BluetoothModule._rfcomm_device}...")
            BluetoothModule._ser = serial.Serial(
                port=BluetoothModule._rfcomm_device,
                baudrate=BluetoothModule._baudrate,
                timeout=1,
                write_timeout=1,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
            )
            BluetoothModule._ser.flushInput()
            BluetoothModule._ser.flushOutput()
            print("✅ Serial connection established")
            return True

        except Exception as e:
            print(f"❌ Serial setup error: {e}")
            return False

    @staticmethod
    def _cleanup_serial():
        """Close serial connection"""
        if BluetoothModule._ser and BluetoothModule._ser.is_open:
            try:
                BluetoothModule._ser.close()
                print("✅ Serial connection closed")
            except Exception as e:
                print(f"⚠️ Serial close warning: {e}")

    @staticmethod
    def _start_reader_thread():
        """Start the bluetooth reader thread"""
        BluetoothModule._reader_thread = threading.Thread(target=BluetoothModule._bluetooth_reader_loop, daemon=True)
        BluetoothModule._reader_thread.start()
        print("📖 Bluetooth reader thread started")

    @staticmethod
    def _bluetooth_reader_loop():
        """Main bluetooth reader loop - runs in separate thread"""
        print("📖 Bluetooth reader active")
        while BluetoothModule._running and BluetoothModule._ser and BluetoothModule._ser.is_open:
            try:
                if BluetoothModule._ser.in_waiting > 0:
                    line = BluetoothModule._ser.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        BluetoothModule._process_bluetooth_line(line)
                else:
                    time.sleep(0.01)  # Small delay to prevent busy waiting
            except Exception as e:
                if BluetoothModule._running:
                    print(f"❌ Bluetooth reader error: {e}")
                break
        print("📖 Bluetooth reader stopped")

    @staticmethod
    def _process_bluetooth_line(line: str):
        """Process a line received from bluetooth"""
        if BluetoothModule._is_protocol_message(line):
            code, content = BluetoothModule._extract_code_content(line)
            BluetoothModule._handle_protocol_message(code, content)
        else:
            # Regular message - add to buffer for external consumption
            BluetoothModule._buffer.append(line)
            print(f"📝 ESP32: {line}")

    @staticmethod
    def _is_protocol_message(line: str) -> bool:
        """Check if line is a protocol message"""
        if len(line) < 6:
            return False
        code = line[:5]
        if line[5] != ' ':
            return False
        return (code in ['RTC00', 'RTC01', 'RTC02', 'CLS01'] or
                code.startswith('PA') or code.startswith('PX') or
                code.startswith('ERR'))

    @staticmethod
    def _extract_code_content(line: str) -> Tuple[str, str]:
        """Extract protocol code and content from line"""
        code = line[:5]
        content = line[6:] if len(line) > 6 else ""
        return code, content

    @staticmethod
    def _handle_protocol_message(code: str, content: str):
        """Handle protocol messages internally"""
        print(f"📥 Protocol: {code} {content}")

        if code == 'RTC00':
            print("🤝 ESP32 requesting connection")
            BluetoothModule._send_bluetooth_message('RTC01', 'Laptop ready')

        elif code == 'RTC02':
            print("🎉 Connection established")
            BluetoothModule._connected = True

        elif code == 'PA000':
            BluetoothModule._handle_image_metadata(content)

        elif code.startswith('PA'):
            BluetoothModule._handle_image_part(int(code[2:]), content)

        elif code.startswith('PX'):
            BluetoothModule._handle_final_image_part(int(code[2:]), content)

        elif code.startswith('ERR'):
            print(f"⚠️ ESP32 Error: {content}")
            # Add error to buffer so Flutter app can see it
            BluetoothModule._buffer.append(f"ERROR: {content}")

    @staticmethod
    def _send_bluetooth_message(code: str, content: str = "") -> bool:
        """Send a message via bluetooth"""
        try:
            if not BluetoothModule._ser or not BluetoothModule._ser.is_open:
                print("❌ Serial not open")
                return False

            msg = f"{code} {content}".strip()
            BluetoothModule._ser.write((msg + "\n").encode("utf-8"))
            BluetoothModule._ser.flush()
            print(f"📤 Sent: {msg}")
            return True

        except Exception as e:
            print(f"❌ Bluetooth send error: {e}")
            return False

    @staticmethod
    def _handle_image_metadata(content: str):
        """Handle image metadata from ESP32"""
        print(f"📷 Image metadata: {content}")
        BluetoothModule._image_metadata = {}
        BluetoothModule._image_parts = {}

        for item in content.split(','):
            item = item.strip()
            if ':' in item:
                k, v = item.split(':', 1)
                BluetoothModule._image_metadata[k.strip()] = v.strip()

        BluetoothModule._expected_parts = int(BluetoothModule._image_metadata.get('parts', '0'))
        BluetoothModule._waiting_for_image = True
        print(f"📊 Expecting {BluetoothModule._expected_parts} image parts")

    @staticmethod
    def _handle_image_part(part_num: int, content: str):
        """Handle image part from ESP32"""
        if not BluetoothModule._waiting_for_image:
            print("⚠️ Image part received unexpectedly")
            return

        BluetoothModule._image_parts[part_num] = content
        print(f"📦 Received image part {part_num}/{BluetoothModule._expected_parts}")

    @staticmethod
    def _handle_final_image_part(part_num: int, content: str):
        """Handle final image part from ESP32"""
        if not BluetoothModule._waiting_for_image:
            print("⚠️ Final image part received unexpectedly")
            return

        BluetoothModule._image_parts[part_num] = content
        print(f"🏁 Final image part {part_num}/{BluetoothModule._expected_parts}")
        BluetoothModule._process_complete_image()

    @staticmethod
    def _process_complete_image():
        """Process complete image received from ESP32"""
        try:
            print("🔄 Processing complete image...")
            base64_data = "".join(BluetoothModule._image_parts.get(i, "") for i in range(1, BluetoothModule._expected_parts + 1))
            image_data = base64.b64decode(base64_data)

            # Save image temporarily and add to buffer for Flutter app
            timestamp = int(time.time())
            image_path = f"/tmp/smartbin_image_{timestamp}.jpg"

            with open(image_path, 'wb') as f:
                f.write(image_data)

            print(f"🖼️ Image saved: {image_path}")

            # Add image notification to buffer
            BluetoothModule._buffer.append(f"IMAGE_RECEIVED: {image_path}")

        except Exception as e:
            print(f"❌ Image processing error: {e}")
            BluetoothModule._send_bluetooth_message('ERR04', 'image_processing_failed')

        finally:
            # Reset image state
            BluetoothModule._waiting_for_image = False
            BluetoothModule._image_metadata = {}
            BluetoothModule._image_parts = {}
            BluetoothModule._expected_parts = 0

