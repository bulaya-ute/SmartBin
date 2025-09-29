import 'dart:convert';

import 'package:flutter/cupertino.dart';
import 'package:smartbin_flutter/modules/base_module.dart';
import 'package:smartbin_flutter/modules/engine.dart';
import 'package:smartbin_flutter/modules/security.dart';

class Bluetooth extends BaseModule {
  static bool _isInitialized = false;
  static String? rfcommBinding;
  static String? serialPort;
  static String moduleName = "BLUETOOTH";
  static void Function()? disconnectCallback;

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

  static Future<bool> connect({
    String macAddress = "EC:E3:34:15:F2:62",
    String? sudoPassword,
  }) async {
    if (!isInitialized) {
      error("Cannot connect: Bluetooth module not initialized");
      return false;
    }

    print("Connecting to device at $macAddress...");

    // Send connect command to Python backend
    String? response = await Engine.sendCommand(
      "bluetooth connect --mac $macAddress --sudo ${Security.sudoPassword}",
      timeout: Duration(seconds: 15),
    );

    if (response == null) {
      print("Connection failed: No response from backend");
      return false;
    }

    response = response.trim();
    if (response.toLowerCase().startsWith("error")) {
      print(response);
      return false;
    } else if (response.toLowerCase().startsWith("success")) {
      print("Successfully connected to Bluetooth device");
      return true;
    } else {
      error("Unexpected message: $response");
      return false;
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
  static Future<List<String>?> readBuffer() async {
    String? response = await Engine.sendCommand(
      "bluetooth get buffer",
      source: moduleName,
    );
    if (response == null) return null;
    List<String> decodedList = jsonDecode(response);
    if (decodedList.isEmpty) return null;
    return decodedList;
  }

  static void print(String message) {
    debugPrint("[BLUETOOTH] $message");
  }

  static void error(String description, {bool throwError = true}) {
    debugPrint("[BLUETOOTH] ⚠️ $description");
    if (throwError) throw Exception(description);
  }

  static void setDisconnectCallback(void Function() callback) {
    disconnectCallback = callback;
  }

  static Future<bool> disconnect() async {
    print("Terminating connection...");
    Engine.sendCommand("bluetooth disconnect");
    disconnectCallback?.call();
    return true;
  }
}
