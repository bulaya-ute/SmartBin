#!/usr/bin/env python3

import sys
import json

# Import modules from our modular structure
from modules.bluetooth_module import BluetoothModule
from modules.classification_module import ClassificationModule


class SmartBinEngine:
    """Main engine class that orchestrates different modules"""

    @staticmethod
    def stop():
        """Stop the engine and free all resources"""
        print("🛑 Stopping SmartBin Engine...")

        # Stop bluetooth if running
        if BluetoothModule.is_initialized():
            BluetoothModule.stop()

        # Stop classification if running
        if ClassificationModule.is_initialized():
            ClassificationModule.stop()

        print("✅ Engine stopped and resources freed")


def handle_classification_init():
    """Initialize classification module"""
    success = ClassificationModule.init()
    if success:
        print("success")
    # Error messages are already printed by the module


def handle_bluetooth_init(sudo_password: str = None):
    """Initialize bluetooth module with optional sudo password"""
    success = BluetoothModule.init(sudo_password)
    if success:
        print("success")
    # Error messages are already printed by the module


def handle_bluetooth_send(message: str):
    """Send message via bluetooth"""
    success = BluetoothModule.send_message(message)
    if success:
        print("success")
    # Error messages are already printed by the module


def handle_bluetooth_get_buffer():
    """Get bluetooth buffer contents and clear the buffer"""
    buffer_content = BluetoothModule.get_buffer()
    print(buffer_content)


def handle_classify(image_path: str):
    """Handle classification request"""
    result = ClassificationModule.classify(image_path)
    if result:
        print(json.dumps(result))
    else:
        print(json.dumps({"error": "Classification failed"}))


def handle_bluetooth_connect(mac_address: str = None):
    """Handle bluetooth connect command"""
    success = BluetoothModule.connect(mac_address)
    if success:
        print("success")
    # Error messages are already printed by the module


def handle_bluetooth_disconnect():
    """Handle bluetooth disconnect command"""
    success = BluetoothModule.disconnect()
    if success:
        print("success")
    # Error messages are already printed by the module


def handle_classification_get_classes():
    """Handle classification get-classes command"""
    classes = ClassificationModule.get_classes()
    print(json.dumps(classes))


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
                SmartBinEngine.stop()

            # Handle classification init command
            elif user_input == 'classification init':
                handle_classification_init()

            # Handle bluetooth init command
            elif user_input.startswith('bluetooth init'):
                # Check if password is provided
                parts = user_input.split(' ', 2)
                sudo_password = parts[2] if len(parts) >= 3 else None
                handle_bluetooth_init(sudo_password)

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
                if not ClassificationModule.is_initialized():
                    print("Error: Classification not initialized")
                    continue

                # Extract the image path (everything after "classify ")
                image_path = user_input[9:].strip()

                # Basic validation - check if path is not empty
                if not image_path:
                    print(json.dumps({"error": "No image path provided"}))
                    continue

                handle_classify(image_path)

            # Handle bluetooth connect command
            elif user_input.startswith('bluetooth connect '):
                mac_address = user_input[17:].strip()  # Everything after "bluetooth connect "
                if not mac_address:
                    print("Error: No MAC address provided")
                else:
                    handle_bluetooth_connect(mac_address)

            # Handle bluetooth disconnect command
            elif user_input == 'bluetooth disconnect':
                handle_bluetooth_disconnect()

            # Handle classification get-classes command
            elif user_input == 'classification get-classes':
                handle_classification_get_classes()

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
    SmartBinEngine.stop()


if __name__ == "__main__":
    main()
