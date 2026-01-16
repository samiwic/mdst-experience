import 'package:flutter/material.dart';

class AppTheme {
  static ThemeData light() {
    const punchRed = Color(0xFFEF233C);

    return ThemeData(
      useMaterial3: true,
      fontFamily: 'Inter',
      scaffoldBackgroundColor: Colors.white,

      colorScheme: ColorScheme.fromSeed(
        seedColor: punchRed,
        brightness: Brightness.light,
      ),

      //  top bar
      appBarTheme: const AppBarTheme(
        backgroundColor: punchRed,
        foregroundColor: Colors.white, // title + back arrow
        elevation: 0,
        centerTitle: true,
      ),

      primaryColor: punchRed,

      textTheme: const TextTheme(
        headlineSmall: TextStyle(fontSize: 22, fontWeight: FontWeight.w600),
        titleMedium: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
        bodyMedium: TextStyle(fontSize: 14, height: 1.25),
        bodySmall: TextStyle(fontSize: 12, height: 1.25),
      ),
    );
  }
}
