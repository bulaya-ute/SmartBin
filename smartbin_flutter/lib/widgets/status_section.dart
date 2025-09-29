import 'package:flutter/material.dart' hide ConnectionState;
import 'package:smartbin_flutter/widgets/section_header.dart';
import '../screens/home_screen.dart';

class StatusSection extends StatefulWidget {
  final int initialRecyclable;
  final int initialNonRecyclable;
  final int initialCoins;
  final Map<String, int>? detectionCounts;
  final ConnectionState connectionState;

  const StatusSection({
    super.key,
    this.initialRecyclable = 0,
    this.initialNonRecyclable = 0,
    this.initialCoins = 0,
    this.detectionCounts,
    this.connectionState = ConnectionState.disconnected,
  });

  @override
  State<StatusSection> createState() => _StatusSectionState();
}

class _StatusSectionState extends State<StatusSection> {
  late int _recyclable = widget.initialRecyclable;
  late int _nonRecyclable = widget.initialNonRecyclable;
  late int _coins = widget.initialCoins;
  late Map<String, int> _detectionCounts = Map.of(
    widget.detectionCounts ??
        const {
          'Plastic': 0,
          'Glass': 0,
          'Carton': 0,
          'Textile': 0,
          'E-waste': 0,
        },
  );

  bool get _areButtonsEnabled => widget.connectionState == ConnectionState.connected;

  Future<void> _setValueDialog({
    required String title,
    required int current,
    required ValueChanged<int> onValue,
  }) async {
    final controller = TextEditingController(text: current.toString());
    final result = await showDialog<int>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(title),
        content: TextField(
          controller: controller,
          keyboardType: TextInputType.number,
          decoration: const InputDecoration(
            labelText: 'Enter value',
            border: OutlineInputBorder(),
          ),
          onSubmitted: (_) =>
              Navigator.of(ctx).pop(int.tryParse(controller.text)),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () =>
                Navigator.of(ctx).pop(int.tryParse(controller.text)),
            child: const Text('Set'),
          ),
        ],
      ),
    );

    if (result != null && result >= 0) {
      onValue(result);
    } else if (result != null) {
      // invalid negative value
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Value must be a non-negative integer')),
      );
    }
  }

  Widget _counterCard({
    required String header,
    required int value,
    required VoidCallback onReset,
    required VoidCallback onSet,
  }) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(header, style: const TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 12),
            Row(
              children: [
                Text(
                  '$value',
                  style: const TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const Spacer(),
                OutlinedButton(
                  onPressed: _areButtonsEnabled ? onReset : null,
                  style: OutlinedButton.styleFrom(
                    foregroundColor: _areButtonsEnabled ? null : Colors.grey,
                  ),
                  child: const Text('Reset'),
                ),
                const SizedBox(width: 8),
                ElevatedButton(
                  onPressed: _areButtonsEnabled ? onSet : null,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: _areButtonsEnabled ? null : Colors.grey,
                  ),
                  child: const Text('Set'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _detectionCard(String label, int value) {
    return SizedBox(
      width: 180,
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(12.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(label, style: const TextStyle(fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              Text(
                '$value',
                style: const TextStyle(
                  fontSize: 22,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Match the style/icon of Classification Results header
            const Text('🧠 Bin Status', style: TextStyle(fontSize: 18)),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: _counterCard(
                    header: 'Recyclable Items',
                    value: _recyclable,
                    onReset: () => setState(() => _recyclable = 0),
                    onSet: () => _setValueDialog(
                      title: 'Set Recyclable Items',
                      current: _recyclable,
                      onValue: (v) => setState(() => _recyclable = v),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _counterCard(
                    header: 'Non-recyclable Items',
                    value: _nonRecyclable,
                    onReset: () => setState(() => _nonRecyclable = 0),
                    onSet: () => _setValueDialog(
                      title: 'Set Non-recyclable Items',
                      current: _nonRecyclable,
                      onValue: (v) => setState(() => _nonRecyclable = v),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _counterCard(
                    header: 'Coin Dispenser',
                    value: _coins,
                    onReset: () => setState(() => _coins = 0),
                    onSet: () => _setValueDialog(
                      title: 'Set Coin Dispenser Count',
                      current: _coins,
                      onValue: (v) => setState(() => _coins = v),
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            const Text('📊 Detection Counts', style: TextStyle(fontSize: 18)),

            const SizedBox(height: 12),
            Wrap(
              spacing: 12,
              runSpacing: 12,
              children: _detectionCounts.entries
                  .map((e) => _detectionCard(e.key, e.value))
                  .toList(),
            ),
          ],
        ),
      ),
    );
  }
}
