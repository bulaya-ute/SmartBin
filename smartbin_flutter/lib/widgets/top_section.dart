import 'package:flutter/material.dart';

class TopSection extends StatelessWidget {
  const TopSection({super.key, required this.leftPaneWidth});

  final double leftPaneWidth;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Card(
          child: SizedBox(width: leftPaneWidth),
        ),
        Expanded(
          child: Card(),
        ),
      ],
    );
  }
}

