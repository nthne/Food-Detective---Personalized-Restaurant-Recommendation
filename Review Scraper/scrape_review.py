import json
import time
import os
from playwright.sync_api import sync_playwright

# =========================
# CONFIG
# =========================
INPUT_FILE = "final_result_link.json"
OUTPUT_DIR = "data"
OUTPUT_FILE = f"{OUTPUT_DIR}/review_result.json"

SCROLL_DELAY = 1.5
MAX_SCROLL = 50   # đủ cho ~200–300 review / nhà hàng

os.makedirs(OUTPUT_DIR, exist_ok=True)

# =========================
# HELPER FUNCTIONS
# =========================
def scroll_until_no_more(page):
    last_height = page.evaluate("document.body.scrollHeight")
    for _ in range(MAX_SCROLL):
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(SCROLL_DELAY)
        new_height = page.evaluate("document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height


def extract_reviews(page, url):
    restaurant_id = page.get_attribute("[data-res-id]", "data-res-id")
    reviews = []

    for item in page.query_selector_all(".review-item"):
        def safe(sel):
            el = item.query_selector(sel)
            return el.inner_text().strip() if el else None

        reviews.append({
            "ID": item.get_attribute("data-review-id"),
            "RestaurantID": restaurant_id,
            "UserID": item.get_attribute("data-user-id"),
            "Rating": safe(".review-points"),
            "Content": safe(".review-des"),
            "CreatedAt": safe(".review-time")
        })

    return {
        "url": url,
        "review": reviews,
        "initData": {}
    }

# =========================
# MAIN SCRIPT
# =========================
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    urls = json.load(f)

results = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    # -------- LOGIN ONCE --------
    page.goto("https://www.foody.vn", timeout=60000)
    print("👉 Vui lòng đăng nhập Foody trong browser")
    input("👉 Đăng nhập xong nhấn ENTER để bắt đầu scrape...")

    for idx, url in enumerate(urls, start=1):
        print("=" * 80)
        print(f"[{idx}/{len(urls)}] Crawling:")
        print(url)
        print("=" * 80)

        try:
            page.goto(url, timeout=60000)
            time.sleep(3)

            print("⬇️ Scrolling reviews...")
            scroll_until_no_more(page)

            block = extract_reviews(page, url)
            print(f"🧾 Reviews scraped: {len(block['review'])}")

            results.append(block)

        except Exception as e:
            print("❌ Error:", e)

        time.sleep(2)

    browser.close()

# =========================
# SAVE OUTPUT
# =========================
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("\n✅ DONE")
print(f"📦 Total restaurants scraped: {len(results)}")
print(f"📁 Output saved to: {OUTPUT_FILE}")
