from playwright.sync_api import sync_playwright, TimeoutError
import json
import time

INPUT_LINKS = "data/raw_data/foody_links_more_than_0_reviews.txt"
OUTPUT_JSONL = "data/raw_data/reviews.jsonl"
FAILED_LINKS = "dan/failed_links.txt"


def scrape_reviews_from_page(page, url):
    page.goto(url, timeout=60000)

    # Scroll to first review
    page.evaluate("""
        () => {
            document.querySelector('li.review-item')
                ?.scrollIntoView({ block: 'start' });
        }
    """)

    last_count = 0

    while True:
        reviews = page.query_selector_all("li.review-item")
        current_count = len(reviews)

        if current_count <= last_count:
            break

        last_count = current_count

        btn = page.query_selector("div.pn-loadmore a.fd-btn-more:not([href])")
        if not btn:
            break

        page.evaluate("(el) => el.scrollIntoView({block: 'center'})", btn)
        page.evaluate("(el) => el.click()", btn)

        time.sleep(0.5)

    results = []

    for item in page.query_selector_all("li.review-item"):
        title_el = item.query_selector("a.rd-title")
        content_el = item.query_selector("div.rd-des span")
        time_el = item.query_selector("span.ru-time")
        rating_el = item.query_selector("div.review-points span")

        results.append({
            "rating": rating_el.inner_text().strip() if rating_el else None,
            "title": title_el.inner_text().strip() if title_el else None,
            "content": content_el.inner_text().strip() if content_el else None,
            "date": time_el.inner_text().strip() if time_el else None
        })

    return results


def get_restaurant_id(url):
    return url.rstrip("/").split("/")[-1]


def main():
    with open(INPUT_LINKS, "r", encoding="utf-8") as f:
        links = [line.strip() for line in f if line.strip()]

    with sync_playwright() as p, \
         open(OUTPUT_JSONL, "w", encoding="utf-8") as out, \
         open(FAILED_LINKS, "w", encoding="utf-8") as failed:

        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        for idx, url in enumerate(links, 1):
            print(f"\n[{idx}/{len(links)}] Scraping: {url}")

            try:
                reviews = scrape_reviews_from_page(page, url)

                record = {
                    "restaurant_id": get_restaurant_id(url),
                    "reviews": reviews
                }

                out.write(json.dumps(record, ensure_ascii=False) + "\n")
                out.flush()

                print(f"✅ Saved {len(reviews)} reviews")

            except TimeoutError:
                print("⛔ Timeout")
                failed.write(url + "\n")

            except Exception as e:
                print(f"⛔ Error: {e}")
                failed.write(url + "\n")

            time.sleep(0.5)

        browser.close()

    print("\n✅ DONE")


if __name__ == "__main__":
    main()
