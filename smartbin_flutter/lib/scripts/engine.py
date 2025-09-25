#!/usr/bin/env python3

import sys
import json
import random
import serial
import subprocess
import threading
import time
import base64
import io
from typing import Tuple

# Known classes for mock classification
CLASSES = ['aluminium', 'plastic', 'paper', 'glass', 'organic', 'metal', 'cardboard']


# State tracking
class EngineState:
    def __init__(self):
        self.classification_initialized = False
        self.bluetooth_initialized = False
        self.bluetooth_buffer = []
        # Bluetooth specific state
        self.ser = None
        self.running = False
        self.connected = False
        self.rfcomm_bound = False
        self.reader_thread = None
        self.esp32_mac = "EC:E3:34:15:F2:62"
        self.rfcomm_device = "/dev/rfcomm0"
        self.baudrate = 115200
        # Image processing state
        self.waiting_for_image = False
        self.image_metadata = {}
        self.image_parts = {}
        self.expected_parts = 0


state = EngineState()


def stop():
    """Stop the engine and free all resources"""
    print("🛑 Stopping SmartBin Engine...")

    # Stop bluetooth if running
    if state.bluetooth_initialized:
        _cleanup_bluetooth()

    # Stop any other resources
    state.classification_initialized = False

    print("✅ Engine stopped and resources freed")


def _cleanup_bluetooth():
    """Clean up bluetooth resources"""
    state.running = False
    state.connected = False

    # Wait for reader thread to finish
    if state.reader_thread and state.reader_thread.is_alive():
        state.reader_thread.join(timeout=2)
        print("✅ Reader thread stopped")

    # Close serial connection
    _cleanup_serial()

    # Release RFCOMM binding
    _cleanup_rfcomm_binding()

    state.bluetooth_initialized = False


def _setup_rfcomm_binding() -> bool:
    """Setup RFCOMM binding to ESP32"""
    try:
        print(f"🔗 Binding RFCOMM to {state.esp32_mac}...")
        # First try to release any existing binding
        try:
            subprocess.run(["sudo", "rfcomm", "release", "0"], capture_output=True, text=True, timeout=5)
        except Exception:
            pass

        # Bind to the ESP32
        res = subprocess.run(["sudo", "rfcomm", "bind", "0", state.esp32_mac, "1"],
                             capture_output=True, text=True, timeout=10)
        if res.returncode != 0:
            print(f"❌ Failed to bind RFCOMM: {res.stderr}")
            return False

        state.rfcomm_bound = True
        print(f"✅ RFCOMM bound to {state.rfcomm_device}")
        time.sleep(1)  # Give it time to establish
        return True

    except Exception as e:
        print(f"❌ RFCOMM setup error: {e}")
        return False


def _cleanup_rfcomm_binding():
    """Release RFCOMM binding"""
    if state.rfcomm_bound:
        try:
            subprocess.run(["sudo", "rfcomm", "release", "0"], capture_output=True, text=True, timeout=5)
            print("✅ RFCOMM released")
        except Exception as e:
            print(f"⚠️ RFCOMM release warning: {e}")
        state.rfcomm_bound = False


def _setup_serial() -> bool:
    """Setup serial connection"""
    try:
        print(f"📡 Opening serial {state.rfcomm_device}...")
        state.ser = serial.Serial(
            port=state.rfcomm_device,
            baudrate=state.baudrate,
            timeout=1,
            write_timeout=1,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
        )
        state.ser.flushInput()
        state.ser.flushOutput()
        print("✅ Serial connection established")
        return True

    except Exception as e:
        print(f"❌ Serial setup error: {e}")
        return False


def _cleanup_serial():
    """Close serial connection"""
    if state.ser and state.ser.is_open:
        try:
            state.ser.close()
            print("✅ Serial connection closed")
        except Exception as e:
            print(f"⚠️ Serial close warning: {e}")


def _start_reader_thread():
    """Start the bluetooth reader thread"""
    state.reader_thread = threading.Thread(target=_bluetooth_reader_loop, daemon=True)
    state.reader_thread.start()
    print("📖 Bluetooth reader thread started")


def _bluetooth_reader_loop():
    """Main bluetooth reader loop - runs in separate thread"""
    print("📖 Bluetooth reader active")
    while state.running and state.ser and state.ser.is_open:
        try:
            if state.ser.in_waiting > 0:
                line = state.ser.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    _process_bluetooth_line(line)
            else:
                time.sleep(0.01)  # Small delay to prevent busy waiting
        except Exception as e:
            if state.running:
                print(f"❌ Bluetooth reader error: {e}")
            break
    print("📖 Bluetooth reader stopped")


def _process_bluetooth_line(line: str):
    """Process a line received from bluetooth"""
    if _is_protocol_message(line):
        code, content = _extract_code_content(line)
        _handle_protocol_message(code, content)
    else:
        # Regular message - add to buffer for external consumption
        state.bluetooth_buffer.append(line)
        print(f"📝 ESP32: {line}")


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


def _extract_code_content(line: str) -> Tuple[str, str]:
    """Extract protocol code and content from line"""
    code = line[:5]
    content = line[6:] if len(line) > 6 else ""
    return code, content


def _handle_protocol_message(code: str, content: str):
    """Handle protocol messages internally"""
    print(f"📥 Protocol: {code} {content}")

    if code == 'RTC00':
        print("🤝 ESP32 requesting connection")
        _send_bluetooth_message('RTC01', 'Laptop ready')

    elif code == 'RTC02':
        print("🎉 Connection established")
        state.connected = True

    elif code == 'PA000':
        _handle_image_metadata(content)

    elif code.startswith('PA'):
        _handle_image_part(int(code[2:]), content)

    elif code.startswith('PX'):
        _handle_final_image_part(int(code[2:]), content)

    elif code.startswith('ERR'):
        print(f"⚠️ ESP32 Error: {content}")
        # Add error to buffer so Flutter app can see it
        state.bluetooth_buffer.append(f"ERROR: {content}")


def _send_bluetooth_message(code: str, content: str = "") -> bool:
    """Send a message via bluetooth"""
    try:
        if not state.ser or not state.ser.is_open:
            print("❌ Serial not open")
            return False

        msg = f"{code} {content}".strip()
        state.ser.write((msg + "\n").encode("utf-8"))
        state.ser.flush()
        print(f"📤 Sent: {msg}")
        return True

    except Exception as e:
        print(f"❌ Bluetooth send error: {e}")
        return False


def _handle_image_metadata(content: str):
    """Handle image metadata from ESP32"""
    print(f"📷 Image metadata: {content}")
    state.image_metadata = {}
    state.image_parts = {}

    for item in content.split(','):
        item = item.strip()
        if ':' in item:
            k, v = item.split(':', 1)
            state.image_metadata[k.strip()] = v.strip()

    state.expected_parts = int(state.image_metadata.get('parts', '0'))
    state.waiting_for_image = True
    print(f"📊 Expecting {state.expected_parts} image parts")


def _handle_image_part(part_num: int, content: str):
    """Handle image part from ESP32"""
    if not state.waiting_for_image:
        print("⚠️ Image part received unexpectedly")
        return

    state.image_parts[part_num] = content
    print(f"📦 Received image part {part_num}/{state.expected_parts}")


def _handle_final_image_part(part_num: int, content: str):
    """Handle final image part from ESP32"""
    if not state.waiting_for_image:
        print("⚠️ Final image part received unexpectedly")
        return

    state.image_parts[part_num] = content
    print(f"🏁 Final image part {part_num}/{state.expected_parts}")
    _process_complete_image()


def _process_complete_image():
    """Process complete image received from ESP32"""
    try:
        print("🔄 Processing complete image...")
        base64_data = "".join(state.image_parts.get(i, "") for i in range(1, state.expected_parts + 1))
        image_data = base64.b64decode(base64_data)

        # Save image temporarily and add to buffer for Flutter app
        timestamp = int(time.time())
        image_path = f"/tmp/smartbin_image_{timestamp}.jpg"

        with open(image_path, 'wb') as f:
            f.write(image_data)

        print(f"🖼️ Image saved: {image_path}")

        # Add image notification to buffer
        state.bluetooth_buffer.append(f"IMAGE_RECEIVED: {image_path}")

    except Exception as e:
        print(f"❌ Image processing error: {e}")
        _send_bluetooth_message('ERR04', 'image_processing_failed')

    finally:
        # Reset image state
        state.waiting_for_image = False
        state.image_metadata = {}
        state.image_parts = {}
        state.expected_parts = 0


def mock_classify(image_path):
    """
    Perform mock classification by generating random confidence values
    that sum to approximately 1.0
    """
    # Generate random weights
    weights = [random.random() for _ in CLASSES]
    total_weight = sum(weights)

    # Normalize to create confidence values
    confidences = {cls: round(weight / total_weight, 2) for cls, weight in zip(CLASSES, weights)}

    return confidences


def handle_classification_init():
    """Initialize classification module"""
    if state.classification_initialized:
        print("Classification module already initialized")
        return

    try:
        # TODO: Add actual classification initialization logic here
        # Example: Load YOLO model, initialize GPU, etc.
        print("Initializing classification module...")

        # Placeholder for actual initialization
        # from ultralytics import YOLO
        # model = YOLO('yolo11n-cls.pt')

        state.classification_initialized = True
        print("success")
    except Exception as e:
        print(f"Error initializing classification: {e}")


def handle_bluetooth_init():
    """Initialize bluetooth module"""
    if state.bluetooth_initialized:
        print("Bluetooth module already initialized")
        return

    try:
        print("Initializing bluetooth module...")

        # Setup RFCOMM binding
        if not _setup_rfcomm_binding():
            print("Error: Failed to setup RFCOMM binding")
            return

        # Setup serial connection
        if not _setup_serial():
            print("Error: Failed to setup serial connection")
            _cleanup_rfcomm_binding()
            return

        # Start the communication
        state.running = True
        _start_reader_thread()

        state.bluetooth_initialized = True
        print("success")

    except Exception as e:
        print(f"Error initializing bluetooth: {e}")
        _cleanup_bluetooth()


def handle_bluetooth_send(message):
    """Send message via bluetooth"""
    if not state.bluetooth_initialized:
        print("Error: Bluetooth not initialized")
        return

    try:
        # Send the message directly (not as protocol message)
        if state.ser and state.ser.is_open:
            state.ser.write((message + "\n").encode("utf-8"))
            state.ser.flush()
            print(f"📤 Sent: {message}")
            print("success")
        else:
            print("Error: Serial connection not available")

    except Exception as e:
        print(f"Error sending bluetooth message: {e}")


def handle_bluetooth_get_buffer():
    """Get bluetooth buffer contents and clear the buffer"""
    if not state.bluetooth_initialized:
        print("Error: Bluetooth not initialized")
        return

    try:
        if state.bluetooth_buffer:
            # Return all buffered lines and clear the buffer
            buffer_content = "\n".join(state.bluetooth_buffer)
            state.bluetooth_buffer.clear()
            print(buffer_content)
        else:
            print("")  # Empty buffer

    except Exception as e:
        print(f"Error reading bluetooth buffer: {e}")


def main():
    # Check if the script is called with "start" argument
    if len(sys.argv) != 2 or sys.argv[1] != "start":
        print("Usage: python script.py start")
        sys.exit(1)

    print("ready")

    while True:
        try:
            # Get user input
            user_input = input().strip()

            # Handle exit commands
            if user_input.lower() in ['exit', 'quit']:
                break

            # Handle stop command
            elif user_input == 'stop':
                stop()

            # Handle classification init command
            elif user_input == 'classification init':
                handle_classification_init()

            # Handle bluetooth init command
            elif user_input == 'bluetooth init':
                handle_bluetooth_init()

            # Handle bluetooth send command
            elif user_input.startswith('bluetooth send '):
                message = user_input[15:].strip()  # Everything after "bluetooth send "
                if not message:
                    print("Error: No message provided")
                else:
                    handle_bluetooth_send(message)

            # Handle bluetooth get buffer command
            elif user_input == 'bluetooth get buffer':
                handle_bluetooth_get_buffer()

            # Handle classify command
            elif user_input.startswith('classify '):
                if not state.classification_initialized:
                    print("Error: Classification not initialized")
                    continue

                # Extract the image path (everything after "classify ")
                image_path = user_input[9:].strip()

                # Basic validation - check if path is not empty
                if not image_path:
                    print(json.dumps({"error": "No image path provided"}))
                    continue

                # Perform mock classification
                result = mock_classify(image_path)
                print(json.dumps(result))

            else:
                # Unknown command
                print("Error: Unknown command")

        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully
            print()
            break
        except EOFError:
            # Handle Ctrl+D or end of input
            break

    # Cleanup before exiting
    stop()


if __name__ == "__main__":
    main()
