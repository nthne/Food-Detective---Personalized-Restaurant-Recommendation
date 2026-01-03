import time

def scroll_until_no_more(page, max_scroll=80, delay=1.5):
    last_height = page.evaluate("document.body.scrollHeight")

    for _ in range(max_scroll):
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(delay)
        new_height = page.evaluate("document.body.scrollHeight")

        if new_height == last_height:
            break
        last_height = new_height
