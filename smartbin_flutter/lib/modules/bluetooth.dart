import 'package:flutter/cupertino.dart';
import 'package:smartbin_flutter/modules/base_module.dart';
import 'package:smartbin_flutter/modules/engine.dart';
import 'package:smartbin_flutter/modules/security.dart';

class Bluetooth extends BaseModule {
  static bool _isInitialized = false;
  static String? rfcommBinding;
  static String? serialPort;

  static bool get isInitialized {
    if (!_isInitialized) {
      return false;
    }
    return true;
  }

  static set isInitialized(bool value) {
    _isInitialized = value;
  }

  /// Initialization method. Sends bluetooth init command to backend
  static Future<void> init() async {
    if (isInitialized) {
      print("Initialization cancelled. Module is already initialized");
      return;
    }

    print("Initializing bluetooth...");

    // Construct command with password if provided
    String command = "bluetooth init";

    String? successResponse = await Engine.sendCommand(command);
    if (successResponse == null) {
      error("Initialization failed. Null success message received");
    } else if (successResponse.toLowerCase().trim().startsWith("success")) {
      isInitialized = true;
      print("Initialization complete.");
    } else {
      throw Exception(
        "Initialization failed. Success message not received. Got: $successResponse",
      );
    }
  }

  static Future<void> connect({
    String macAddress = "EC:E3:34:15:F2:62",
    String? sudoPassword,
  }) async {
    if (!isInitialized) {
      error("Cannot connect: Bluetooth module not initialized");
      return;
    }

    print("Connecting to device at $macAddress...");

    try {
      // Send connect command to Python backend
      String? response = await Engine.sendCommand(
        "bluetooth connect --mac $macAddress --sudo ${Security.sudoPassword}",
        timeout: Duration(seconds: 15),
      );

      if (response == null) {
        error("Connection failed: No response from backend");
        return;
      }

      // Check for connection progress messages
      if (response.toLowerCase().contains("connecting to esp32")) {
        print("Backend is attempting connection...");

        // Update the response
        response = await Engine.waitForResponse(Duration(seconds: 10));
        if (response == null) {
          error("Error: Timeout waiting for response");
          return;
        }

        // Handle message for opening serial port
        if (response.toLowerCase().contains("opening serial")) {
          serialPort = response.substring(15, response.length + 1);
          print("Opening serial: $serialPort");
          response = await Engine.waitForResponse(Duration(seconds: 15));
        }

        // Update the response
        response = await Engine.waitForResponse(Duration(seconds: 10));
        if (response == null) {
          error("Error: Could not open serial to $serialPort");
          return;
        }

        // Wait for additional responses about RFCOMM binding
        rfcommBinding = response
            .substring("info: rfcomm bound to ".length)
            .trim();
        print("RFCOMM bound to $rfcommBinding");

        // Update the response
        response = await Engine.waitForResponse(Duration(seconds: 10));
        if (response == null) {
          error("Error: Error trying to get config");
          return;
        }

        // Get configuration information
        if (response.toLowerCase().contains("serial connection established")) {
          String? configData1 = await Engine.waitForResponse();
          String? configData2 = await Engine.waitForResponse();
          print("Successfully connected to ESP32");

        }

        // // Wait for final success message
        // // String? response = await Engine.waitForResponse(
        // //   Duration(seconds: 10),
        // // );
        // if (response.toLowerCase().contains("successfully connected")) {
        //   print("Successfully connected to ESP32");
        //
        //   // Wait for the "success" confirmation
        //   String? successResponse = await Engine.waitForResponse(
        //     Duration(seconds: 5),
        //   );
        //   if (successResponse?.toLowerCase().trim() == "success") {
        //     print("Connection established successfully");
        //   }
        // } else {
        //   error(
        //     "Connection failed: Expected success confirmation not received. Got: $response",
        //   );
        // }

      } else if (response.toLowerCase().contains("already connected")) {
        print("Already connected.");
      } else if (response.toLowerCase().startsWith("error:")) {
        error("Connection failed: $response");
      } else if (response.toLowerCase().trim() == "success") {
        print("Connection established successfully");
      } else {
        error("Unexpected connection response: $response");
      }
    } catch (e) {
      error("Connection failed with exception: $e");
    }
  }

  /// Transmit message over bluetooth
  static Future<void> transmitMessage({
    String? message,
    String? protocolCode,
  }) async {
    String constructedMessage = "";
    if (protocolCode != null && protocolCode.isNotEmpty) {
      constructedMessage += protocolCode;
    }
    if (message != null && message.isNotEmpty) {
      constructedMessage += " $message";
    }
    if (constructedMessage.trim().isEmpty) {
      print("Dropping blank message");
      return;
    }
    Engine.sendCommand("bluetooth send $constructedMessage");
  }

  /// Read bluetooth buffer
  static Future<String?> readBuffer() async {
    String? response = await Engine.sendCommand("bluetooth get buffer");
    return response;
  }

  static void print(String message) {
    debugPrint("[BLUETOOTH] $message");
  }

  static void error(String description, {bool throwError = true}) {
    debugPrint("[BLUETOOTH ⚠️] $description");
    if (throwError) throw Exception(description);
  }
}
