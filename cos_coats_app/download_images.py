import json
import os
import re
import urllib.request

INPUT_FILE = "products_with_details.json"
OUT_DIR = "assets/images"

def safe_name(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")

def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        products = json.load(f)

    os.makedirs(OUT_DIR, exist_ok=True)

    for i, p in enumerate(products):
        url = p.get("image_url", "")
        title = p.get("title", "product")
        if not url:
            continue

        filename = safe_name(title) + ".jpg"
        path = os.path.join(OUT_DIR, filename)

        try:
            urllib.request.urlretrieve(url, path)
            p["local_image"] = "assets/images/" + filename
            print(f"[{i+1}/{len(products)}] saved {filename}")
        except Exception as e:
            print(f"[{i+1}/{len(products)}] failed {title}: {e}")

    with open(INPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)

    print("updated json with local_image paths")

if __name__ == "__main__":
    main()
