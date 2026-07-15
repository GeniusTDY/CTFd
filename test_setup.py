from playwright.sync_api import sync_playwright
import os

# Ensure the test database is clean
os.system("rm -f /workspace/CTFd/ctfd.db && fuser -k 4000/tcp 2>/dev/null; sleep 1")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    # Navigate to setup page
    page.goto('http://127.0.0.1:4000/setup')
    page.wait_for_load_state('networkidle')
    
    # Take initial screenshot
    page.screenshot(path='/tmp/setup_initial.png', full_page=True)
    print("Initial screenshot saved")
    
    # Check the form HTML for required attributes
    form_html = page.locator('#setup-form').inner_html()
    required_count = form_html.count('required')
    novalidate = 'novalidate' in page.locator('#setup-form').get_attribute('outer_html') or ''
    print(f"Form has 'required' attribute count: {required_count}")
    print(f"Form has 'novalidate': {novalidate}")
    
    # Check if required fields are visible
    name_visible = page.locator('input[name="name"]').is_visible()
    email_visible = page.locator('input[name="email"]').is_visible()
    password_visible = page.locator('input[name="password"]').is_visible()
    print(f"Name field visible: {name_visible}")
    print(f"Email field visible: {email_visible}")
    print(f"Password field visible: {password_visible}")
    
    # Check which tab is active
    active_tab = page.locator('.tab-pane.active').get_attribute('id')
    print(f"Active tab: {active_tab}")
    
    # Check if the fields are in a hidden container
    admin_tab = page.locator('#administration')
    admin_display = admin_tab.evaluate("el => window.getComputedStyle(el).display")
    print(f"Administration tab display: {admin_display}")
    
    # Try to click submit directly and check for validation
    print("\n=== Attempting to submit empty form ===")
    page.locator('#_submit').click(force=True)
    page.wait_for_timeout(1000)
    
    # Take screenshot after submit attempt
    page.screenshot(path='/tmp/setup_after_submit.png', full_page=True)
    print("After-submit screenshot saved")
    
    # Check page URL to see if form was submitted
    current_url = page.url
    print(f"Current URL after submit: {current_url}")
    
    # Check for validation message
    try:
        # Try to get validation message via JS
        name_validity = page.locator('input[name="name"]').evaluate("el => el.validity.valid")
        email_validity = page.locator('input[name="email"]').evaluate("el => el.validity.valid")
        password_validity = page.locator('input[name="password"]').evaluate("el => el.validity.valid")
        print(f"Name valid: {name_validity}")
        print(f"Email valid: {email_validity}")
        print(f"Password valid: {password_validity}")
        
        name_msg = page.locator('input[name="name"]').evaluate("el => el.validationMessage")
        print(f"Name validation message: '{name_msg}'")
    except Exception as e:
        print(f"Error checking validity: {e}")
    
    # Check if form was actually submitted (URL changed)
    if '/setup' not in current_url:
        print("Form was SUBMITTED - browser validation was BYPASSED")
    else:
        print("Form was NOT submitted - still on setup page")
    
    browser.close()