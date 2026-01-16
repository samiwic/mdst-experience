import json
from playwright.sync_api import sync_playwright

LISTING_FILE = "products_listing.json"
OUTPUT_FILE = "products_with_details.json"

# convert common EU numeric sizes to US numeric sizes
EU_TO_US_WOMENS = {
    "32": "2",
    "34": "4",
    "36": "6",
    "38": "8",
    "40": "10",
    "42": "12",
    "44": "14"
}


def extract_description(page) -> str | None:
    """
    Extract description from the DESCRIPTION accordion.
    If the accordion content isn't readable, fall back to JSON-LD Product.description.
    """
    button = page.query_selector(
        '[data-testid="accordion-button-product-details-description-accordion"]'
    )
    if button:
        panel_id = button.get_attribute("aria-controls")

        if button.get_attribute("aria-expanded") != "true":
            button.click()
            page.wait_for_timeout(300)

        if panel_id:
            panel = page.query_selector("#" + panel_id)
            if panel:
                text = panel.text_content()
                if text and text.strip():
                    return text.strip()

    scripts = page.query_selector_all('script[type="application/ld+json"]')
    for script in scripts:
        raw = script.text_content()
        if not raw:
            continue

        try:
            data = json.loads(raw)
        except Exception:
            continue

        objs = data if isinstance(data, list) else [data]
        for obj in objs:
            if isinstance(obj, dict) and obj.get("@type") == "Product":
                desc = obj.get("description")
                if isinstance(desc, str) and desc.strip():
                    return desc.strip()

    return None


def extract_color_segment_from_url(url: str) -> str | None:
    """
    COS uses one PDP per color and encodes the full color segment in the slug:
      .../product/<name>-<color-segment>-<itemid>
    Example:
      cropped-knitted-merino-wool-jacket-dark-brown-mlange-1321328001
      -> color segment = dark-brown-mlange

    We return a human-friendly title-cased string:
      "Dark Brown Mlange"
    """
    slug = url.split("/")[-1]  # last path segment
    parts = slug.split("-")

    # find trailing numeric item id (last token), e.g. 1321328001
    if len(parts) < 3:
        return None

    last = parts[-1]
    if not last.isdigit():
        return None

    # remove item id
    body = parts[:-1]

    # Heuristic: color segment is after the product name.
    # We locate the last 1-4 tokens that look like color-like words.
    # But simplest: COS often has color segment starting at the first token
    # that matches a known color family word OR any token after "jacket/coat/etc".
    #
    # We'll do this:
    #   Take the last up to 4 tokens before the numeric id as the color segment.
    # This works well for: black, navy, charcoal, dark-brown-mlange, light-beige, etc.
    #
    # If you ever see a 5-token color, increase 4 -> 5.
    color_tokens = body[-4:]

    # join and format
    color_raw = "-".join(color_tokens).strip("-")
    if not color_raw:
        return None

    return color_raw.replace("-", " ").title()


def normalize_size_label(label: str) -> str:
    """
    Convert EU numeric sizes (32,34,...) to US numeric sizes (2,4,...)
    when applicable. Leave letter sizes (XS/S/M/...) as-is.
    """
    clean = str(label).strip()

    # if it's numeric and matches our EU mapping, convert
    if clean.isdigit() and clean in EU_TO_US_WOMENS:
        return EU_TO_US_WOMENS[clean]

    return clean


def extract_sizes_from_stock(payload: dict) -> list:
    """
    Walk the stock endpoint payload and collect size records.
    Then normalize EU numeric sizes -> US numeric sizes where needed.
    """
    sizes = []
    seen = set()

    def walk(obj):
        if isinstance(obj, dict):
            if "name" in obj and "stock" in obj and ("sizeId" in obj or "sku" in obj):
                raw_name = obj.get("name")
                stock = obj.get("stock")

                label = normalize_size_label(raw_name)
                if label and label not in seen:
                    seen.add(label)
                    sizes.append({
                        "label": label,
                        "available": stock != "no"
                    })

            for v in obj.values():
                walk(v)

        elif isinstance(obj, list):
            for item in obj:
                walk(item)

    walk(payload)
    return sizes


def scrape_details(page, product_url: str, debug: bool = False) -> dict:
    """
    Load PDP, extract description.
    Sizes/availability come from stock endpoint.
    Color is derived from URL slug color segment.
    """
    captured_stock_payloads = []
    captured_stock_urls = []

    def handle_response(resp):
        url = resp.url

        # robust match for stock endpoint even with extra params
        if "stock" not in url or "market=us" not in url:
            return

        try:
            data = resp.json()
        except Exception:
            return

        if isinstance(data, dict):
            captured_stock_payloads.append(data)
            captured_stock_urls.append(url)

    page.on("response", handle_response)

    page.goto(product_url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_selector("h1", timeout=60000)

    # allow stock request to finish
    page.wait_for_timeout(2500)

    description = extract_description(page)

    if debug:
        print("stock payloads captured:", len(captured_stock_payloads))
        if captured_stock_urls:
            print("stock url:", captured_stock_urls[0])

    sizes = []
    if captured_stock_payloads:
        # pick payload that yields the most sizes
        best = []
        for payload in captured_stock_payloads:
            candidate = extract_sizes_from_stock(payload)
            if len(candidate) > len(best):
                best = candidate
        sizes = best

    color_name = extract_color_segment_from_url(product_url)
    colors = [{"name": color_name, "url": product_url}] if color_name else []

    try:
        page.off("response", handle_response)
    except Exception:
        pass

    return {
        "description": description,
        "sizes": sizes,
        "colors": colors
    }


def main() -> None:
    with open(LISTING_FILE, "r", encoding="utf-8") as f:
        products = json.load(f)

    print("Loaded products:", len(products))

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(locale="en-US")
        page = context.new_page()

        for i, product in enumerate(products):
            title = product.get("title")
            url = product.get("url")

            if not url:
                print("Skipping (no url):", title)
                product["description"] = None
                product["sizes"] = []
                product["colors"] = []
                continue

            print(f"[{i+1}/{len(products)}] Scraping details for:", title)

            details = scrape_details(page, url, debug=False)
            product["description"] = details["description"]
            product["sizes"] = details["sizes"]
            product["colors"] = details["colors"]

        browser.close()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)

    print("Saved:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
