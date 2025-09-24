import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter/cupertino.dart';


/// Responsible for communication with python backend, which is used for
/// running classification model and bluetooth communication
class Engine {
  static bool _isInitialized = false;
  static String outputBuffer = "";
  static Process? process;
  static String classifierScript = "lib/scripts/classifier.py";

  bool get isInitialized {
    if (!_isInitialized) {
      return false;
    }
    return true;
  }

  set isInitialized(bool value) {
    _isInitialized = value;
  }

  Future<void> init() async {
    process = await Process.start('python', [classifierScript, "start"]);

    String? response = await waitForResponse(Duration(seconds: 30));
    print("Response: $response");
    if (response?.toLowerCase() == "ready") {
      isInitialized = true;
      print("Initialization complete");
    } else {
      isInitialized = false;
    }

  }


  /// Waits for a non-empty response from the Python process within the specified timeout.
  static Future<String?> waitForResponse(Duration timeout) async {
    final completer = Completer<String?>();
    late StreamSubscription subscription;
    late Timer timeoutTimer;

    subscription = process!.stdout.transform(utf8.decoder).listen((data) {
      final trimmed = data.trim();
      if (trimmed.isNotEmpty) {
        subscription.cancel();
        timeoutTimer.cancel();
        completer.complete(trimmed);
      }
    });
    timeoutTimer = Timer(timeout, () {
      subscription.cancel();
      completer.complete(null);
    });

    return await completer.future;
  }


    static Future<String?> sendCommand(String command, Duration timeout) async {
    if (!isInitialized || process == null) {
      print("Error: Not initialized. Call start() first.");
      return null;
    }

    try {
      // Send the command
      process!.stdin.writeln(command);

      // Wait for any non-empty response within the timeout
      return await waitForResponse(timeout);
    } catch (e) {
      print("Error sending command '$command': $e");
      return null;
    }
  }


  static void print(String message) {
    debugPrint("[ENGINE] $message");
  }

}