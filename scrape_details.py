import json
import os
import re
import urllib.parse
import urllib.request
import unicodedata
from playwright.sync_api import sync_playwright


LISTING_FILE = "products_listing.json"

# set this to your flutter project folder
# ex: my mac descktop folder
FLUTTER_APP_DIR = "/Users/samiraa/Desktop/mdst exercise/cos_coats_app"

MAX_MEDIA_PER_COLOR = 6

ASSETS_DIR = os.path.join(FLUTTER_APP_DIR, "assets")
IMAGES_DIR = os.path.join(ASSETS_DIR, "images")
# writing json directly into flutter assets (hardcoding)
OUTPUT_FILE = os.path.join(ASSETS_DIR, "products_with_details.json")
# convert EU to US 
EU_TO_US_WOMENS = {
    "32": "2",
    "34": "4",
    "36": "6",
    "38": "8",
    "40": "10",
    "42": "12",
    "44": "14"
}
#helpers
def dedupe_keep_order(items: list) -> list:
    out = []
    for x in items:
        if x not in out:
            out.append(x)
    return out


import unicodedata

def safe_slug(text: str) -> str:
    if not text:
        return ""
    ## strage color names
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")

    clean = text.strip().upper()
    clean = clean.replace(" ", "_")
    clean = clean.replace("/", "_")
    clean = clean.replace("\\", "_")
    clean = clean.replace(":", "_")
    clean = clean.replace("&", "AND")

    while "__" in clean:
        clean = clean.replace("__", "_")

    return clean


def extract_product_id_from_url(product_url: str) -> str:
    last = (product_url or "").split("-")[-1]
    if last.isdigit():
        return last
    path = urllib.parse.urlparse(product_url).path.strip("/").split("/")[-1]
    return safe_slug(path)


def normalize_image_url(url: str) -> str:
    if not url:
        return url
    # force large image width if imwidth exists
    return re.sub(r"imwidth=\d+", "imwidth=2160", url)


def detach_response_listener(context, handler) -> None:
    # context.remove_listener exists in playwright python; keep a safe wrapper
    try:
        context.remove_listener("response", handler)
    except Exception:
        pass


#desc

def extract_description(page) -> str | None:
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

    # json-ld fallback
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
            if isinstance(obj, dict) and "@type" in obj and obj["@type"] == "Product":
                if "description" in obj and isinstance(obj["description"], str):
                    desc = obj["description"].strip()
                    if desc:
                        return desc

    return None


#size

def normalize_size_label(label: str) -> str:
    clean = str(label).strip()
    if clean.isdigit() and clean in EU_TO_US_WOMENS:
        return EU_TO_US_WOMENS[clean]
    return clean


def extract_sizes_from_stock(payload: dict) -> list:
    sizes = []
    seen_labels = []

    def walk(obj):
        if isinstance(obj, dict):
            has_name = "name" in obj
            has_stock = "stock" in obj
            has_id = ("sizeId" in obj) or ("sku" in obj)

            if has_name and has_stock and has_id:
                raw_name = obj["name"]
                stock = obj["stock"]

                label = normalize_size_label(raw_name)
                if label and label not in seen_labels:
                    seen_labels.append(label)
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


##colors#

def extract_colors_from_dom(page) -> list:
    colors = []
    seen_keys = []

    selectors = [
        '[data-testid*="color"] a',
        '[role="radiogroup"] [role="radio"]',
        'a[aria-label*="Color"]',
    ]

    elements = []
    for sel in selectors:
        els = page.query_selector_all(sel)
        if len(els) > len(elements):
            elements = els

    for el in elements:
        name = el.get_attribute("aria-label") or el.text_content()
        if not name:
            continue

        # normalize like: "Color: Black" -> "BLACK"
        name = name.split(":")[-1].strip()
        if not name:
            continue

        color_key = name.upper()
        color_name = name

        href = el.get_attribute("href")
        if href and href.startswith("/"):
            href = "https://www.cos.com" + href

        key = color_key + "|" + str(href)
        if key in seen_keys:
            continue

        seen_keys.append(key)
        colors.append({
            "color_key": color_key,
            "color_name": color_name,
            "url": href
        })

    return colors

##care##

def open_details_panel(page) -> None:
    candidates = [
        '[data-testid*="product-details" i] button',
        'button:has-text("Details")',
        'button:has-text("Product details")',
        'a:has-text("Details")',
        'a:has-text("Product details")',
    ]

    for sel in candidates:
        btn = page.query_selector(sel)
        if btn:
            try:
                btn.click(force=True)
                page.wait_for_timeout(500)
                return
            except Exception:
                pass

def extract_care_guide(page) -> list:
    open_details_panel(page)
    page.wait_for_timeout(500)

    care_btn = page.query_selector('button:has-text("Care guide")')
    if not care_btn:
        care_btn = page.query_selector('button:has-text("CARE GUIDE")')
    if not care_btn:
        care_btn = page.query_selector('button:has-text("Care Guide")')

    if not care_btn:
        return [
            "Make sure that your favourite items remain long-loved pieces for years to come; read our product care guide."
        ]

    panel_id = care_btn.get_attribute("aria-controls")

    if care_btn.get_attribute("aria-expanded") != "true":
        try:
            care_btn.click(force=True)
        except Exception:
            pass
        page.wait_for_timeout(500)

    if not panel_id:
        return [
            "Make sure that your favourite items remain long-loved pieces for years to come; read our product care guide."
        ]

    panel = page.query_selector('[id="' + panel_id + '"]')
    if not panel:
        return [
            "Make sure that your favourite items remain long-loved pieces for years to come; read our product care guide."
        ]

    text = panel.text_content() or ""
    lines = []

    for line in text.split("\n"):
        clean = line.strip()
        if clean.startswith("-") or clean.startswith("•"):
            clean = clean[1:].strip()
        if clean:
            lines.append(clean)

    lines = dedupe_keep_order(lines)
    if not lines:
        return [
            "Make sure that your favourite items remain long-loved pieces for years to come; read our product care guide."
        ]
    return lines


# images

def extract_images_from_dom(page) -> list:
    urls = []
    selectors = ["img", "source"]
    for sel in selectors:
        els = page.query_selector_all(sel)
        for el in els:
            src = el.get_attribute("src")
            if not src:
                src = el.get_attribute("srcset")
            if not src:
                src = el.get_attribute("data-src")
            if not src:
                src = el.get_attribute("data-srcset")
            if not src:
                continue
            if "," in src and " " in src:
                first = src.split(",")[0].strip()
                src = first.split(" ")[0].strip()
            src = normalize_image_url(src)
            if "media.cos.com/assets/" not in src:
                continue
            urls.append(src)
    return dedupe_keep_order(urls)


def download_image_to_assets(image_url: str, product_id: str, color_key: str, index_1based: int) -> str | None:
    if not image_url:
        return None

    parsed = urllib.parse.urlparse(image_url)
    ext = os.path.splitext(parsed.path)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
        ext = ".jpg"
    folder = os.path.join(IMAGES_DIR, product_id, safe_slug(color_key))
    os.makedirs(folder, exist_ok=True)
    filename = str(index_1based) + ext
    out_path = os.path.join(folder, filename)
    if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
        rel = os.path.relpath(out_path, FLUTTER_APP_DIR)
        return rel.replace("\\", "/")
    req = urllib.request.Request(
        image_url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.cos.com/",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        with open(out_path, "wb") as f:
            f.write(data)
    except Exception as e:
        print("image download failed:", image_url)
        print("reason:", repr(e))
        return None

    rel = os.path.relpath(out_path, FLUTTER_APP_DIR)
    return rel.replace("\\", "/")


def download_variant_media(image_urls: list, product_id: str, color_key: str) -> list:
    cleaned = []
    urls = dedupe_keep_order(image_urls)
    for u in urls:
        if not u:
            continue
        low = u.lower()
        if "media.cos.com/assets/" not in low:
            continue
        if low.endswith(".mp4"):
            continue
        cleaned.append(u)
        if len(cleaned) >= MAX_MEDIA_PER_COLOR:
            break

    local_paths = []
    i = 1
    for remote in cleaned:
        saved = download_image_to_assets(remote, product_id, color_key, i)
        if saved:
            local_paths.append(saved)
            i += 1
        if len(local_paths) >= MAX_MEDIA_PER_COLOR:
            break
    return local_paths

#variant#####
def scrape_variant(context, page, color_key: str, color_name: str, color_url: str, product_id: str) -> dict:
    captured_stock_payloads = []
    def handle_response(resp):
        url = resp.url.lower()
        if "stock" not in url:
            return
        try:
            data = resp.json()
        except Exception:
            return
        if isinstance(data, dict):
            captured_stock_payloads.append(data)

    context.on("response", handle_response)

    page.goto(color_url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_selector("h1", timeout=60000)
    page.wait_for_timeout(2000)
    try:
        page.mouse.wheel(0, 1400)
        page.wait_for_timeout(400)
        page.mouse.wheel(0, 1400)
        page.wait_for_timeout(400)
    except Exception:
        pass

    remote_images = extract_images_from_dom(page)
    local_images = download_variant_media(remote_images, product_id, color_key)
    if not local_images:
        hero = page.query_selector('img[src*="media.cos.com/assets/"]')
        hero_src = hero.get_attribute("src") if hero else None
        if hero_src:
            hero_src = normalize_image_url(hero_src)
            saved = download_image_to_assets(hero_src, product_id, color_key, 1)
            if saved:
                local_images = [saved]

    sizes = []
    if captured_stock_payloads:
        best = []
        for payload in captured_stock_payloads:
            candidate = extract_sizes_from_stock(payload)
            if len(candidate) > len(best):
                best = candidate
        sizes = best

    detach_response_listener(context, handle_response)

    return {
        "color_key": color_key,
        "color_name": color_name,
        "url": color_url,
        "images": local_images,
        "sizes": sizes
    }

# details!!!!
def scrape_details(context, page, product_url: str, debug: bool = False) -> dict:
    product_id = extract_product_id_from_url(product_url)
    captured_stock_payloads = []
    captured_stock_urls = []
    def handle_response(resp):
        url = resp.url.lower()
        if "stock" not in url:
            return
        try:
            data = resp.json()
        except Exception:
            return

        if isinstance(data, dict):
            captured_stock_payloads.append(data)
            captured_stock_urls.append(resp.url)

    context.on("response", handle_response)
    page.goto(product_url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_selector("h1", timeout=60000)
    page.wait_for_timeout(2500)

    description = extract_description(page)
    care_guide = extract_care_guide(page)
    sizes = []
    if captured_stock_payloads:
        best = []
        for payload in captured_stock_payloads:
            candidate = extract_sizes_from_stock(payload)
            if len(candidate) > len(best):
                best = candidate
        sizes = best
    colors = extract_colors_from_dom(page)
    variants = []
    for c in colors:
        color_key = c["color_key"] if "color_key" in c else ""
        color_name = c["color_name"] if "color_name" in c else ""
        color_url = c["url"] if "url" in c else ""
        if color_key and color_url:
            variants.append(scrape_variant(context, page, color_key, color_name, color_url, product_id))

    detach_response_listener(context, handle_response)
    thumbnail_url = None
    for v in variants:
        if "url" in v and v["url"] == product_url:
            if "images" in v and isinstance(v["images"], list) and len(v["images"]) > 0:
                thumbnail_url = v["images"][0]
            break

    if not thumbnail_url and variants:
        v0 = variants[0]
        if "images" in v0 and isinstance(v0["images"], list) and len(v0["images"]) > 0:
            thumbnail_url = v0["images"][0]

    if debug:
        print("stock payloads captured:", len(captured_stock_payloads))
        if captured_stock_urls:
            print("example stock url:", captured_stock_urls[0])
        print("sizes count:", len(sizes))
        print("colors count:", len(colors))
        print("variants count:", len(variants))

    return {
        "description": description,
        "care_guide": care_guide,
        "sizes": sizes,
        "colors": colors,
        "variants": variants,
        "thumbnail_url": thumbnail_url
    }


# main yay

def main() -> None:
    # make sure flutter assets folders exist
    os.makedirs(ASSETS_DIR, exist_ok=True)
    os.makedirs(IMAGES_DIR, exist_ok=True)

    with open(LISTING_FILE, "r", encoding="utf-8") as f:
        products = json.load(f)

    print("Loaded products:", len(products))
    print("Writing json to:", OUTPUT_FILE)
    print("Saving images under:", IMAGES_DIR)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(locale="en-US")
        page = context.new_page()

        i = 0
        total = len(products)

        for product in products:
            i += 1
            title = product["title"] if "title" in product else None
            url = product["url"] if "url" in product else None

            if not url:
                print("Skipping (no url):", title)
                product["description"] = None
                product["care_guide"] = [
                    "Make sure that your favourite items remain long-loved pieces for years to come; read our product care guide."
                ]
                product["sizes"] = []
                product["colors"] = []
                product["variants"] = []
                product["thumbnail_url"] = product["image_url"] if "image_url" in product else None
                continue

            print("[", i, "/", total, "] Scraping details for:", title)

            details = scrape_details(context, page, url, debug=False)

            product["description"] = details["description"]
            product["care_guide"] = details["care_guide"]
            product["sizes"] = details["sizes"]
            product["colors"] = details["colors"]
            product["variants"] = details["variants"]
            product["thumbnail_url"] = details["thumbnail_url"]
        browser.close()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)

    print("Saved:", OUTPUT_FILE)
    print("done")


if __name__ == "__main__":
    main()
