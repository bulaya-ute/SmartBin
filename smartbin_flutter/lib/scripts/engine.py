#!/usr/bin/env python3
from modules.utils import split_command
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

    @staticmethod
    def process_command(command: str):
        """Process a single command, and dispatch to appropriate module"""

        # Handle stop command
        if command == 'stop':
            SmartBinEngine.stop()

        # Split the command
        command_parts = split_command(command)

        if not command_parts:
            print("Error: Empty command")
            return
        elif len(command_parts) == 1:
            remaining_args = []
        else:
            remaining_args = command_parts[1:]

        # Get the main command (first part)
        main_command = command_parts[0]

        # Dispatch to appropriate module
        if main_command in ['classify', "classification"]:
            ClassificationModule.handle_command(remaining_args)
        elif main_command == 'bluetooth':
            BluetoothModule.handle_command(remaining_args)
        else:
            print("Error: Unknown command")


    # @staticmethod
    # def handle_classification_init():
    #     """Initialize classification module"""
    #     success = ClassificationModule.init()
    #     # if success:
    #     #     print("success")
    #     # Error messages are already printed by the module

    # @staticmethod
    # def handle_bluetooth_init(sudo_password: str = None):
    #     """Initialize bluetooth module with optional sudo password"""
    #     success = BluetoothModule.init(sudo_password)
    #     # if success:
    #     #     print("success")
    #     # Error messages are already printed by the module

    # @staticmethod
    # def handle_bluetooth_send(message: str):
    #     """Send message via bluetooth"""
    #     success = BluetoothModule.send_message(message)
    #     # if success:
    #     #     print("success")
    #     # Error messages are already printed by the module
    #
    # @staticmethod
    # def handle_bluetooth_get_buffer():
    #     """Get bluetooth buffer contents and clear the buffer"""
    #     buffer_content = BluetoothModule.get_buffer()
    #     print(buffer_content)
    #
    # @staticmethod
    # def handle_classify(image_path: str):
    #     """Handle classification request"""
    #     result = ClassificationModule.classify(image_path)
    #     if result:
    #         print(json.dumps(result))
    #     else:
    #         print(json.dumps({"error": "Classification failed"}))
    #
    # @staticmethod
    # def handle_bluetooth_connect(mac_address: str = None):
    #     """Handle bluetooth connect command"""
    #     success = BluetoothModule.connect(mac_address)
    #     if success:
    #         print("success")
    #     # Error messages are already printed by the module
    #
    # @staticmethod
    # def handle_bluetooth_disconnect():
    #     """Handle bluetooth disconnect command"""
    #     success = BluetoothModule.disconnect()
    #     if success:
    #         print("success")
    #     # Error messages are already printed by the module

    # @staticmethod
    # def handle_classification_get_classes():
    #     """Handle classification get-classes command"""
    #     classes = ClassificationModule.get_classes()
    #     print(json.dumps(classes))

    @staticmethod
    def main_loop():
        # Check if the script is called with "start" argument
        if len(sys.argv) != 2 or sys.argv[1] != "start":
            print("Usage: python script.py start")
            sys.exit(1)

        print("ready")

        while True:
            try:
                # Get user input
                command = input().strip()

                if command.lower().strip() in ['exit', 'quit']:
                    break

                SmartBinEngine.process_command(command)

                # # # Handle exit commands
                # # if command.lower() in ['exit', 'quit']:
                # #     break
                #
                # # Handle stop command
                # elif command == 'stop':
                #     SmartBinEngine.stop()
                #
                # else:
                #     # Import split_command function
                #     from modules.utils import split_command
                #
                #     # Split the command
                #     command_parts = split_command(command)
                #
                #     if not command_parts:
                #         print("Error: Empty command")
                #         continue
                #
                #     # Get the main command (first part)
                #     main_command = command_parts[0]
                #     remaining_args = command_parts[1:]
                #
                #     # Dispatch to appropriate module
                #     if main_command == 'classify' or main_command == 'classification':
                #         ClassificationModule.handle_command(remaining_args)
                #     elif main_command == 'bluetooth':
                #         BluetoothModule.handle_command(remaining_args)
                #     else:
                #         print("Error: Unknown command")

            except KeyboardInterrupt:
                print()
                break
            except EOFError:
                break

        # Cleanup before exiting
        SmartBinEngine.stop()


if __name__ == "__main__":
    SmartBinEngine.main_loop()
