import 'package:flutter/cupertino.dart';
import 'package:smartbin_flutter/modules/engine.dart';

class Bluetooth {
  static bool _isInitialized = false;

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
    }

    String? response = await Engine.sendCommand("bluetooth init", timeout: Duration(seconds: 10));
    if (response?.toLowerCase() == "success") {
      print("Error: Initialization failed. Success message not received");
    }
  }

  /// Transmit message over bluetooth
  static Future<void> transmitMessage({String? message, String? protocolCode = null}) async {
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

}
