import 'dart:convert';
import 'dart:io';

import 'package:flutter/cupertino.dart';
import 'package:smartbin_flutter/modules/base_module.dart';
import 'package:path/path.dart' as Path;
import 'package:flutter/services.dart' show rootBundle;

class Config extends BaseModule {
  // Callback for log messages
  static void Function(String message, {Color? messageColor})? _logCallback;

  // Config defaults
  static Map<String, dynamic> configDefaults = {
    "theme": "system",
    "layout": {
      "topRatio": 0.6,
      "leftRatio": 0.5
    },
    "detectionCounts": {
      "aluminium": 0, "carton": 0, "e_waste": 0,
      "glass": 0, "organic_waste": 0, "paper_and_cardboard": 0,
      "plastic": 0, "textile": 0, "wood": 0
    },

    // Support for a list of saved devices to be added in a future update
    "deviceList": [
      {
        "macAddress": "EC:E3:34:15:F2:62",
        "name": "ESP32-Cam",
      }
    ]
  };

  static String moduleName = "CONFIG";
  static bool isInitialized = false;
  static String? sudoPassword;
  static Map<String, dynamic>? config;
  static String workingDir = Path.join(
    File(Platform.script.toFilePath()).parent.path,
    "lib",
    "scripts",
  );
  static String pythonExecutablePath = Path.join(
    workingDir,
    ".venv/bin/python",
  );
  static String engineScriptPath = Path.join(workingDir, "engine.py");
  static String configFile = Path.join(workingDir, "config.json");

  /// Initialization
  static Future<void> init() async {
    if (isInitialized) {
      print("Initialization cancelled. Config module already initialized.");
      return;
    }
    print("Loading configurations...");

    try {
      // First check that the config file exists.
      // Create the file if it is missing, populated with defaults
      // <insert logic here>

      // Next, verify that the config file contains the desired keys
      // by comparing with the defaults as a template
      // <insert logic here>

      // Finally, load the config from the file
      loadConfig();
    } catch (e) {
      error("Error loading config: $e");
    }
    print("Configurations loaded.");
    isInitialized = true;
  }

  static void print(String message) {
    debugPrint("[CONFIG] $message");
  }

  // Raise an error
  static void error(String description, {bool throwError = true}) {
    debugPrint("[$moduleName] ⚠️ $description");

    // Call the log callback if set, using red color for error messages
    _logCallback?.call("[$moduleName] ⚠️ $description");

    if (throwError) throw Exception(description);
  }

  /// Load all the contents of the configuration json file into memory
  static Future<void> loadConfig() async {
    String jsonString = await rootBundle.loadString(configFile);
    config = jsonDecode(jsonString);
  }

  static Map<String, int> loadDetectionCounts() {
    final detectionCounts = config!["detectionCounts"];
    return detectionCounts;
  }

  static void saveDetectionCounts() {}
}
