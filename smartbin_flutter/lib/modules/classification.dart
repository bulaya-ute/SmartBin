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
      print("Initialization cancelled. Classification module already initialized.");
      return;
    }
    print("Initializing module...");
    String? response = await Engine.sendCommand("classification init");
    if (response?.toLowerCase() != "success") {
      print("Module initialized successfully.");
    }

  }

  static Future<Object?> classify(String imagePath) async {
    // if (!isInitialized) {
    //   print("Error: Not initialized");
    // }
    // String? response = await sendCommand("classify $imagePath", Duration(seconds: 5));
    // if (response == null) {
    //   return response;
    // }
    // return json.decode(response) as Map<String, dynamic>;
  }

  static void print(String message) {
    debugPrint("[CLASSIFICATION] $message");
  }
}