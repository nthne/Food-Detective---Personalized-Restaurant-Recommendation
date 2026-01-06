import json
import re
import time
import requests
from datetime import datetime, timezone, timedelta


# =========================
# CONFIG
# =========================
INPUT_FILE = "restaurants_missing_manual.json"
OUTPUT_FILE = "review_less_13_retry.json"
MISSING_FILE = "restaurants_missing_backup.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# =========================
# UTILITIES
# =========================
def normalize_url(url):
    if not url:
        return None
    if url.startswith("/"):
        return "https://www.foody.vn" + url
    if not url.startswith("http"):
        return "https://www.foody.vn/" + url
    return url

def extract_init_data_reviews(html):
    m = re.search(r'var\s+initDataReviews\s*=\s*(\{.*?\});', html, re.S)
    if not m:
        return None
    return json.loads(m.group(1))

def parse_foody_date(date_str):
    if not date_str:
        return None

    m = re.search(r'Date\((\d+)\)', date_str)
    if not m:
        return None

    ts = int(m.group(1)) / 1000
    vn_time = datetime.fromtimestamp(
        ts, tz=timezone.utc
    ).astimezone(timezone(timedelta(hours=7)))

    return {
        "CreatedAt": vn_time.strftime("%d-%m-%Y"),
        "CreatedAtTimestamp": int(vn_time.timestamp())
    }

def parse_review_item(item, restaurant_id):
    time_data = parse_foody_date(item.get("CreatedDate"))

    return {
        "ID": item.get("Id"),
        "RestaurantID": restaurant_id,
        "UserID": item.get("Owner", {}).get("Id"),
        "UserName": item.get("Owner", {}).get("DisplayName"),
        "Rating": item.get("AvgRating"),
        "Title": item.get("Title"),
        "Content": item.get("Description"),
        "CreatedAt": time_data["CreatedAt"] if time_data else None,
    }

def deduplicate_reviews(reviews):
    seen = set()
    unique = []
    for r in reviews:
        key = r.get("ID") or (r.get("Title"), r.get("Content"))
        if key in seen:
            continue
        seen.add(key)
        unique.append(r)
    return unique

# =========================
# LOAD INPUT
# =========================
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    restaurants = json.load(f)

results = []
missing = []
total_reviews = 0

# =========================
# SCRAPER
# =========================
for idx, res in enumerate(restaurants, start=1):
    url = normalize_url(
        res.get("url")
        or res.get("RestaurantUrl")
        or res.get("MicrositeUrl")
    )

    if not url:
        missing.append(res)
        continue

    print(f"[{idx}/{len(restaurants)}] {url}")

    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
    except Exception:
        missing.append(res)
        continue

    init_reviews = extract_init_data_reviews(r.text)
    if not init_reviews or not init_reviews.get("Items"):
        missing.append(res)
        continue

    parsed_reviews = [
        parse_review_item(item, init_reviews.get("ResId"))
        for item in init_reviews["Items"]
    ]

    parsed_reviews = [
        r for r in parsed_reviews if r.get("Content")
    ]

    parsed_reviews = deduplicate_reviews(parsed_reviews)

    expected = res.get("TotalReview", len(parsed_reviews))
    parsed_reviews = parsed_reviews[:expected]

    total_reviews += len(parsed_reviews)

    results.append({
        "url": url,
        "review": parsed_reviews,
        "initData": {}
    })

    print(f"  ✅ Scraped {len(parsed_reviews)} review(s)")
    time.sleep(0.8)

# =========================
# SAVE OUTPUT
# =========================
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

with open(MISSING_FILE, "w", encoding="utf-8") as f:
    json.dump(missing, f, ensure_ascii=False, indent=2)

# =========================
# SUMMARY
# =========================
print("\n====================")
print("✅ DONE")
print(f"📊 Tổng quán scrape OK: {len(results)}")
print(f"🧾 Tổng review: {total_reviews}")
print(f"❌ Quán scrape FAIL: {len(missing)}")
print(f"📁 Output: {OUTPUT_FILE}")
print(f"📁 Missing: {MISSING_FILE}")
