import json
import time
import os
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError

# =========================
# CONFIG
# =========================
INPUT_FILE = "final_result_link.json"

DATA_DIR = "data"
OUTPUT_FILE = f"{DATA_DIR}/review_result.json"
CHECKPOINT_FILE = f"{DATA_DIR}/checkpoint.json"
ERROR_FILE = f"{DATA_DIR}/scrape_errors.json"

SAVE_EVERY = 20
MAX_RETRY = 3
SCROLL_DELAY = 1.5
MAX_SCROLL = 80     # đủ cho hàng trăm review

os.makedirs(DATA_DIR, exist_ok=True)

# =========================
# UTILITIES
# =========================
def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def estimate_eta(start_time, done, total):
    elapsed = time.time() - start_time
    avg = elapsed / max(done, 1)
    remaining = avg * (total - done)
    return time.strftime("%H:%M:%S", time.gmtime(remaining))


# =========================
# BROWSER HELPERS
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
    res_id = page.get_attribute("[data-res-id]", "data-res-id")
    reviews = []

    for item in page.query_selector_all(".review-item"):
        def safe(sel):
            el = item.query_selector(sel)
            return el.inner_text().strip() if el else None

        reviews.append({
            "ID": item.get_attribute("data-review-id"),
            "RestaurantID": res_id,
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
# LOAD DATA
# =========================
urls = load_json(INPUT_FILE, [])
checkpoint = load_json(CHECKPOINT_FILE, {
    "last_index": 0,
    "results": []
})
errors = load_json(ERROR_FILE, [])

start_index = checkpoint["last_index"]
results = checkpoint["results"]

total = len(urls)
start_time = time.time()

# =========================
# MAIN
# =========================
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()

    # -------- LOGIN ONCE --------
    page.goto("https://www.foody.vn", timeout=60000)
    print("👉 Vui lòng đăng nhập Foody trong browser")
    input("👉 Đăng nhập xong nhấn ENTER để bắt đầu scrape...")

    for i in range(start_index, total):
        url = urls[i]
        print("=" * 80)
        print(f"[{i+1}/{total}] Crawling:")
        print(url)

        success = False

        for attempt in range(1, MAX_RETRY + 1):
            try:
                page.goto(url, timeout=60000)
                time.sleep(3)

                scroll_until_no_more(page)
                block = extract_reviews(page, url)

                print(f"🧾 Reviews scraped: {len(block['review'])}")

                results.append(block)
                success = True
                break

            except TimeoutError:
                print(f"⚠️ Timeout (attempt {attempt})")
                time.sleep(3)
            except Exception as e:
                print(f"❌ Error (attempt {attempt}): {e}")
                time.sleep(3)

        if not success:
            errors.append({
                "url": url,
                "index": i,
                "time": datetime.now().isoformat()
            })

        # -------- SAVE CHECKPOINT --------
        if (i + 1) % SAVE_EVERY == 0 or i == total - 1:
            save_json(OUTPUT_FILE, results)
            save_json(CHECKPOINT_FILE, {
                "last_index": i + 1,
                "results": results
            })
            save_json(ERROR_FILE, errors)

            eta = estimate_eta(start_time, i + 1 - start_index, total - start_index)
            print(f"💾 Saved @ {i+1}/{total} | ETA: {eta}")

        time.sleep(2)

    browser.close()

# =========================
# DONE
# =========================
print("\n✅ SCRAPE COMPLETE")
print(f"📦 Total restaurants scraped: {len(results)}")
print(f"❌ Errors: {len(errors)}")
print(f"📁 Output: {OUTPUT_FILE}")
