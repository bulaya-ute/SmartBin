#!/usr/bin/env python3
import os
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
    _sudo_password = None

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
    def handle_command(args: list):
        """Handle bluetooth commands"""
        if not args:
            print("Error: No bluetooth subcommand provided")
            return

        subcommand = args[0]

        if subcommand == 'init':
            sudo_password = args[1] if len(args) > 1 else None
            BluetoothModule.init(sudo_password)

        elif subcommand == 'connect':
            mac_address = args[1] if len(args) > 1 else None
            success = BluetoothModule.connect(mac_address)
            if success:
                print("success")

        elif subcommand == 'disconnect':
            success = BluetoothModule.disconnect()
            if success:
                print("success")

        elif subcommand == 'send':
            if len(args) < 2:
                print("Error: No message provided")
                return
            message = ' '.join(args[1:])  # Join remaining args as message
            success = BluetoothModule.transmit_message(message)

        elif len(args) >= 2 and args[0] == 'get' and args[1] == 'buffer':
            buffer_content = BluetoothModule.get_buffer()
            print(buffer_content)

        else:
            print("Error: Unknown bluetooth subcommand")

    @staticmethod
    def transmit_message(message: str) -> bool:
        """Transmit a message via bluetooth"""
        if not BluetoothModule._connected:
            print("Error: Not connected to ESP32")
            return False

        try:
            # Add to buffer for logging
            BluetoothModule._buffer.append(f"SENT: {message}")

            # Send the message
            return BluetoothModule._send_bluetooth_message("", message)
        except Exception as e:
            print(f"Error transmitting message: {e}")
            return False

    @staticmethod
    def get_buffer() -> list:
        """Get and clear the bluetooth buffer"""
        buffer_copy = BluetoothModule._buffer.copy()
        BluetoothModule._buffer.clear()
        return buffer_copy

    @staticmethod
    def read_buffer() -> list:
        """Read the bluetooth buffer without clearing it"""
        return BluetoothModule._buffer.copy()

    @staticmethod
    def is_initialized() -> bool:
        """Check if bluetooth module is initialized"""
        return BluetoothModule._initialized

    @staticmethod
    def init(sudo_password: str = None) -> bool:
        """Initialize bluetooth module (setup prerequisites only)"""
        if BluetoothModule._initialized:
            print("Bluetooth module already initialized")
            return True

        try:
            # Lazy import serial only when needed
            global serial
            import serial

            # Store sudo password for later use
            BluetoothModule._sudo_password = sudo_password

            BluetoothModule._initialized = True
            print("Success")
            return True

        except Exception as e:
            print(f"Error: {e}")
            return False

    @staticmethod
    def connect(mac_address: str = None) -> bool:
        """Connect to ESP32 via bluetooth"""
        if not BluetoothModule._initialized:
            print("Error: Bluetooth module not initialized")
            return False

        if BluetoothModule._connected:
            print("Already connected to ESP32")
            return True

        # Use provided mac address or default
        target_mac = mac_address if mac_address else BluetoothModule._esp32_mac

        try:
            print(f"Connecting to ESP32 at {target_mac}...")

            # Setup RFCOMM binding
            if not BluetoothModule._setup_rfcomm_binding(target_mac, BluetoothModule._sudo_password):
                print("Error: Failed to setup RFCOMM binding")
                return False

            # Setup serial connection
            if not BluetoothModule._setup_serial():
                print("Error: Failed to setup serial connection")
                BluetoothModule._cleanup_rfcomm_binding(BluetoothModule._sudo_password)
                return False

            # Start the communication
            BluetoothModule._running = True
            BluetoothModule._start_reader_thread()

            BluetoothModule._connected = True
            print("Successfully connected to ESP32")
            return True

        except Exception as e:
            print(f"Error connecting to ESP32: {e}")
            BluetoothModule._cleanup_connection()
            return False

    @staticmethod
    def disconnect() -> bool:
        """Disconnect from ESP32"""
        if not BluetoothModule._connected:
            print("Not connected to ESP32")
            return True

        try:
            print("Disconnecting from ESP32...")
            BluetoothModule._cleanup_connection()
            print("Successfully disconnected from ESP32")
            return True

        except Exception as e:
            print(f"Error during disconnect: {e}")
            return False

    @staticmethod
    def _cleanup_connection():
        """Clean up connection resources (not the module itself)"""
        BluetoothModule._running = False
        BluetoothModule._connected = False

        # Wait for reader thread to finish
        if BluetoothModule._reader_thread and BluetoothModule._reader_thread.is_alive():
            BluetoothModule._reader_thread.join(timeout=2)
            print("✅ Reader thread stopped")

        # Close serial connection
        BluetoothModule._cleanup_serial()

        # Release RFCOMM binding
        BluetoothModule._cleanup_rfcomm_binding(BluetoothModule._sudo_password)

    @staticmethod
    def stop():
        """Stop the bluetooth module and free all resources"""
        if BluetoothModule._initialized:
            # Disconnect first if connected
            if BluetoothModule._connected:
                BluetoothModule.disconnect()

            # Clean up module
            BluetoothModule._initialized = False
            BluetoothModule._sudo_password = None
            print("✅ Bluetooth module stopped")

    @staticmethod
    def _cleanup():
        """Clean up bluetooth resources (legacy method for compatibility)"""
        BluetoothModule._cleanup_connection()
        BluetoothModule._initialized = False

    @staticmethod
    def _setup_rfcomm_binding(mac_address: str, sudo_password: str = None) -> bool:
        """Setup RFCOMM binding to specified MAC address"""
        try:
            # First try to release any existing binding
            try:
                if sudo_password:
                    release_cmd = subprocess.Popen(
                        ["sudo", "-S", "rfcomm", "release", "0"],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    release_cmd.communicate(input=sudo_password + "\n", timeout=5)
                else:
                    subprocess.run(["sudo", "rfcomm", "release", "0"], capture_output=True, text=True, timeout=5)
            except Exception:
                pass

            # Bind to the specified MAC address
            if sudo_password:
                bind_cmd = subprocess.Popen(
                    ["sudo", "-S", "rfcomm", "bind", "0", mac_address, "1"],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                stdout, stderr = bind_cmd.communicate(input=sudo_password + "\n", timeout=10)

                if bind_cmd.returncode != 0:
                    print(f"Error: Failed to bind RFCOMM: {stderr}")
                    return False
            else:
                res = subprocess.run(["sudo", "rfcomm", "bind", "0", mac_address, "1"],
                                   capture_output=True, text=True, timeout=10)
                if res.returncode != 0:
                    print(f"Error: Failed to bind RFCOMM: {res.stderr}")
                    return False

            BluetoothModule._rfcomm_bound = True
            print(f"Info: RFCOMM bound to {BluetoothModule._rfcomm_device}")
            time.sleep(1)  # Give it time to establish
            return True

        except Exception as e:
            print(f"❌ RFCOMM setup error: {e}")
            return False

    @staticmethod
    def _cleanup_rfcomm_binding(sudo_password: str = None):
        """Release RFCOMM binding"""
        if BluetoothModule._rfcomm_bound:
            try:
                if sudo_password:
                    release_cmd = subprocess.Popen(
                        ["sudo", "-S", "rfcomm", "release", "0"],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    release_cmd.communicate(input=sudo_password + "\n", timeout=5)
                else:
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
        print("📖 Bluetooth reader stopped. Disconnecting bluetooth...")
        BluetoothModule.handle_command(["disconnect"])


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
            # timestamp = int(time.time())
            image_path = f"./smartbin_capture.jpg"

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

