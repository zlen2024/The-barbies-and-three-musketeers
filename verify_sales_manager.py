import time
from playwright.sync_api import sync_playwright

def verify_frontend():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        # Start at login
        page.goto('http://localhost:5000')

        # Log in as sales user to verify Sales Hub
        page.fill('input[type="text"]', 'sales')
        page.fill('input[type="password"]', 'password')
        page.click('button[type="submit"]')

        # Go to Sales Hub page
        page.click('a:has-text("Sales Hub")')
        page.wait_for_selector('text="Sales Hub"')

        # Take screenshot of Sales Hub page for sales user
        page.screenshot(path='sales_hub.png')

        # Log out
        page.goto('http://localhost:5000')
        page.evaluate('localStorage.removeItem("userRole")')
        page.evaluate('localStorage.removeItem("username")')
        page.evaluate('localStorage.removeItem("userId")')
        page.goto('http://localhost:5000')

        # Log in as manager user to verify Team Mgmt page
        page.fill('input[type="text"]', 'manager')
        page.fill('input[type="password"]', 'password')
        page.click('button[type="submit"]')

        # Go to Team Management page
        page.click('a:has-text("Team Mgmt")')
        page.wait_for_selector('text="Assign User to Location"')

        # Take screenshot of Team Mgmt page for manager user
        page.screenshot(path='team_mgmt.png')

        browser.close()

if __name__ == '__main__':
    verify_frontend()