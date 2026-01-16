<img width="2880" height="1800" alt="image" src="https://github.com/user-attachments/assets/f8198239-4cda-404c-8559-359e41859679" />


This project is a Flutter web and mobile app that displays COS wool coats using scraped product data.
  Here is the URL: https://www.cos.com/en-us/women/coats-and-jackets/wool-coats 

All web scraping logic is written in Python and lives outside the Flutter app.

download_listing_playwright.py collects product listing URLs from the COS website.

scrape_details.py scrapes individual product pages for descriptions, colors, sizes, care guides, and images.

Downloaded images are saved to cos_coats_app/assets/images/.

All scraped product data is written to cos_coats_app/assets/products_with_details.json.

The Flutter app reads this JSON file at runtime to render the UI.

All Flutter source code lives inside the lib/ directory.

ProductListScreen displays the product catalog grid.

ProductDetailScreen handles the image carousel, color selection, size availability, and product details.

The app theme and colors are defined in lib/theme/app_theme.dart.

Assets are registered in pubspec.yaml.

Thank you!

<img width="2880" height="1502" alt="image" src="https://github.com/user-attachments/assets/98bc73fa-4810-49c3-8419-503fa6863a97" />
