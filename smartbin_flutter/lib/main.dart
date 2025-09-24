import 'package:flutter/material.dart';
import 'package:smartbin_flutter/modules/classification_module.dart';
import 'package:smartbin_flutter/screens/home_screen.dart';
import 'package:smartbin_flutter/screens/initialization_screen.dart';
import 'package:smartbin_flutter/themes.dart';
import 'models/init_step.dart';

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

  Future<void> _loadConfig() async {
    // TODO: load config from disk if needed
    await Future.delayed(const Duration(milliseconds: 600));
  }

  Future<void> _initBluetooth() async {
    // TODO: prepare platform Bluetooth permissions/stack
    await Future.delayed(const Duration(milliseconds: 900));
  }

  Future<void> _preloadAssets() async {
    // TODO: e.g., precache images/fonts if necessary
    await Future.delayed(const Duration(milliseconds: 700));
  }

  Future<void> _warmupModel() async {
    // TODO: warm up model / spawn background service if needed
    await Future.delayed(const Duration(milliseconds: 1200));
  }

  @override
  Widget build(BuildContext context) {
    final steps = <InitStep>[
      InitStep(description: 'Loading assets', weight: 1.0, action: _preloadAssets),
      InitStep(description: 'Initializing classification module', weight: 3.0, action: Classification.init),
      InitStep(description: 'Loading configuration', weight: 1.0, action: _loadConfig),
      InitStep(description: 'Initializing Bluetooth', weight: 2.0, action: _initBluetooth),
    ];

    return InitializationScreen(
      steps: steps,
      title: 'Initializing SmartBin...',
      nextPageBuilder: (_) => const HomeScreen(),
    );
  }
}

