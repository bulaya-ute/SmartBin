import 'dart:convert';
import 'dart:io';

import 'package:flutter/cupertino.dart';
import 'package:smartbin_flutter/modules/base_module.dart';
import 'package:path/path.dart' as Path;
import 'package:flutter/services.dart' show rootBundle;

class Config extends BaseModule {
  static String moduleName = "CONFIG";
  static bool isInitialized = false;
  static String? sudoPassword;
  static Map<String, dynamic>? config;
  static String workingDir = Path.join(
    File(Platform.script.toFilePath()).parent.path,
    "lib",
    "scripts",
  );
  static String pythonExecutablePath = Path.join(workingDir, ".venv/bin/python");
  static String engineScriptPath = Path.join(workingDir, "engine.py");
  static String configFile = Path.join(workingDir, "config.json");

  /// Initialization
  static Future<void> init() async {
    if (isInitialized) {
      print("Initialization cancelled. Config module already initialized.");
      return;
    }
    print("Loading configurations...");
    loadConfig();
    print("Configurations loaded.");
  }

  static void print(String message) {
    debugPrint("[CONFIG] $message");
  }

  /// Load all the contents of the configuration json file into memory
  static Future<void> loadConfig() async {
    String jsonString = await rootBundle.loadString(configFile);
    config = jsonDecode(jsonString);
  }

  static Map<String, int> loadDetectionCounts()  {
    final detectionCounts = config!["detectionCounts"];
    return detectionCounts;
  }

  static void saveDetectionCounts() {

  }

}