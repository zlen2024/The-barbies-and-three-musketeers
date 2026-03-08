from playwright.sync_api import sync_playwright
import time

def test_copilot_chat():
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # 1. Login
        print("Logging in...")
        page.goto("http://localhost:5173/login")
        page.fill("input[type='text']", "admin")
        page.fill("input[type='password']", "password")
        page.click("button:has-text('Sign in')")

        # Wait for navigation to dashboard
        page.wait_for_url("**/", timeout=10000)

        print("Waiting a bit to ensure session is stored...")
        time.sleep(2)
        page.screenshot(path="dashboard_after_login.png")
        print("Dashboard screenshot saved.")

        # 2. Navigate to product detail page directly
        sku = "test-ACC-DRAIN"
        print(f"Navigating to product {sku}...")
        page.goto(f"http://localhost:5173/inventory/{sku}")

        print("Waiting 5 seconds for page load...")
        time.sleep(5)
        page.screenshot(path="product_page.png")
        print("Screenshot saved to product_page.png")

        # Close browser
        browser.close()

if __name__ == "__main__":
    test_copilot_chat()
