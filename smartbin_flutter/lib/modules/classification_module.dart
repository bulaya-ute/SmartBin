import 'dart:io';
import 'package:flutter/cupertino.dart';



class Classification {
  static bool isInitialized = false;
  static String outputBuffer = "";
  static Process? process;

  static Future<void> init() async {
    process = await Process.start('python ../', []);
    debugPrint("Initializing classification module");
  }

  static Future<void> init() async {

  }
}