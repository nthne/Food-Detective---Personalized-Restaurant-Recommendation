import json

with open("data/review_result.json", "r", encoding="utf-8") as f:
    data = json.load(f)

total_restaurants = len(data)
total_reviews = sum(len(r["review"]) for r in data)

print("📦 Nhà hàng:", total_restaurants)
print("🧾 Tổng review:", total_reviews)
print("📊 Trung bình:", total_reviews / max(total_restaurants, 1))
