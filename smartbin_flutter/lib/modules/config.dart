import 'package:flutter/cupertino.dart';
import 'package:smartbin_flutter/modules/base_module.dart';

class Config extends BaseModule {
  static String moduleName = "CONFIG";
  static bool isInitialized = false;

  static String? sudoPassword;

  /// Initialization
  static Future<void> init() async {
    if (isInitialized) {
      print("Initialization cancelled. Config module already initialized.");
      return;
    }
    print("Loading configurations...");
    // TODO: Put init logic here
    print("Configurations loaded.");
  }

  static void print(String message) {
    debugPrint("[CONFIG] $message");
  }

}