import 'package:flutter/material.dart';
import 'package:smartbin_flutter/widgets/image_preview_section.dart';
import 'package:smartbin_flutter/widgets/status_section.dart';

class TopSection extends StatelessWidget {
  const TopSection({
    super.key,
    required this.leftRatio,
    required this.minLeftWidth,
    required this.minRightWidth,
    required this.splitterThickness,
    required this.onLeftRatioChanged,
  });

  final double leftRatio; // fraction of available width for left panel
  final double minLeftWidth;
  final double minRightWidth;
  final double splitterThickness;
  final ValueChanged<double> onLeftRatioChanged;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final totalWidth = constraints.maxWidth;
        final availableWidth = (totalWidth - splitterThickness).clamp(0, double.infinity);

        // If very small, avoid division by zero and fallback
        if (availableWidth <= 0) {
          return Row(
            children: const [Expanded(child: SizedBox()),],
          );
        }

        final minLeftRatio = (minLeftWidth / availableWidth).clamp(0.0, 1.0);
        final minRightRatio = (minRightWidth / availableWidth).clamp(0.0, 1.0);
        final maxLeftRatio = (1.0 - minRightRatio).clamp(0.0, 1.0);

        // Clamp incoming ratio to ensure both sides respect min widths
        final clampedLeftRatio = leftRatio.clamp(minLeftRatio, maxLeftRatio);
        final leftWidth = (availableWidth * clampedLeftRatio).clamp(minLeftWidth, availableWidth - minRightWidth);

        return Row(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Left: Image preview section
            ImagePreviewSection(width: leftWidth),

            // Vertical splitter handle
            SizedBox(
              width: splitterThickness,
              child: MouseRegion(
                cursor: SystemMouseCursors.resizeColumn,
                child: GestureDetector(
                  behavior: HitTestBehavior.opaque,
                  onHorizontalDragUpdate: (details) {
                    final newLeftWidth = (leftWidth + details.delta.dx)
                        .clamp(minLeftWidth, availableWidth - minRightWidth);
                    final newRatio = newLeftWidth / availableWidth;
                    onLeftRatioChanged(newRatio);
                  },
                  child: Container(
                    color: const Color(0xFFE0E0E0),
                    child: Center(
                      child: Container(
                        width: 3,
                        height: 40,
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

            // Right: Status section grows to fill remaining space
            const Expanded(child: StatusSection()),
          ],
        );
      },
    );
  }
}
