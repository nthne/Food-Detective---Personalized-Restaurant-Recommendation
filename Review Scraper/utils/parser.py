def parse_reviews(page, url):
    res_id = page.get_attribute("[data-res-id]", "data-res-id")
    reviews = []

    for item in page.query_selector_all(".review-item"):
        reviews.append({
            "ID": item.get_attribute("data-review-id"),
            "RestaurantID": res_id,
            "UserID": item.get_attribute("data-user-id"),
            "Rating": safe(item, ".review-points"),
            "Content": safe(item, ".review-des"),
            "CreatedAt": safe(item, ".review-time")
        })

    return {
        "url": url,
        "review": reviews,
        "initData": {}
    }
