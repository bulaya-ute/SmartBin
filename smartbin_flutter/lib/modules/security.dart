import 'dart:convert';
import 'package:encrypt/encrypt.dart' as encrypt;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:device_info_plus/device_info_plus.dart';
import 'package:flutter/material.dart';
import 'package:smartbin_flutter/modules/base_module.dart';

class Security extends BaseModule {
  static bool isInitialized = false;
  static String moduleName = "SECURITY";
  static const _passwordKey = 'sudo_password_encrypted';
  static String? _sudoPassword;

  // Public getter for the sudo password (returns null if not available)
  static String? get sudoPassword => _sudoPassword;

  // Initialization method to be called during app startup
  static Future<void> init(BuildContext context) async {
    final prefs = await SharedPreferences.getInstance();
    final encrypted = prefs.getString(_passwordKey);
    final key = await _generateKey();
    if (encrypted != null) {
      try {
        final decrypted = _decryptPassword(encrypted, key);
        _sudoPassword = decrypted;
        isInitialized = true;
        return;
      } catch (_) {
        // If decryption fails, treat as not initialized
        _sudoPassword = null;
        isInitialized = false;
      }
    }
    // Prompt user for password if not available or decryption failed
    final password = await _promptForPassword(context);
    if (password != null && password.isNotEmpty) {
      final encrypted = _encryptPassword(password, key);
      await prefs.setString(_passwordKey, encrypted);
      _sudoPassword = password;
      isInitialized = true;
    } else {
      isInitialized = false;
    }
  }

  // Show a dialog to prompt the user for the sudo password
  static Future<String?> _promptForPassword(BuildContext context) async {
    final controller = TextEditingController();
    return showDialog<String>(
      context: context,
      barrierDismissible: false,
      builder: (context) {
        return AlertDialog(
          title: const Text('Enter Sudo Password'),
          content: TextField(
            controller: controller,
            obscureText: true,
            decoration: const InputDecoration(labelText: 'Sudo Password'),
            autofocus: true,
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('Cancel'),
            ),
            ElevatedButton(
              onPressed: () => Navigator.of(context).pop(controller.text),
              child: const Text('OK'),
            ),
          ],
        );
      },
    );
  }

  // Encrypt the password using the generated key
  static String _encryptPassword(String password, encrypt.Key key) {
    final iv = encrypt.IV.fromLength(16);
    final encrypter = encrypt.Encrypter(encrypt.AES(key));
    final encrypted = encrypter.encrypt(password, iv: iv);
    return base64Encode(iv.bytes) + ':' + encrypted.base64;
  }

  // Decrypt the password using the generated key
  static String _decryptPassword(String encrypted, encrypt.Key key) {
    final parts = encrypted.split(':');
    if (parts.length != 2) throw Exception('Invalid encrypted format');
    final iv = encrypt.IV(base64Decode(parts[0]));
    final encrypter = encrypt.Encrypter(encrypt.AES(key));
    final decrypted = encrypter.decrypt64(parts[1], iv: iv);
    return decrypted;
  }

  // Generate a device-specific key for encryption
  static Future<encrypt.Key> _generateKey() async {
    final deviceInfo = DeviceInfoPlugin();
    String rawKey = '';
    try {
      if (await deviceInfo.deviceInfo is AndroidDeviceInfo) {
        final info = await deviceInfo.androidInfo;
        rawKey = '${info.id}${info.model}${info.board}${info.fingerprint}';
      } else if (await deviceInfo.deviceInfo is LinuxDeviceInfo) {
        final info = await deviceInfo.linuxInfo;
        rawKey = '${info.machineId}${info.name}${info.version}';
      } else if (await deviceInfo.deviceInfo is WebBrowserInfo) {
        final info = await deviceInfo.webBrowserInfo;
        rawKey = '${info.userAgent}${info.vendor}${info.hardwareConcurrency}';
      } else {
        final info = await deviceInfo.deviceInfo;
        rawKey = info.toString();
      }
    } catch (_) {
      rawKey = 'default_key';
    }
    // Hash the rawKey to 32 bytes for AES-256
    final hash = encrypt.Key.fromUtf8(
      base64Url.encode(utf8.encode(rawKey)).padRight(32).substring(0, 32),
    );
    return hash;
  }

  // For testing: clear the stored password
  static Future<void> clearPassword() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_passwordKey);
    _sudoPassword = null;
    isInitialized = false;
  }
}
