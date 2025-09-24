import 'package:flutter/material.dart';

import '../models/log_message.dart';
import '../widgets/bottom_controls.dart';
import '../widgets/message_section.dart';
import '../widgets/top_section.dart';

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

  bool _connected = false;
  bool autoscroll = true;
  bool autoReconnect = true;

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
      appBar: AppBar(title: const Text('📱 SmartBin Control'), elevation: 2),
      bottomNavigationBar: BottomControls(
        connected: _connected,
        onToggleConnect: () => setState(() => _connected = !_connected),
        autoReconnect: autoReconnect,
        onToggleAutoReconnect: (v) => setState(() => autoReconnect = v),
        macController: _macCtl,
        onSendCommand: (cmd) {
          setState(() {
            _messages.add(LogMessage(text: '→ $cmd', color: Colors.green));
          });
        },
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
