// This is a basic Flutter widget test.
//
// To perform an interaction with a widget in your test, use the WidgetTester
// utility in the flutter_test package. For example, you can send tap and scroll
// gestures. You can also use WidgetTester to find child widgets in the widget
// tree, read text, and verify that the values of widget properties are correct.

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:smartbin_flutter/main.dart';

void main() {
  testWidgets('SmartBin UI smoke test', (WidgetTester tester) async {
    // Build our app and trigger a frame.
    await tester.pumpWidget(const MyApp());

    // App should render the top app bar title and main sections
    expect(find.text('Communication Log'), findsOneWidget);

    // Bottom control shows Connected by default
    expect(find.textContaining('Connected'), findsOneWidget);
  });
}
