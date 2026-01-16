import 'package:flutter/material.dart';
import '../models/product.dart';
import '../widgets/image_carousel.dart';

class ProductDetailScreen extends StatefulWidget {
  final Product product;
  const ProductDetailScreen({super.key, required this.product});

  @override
  State<ProductDetailScreen> createState() => _ProductDetailScreenState();
}

class _ProductDetailScreenState extends State<ProductDetailScreen> {
  final _pageController = PageController();
  int _selectedVariantIndex = 0;

  // mdst secondary colors
  static const Color _lavender = Color(0xFFE6E0FF);
  static const Color _coolSteel = Color(0xFF9AA4B2);

  @override
  void initState() {
    super.initState();
    _selectedVariantIndex = 0;
  }

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  void _selectVariant(int index) {
    if (index == _selectedVariantIndex) return;

    setState(() {
      _selectedVariantIndex = index;
    });

    // keep carousel in sync when the image list changes
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      if (_pageController.hasClients) {
        _pageController.jumpToPage(0);
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final p = widget.product;

    final hasVariants = p.variants.isNotEmpty;
    final safeIndex = hasVariants
        ? _selectedVariantIndex.clamp(0, p.variants.length - 1)
        : 0;

    final selectedVariant = hasVariants ? p.variants[safeIndex] : null;

    final variantImages = (selectedVariant != null) ? selectedVariant.images : [];
    final List<String> images = (variantImages.isNotEmpty)
        ? List<String>.from(variantImages)
        : List<String>.from(p.bestDetailImages());

    final sizes = (selectedVariant != null) ? selectedVariant.sizes : [];

    return Scaffold(
      appBar: AppBar(
        title: Text(
          p.title,
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            ImageCarousel(
              images: images,
              pageController: _pageController,
              fallbackImage: p.thumbnailUrl ?? p.imageUrl,
            ),
            const SizedBox(height: 14),
            Text(p.title, style: Theme.of(context).textTheme.headlineSmall),
            const SizedBox(height: 6),
            Text(
              p.price ?? '',
              style: const TextStyle(fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 16),

            if (hasVariants) ...[
              Text(
                'Available colors',
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const SizedBox(height: 8),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: List.generate(p.variants.length, (i) {
                  final v = p.variants[i];
                  final isSelected = i == safeIndex;

                  return ChoiceChip(
                    label: Text(
                      v.colorName.toUpperCase(),
                      style: TextStyle(
                        fontWeight: FontWeight.w600,
                        color: Colors.black,
                      ),
                    ),
                    selected: isSelected,
                    showCheckmark: true,
                    checkmarkColor: Colors.black,
                    selectedColor: _lavender,
                    backgroundColor: Colors.white,
                    side: BorderSide(
                      color: isSelected ? _lavender : _coolSteel.withOpacity(0.35),
                    ),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                    onSelected: (_) => _selectVariant(i),
                  );
                }),
              ),
              const SizedBox(height: 16),

              Text(
                'Available sizes',
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const SizedBox(height: 8),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: sizes.map((s) {
                  final isAvailable = s.available;

                  return Chip(
                    label: Text(
                      s.label,
                      style: TextStyle(
                        fontWeight: FontWeight.w600,
                        color: Colors.black,
                      ),
                    ),
                    backgroundColor: isAvailable ? Colors.white : _coolSteel.withOpacity(0.20),
                    side: BorderSide(
                      color: isAvailable ? _coolSteel.withOpacity(0.35) : _coolSteel.withOpacity(0.20),
                    ),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  );
                }).toList(),
              ),
              const SizedBox(height: 16),
            ],

            Text('Description', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            Text(p.description ?? 'No description available.'),

            const SizedBox(height: 16),
            Text('Care guide', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            ...p.careGuide.map(
              (line) => Padding(
                padding: const EdgeInsets.only(bottom: 6),
                child: Text('• $line'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
