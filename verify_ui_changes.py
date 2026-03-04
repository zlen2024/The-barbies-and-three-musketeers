import time
from playwright.sync_api import sync_playwright

def verify_frontend():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        # Start at login
        page.goto('http://localhost:5000')

        # Log in as warehouse user to verify Dashboard PR button
        page.fill('input[type="text"]', 'warehouse')
        page.fill('input[type="password"]', 'password')
        page.click('button[type="submit"]')

        # Wait for dashboard to load
        page.wait_for_selector('text="Procurement & Pricing Intelligence"')

        # Take screenshot of Dashboard for warehouse user
        page.screenshot(path='warehouse_dashboard.png')

        # Log out
        page.click('button:has-text("warehouse")')
        page.click('button:has-text("Logout")')

        # Log in as manager user to verify Suppliers page
        page.fill('input[type="text"]', 'manager')
        page.fill('input[type="password"]', 'password')
        page.click('button[type="submit"]')

        # Go to suppliers page
        page.click('a:has-text("Suppliers")')
        page.wait_for_selector('text="Manage your vendors and suppliers."')

        # Take screenshot of Suppliers page for manager user
        page.screenshot(path='manager_suppliers.png')

        # Log out
        page.click('button:has-text("manager")')
        page.click('button:has-text("Logout")')

        # Log in as staff user to verify Suppliers page
        page.fill('input[type="text"]', 'admin')
        page.fill('input[type="password"]', 'password')
        page.click('button[type="submit"]')

        # Go to suppliers page
        page.click('a:has-text("Suppliers")')
        page.wait_for_selector('text="Manage your vendors and suppliers."')

        # Take screenshot of Suppliers page for staff user
        page.screenshot(path='staff_suppliers.png')

        browser.close()

if __name__ == '__main__':
    verify_frontend()
