import 'package:flutter/material.dart';

class DenseTextfield extends StatefulWidget {


  const DenseTextfield({
    super.key,
    required this.controller,
    required this.hintText,
    required this.onChanged,
  });

  @override
  State<DenseTextfield> createState() => _DenseTextfieldState();
}

class _DenseTextfieldState extends State<DenseTextfield> {
  @override
  Widget build(BuildContext context) {
    return const Placeholder();
  }
}
