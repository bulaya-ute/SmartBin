import 'package:flutter/cupertino.dart';
import 'package:smartbin_flutter/modules/base_module.dart';

class Config extends BaseModule {
  static String moduleName = "CONFIG";
  static bool isInitialized = false;

  static String? sudoPasswordEncrypt;

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

  // static void print(String message) {
  //   debugPrint("[CONFIG] $message");
  // }

}