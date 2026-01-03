print("1. Test 1 URL")
print("2. Scrape all (simple)")
print("3. Scrape all (advanced)")

choice = input("> ")

if choice == "1":
    import test_review
elif choice == "2":
    import scrape_review
elif choice == "3":
    import scrape_review_advanced
