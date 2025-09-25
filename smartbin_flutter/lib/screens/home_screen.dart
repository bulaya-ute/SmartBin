import 'package:flutter/material.dart';
import 'dart:async';
import 'dart:convert';

import '../models/log_message.dart';
import '../widgets/bottom_controls.dart';
import '../widgets/message_section.dart';
import '../widgets/top_section.dart';
import '../widgets/custom_app_bar.dart';
import '../modules/bluetooth.dart';
import '../modules/engine.dart';
import '../modules/classification.dart';

enum ConnectionState {
  disconnected,
  connecting,
  connected,
}

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  late final TextEditingController _macCtl = TextEditingController(
    text: 'EC:E3:34:15:F2:62',
  );

  // Ratios for resizable panes
  double _topRatio = 0.6; // fraction of vertical space for top section
  double _leftRatio = 0.4; // fraction of top width for left image section

  // Minimum constraints and splitter thickness
  static const double _splitterThickness = 8;
  static const double _minTopHeight = 220;
  static const double _minMessageHeight = 180;

  // Minimum widths within top section (left/right)
  static const double _minLeftWidth = 200;
  static const double _minRightWidth = 280;

  ConnectionState _connectionState = ConnectionState.disconnected;
  bool autoscroll = true;
  bool autoReconnect = false;

  // Real data from backend
  List<String> _detectionClasses = [];
  Map<String, dynamic>? _classificationResult;
  Timer? _bufferReadTimer;

  final List<LogMessage> _messages = [];

  // Computed getters for connection state
  bool get isConnected => _connectionState == ConnectionState.connected;
  bool get isConnecting => _connectionState == ConnectionState.connecting;
  bool get isDisconnected => _connectionState == ConnectionState.disconnected;

  @override
  void initState() {
    super.initState();
    _initializeModules();
    _startBufferReading();
  }

  @override
  void dispose() {
    _macCtl.dispose();
    _bufferReadTimer?.cancel();
    super.dispose();
  }

  Future<void> _initializeModules() async {
    try {
      // Initialize engine first
      await Engine.init();

      // Initialize classification module
      await Classification.init();

      // Get available classes
      await _loadDetectionClasses();

    } catch (e) {
      _addLogMessage('Error initializing modules: $e', Colors.red);
    }
  }

  Future<void> _loadDetectionClasses() async {
    try {
      String? response = await Engine.sendCommand('classification get-classes');
      if (response != null) {
        // Parse JSON response
        final List<dynamic> classes = jsonDecode(response);
        setState(() {
          _detectionClasses = classes.cast<String>();
        });
        _addLogMessage('Loaded ${_detectionClasses.length} detection classes', Colors.blue);
      }
    } catch (e) {
      _addLogMessage('Error loading detection classes: $e', Colors.red);
    }
  }

  void _startBufferReading() {
    _bufferReadTimer = Timer.periodic(Duration(milliseconds: 500), (timer) async {
      if (isConnected) {
        try {
          String? buffer = await Bluetooth.readBuffer();
          if (buffer != null && buffer.isNotEmpty) {
            // Split multiple messages
            final messages = buffer.split('\n').where((msg) => msg.trim().isNotEmpty);
            for (String message in messages) {
              _processReceivedMessage(message.trim());
            }
          }
        } catch (e) {
          // Silently handle buffer read errors to avoid spam
        }
      }
    });
  }

  void _processReceivedMessage(String message) {
    Color messageColor = Colors.grey;

    // Format PA/PX messages in yellow
    if (message.startsWith('PA') || message.startsWith('PX')) {
      messageColor = Colors.yellow;
      _addLogMessage('← $message', messageColor);
    } else if (message.startsWith('ERROR:')) {
      messageColor = Colors.red;
      _addLogMessage('← $message', messageColor);
    } else if (message.startsWith('IMAGE_RECEIVED:')) {
      messageColor = Colors.green;
      _addLogMessage('← Image received from ESP32', messageColor);
      // Extract image path and potentially trigger classification
      final imagePath = message.substring('IMAGE_RECEIVED:'.length).trim();
      _triggerClassification(imagePath);
    } else {
      _addLogMessage('← $message', messageColor);
    }
  }

  Future<void> _triggerClassification(String imagePath) async {
    try {
      _addLogMessage('→ Classifying image: $imagePath', Colors.blue);
      String? response = await Engine.sendCommand('classify $imagePath');
      if (response != null) {
        final result = jsonDecode(response);
        setState(() {
          _classificationResult = result;
        });

        // Find the class with highest confidence
        if (result is Map<String, dynamic>) {
          String topClass = '';
          double maxConfidence = 0.0;

          result.forEach((className, confidence) {
            if (confidence is num && confidence > maxConfidence) {
              maxConfidence = confidence.toDouble();
              topClass = className;
            }
          });

          _addLogMessage('← Classification: $topClass (${(maxConfidence * 100).toStringAsFixed(1)}%)', Colors.green);
        }
      }
    } catch (e) {
      _addLogMessage('Error during classification: $e', Colors.red);
    }
  }

  void _addLogMessage(String text, [Color? color]) {
    if (mounted) {
      setState(() {
        _messages.add(LogMessage(
          text: '[${DateTime.now().toString().substring(11, 19)}] $text',
          color: color,
        ));
      });
    }
  }

  Future<void> _toggleConnection() async {
    if (isConnected) {
      // Disconnect
      try {
        setState(() {
          _connectionState = ConnectionState.disconnected;
        });
        await Engine.sendCommand('bluetooth disconnect');
        _addLogMessage('Disconnected from SmartBin', Colors.orange);
      } catch (e) {
        _addLogMessage('Error disconnecting: $e', Colors.red);
        setState(() {
          _connectionState = ConnectionState.disconnected;
        });
      }
    } else if (isDisconnected) {
      // Connect
      try {
        setState(() {
          _connectionState = ConnectionState.connecting;
        });
        _addLogMessage('→ Connecting to SmartBin...', Colors.blue);
        await Bluetooth.connect(macAddress: _macCtl.text);
        setState(() {
          _connectionState = ConnectionState.connected;
        });
        _addLogMessage('← Device connected successfully', Colors.green);
      } catch (e) {
        _addLogMessage('Connection failed: $e', Colors.red);
        setState(() {
          _connectionState = ConnectionState.disconnected;
        });
      }
    }
    // If connecting, do nothing (button should be disabled)
  }

  Future<void> _sendCommand(String command) async {
    try {
      _addLogMessage('→ $command', Colors.green);

      if (command.toLowerCase().startsWith('bluetooth send')) {
        // Extract message part and use transmitMessage
        final message = command.substring('bluetooth send'.length).trim();
        await Bluetooth.transmitMessage(message: message);
      } else {
        // Send other commands directly to engine
        String? response = await Engine.sendCommand(command);
        if (response != null && response.isNotEmpty) {
          _addLogMessage('← $response', Colors.grey);
        }
      }
    } catch (e) {
      _addLogMessage('Error sending command: $e', Colors.red);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: CustomAppBar(
        connectionState: _connectionState,
        onConnectionTap: _toggleConnection,
      ),
      bottomNavigationBar: BottomControls(
        connectionState: _connectionState,
        onToggleConnect: _toggleConnection,
        autoReconnect: autoReconnect,
        onToggleAutoReconnect: (v) => setState(() => autoReconnect = v),
        macController: _macCtl,
        onSendCommand: _sendCommand,
      ),
      body: LayoutBuilder(
        builder: (context, constraints) {
          final totalHeight = constraints.maxHeight;

          // Compute top height from ratio and clamp to min constraints
          final availableForPanels = totalHeight - _splitterThickness;
          final minTopRatio = _minTopHeight / availableForPanels;
          final maxTopRatio = 1 - (_minMessageHeight / availableForPanels);
          final clampedTopRatio = _topRatio.clamp(minTopRatio, maxTopRatio);
          if (clampedTopRatio != _topRatio) {
            // Keep ratio valid under extreme window sizes
            _topRatio = clampedTopRatio.toDouble();
          }
          final topHeight = availableForPanels * _topRatio;

          return Padding(
            padding: const EdgeInsets.all(8.0),
            child: Column(
              children: [
                // Top section with internal vertical splitter
                SizedBox(
                  height: topHeight,
                  child: TopSection(
                    leftRatio: _leftRatio,
                    minLeftWidth: _minLeftWidth,
                    minRightWidth: _minRightWidth,
                    splitterThickness: _splitterThickness,
                    onLeftRatioChanged: (r) => setState(() => _leftRatio = r),
                    // Pass real data to TopSection
                    detectionClasses: _detectionClasses,
                    classificationResult: _classificationResult,
                    connectionState: _connectionState,
                  ),
                ),

                // Horizontal splitter handle
                SizedBox(
                  height: _splitterThickness,
                  child: MouseRegion(
                    cursor: SystemMouseCursors.resizeRow,
                    child: GestureDetector(
                      behavior: HitTestBehavior.opaque,
                      onVerticalDragUpdate: (details) {
                        final newTopHeight = (topHeight + details.delta.dy)
                            .clamp(
                              _minTopHeight,
                              availableForPanels - _minMessageHeight,
                            );
                        final newRatio = newTopHeight / availableForPanels;
                        setState(() => _topRatio = newRatio);
                      },
                      child: Container(
                        margin: const EdgeInsets.symmetric(horizontal: 10),
                        decoration: BoxDecoration(
                          color: const Color(0xFFE0E0E0),
                          borderRadius: BorderRadius.circular(4),
                        ),
                        child: Center(
                          child: Container(
                            width: 40,
                            height: 3,
                            decoration: BoxDecoration(
                              color: const Color(0xFF666666),
                              borderRadius: BorderRadius.circular(2),
                            ),
                          ),
                        ),
                      ),
                    ),
                  ),
                ),

                // Message section takes remaining space
                Expanded(
                  child: MessageSection(
                    messages: _messages,
                    autoscroll: autoscroll,
                    onToggleAutoscroll: (v) => setState(() {
                      autoscroll = v ?? false;
                    }),
                    onClear: () => setState(() => _messages.clear()),
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}
