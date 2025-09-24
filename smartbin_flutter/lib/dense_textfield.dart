import 'package:flutter/material.dart';

/// A compact TextField with dense layout and 5px padding all around.
///
/// You can pass a custom [decoration]; any non-null fields will override
/// the defaults (isDense + EdgeInsets.all(5) + OutlineInputBorder).
class DenseTextField extends StatelessWidget {
  const DenseTextField({
    super.key,
    this.controller,
    this.focusNode,
    this.decoration,
    this.keyboardType,
    this.textInputAction,
    this.onChanged,
    this.onSubmitted,
    this.obscureText = false,
    this.enabled,
    this.maxLines = 1,
    this.minLines,
    this.readOnly = false,
    this.style,
  });

  final TextEditingController? controller;
  final FocusNode? focusNode;
  final InputDecoration? decoration;
  final TextInputType? keyboardType;
  final TextInputAction? textInputAction;
  final ValueChanged<String>? onChanged;
  final ValueChanged<String>? onSubmitted;
  final bool obscureText;
  final bool? enabled;
  final int? minLines;
  final int? maxLines;
  final bool readOnly;
  final TextStyle? style;

  @override
  Widget build(BuildContext context) {
    final base = const InputDecoration(
      isDense: true,
      contentPadding: EdgeInsets.all(5),
      border: OutlineInputBorder(),

    );

    final merged = _mergeDecoration(base, decoration);

    return TextField(
      controller: controller,
      focusNode: focusNode,
      decoration: merged,
      keyboardType: keyboardType,
      textInputAction: textInputAction,
      onChanged: onChanged,
      onSubmitted: onSubmitted,
      obscureText: obscureText,
      enabled: enabled,
      minLines: minLines,
      maxLines: maxLines,
      readOnly: readOnly,
      style: TextStyle(
        fontFamily: "JetBrainsMono"
      ),
    );
  }

  // Merge incoming decoration over defaults; non-null incoming fields override.
  InputDecoration _mergeDecoration(InputDecoration base, InputDecoration? incoming) {
    if (incoming == null) return base;
    return base.copyWith(
      icon: incoming.icon,
      labelText: incoming.labelText,
      labelStyle: incoming.labelStyle,
      helperText: incoming.helperText,
      helperStyle: incoming.helperStyle,
      hintText: incoming.hintText,
      hintStyle: incoming.hintStyle,
      prefixIcon: incoming.prefixIcon,
      suffixIcon: incoming.suffixIcon,
      prefixText: incoming.prefixText,
      suffixText: incoming.suffixText,
      enabledBorder: incoming.enabledBorder,
      focusedBorder: incoming.focusedBorder,
      errorBorder: incoming.errorBorder,
      focusedErrorBorder: incoming.focusedErrorBorder,
      disabledBorder: incoming.disabledBorder,
      border: incoming.border ?? base.border,
      isDense: incoming.isDense ?? base.isDense,
      contentPadding: incoming.contentPadding ?? base.contentPadding,
      fillColor: incoming.fillColor,
      filled: incoming.filled,
      errorText: incoming.errorText,
      errorMaxLines: incoming.errorMaxLines,
      counterText: incoming.counterText,
      constraints: incoming.constraints,
      // Add others as needed
    );
  }
}

