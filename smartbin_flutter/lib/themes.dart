import 'package:flutter/material.dart';

// Light Mode Color Scheme
const _lightColorScheme = ColorScheme(
  brightness: Brightness.light,
  primary: Color(0xFF0061A4),
  onPrimary: Color(0xFFFFFFFF),
  primaryContainer: Color(0xFFD1E4FF),
  onPrimaryContainer: Color(0xFF001D36),
  secondary: Color(0xFF535F70),
  onSecondary: Color(0xFFFFFFFF),
  secondaryContainer: Color(0xFFD7E3F8),
  onSecondaryContainer: Color(0xFF101C2B),
  tertiary: Color(0xFF6B5778),
  onTertiary: Color(0xFFFFFFFF),
  tertiaryContainer: Color(0xFFF3DAFF),
  onTertiaryContainer: Color(0xFF251432),
  error: Color(0xFFBA1A1A),
  onError: Color(0xFFFFFFFF),
  errorContainer: Color(0xFFFFDAD6),
  onErrorContainer: Color(0xFF410002),
  background: Color(0xFFFDFCFF),
  onBackground: Color(0xFF1A1C1E),
  surface: Color(0xFFFDFCFF), // Main surface color for light theme
  onSurface: Color(0xFF1A1C1E),
  surfaceVariant: Color(0xFFDFE2EB), // Will be used for card background
  onSurfaceVariant: Color(0xFF43474E),
  outline: Color(0xFF73777F),
  outlineVariant: Color(0xFFC3C7CF),
  shadow: Color(0xFF000000),
  scrim: Color(0xFF000000),
  inverseSurface: Color(0xFF2F3133),
  onInverseSurface: Color(0xFFF1F0F4),
  inversePrimary: Color(0xFF9FCAFF),
  surfaceTint: Color(0xFF0061A4),
);

// Dark Mode Color Scheme
const _darkColorScheme = ColorScheme(
  brightness: Brightness.dark,
  primary: Color(0xFF9FCAFF),
  onPrimary: Color(0xFF003258),
  primaryContainer: Color(0xFF00497D),
  onPrimaryContainer: Color(0xFFD1E4FF),
  secondary: Color(0xFFBBC7DB),
  onSecondary: Color(0xFF253140),
  secondaryContainer: Color(0xFF3C4858),
  onSecondaryContainer: Color(0xFFD7E3F8),
  tertiary: Color(0xFFD7BDE4),
  onTertiary: Color(0xFF3B2948),
  tertiaryContainer: Color(0xFF523F5F),
  onTertiaryContainer: Color(0xFFF3DAFF),
  error: Color(0xFFFFB4AB),
  onError: Color(0xFF690005),
  errorContainer: Color(0xFF93000A),
  onErrorContainer: Color(0xFFFFB4AB),
  background: Color(0xFF1A1C1E),
  onBackground: Color(0xFFE2E2E6),
  surface: Color(0xFF1A1C1E), // Main surface color for dark theme
  onSurface: Color(0xFFE2E2E6),
  surfaceVariant: Color(0xFF43474E), // Will be used for card background
  onSurfaceVariant: Color(0xFFC3C7CF),
  outline: Color(0xFF8D9199),
  outlineVariant: Color(0xFF43474E),
  shadow: Color(0xFF000000),
  scrim: Color(0xFF000000),
  inverseSurface: Color(0xFFE2E2E6),
  onInverseSurface: Color(0xFF1A1C1E),
  inversePrimary: Color(0xFF0061A4),
  surfaceTint: Color(0xFF9FCAFF),
);

// Card Theme for Light Mode
final _lightCardTheme = CardThemeData(
  color: _lightColorScheme.surfaceVariant, // MODIFIED: Explicitly set card color
  elevation: 8.0,
  shadowColor: Color(0x40000000),
  margin: EdgeInsets.symmetric(horizontal: 12.0, vertical: 6.0),
  shape: RoundedRectangleBorder(
    borderRadius: BorderRadius.all(Radius.circular(12.0)),
    side: BorderSide(
      // color: _lightColorScheme.outlineVariant, // MODIFIED: Adjusted border for new card color
      width: 1.0,
    ),
  ),
);

// Card Theme for Dark Mode
final _darkCardTheme = CardThemeData(
  color: _darkColorScheme.surfaceVariant, // MODIFIED: Explicitly set card color
  elevation: 10.0,
  shadowColor: Color(0x50000000),
  margin: EdgeInsets.symmetric(horizontal: 12.0, vertical: 6.0),
  shape: RoundedRectangleBorder(
    borderRadius: BorderRadius.all(Radius.circular(12.0)),
    side: BorderSide(
      // color: _darkColorScheme.outline, // MODIFIED: Adjusted border for new card color
      width: 1.0,
    ),
  ),
);

// Light Theme
final appLightTheme = ThemeData(
  useMaterial3: true,
  colorScheme: _lightColorScheme,
  cardTheme: _lightCardTheme,
  appBarTheme: AppBarTheme(
    backgroundColor: _lightColorScheme.primary,
    foregroundColor: _lightColorScheme.onPrimary,
    elevation: 4.0,
  ),
  // Add other theme properties as needed (textTheme, buttonTheme, etc.)
);

// Dark Theme
final appDarkTheme = ThemeData(
  useMaterial3: true,
  colorScheme: _darkColorScheme,
  cardTheme: _darkCardTheme,
  appBarTheme: AppBarTheme(
    backgroundColor: _darkColorScheme.surface,
    foregroundColor: _darkColorScheme.onSurface,
    elevation: 4.0,
  ),
  // Add other theme properties as needed (textTheme, buttonTheme, etc.)
);
