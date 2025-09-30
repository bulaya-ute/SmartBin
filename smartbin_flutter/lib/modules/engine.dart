import 'dart:async';
import 'dart:collection';
import 'dart:convert';
import 'dart:io';
import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:path/path.dart' as Path;

import 'config.dart';

/// Responsible for communication with python backend, which is used for
/// running classification model and bluetooth communication
class Engine {
  static bool _isInitialized = false;
  static Process? process;

  // Stream management
  static StreamSubscription? _stdoutSubscription;
  static StreamController<String>? _responseController;
  static Stream<String>? _responseStream;
  static final Queue<String> _lineBuffer = Queue<String>();
  static String moduleName = "ENGINE";

  // Callback for log messages
  static void Function(String message, {Color? messageColor})? _logCallback;

  /// Set the log callback function to receive Engine.print() messages
  static void setLogCallback(
    void Function(String message, {Color? messageColor})? callback,
  ) {
    _logCallback = callback;
  }

  /// Initialization method. Establishes communication with the python API
  static Future<void> init() async {
    if (isInitialized) {
      print("Initialization cancelled. Module is already initialized");
      return;
    }

    print(
      "Starting engine... Working dir: $Config.workingDir \n"
      "Python executable: $Config.pythonExecutablePath \n"
      "Python script: $Config.engineScriptPath",
    );
    try {
      process = await Process.start(Config.pythonExecutablePath, [
        Config.engineScriptPath,
        "start",
      ], workingDirectory: Config.workingDir);

      // Set up single persistent stream listener
      _setupStreamListener();

      String? response = await waitForResponse(Duration(seconds: 30));
      if (response?.toLowerCase() == "ready") {
        isInitialized = true;
        print("Initialization success");
      } else {
        isInitialized = false;
        await _cleanup();
        throw Exception(
          "Error: Initialization failed. Ready status not received from backend",
        );
      }
    } catch (e) {
      error("Engine initialization failed: $e");
      isInitialized = false;
      await _cleanup();
    }
  }

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

  // Modify _setupStreamListener to add lines to the buffer
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
              _lineBuffer.add(trimmed); // Buffer the line
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

  static Future<String?> waitForResponse([
    Duration timeout = const Duration(seconds: 2),
  ]) async {
    final start = DateTime.now();
    while (_lineBuffer.isEmpty) {
      final elapsed = DateTime.now().difference(start);
      if (elapsed >= timeout) {
        return null;
      }
      // Sleep briefly to avoid busy-waiting
      await Future.delayed(const Duration(milliseconds: 10));
    }
    String line = _lineBuffer.removeFirst();
    print("← $line");
    return line;
  }

  /// Send a command to the engine
  static Future<String?> sendCommand(
    String command, {
    String? source,
    Duration timeout = const Duration(seconds: 5),
  }) async {
    if (!isInitialized) {
      print("Error: Engine not initialized.", source: source);
      return null;
    }

    try {
      // Send the command
      process!.stdin.writeln(command);
      await process!.stdin.flush();

      print("→ $command", source: source);

      // Wait for response
      return await waitForResponse(timeout);
    } catch (e) {
      print("Error sending command '$command': $e", source: source);
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

  static void print(
    String message, {
    bool hideBufferRequests = true,
    String? source,
  }) {
    source = source ?? moduleName;

    // Regex matches --sudo <password> or --sudo=<password>
    final sudoRegex = RegExp(r'(--sudo(?:=|\s+))([^\s]+)');
    final obscured = message.replaceAllMapped(
      sudoRegex,
      (match) => '${match[1]}${'*' * match[2]!.length}',
    );
    debugPrint("[$source] $obscured");

    if (hideBufferRequests) {
      if (message.contains("bluetooth get buffer") ||
          message.trim() == "← []") {
        return;
      }
    }
    // debugPrint(" --- '$obscured'");
    // Call the log callback if set, using blue color for engine messages
    _logCallback?.call("[$source] $obscured");
  }

  // Raise an error
  static void error(
    String description, {
    bool throwError = true,
    String? source,
  }) {
    source = source ?? moduleName;

    debugPrint("[$source] ⚠️ $description");

    // Call the log callback if set, using red color for error messages
    _logCallback?.call("[$source] ⚠️ $description");

    if (throwError) throw Exception(description);
  }
}
