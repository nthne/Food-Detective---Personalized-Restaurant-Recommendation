from playwright.sync_api import sync_playwright

def launch_browser(headless=False):
    p = sync_playwright().start()
    browser = p.chromium.launch(headless=headless)
    context = browser.new_context()
    page = context.new_page()
    return p, browser, page


def login_foody(page):
    page.goto("https://www.foody.vn", timeout=60000)
    print("👉 Vui lòng đăng nhập Foody trong browser")
    input("👉 Login xong nhấn ENTER để tiếp tục...")
