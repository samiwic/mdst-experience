import 'package:flutter/material.dart';
import 'theme/app_theme.dart';
import 'screens/product_list_screen.dart';

void main() {
  runApp(const CosCoatsApp());
}

class CosCoatsApp extends StatelessWidget {
  const CosCoatsApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'COS Coats',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light(),
      home: const ProductListScreen(),
    );
  }
}
