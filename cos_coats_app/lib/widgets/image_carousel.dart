import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

class ImageCarousel extends StatefulWidget {
  final List<String> images;
  final PageController pageController;
  final String? fallbackImage;

  const ImageCarousel({
    super.key,
    required this.images,
    required this.pageController,
    this.fallbackImage,
  });

  @override
  State<ImageCarousel> createState() => _ImageCarouselState();
}

class _ImageCarouselState extends State<ImageCarousel> {
  int _page = 0;

  @override
  void didUpdateWidget(covariant ImageCarousel oldWidget) {
    super.didUpdateWidget(oldWidget);

    // if the image list changes, reset to first page safely
    if (oldWidget.images != widget.images) {
      _page = 0;

      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (!mounted) return;
        if (widget.pageController.hasClients) {
          widget.pageController.jumpToPage(0);
        }
        setState(() {});
      });
    }
  }

  String _normalize(String s) {
    return s.trim();
  }

  @override
  Widget build(BuildContext context) {
    final imgs = widget.images.isNotEmpty
        ? widget.images.map(_normalize).where((x) => x.isNotEmpty).toList()
        : (widget.fallbackImage == null
            ? <String>[]
            : <String>[_normalize(widget.fallbackImage!)]);

    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        SizedBox(
          height: 380, // fixed frame for consistency
          child: ClipRRect(
            borderRadius: BorderRadius.circular(14),
            child: imgs.isEmpty
                ? const _ImagePlaceholder()
                : PageView.builder(
                    controller: widget.pageController,
                    itemCount: imgs.length,
                    onPageChanged: (i) => setState(() => _page = i),
                    itemBuilder: (context, i) {
                      final path = imgs[i];
                      final isAsset =
                          path.startsWith('assets/') ||
                          path.startsWith('images/');

                      final imageWidget = isAsset
                          ? Image.asset(
                              kIsWeb && path.startsWith('assets/')
                                  ? path.substring('assets/'.length)
                                  : path,
                              fit: BoxFit.contain, // show full image
                              errorBuilder: (_, __, ___) =>
                                  const _ImagePlaceholder(),
                            )
                          : Image.network(
                              path,
                              fit: BoxFit.contain, // show full image
                              loadingBuilder: (context, child, progress) {
                                if (progress == null) return child;
                                return const Center(
                                  child: SizedBox(
                                    width: 28,
                                    height: 28,
                                    child: CircularProgressIndicator(
                                      strokeWidth: 2,
                                    ),
                                  ),
                                );
                              },
                              errorBuilder: (_, __, ___) =>
                                  const _ImagePlaceholder(),
                            );

                      return ColoredBox(
                        color: const Color(0xFFFFFFFF), // mdst primary white
                        child: Center(child: imageWidget),
                      );
                    },
                  ),
          ),
        ),
        const SizedBox(height: 8),
        if (imgs.length > 1)
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: List.generate(
              imgs.length,
              (i) => AnimatedContainer(
                duration: const Duration(milliseconds: 180),
                width: i == _page ? 16 : 6,
                height: 6,
                margin: const EdgeInsets.symmetric(horizontal: 3),
                decoration: BoxDecoration(
                  color: i == _page ? Colors.black : Colors.black26,
                  borderRadius: BorderRadius.circular(99),
                ),
              ),
            ),
          ),
      ],
    );
  }
}

class _ImagePlaceholder extends StatelessWidget {
  const _ImagePlaceholder();

  @override
  Widget build(BuildContext context) {
    return const ColoredBox(
      color: Color(0xFFEAEAEA),
      child: Center(
        child: Icon(
          Icons.image,
          color: Colors.black26,
          size: 40,
        ),
      ),
    );
  }
}
