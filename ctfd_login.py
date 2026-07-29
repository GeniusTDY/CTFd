from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(locale='zh-CN')
    page = context.new_page()

    # Navigate to login page
    page.goto('http://localhost:4000/login')
    page.wait_for_load_state('networkidle')
    page.screenshot(path='/tmp/login_page.png', full_page=True)
    print("Login page screenshot saved")

    # Fill login form
    page.fill('input[name="name"]', 'admin')
    page.fill('input[name="password"]', 'admin')
    page.screenshot(path='/tmp/login_filled.png', full_page=True)
    print("Login form filled")

    # Submit form
    page.click('button[type="submit"], #_submit, button:not([type="button"])')
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(2000)

    # Screenshot after login
    page.screenshot(path='/tmp/home_page.png', full_page=True)
    print(f"After login URL: {page.url}")
    print("Home page screenshot saved")

    # Navigate to challenges
    page.goto('http://localhost:4000/challenges')
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(2000)
    page.screenshot(path='/tmp/challenges_page.png', full_page=True)
    print(f"Challenges URL: {page.url}")
    print("Challenges page screenshot saved")

    # Navigate to scoreboard
    page.goto('http://localhost:4000/scoreboard')
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(2000)
    page.screenshot(path='/tmp/scoreboard_page.png', full_page=True)
    print(f"Scoreboard URL: {page.url}")

    # Navigate to remote desktop dashboard
    page.goto('http://localhost:4000/remote-desktop/dashboard')
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(2000)
    page.screenshot(path='/tmp/remote_desktop_dashboard.png', full_page=True)
    print(f"Remote Desktop Dashboard URL: {page.url}")

    browser.close()
    print("Done!")
