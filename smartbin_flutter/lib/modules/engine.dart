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

  // Stream management
  static StreamSubscription? _stdoutSubscription;
  static StreamController<String>? _responseController;
  static Stream<String>? _responseStream;

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
      return;
    }

    print("Starting engine");
    try {
      process = await Process.start('python', [engineScript, "start"]);

      // Set up single persistent stream listener
      _setupStreamListener();

      String? response = await waitForResponse(Duration(seconds: 30));
      if (response?.toLowerCase() == "ready") {
        isInitialized = true;
        print("Initialization success");
      } else {
        isInitialized = false;
        print(
          "Error: Initialization failed. Ready status not received from backend",
        );
        await _cleanup();
      }
    } catch (e) {
      print("Error during initialization: $e");
      isInitialized = false;
      await _cleanup();
    }
  }

  /// Set up a single persistent listener that broadcasts to multiple waiters
  static void _setupStreamListener() {
    _responseController = StreamController<String>.broadcast();
    _responseStream = _responseController!.stream;

    _stdoutSubscription = process!.stdout
        .transform(utf8.decoder)
        .transform(LineSplitter())
        .listen(
          (line) {
            final trimmed = line.trim();
            if (trimmed.isNotEmpty) {
              _responseController!.add(trimmed);
            }
          },
          onError: (error) {
            print("Stream error: $error");
            _responseController!.addError(error);
          },
          onDone: () {
            print("Python process stdout closed");
            _responseController!.close();
          },
        );
  }

  /// Waits for a non-empty response from the Python process within the specified timeout.
  static Future<String?> waitForResponse(Duration timeout) async {
    if (_responseStream == null) {
      print("Error: Response stream not available");
      return null;
    }

    try {
      final response = await _responseStream!.first.timeout(timeout);
      print("← $response");
      return response;
    } on TimeoutException {
      print("Timeout waiting for response after ${timeout.inSeconds} seconds");
      return null;
    } catch (e) {
      print("Error waiting for response: $e");
      return null;
    }
  }

  /// Send a command to the engine
  static Future<String?> sendCommand(
    String command, {
    Duration timeout = const Duration(seconds: 5),
  }) async {
    if (!isInitialized) {
      print("Error: Engine not initialized.");
      return null;
    }

    try {
      // Send the command
      process!.stdin.writeln(command);
      await process!.stdin.flush();

      print("→ $command");

      // Wait for response
      return await waitForResponse(timeout);
    } catch (e) {
      print("Error sending command '$command': $e");
      return null;
    }
  }

  /// Clean up resources
  static Future<void> _cleanup() async {
    await _stdoutSubscription?.cancel();
    await _responseController?.close();
    _stdoutSubscription = null;
    _responseController = null;
    _responseStream = null;

    try {
      process?.kill();
    } catch (e) {
      print("Error killing process: $e");
    }
    process = null;
  }

  /// Stop the engine and clean up
  static Future<void> stop() async {
    if (isInitialized) {
      try {
        await sendCommand("stop", timeout: Duration(seconds: 2));
      } catch (e) {
        print("Error sending stop command: $e");
      }
    }

    await _cleanup();
    isInitialized = false;
    print("Engine stopped and cleaned up");
  }

  static void print(String message) {
    // Regex matches --sudo <password> or --sudo=<password>
    final sudoRegex = RegExp(r'(--sudo(?:=|\s+))([^\s]+)');
    final obscured = message.replaceAllMapped(
      sudoRegex,
      (match) => '${match[1]}${'*' * match[2]!.length}',
    );
    debugPrint("[ENGINE] $obscured");
  }
}
