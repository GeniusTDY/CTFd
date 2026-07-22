from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    # Mobile viewport
    context = browser.new_context(
        viewport={'width': 375, 'height': 667},
        user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15'
    )
    page = context.new_page()

    # Go to admin panel
    page.goto('http://localhost:4000/admin')
    page.wait_for_load_state('networkidle')

    # Take screenshot of initial state
    page.screenshot(path='/workspace/test_screenshots/admin_mobile_initial.png', full_page=True)

    # Click the navbar toggler to expand the sidebar
    toggler = page.locator('.navbar-toggler')
    if toggler.count() > 0:
        toggler.first.click()
        page.wait_for_timeout(500)

    # Take screenshot after expanding navbar
    page.screenshot(path='/workspace/test_screenshots/admin_mobile_navbar_expanded.png', full_page=True)

    # Click the language dropdown toggle
    lang_toggle = page.locator('.navbar-right .dropdown-toggle')
    if lang_toggle.count() > 0:
        lang_toggle.first.click()
        page.wait_for_timeout(500)

        # Take screenshot of the dropdown
        page.screenshot(path='/workspace/test_screenshots/admin_mobile_lang_dropdown.png', full_page=True)

        # Check the dropdown menu position
        dropdown_menu = page.locator('.navbar-right .dropdown-menu')
        if dropdown_menu.count() > 0:
            box = dropdown_menu.first.bounding_box()
            viewport_height = 667
            print(f"Dropdown menu box: {box}")
            if box:
                bottom = box['y'] + box['height']
                print(f"Dropdown bottom: {bottom}, viewport height: {viewport_height}")
                if bottom > viewport_height:
                    print(f"ISSUE: Dropdown extends {bottom - viewport_height}px beyond viewport!")
                else:
                    print("OK: Dropdown fits within viewport")

            # Check if all language items are visible
            items = page.locator('.navbar-right .dropdown-menu .dropdown-item')
            print(f"Total language items: {items.count()}")
            for i in range(items.count()):
                item_box = items.nth(i).bounding_box()
                if item_box:
                    item_bottom = item_box['y'] + item_box['height']
                    visible = item_bottom <= viewport_height
                    print(f"  Item {i}: y={item_box['y']:.0f}, bottom={item_bottom:.0f}, visible={visible}")
        else:
            print("No dropdown menu found")
    else:
        print("No language toggle found")

    browser.close()
