import 'package:flutter/cupertino.dart';

class Config {
  static bool isInitialized = false;

  /// Initialization
  static Future<void> init() async {
    if (isInitialized) {
      print("Initialization cancelled. Config module already initialized.");
      return;
    }
    print("Initializing module...");
    // TODO: Put init logic here
    print("Initialization successful.");
  }

  static void print(String message) {
    debugPrint("[CONFIG] $message");
  }

}