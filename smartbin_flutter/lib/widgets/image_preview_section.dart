import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:smartbin_flutter/widgets/section_header.dart';

class ClassificationEntry {
  final String label;
  final String value; // e.g., '94.2%'
  const ClassificationEntry(this.label, this.value);
}

class ImagePreviewSection extends StatelessWidget {
  const ImagePreviewSection({
    super.key,
    required this.width,
    this.image,
    this.imageSize,
    this.detectedText = 'Detected: recyclable',
    this.classifications = const [
      ClassificationEntry('Plastic', '94.2%'),
      ClassificationEntry('glass', '3%'),
    ],
  });

  final double width;
  final ImageProvider? image;
  final Size? imageSize;
  final String detectedText;
  final List<ClassificationEntry> classifications;

  @override
  Widget build(BuildContext context) {
    final dimsText = imageSize != null
        ? 'Size: ${imageSize!.width.toInt()}x${imageSize!.height.toInt()}'
        : 'Size: -';

    return Card(
      child: SizedBox(
        width: width,
        child: Padding(
          padding: const EdgeInsets.all(12.0),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Left: preview + metadata
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // const Text(
                    //   'Last Captured Image',
                    //   style: TextStyle(fontSize: 18),
                    // ),
                    const SizedBox(height: 12),
                    Expanded(
                      child: Container(
                        // width: double.infinity,
                        decoration: BoxDecoration(
                          color: const Color(0xFFF0F0F0),
                          border: Border.all(
                            color: const Color(0xFFCCCCCC),
                            width: 2,
                          ),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Center(
                          child: image == null
                              ? const Text(
                                  'No image captured yet',
                                  style: TextStyle(color: Color(0xFF666666)),
                                )
                              : Image(
                                  image: image!,
                                  fit: BoxFit.contain,
                                  width: double.infinity,
                                  height: double.infinity,
                                ),
                        ),
                      ),
                    ),
                    const SizedBox(height: 8),
                    // Row 1: dimensions
                    Text(
                      dimsText,
                      style: Theme.of(context).textTheme.bodyMedium,
                    ),
                    const SizedBox(height: 4),
                    // Row 2: detected text
                    Text(
                      detectedText,
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ),

              const SizedBox(width: 12),
              // Right: classification list
              SizedBox(
                width: 240,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Classification Results',
                      style: TextStyle(fontSize: 18),
                    ),
                    const SizedBox(height: 12),
                    SingleChildScrollView(
                      child: Column(
                        children: [
                          ...classifications.map(
                                (e) => _classificationChip(e, context),
                          ),

                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _classificationChip(ClassificationEntry entry, BuildContext context) {

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      decoration: BoxDecoration(
        color: Color.alphaBlend(
          Theme.of(context).colorScheme.surface.withAlpha(128),
          Theme.of(context).cardTheme.color!,
        ), // light azure
        border: Border.all(color: Colors.grey.withAlpha(25)),
        borderRadius: BorderRadius.circular(8),
      ),
      padding: const EdgeInsets.all(12),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        // mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            entry.label.toUpperCase(),
            // style: const TextStyle(fontWeight: FontWeight.bold),
          ),
          // const SizedBox(height: 4),
          Text(
            entry.value,
            // style: const TextStyle(fontSize: 14, color: Color(0xFF666666)),
          ),
        ],
      ),
    );
  }
}
