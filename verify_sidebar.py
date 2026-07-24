from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    # Login to admin panel
    page.goto('http://localhost:8000/login')
    page.wait_for_load_state('networkidle')

    # Fill login form
    page.fill('input[name=name]', 'admin')
    page.fill('input[name=password]', 'password')
    page.click('button[type=submit]')
    page.wait_for_load_state('networkidle')

    # Go to admin panel
    page.goto('http://localhost:8000/admin')
    page.wait_for_load_state('networkidle')

    # Take screenshot of the admin sidebar
    page.screenshot(path='/workspace/admin_sidebar.png', full_page=True)

    # Check the dropdown menus in the navbar
    dropdowns = page.locator('.navbar-nav .dropdown-toggle').all()
    print(f"Found {len(dropdowns)} dropdown toggles:")
    for d in dropdowns:
        print(f"  - {d.inner_text().strip()}")

    # Check for specific menu items
    menu_items = page.locator('.navbar-nav .dropdown-item').all()
    print(f"\nFound {len(menu_items)} dropdown items:")
    for item in menu_items:
        text = item.inner_text().strip()
        href = item.get_attribute('href') or ''
        print(f"  - {text} -> {href}")

    browser.close()
