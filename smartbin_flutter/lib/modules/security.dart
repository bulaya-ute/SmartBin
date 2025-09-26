import 'dart:convert';
import 'dart:io';
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

  static String? get sudoPassword {
    return _sudoPassword;
  }

  static set sudoPassword(String? value) {
    _sudoPassword = value;
  }

  /// Checks if the stored sudo password is valid, when no argument is provided.
  /// Checks if the argument is the correct sudo password if provided.
  static Future<bool> validateSudo([String? sudo]) async {
    String? passwordToCheck = sudo ?? sudoPassword;
    if (passwordToCheck == null) {
      return false;
    }

    try {
      final process = await Process.start(
        'sudo',
        ['-S', '-k', 'true'],
        runInShell: true,
        environment: Platform.environment,
        workingDirectory: Directory.current.path,
      );
      // Write password to stdin
      process.stdin.writeln(passwordToCheck);
      await process.stdin.flush();
      await process.stdin.close();

      final exitCode = await process.exitCode;
      return exitCode == 0;
    } catch (_) {
      return false;
    }
  }

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

    // // Prompt user for password if not available or decryption failed
    // final password = await _promptForPassword(context);
    // if (password != null && password.isNotEmpty) {
    //   final encrypted = _encryptPassword(password, key);
    //   await prefs.setString(_passwordKey, encrypted);
    //   _sudoPassword = password;
    //   isInitialized = true;
    // } else {
    //   isInitialized = false;
    // }
  }


  // Encrypt the password using the generated key
  static String _encryptPassword(String password, encrypt.Key key) {
    final iv = encrypt.IV.fromLength(16);
    final encrypter = encrypt.Encrypter(encrypt.AES(key));
    final encrypted = encrypter.encrypt(password, iv: iv);
    return '${base64Encode(iv.bytes)}:${encrypted.base64}';
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
