// Copilot: Unique comment for verification - Security module integration planned here.
import 'package:flutter/material.dart';
import 'package:smartbin_flutter/modules/bluetooth.dart';
import 'package:smartbin_flutter/modules/config.dart';
import 'package:smartbin_flutter/modules/engine.dart';
import 'package:smartbin_flutter/screens/home_screen.dart';
import 'package:smartbin_flutter/screens/initialization_screen.dart';
import 'package:smartbin_flutter/themes.dart';
import 'models/init_step.dart';
import 'modules/classification.dart';
import 'package:smartbin_flutter/modules/security.dart';

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

class StartupEntry extends StatefulWidget {
  const StartupEntry({super.key});

  @override
  State<StartupEntry> createState() => _StartupEntryState();
}

class _StartupEntryState extends State<StartupEntry> {
  bool _dialogShown = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _showSudoDialog());
  }

  Future<void> _showSudoDialog() async {
    // Skip prompt if valid sudo password is already stored
    if (await Security.validateSudo()) {
      // Navigator.of(context).pop(controller.text);

      return;
    }
    if (_dialogShown) return;

    bool incorrectEntry = false;
    bool isLoading = false;

    _dialogShown = true;
    String? password = await showDialog<String>(
      context: context,
      barrierDismissible: false,
      builder: (context) {
        final controller = TextEditingController();
        return AlertDialog(
          title: const Text('Sudo Password Required'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text(
                'To use SmartBin, your sudo password is required for privileged operations (e.g., Bluetooth). ',
              ),
              const SizedBox(height: 16),
              if (incorrectEntry)
                Text(
                  "Sorry, the password you entered is incorrect",
                  style: TextStyle(color: Colors.red),
                ),
              TextField(
                controller: controller,
                obscureText: true,
                decoration: const InputDecoration(labelText: 'Sudo Password'),
                autofocus: true,
              ),
            ],
          ),
          actions: [
            // TextButton(
            //   onPressed: () => Navigator.of(context).pop(null),
            //   child: const Text('Cancel'),
            // ),
            ElevatedButton(
              onPressed: isLoading ? null : () async {
                setState(() {
                  isLoading = true;
                });

                // Inform the user that the password is incorrect, if it is
                if (!await Security.validateSudo(controller.text)) {
                  incorrectEntry = true;
                  // ScaffoldMessenger.of(context).showSnackBar(
                  //   SnackBar(
                  //     backgroundColor: Colors.red,
                  //     content: Text(
                  //       "Incorrect password",
                  //       style: TextStyle(color: Colors.white),
                  //     ),
                  //   ),
                  // );

                  setState(() {
                    isLoading = false;
                  });
                  return;
                }

                // Save the password
                Security.sudoPassword = controller.text;

                if (mounted) {
                  Navigator.of(context).pop(controller.text);
                }

                setState(() {
                  isLoading = false;
                });
              },
              child: isLoading ? const Text("Checking...") : const Text('Continue'),
            ),
          ],
        );
      },
    );

    if (password != null && password.isNotEmpty) {
      // Print the password to the console
      // ignore: avoid_print
      print('Sudo password entered: $password');
      // Proceed to initialization screen
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(
          builder: (context) => InitializationScreen(
            steps: <InitStep>[
              InitStep(
                description: 'Security check',
                weight: 1.0,
                action: () => Security.init(context),
              ),
              InitStep(
                description: 'Loading config',
                weight: 1.0,
                action: Config.init,
              ),
              InitStep(
                description: 'Starting engine',
                weight: 1.0,
                action: Engine.init,
              ),
              InitStep(
                description: 'Initializing bluetooth protocol module',
                weight: 1.0,
                action: Bluetooth.init,
              ),
              InitStep(
                description: 'Initializing classification module',
                weight: 1.0,
                action: Classification.init,
              ),
            ],
            title: 'Initializing SmartBin...',
            nextPageBuilder: (_) => const HomeScreen(),
          ),
        ),
      );
    } else {
      // Optionally, close the app or show a message
    }
  }

  @override
  Widget build(BuildContext context) {
    // Show a blank screen while waiting for password
    return const Scaffold(body: Center(child: CircularProgressIndicator()));
  }
}
