import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:smartbin_flutter/themes.dart';
import 'package:smartbin_flutter/widgets/top_section.dart';
import 'package:smartbin_flutter/widgets/message_section.dart';
import 'package:smartbin_flutter/widgets/bottom_controls.dart';
import 'package:smartbin_flutter/models/log_message.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'SmartBin Control',
      theme: appLightTheme,
      // Set the light theme as the default
      darkTheme: appDarkTheme,
      // Set the dark theme
      themeMode: ThemeMode.system,
      home: const SmartBinHomePage(),
      debugShowCheckedModeBanner: false,
    );
  }
}

class SmartBinHomePage extends StatefulWidget {
  const SmartBinHomePage({super.key});

  @override
  State<SmartBinHomePage> createState() => _SmartBinHomePageState();
}

class _SmartBinHomePageState extends State<SmartBinHomePage> {
  late final TextEditingController _macCtl = TextEditingController(
    text: 'EC:E3:34:15:F2:62',
  );

  // Initial sizes based on mockup
  double _leftPaneWidth = 300; // image section
  double _midPaneWidth = 0; // image section

  // Minimum/maximum constraints
  double _topSectionHeight = 400; // resizable top height
  static const double _minPaneWidth = 200;
  static const double _minRightPaneWidth = 280;
  static const double _splitterThickness = 8;
  static const double _minTopHeight = 220;
  static const double _minMessageHeight = 180;

  bool _connected = false;
  bool autoscroll = true;
  bool autoReconnect = true;

  // Messages list as objects with color and text
  final List<LogMessage> _messages = [
    const LogMessage(text: '[14:23:45] → Connecting to SmartBin...'),
    const LogMessage(text: '[14:23:47] ← Device connected successfully'),
    const LogMessage(text: '[14:24:02] ← Image captured: 1024x768'),
    const LogMessage(text: '[14:24:03] ← Classification: plastic (94.2%)'),
    const LogMessage(text: '[14:24:04] → Opening plastic bin...'),
    const LogMessage(text: '[14:24:05] ← Bin opened successfully'),
  ];

  @override
  void dispose() {
    _macCtl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('📱 SmartBin Control'),
        backgroundColor: Colors.blue,
        foregroundColor: Colors.white,
        elevation: 2,
      ),
      bottomNavigationBar: BottomControls(
        connected: _connected,
        onToggleConnect: () => setState(() => _connected = !_connected),
        autoReconnect: autoReconnect,
        onToggleAutoReconnect: (v) => setState(() => autoReconnect = v),
        macController: _macCtl,
        onSendCommand: (cmd) {
          // Placeholder: append to log for now
          setState(() {
            _messages.add(LogMessage(text: '→ $cmd', color: Colors.green));
          });
        },
      ),
      body: LayoutBuilder(
        builder: (context, constraints) {
          final totalWidth = constraints.maxWidth;
          final totalHeight = constraints.maxHeight;

          // Ensure widths fit within available space
          final reservedForSplitters =
              _splitterThickness * 2; // two vertical splitters
          final maxLeftPlusMid =
              totalWidth - _minRightPaneWidth - reservedForSplitters;
          if (_leftPaneWidth + _midPaneWidth > maxLeftPlusMid) {
            final overflow = _leftPaneWidth + _midPaneWidth - maxLeftPlusMid;
            // Reduce both proportionally but respect min widths
            final leftShare = _leftPaneWidth / (_leftPaneWidth + _midPaneWidth);
            _leftPaneWidth = (_leftPaneWidth - overflow * leftShare).clamp(
              _minPaneWidth,
              math.max(_minPaneWidth, maxLeftPlusMid - _minPaneWidth),
            );
            _midPaneWidth = (_midPaneWidth - overflow * (1 - leftShare)).clamp(
              _minPaneWidth,
              math.max(_minPaneWidth, maxLeftPlusMid - _leftPaneWidth),
            );
          }

          // Ensure top height within available vertical space (reserve splitter and min message)
          final availableTop =
              totalHeight - _splitterThickness - _minMessageHeight;
          final lowerBound = math.min(_minTopHeight, totalHeight);
          final upperBound = math.max(
            lowerBound,
            math.min(availableTop, totalHeight),
          );
          _topSectionHeight = _topSectionHeight.clamp(lowerBound, upperBound);

          return Padding(
            padding: const EdgeInsets.all(8.0),
            child: Column(
              children: [
                SizedBox(
                  height: _topSectionHeight,
                  child: TopSection(leftPaneWidth: _leftPaneWidth),
                ),
                const SizedBox(height: 16),
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

