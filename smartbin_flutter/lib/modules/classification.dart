import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter/cupertino.dart';
import 'package:smartbin_flutter/modules/engine.dart';

class Classification {
  static bool isInitialized = false;

  /// Initialize the module
  static Future<void> init() async {
    if (isInitialized) {
      print(
        "Initialization cancelled. Classification module already initialized.",
      );
      return;
    }
    print("Initializing classification...");
    String? response = await Engine.sendCommand("classify init", timeout: Duration(seconds: 30));
    // print("DEBUG $response");
    if (response == null) {
      error("Initialization failed. Null message received");
    } else if (response.toLowerCase() == "success") {
      print("Module initialized successfully.");
    }  else {
      print(
        "Error initializing classification module. Success message not received. Got: $response",
      );
      throw Exception(
        "Error initializing classification module. Success message not received",
      );
    }
  }

  static Future<Object?> classify(String imagePath) async {
    if (!isInitialized) {
      print("Error: Not initialized");
    }
    String? response = await Engine.sendCommand(
      "classify $imagePath",
      timeout: Duration(seconds: 5),
    );
    if (response == null) {
      return response;
    }
    return json.decode(response) as Map<String, dynamic>;
  }

  static void print(String message) {
    debugPrint("[CLASSIFICATION] $message");
  }

  static void error(String description, {bool throwError = true}) {
    debugPrint("[CLASSIFICATION ⚠️] $description");
    if (throwError) throw Exception(description);
  }
}
