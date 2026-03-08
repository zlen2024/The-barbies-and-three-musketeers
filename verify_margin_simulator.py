from playwright.sync_api import sync_playwright, expect
import time

def verify_margin_simulator():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()

        print("Navigating to app...")
        page.goto("http://localhost:5173/")

        # Inject localStorage so we don't have to deal with the backend login loop
        print("Injecting localStorage...")
        page.evaluate("""() => {
            localStorage.setItem('userRole', 'Admin');
            localStorage.setItem('userId', '1');
            localStorage.setItem('userEmail', 'testadmin@chinhinforcast.com');
            localStorage.setItem('userName', 'testadmin');
        }""")

        print("Navigating to Margin Simulator...")
        page.goto("http://localhost:5173/margin-simulator")

        page.wait_for_selector("text=Select Product", timeout=10000)

        # Give some time for API calls to hopefully return something or just render the skeleton
        time.sleep(2)

        print("Taking screenshot...")
        page.screenshot(path="margin_simulator_verified.png", full_page=True)
        print("Done!")

        browser.close()

if __name__ == "__main__":
    verify_margin_simulator()
