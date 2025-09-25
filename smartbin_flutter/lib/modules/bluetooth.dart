import 'package:flutter/cupertino.dart';
import 'package:smartbin_flutter/modules/base_module.dart';
import 'package:smartbin_flutter/modules/engine.dart';

class Bluetooth extends BaseModule {
  static bool _isInitialized = false;
  static String? sudoPassword;
  static String? rfcommBinding;

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

  static Future<void> connect({String macAddress = "EC:E3:34:15:F2:62"}) async {
    if (!isInitialized) {
      error("Cannot connect: Bluetooth module not initialized");
      return;
    }

    print("Connecting to device at $macAddress...");

    try {
      // Send connect command to Python backend
      String? connectResponse = await Engine.sendCommand(
        "bluetooth connect $macAddress",
        timeout: Duration(seconds: 15),
      );

      if (connectResponse == null) {
        error("Connection failed: No response from backend");
        return;
      }
      print("Connected response $connectResponse");

      // Check for connection progress messages
      if (connectResponse.toLowerCase().contains("connecting to esp32")) {
        print("Backend is attempting connection...");

        // Wait for additional responses about RFCOMM binding
        String? rfcommResponse = await Engine.sendCommand(
          "bluetooth connect ",
          timeout: Duration(seconds: 10),
        );
        if (rfcommResponse != null &&
            rfcommResponse.toLowerCase().startsWith("info: rfcomm bound to")) {
          rfcommBinding = rfcommResponse
              .substring("info: rfcomm bound to ".length)
              .trim();
          print("RFCOMM bound to $rfcommBinding");
        }

        // Wait for final success message
        String? finalResponse = await Engine.waitForResponse(
          Duration(seconds: 10),
        );
        if (finalResponse != null &&
            finalResponse.toLowerCase().contains("successfully connected")) {
          print("Successfully connected to ESP32");

          // Wait for the "success" confirmation
          String? successResponse = await Engine.waitForResponse(
            Duration(seconds: 5),
          );
          if (successResponse?.toLowerCase().trim() == "success") {
            print("Connection established successfully");
          }
        } else {
          error(
            "Connection failed: Expected success confirmation not received. Got: $finalResponse",
          );
        }
      } else if (connectResponse.toLowerCase().contains("already connected")) {
        print("Already connected.");
      } else if (connectResponse.toLowerCase().startsWith("error:")) {
        error("Connection failed: $connectResponse");
      } else if (connectResponse.toLowerCase().trim() == "success") {
        print("Connection established successfully");
      } else {
        error("Unexpected connection response: $connectResponse");
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
