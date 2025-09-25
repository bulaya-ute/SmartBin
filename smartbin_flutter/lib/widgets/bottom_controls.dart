import 'package:flutter/material.dart' hide ConnectionState;
import 'package:smartbin_flutter/dense_textfield.dart';
import '../screens/home_screen.dart';

class BottomControls extends StatefulWidget {
  const BottomControls({
    super.key,
    required this.connectionState,
    required this.onToggleConnect,
    required this.autoReconnect,
    required this.onToggleAutoReconnect,
    required this.macController,
    this.onSendCommand,
  });

  final ConnectionState connectionState;
  final VoidCallback onToggleConnect;
  final bool autoReconnect;
  final ValueChanged<bool> onToggleAutoReconnect;
  final TextEditingController macController;
  final ValueChanged<String>? onSendCommand;

  @override
  State<BottomControls> createState() => _BottomControlsState();
}

class _BottomControlsState extends State<BottomControls> {
  late final TextEditingController _cmdCtl = TextEditingController();

  void _sendCommandIfAny([String? value]) {
    final text = (value ?? _cmdCtl.text).trim();
    if (text.isEmpty) return;
    widget.onSendCommand?.call(text);
    _cmdCtl.clear();
  }

  String _getConnectButtonText() {
    switch (widget.connectionState) {
      case ConnectionState.connected:
        return 'Disconnect';
      case ConnectionState.connecting:
        return 'Connecting...';
      case ConnectionState.disconnected:
      default:
        return 'Connect';
    }
  }

  bool _isConnectButtonEnabled() {
    return widget.connectionState != ConnectionState.connecting;
  }

  bool _areCommandControlsEnabled() {
    return widget.connectionState == ConnectionState.connected;
  }

  @override
  void dispose() {
    _cmdCtl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final cardColor = Theme.of(context).cardTheme.color;

    return Container(
      decoration: BoxDecoration(color: cardColor),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            children: [
              const SizedBox(width: 16),
              ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: _isConnectButtonEnabled() ? Colors.blue : Colors.grey,
                  foregroundColor: Colors.white,
                ),
                onPressed: _isConnectButtonEnabled() ? widget.onToggleConnect : null,
                child: Text(_getConnectButtonText()),
              ),
              const SizedBox(width: 20),
              Transform.scale(
                scale: 0.9,
                child: Switch(
                  value: widget.autoReconnect,
                  onChanged: widget.onToggleAutoReconnect,
                  materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                ),
              ),
              const Text('Auto-reconnect'),
              const SizedBox(width: 20),
              const Text('ESP32 MAC:'),
              const SizedBox(width: 8),
              SizedBox(
                width: 300,
                child: DenseTextField(controller: widget.macController),
              ),
              const Spacer(),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Text(
                'Send command:',
                style: TextStyle(
                  color: _areCommandControlsEnabled() ? null : Colors.grey,
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: DenseTextField(
                  controller: _cmdCtl,
                  enabled: _areCommandControlsEnabled(),
                  textInputAction: TextInputAction.send,
                  onSubmitted: _areCommandControlsEnabled() ? _sendCommandIfAny : null,
                  decoration: InputDecoration(
                    hintText: _areCommandControlsEnabled() ? 'e.g. RTC00' : 'Connect to enable commands',
                    hintStyle: TextStyle(
                      color: _areCommandControlsEnabled() ? null : Colors.grey,
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 16),
              ElevatedButton(
                onPressed: _areCommandControlsEnabled() ? _sendCommandIfAny : null,
                style: ElevatedButton.styleFrom(
                  backgroundColor: _areCommandControlsEnabled() ? null : Colors.grey,
                ),
                child: const Text('Send'),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
