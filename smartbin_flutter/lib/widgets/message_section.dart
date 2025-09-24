import 'package:flutter/material.dart';
import 'package:smartbin_flutter/models/log_message.dart';
import 'package:smartbin_flutter/widgets/section_header.dart';

class MessageSection extends StatelessWidget {
  const MessageSection({
    super.key,
    required this.messages,
    required this.autoscroll,
    this.onToggleAutoscroll,
    this.onClear,
  });

  final List<LogMessage> messages;
  final bool autoscroll;
  final ValueChanged<bool?>? onToggleAutoscroll;
  final VoidCallback? onClear;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const SectionHeader(icon: '💬', title: 'Communication Log'),
                const Spacer(),
                Checkbox(
                  value: autoscroll,
                  onChanged: onToggleAutoscroll,
                ),
                const Text(
                  'Autoscroll',
                  style: TextStyle(fontWeight: FontWeight.bold),
                ),
                const SizedBox(width: 20),
                ElevatedButton(
                  onPressed: onClear,
                  child: const Text('Clear'),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Expanded(
              child: Card(
                child: ListView.builder(
                  itemCount: messages.length,
                  itemBuilder: (context, index) {
                    final msg = messages[index];
                    final color = msg.color ?? Theme.of(context).colorScheme.onSurface;
                    return Padding(
                      padding: const EdgeInsets.symmetric(
                        vertical: 2.0,
                        horizontal: 8.0,
                      ),
                      child: Text(msg.text, style: TextStyle(color: color)),
                    );
                  },
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

