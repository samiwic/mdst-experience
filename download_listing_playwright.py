from playwright.sync_api import sync_playwright

URL = "https://www.cos.com/en-us/women/coats-and-jackets/wool-coats"

def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(locale="en-US")
        page = context.new_page()
        page.goto(URL, wait_until="load", timeout=60000)
        page.wait_for_timeout(4000)  # 4 secs
        html = page.content()
        with open("listing_rendered.html", "w", encoding="utf-8") as f:
            f.write(html)
        context.close()
        browser.close()

if __name__ == "__main__":
    main()
