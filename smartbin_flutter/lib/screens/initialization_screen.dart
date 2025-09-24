import 'dart:async';
import 'package:flutter/material.dart';

import '../models/init_step.dart';


class InitializationScreen extends StatefulWidget {
  const InitializationScreen({
    super.key,
    required this.steps,
    required this.nextPageBuilder,
    this.title = 'Initializing SmartBin...',
  });

  final List<InitStep> steps;
  final WidgetBuilder nextPageBuilder;
  final String title;

  @override
  State<InitializationScreen> createState() => _InitializationScreenState();
}


class _InitializationScreenState extends State<InitializationScreen> {
  late final double _totalWeight = widget.steps.fold(
    0.0,
    (sum, s) => sum + s.weight,
  );
  double _completedWeight = 0.0;
  int _currentIndex = -1;
  String _currentDescription = '';
  bool _finished = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    // Kick off after first frame to ensure overlay/layout is ready
    WidgetsBinding.instance.addPostFrameCallback((_) => _run());
  }

  Future<void> _run() async {
    try {
      for (var i = 0; i < widget.steps.length; i++) {
        final step = widget.steps[i];
        setState(() {
          _currentIndex = i;
          _currentDescription = step.description;
          _error = null;
        });
        try {
          await step.action();
        } catch (e) {
          // Record error but continue; you can change to rethrow to stop
          _error = e.toString();
        }
        setState(() {
          _completedWeight += step.weight;
        });
      }
      setState(() {
        _finished = true;
      });
      // Navigate to the next page
      if (mounted) {
        Navigator.of(
          context,
        ).pushReplacement(MaterialPageRoute(builder: widget.nextPageBuilder));
      }
    } catch (e) {
      setState(() {
        _error = e.toString();
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final progress = (_totalWeight == 0)
        ? 1.0
        : (_completedWeight / _totalWeight).clamp(0.0, 1.0);
    final percent = (progress * 100).toStringAsFixed(0);

    return Scaffold(
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 500),
          child: Padding(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                Text(
                  widget.title,
                  style: Theme.of(
                    context,
                  ).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 16),
                LinearProgressIndicator(value: progress),
                const SizedBox(height: 8),
                Text('$percent% complete'),
                const SizedBox(height: 16),
                if (_currentIndex >= 0)
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      ),
                      const SizedBox(width: 8),
                      Flexible(
                        child: Text(
                          _currentDescription,
                          textAlign: TextAlign.center,
                        ),
                      ),
                    ],
                  ),
                if (_error != null) ...[
                  const SizedBox(height: 12),
                  Text(
                    'Note: $_error',
                    style: TextStyle(
                      color: Theme.of(context).colorScheme.error,
                    ),
                    textAlign: TextAlign.center,
                  ),
                ],
                if (_finished) ...[
                  const SizedBox(height: 12),
                  const Text('Done. Launching...'),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }
}
