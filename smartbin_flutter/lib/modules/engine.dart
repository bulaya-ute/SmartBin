import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter/cupertino.dart';

/// Responsible for communication with python backend, which is used for
/// running classification model and bluetooth communication
class Engine {
  static bool _isInitialized = false;
  static Process? process;
  static String engineScript = "lib/scripts/engine.py";

  static bool get isInitialized {
    if (!_isInitialized) {
      return false;
    } else if (process == null) {
      return false;
    }
    return true;
  }

  static set isInitialized(bool value) {
    _isInitialized = value;
  }

  /// Initialization method. Establishes communication with the python API
  static Future<void> init() async {
    if (isInitialized) {
      print("Initialization cancelled. Module is already initialized");
    }
    
    process = await Process.start('python', [engineScript, "start"]);

    String? response = await waitForResponse(Duration(seconds: 30));
    print("Response: $response");
    if (response?.toLowerCase() == "ready") {
      isInitialized = true;
      print("Initialization success");
    } else {
      isInitialized = false;
      print("Error: Initialization failed. Ready status not received from backend");
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

  /// Send a command to the engine
  static Future<String?> sendCommand(String command, {Duration timeout = const Duration(seconds: 2)}) async {
    if (!isInitialized) { // Fixed: should be !isInitialized
      print("Error: Engine not initialized.");
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
