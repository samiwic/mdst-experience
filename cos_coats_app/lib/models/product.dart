class Product {
  final String title;
  final String url;
  final String? price;
  final String? imageUrl;
  final String? thumbnailUrl;

  final String? description;
  final List<String> careGuide;

  final List<Variant> variants;

  Product({
    required this.title,
    required this.url,
    this.price,
    this.imageUrl,
    this.thumbnailUrl,
    this.description,
    required this.careGuide,
    required this.variants,
  });

  factory Product.fromJson(Map<String, dynamic> json) {
    final variantsJson = (json['variants'] as List?) ?? const [];
    final variants = variantsJson
        .map((v) => Variant.fromJson(v as Map<String, dynamic>))
        .toList();

    final care = (json['care_guide'] as List?) ?? const [];
    final careGuide = care.map((x) => x.toString()).toList();

    return Product(
      title: (json['title'] ?? '').toString(),
      url: (json['url'] ?? '').toString(),
      price: json['price']?.toString(),
      imageUrl: json['image_url']?.toString(),
      thumbnailUrl: json['thumbnail_url']?.toString(),
      description: json['description']?.toString(),
      careGuide: careGuide,
      variants: variants,
    );
  }

  List<String> bestDetailImages() {
    if (variants.isNotEmpty && variants.first.images.isNotEmpty) {
      return variants.first.images;
    }
    if (thumbnailUrl != null && thumbnailUrl!.isNotEmpty) return [thumbnailUrl!];
    if (imageUrl != null && imageUrl!.isNotEmpty) return [imageUrl!];
    return const [];
  }
}

class Variant {
  final String colorKey;
  final String colorName;
  final List<String> images;
  final List<SizeOption> sizes;

  Variant({
    required this.colorKey,
    required this.colorName,
    required this.images,
    required this.sizes,
  });

  factory Variant.fromJson(Map<String, dynamic> json) {
    final imgs = (json['images'] as List?) ?? const [];
    final images = imgs.map((x) => x.toString()).toList();

    final sizesJson = (json['sizes'] as List?) ?? const [];
    final sizes = sizesJson
        .map((s) => SizeOption.fromJson(s as Map<String, dynamic>))
        .toList();

    return Variant(
      colorKey: (json['color_key'] ?? '').toString(),
      colorName: (json['color_name'] ?? '').toString(),
      images: images,
      sizes: sizes,
    );
  }
}

class SizeOption {
  final String label;
  final bool available;

  SizeOption({required this.label, required this.available});

  factory SizeOption.fromJson(Map<String, dynamic> json) {
    return SizeOption(
      label: (json['label'] ?? '').toString(),
      available: (json['available'] == true),
    );
  }
}
