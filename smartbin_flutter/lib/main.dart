import 'package:flutter/material.dart';
import 'package:smartbin_flutter/modules/config.dart';
import 'package:smartbin_flutter/modules/engine.dart';
import 'package:smartbin_flutter/screens/home_screen.dart';
import 'package:smartbin_flutter/screens/initialization_screen.dart';
import 'package:smartbin_flutter/themes.dart';
import 'models/init_step.dart';
import 'modules/classification.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'SmartBin Control',
      theme: appLightTheme,
      darkTheme: appDarkTheme,
      themeMode: ThemeMode.system,
      home: const StartupEntry(),
      debugShowCheckedModeBanner: false,
    );
  }
}

class StartupEntry extends StatelessWidget {
  const StartupEntry({super.key});

  @override
  Widget build(BuildContext context) {
    final steps = <InitStep>[
      InitStep(description: 'Loading config', weight: 1.0, action: Config.init),
      InitStep(description: 'Starting engine', weight: 1.0, action: Engine.init),
      InitStep(description: 'Initializing classification module', weight: 1.0, action: Classification.init),
      InitStep(description: 'Initializing bluetooth protocol module', weight: 1.0, action: Classification.init),
    ];

    return InitializationScreen(
      steps: steps,
      title: 'Initializing SmartBin...',
      nextPageBuilder: (_) => const HomeScreen(),
    );
  }
}

