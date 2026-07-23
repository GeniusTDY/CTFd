from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    # Go to setup page
    page.goto('http://127.0.0.1:4000/setup')
    page.wait_for_load_state('networkidle')
    page.screenshot(path='/workspace/setup_page.png', full_page=True)

    # Fill setup form
    page.fill('input[name="ctf_name"]', 'TestCTF')
    page.fill('input[name="ctf_description"]', 'Test')
    page.fill('input[name="name"]', 'admin')
    page.fill('input[name="email"]', 'admin@test.com')
    page.fill('input[name="password"]', 'admin123456')
    page.fill('input[name="nonce"]', 'admin123456')

    # Submit
    page.click('button[type="submit"]')
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(3000)

    # Now go to admin statistics page
    page.goto('http://127.0.0.1:4000/admin/statistics')
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(5000)

    # Take full page screenshot (desktop)
    page.screenshot(path='/workspace/stats_desktop.png', full_page=True)

    # Take mobile screenshot
    mobile_page = browser.new_page(viewport={'width': 375, 'height': 812})
    mobile_page.goto('http://127.0.0.1:4000/admin/statistics')
    mobile_page.wait_for_load_state('networkidle')
    mobile_page.wait_for_timeout(5000)
    mobile_page.screenshot(path='/workspace/stats_mobile.png', full_page=True)

    browser.close()
    print("Done")
