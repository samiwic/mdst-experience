import 'dart:convert';
import 'package:flutter/services.dart';
import '../models/product.dart';

class ProductRepository {
  Future<List<Product>> loadProducts() async {
    final raw = await rootBundle.loadString('assets/products_with_details.json');
    final decoded = json.decode(raw) as List;
    return decoded.map((e) => Product.fromJson(e as Map<String, dynamic>)).toList();
  }
}
