import 'package:flutter/material.dart';
import 'package:smartbin_flutter/dense_textfield.dart';

class BottomControls extends StatelessWidget {
  const BottomControls({
    super.key,
    required this.connected,
    required this.onToggleConnect,
    required this.autoReconnect,
    required this.onToggleAutoReconnect,
    required this.macController,
    this.onSendCommand,
  });

  final bool connected;
  final VoidCallback onToggleConnect;
  final bool autoReconnect;
  final ValueChanged<bool> onToggleAutoReconnect;
  final TextEditingController macController;
  final ValueChanged<String>? onSendCommand;

  @override
  Widget build(BuildContext context) {
    final cardColor = Theme.of(context).cardTheme.color;
    final cmdCtl = TextEditingController();

    return Container(
      decoration: BoxDecoration(color: cardColor),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            children: [
              Container(
                decoration: BoxDecoration(
                  color: connected
                      ? const Color(0xFFD4EDDA)
                      : const Color(0xFFF8D7DA),
                  border: Border.all(
                    color: connected
                        ? const Color(0xFFC3E6CB)
                        : const Color(0xFFF5C6CB),
                  ),
                  borderRadius: BorderRadius.circular(16),
                ),
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                child: Text(
                  connected ? '🟢 Connected' : '🔴 Disconnected',
                  style: TextStyle(
                    color: connected
                        ? const Color(0xFF155724)
                        : const Color(0xFF721C24),
                    fontWeight: FontWeight.bold,
                    fontSize: 12,
                  ),
                ),
              ),
              const SizedBox(width: 16),
              ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.blue,
                  foregroundColor: Colors.white,
                ),
                onPressed: onToggleConnect,
                child: Text(connected ? 'Disconnect' : 'Connect'),
              ),
              const SizedBox(width: 20),
              Transform.scale(
                scale: 0.9,
                child: Switch(
                  value: autoReconnect,
                  onChanged: onToggleAutoReconnect,
                  materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                ),
              ),
              const Text('Auto-reconnect'),
              const SizedBox(width: 20),
              const Text('ESP32 MAC:'),
              const SizedBox(width: 8),
              SizedBox(
                width: 300,
                child: DenseTextField(controller: macController),
              ),
              const Spacer(),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              const Text('Send command:'),
              const SizedBox(width: 8),
              Expanded(
                child: DenseTextField(
                  controller: cmdCtl,
                  decoration: const InputDecoration(
                    hintText: 'e.g. RTC00',
                  ),
                ),
              ),
              const SizedBox(width: 16),
              ElevatedButton(
                onPressed: () {
                  final text = cmdCtl.text.trim();
                  if (text.isNotEmpty) onSendCommand?.call(text);
                },
                child: const Text('Send'),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
