import 'package:flutter/cupertino.dart';

abstract class BaseModule {
  static String moduleName = "UNIMPLEMENTED-MODULE";
  static bool _isInitialized = false;

  static bool get isInitialized {

    if (!_isInitialized || moduleName.toUpperCase() == "UNIMPLEMENTED-MODULE") {
      return false;
    }
    return true;
  }

  static set isInitialized(bool value) {
    _isInitialized = value;
  }

  /// Initialization method. Sends bluetooth init command to backend
  static Future<void> init() async {
    throw Exception("Initialization method not implemented");
  }



  static void print(String message) {
    debugPrint("[$moduleName] $message");
  }


  static void error(String description, {bool throwError = true}) {
    debugPrint("[$moduleName ⚠️] $description");
    if (throwError) throw Exception(description);
  }

}