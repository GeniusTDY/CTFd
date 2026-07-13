from playwright.sync_api import sync_playwright
import time

def test_setup():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Collect console errors
        console_errors = []
        page.on("console", lambda msg: 
            console_errors.append(f"[{msg.type}] {msg.text}") if msg.type in ("error", "warning") else None
        )
        page.on("pageerror", lambda err: console_errors.append(f"[PAGE ERROR] {err}"))
        
        # Navigate to setup page
        print("=== Step 1: Initial load ===")
        page.goto('http://127.0.0.1:4000/setup')
        page.wait_for_load_state('networkidle')
        time.sleep(1)
        
        # Check initial state
        general_tab = page.locator('.tab-pane#general')
        print(f"General tab visible: {general_tab.is_visible()}")
        print(f"General tab has 'active' class: {'active' in (general_tab.get_attribute('class') or '')}")
        
        # Try clicking the Next button on general tab
        next_btn = page.locator('.tab-pane#general button[data-href="#mode"]')
        print(f"Next button exists: {next_btn.count() > 0}")
        if next_btn.count() > 0:
            next_btn.click()
            time.sleep(0.5)
            mode_tab = page.locator('.tab-pane#mode')
            print(f"Mode tab visible after click: {mode_tab.is_visible()}")
            print(f"Mode tab has 'active' class: {'active' in (mode_tab.get_attribute('class') or '')}")
        
        print(f"\nConsole errors after initial load: {len(console_errors)}")
        for err in console_errors:
            print(f"  {err}")
        console_errors.clear()
        
        # Switch to English
        print("\n=== Step 2: Switch to English ===")
        # Click language dropdown
        lang_dropdown = page.locator('[data-bs-toggle="dropdown"]').filter(has_text="简体中文")
        if lang_dropdown.count() == 0:
            lang_dropdown = page.locator('.nav-link[data-bs-toggle="dropdown"]')
            print(f"Language dropdown count: {lang_dropdown.count()}")
        if lang_dropdown.count() > 0:
            lang_dropdown.first.click()
            time.sleep(0.3)
            # Click English option
            en_option = page.locator('.dropdown-item[value="en"]')
            print(f"English option count: {en_option.count()}")
            if en_option.count() > 0:
                en_option.first.click()
                time.sleep(2)
                page.wait_for_load_state('networkidle')
                time.sleep(1)
        
        print(f"Current URL: {page.url}")
        print(f"Page title: {page.title()}")
        
        # Check if buttons work in English
        general_tab = page.locator('.tab-pane#general')
        print(f"General tab visible: {general_tab.is_visible()}")
        next_btn = page.locator('.tab-pane#general button[data-href="#mode"]')
        print(f"Next button exists: {next_btn.count() > 0}")
        if next_btn.count() > 0:
            next_btn.click()
            time.sleep(0.5)
            mode_tab = page.locator('.tab-pane#mode')
            print(f"Mode tab visible after click: {mode_tab.is_visible()}")
            print(f"Mode tab has 'active' class: {'active' in (mode_tab.get_attribute('class') or '')}")
        
        print(f"\nConsole errors after English switch: {len(console_errors)}")
        for err in console_errors:
            print(f"  {err}")
        console_errors.clear()
        
        # Switch back to Chinese
        print("\n=== Step 3: Switch back to Chinese ===")
        lang_dropdown = page.locator('[data-bs-toggle="dropdown"]').filter(has_text="English")
        if lang_dropdown.count() == 0:
            lang_dropdown = page.locator('.nav-link[data-bs-toggle="dropdown"]')
            print(f"Language dropdown count: {lang_dropdown.count()}")
        if lang_dropdown.count() > 0:
            lang_dropdown.first.click()
            time.sleep(0.3)
            zh_option = page.locator('.dropdown-item[value="zh_CN"]')
            print(f"Chinese option count: {zh_option.count()}")
            if zh_option.count() > 0:
                zh_option.first.click()
                time.sleep(2)
                page.wait_for_load_state('networkidle')
                time.sleep(1)
        
        print(f"Current URL: {page.url}")
        
        # Check if buttons work after switching back to Chinese
        general_tab = page.locator('.tab-pane#general')
        print(f"General tab visible: {general_tab.is_visible()}")
        print(f"General tab HTML: {general_tab.inner_html()[:200] if general_tab.is_visible() else 'NOT VISIBLE'}")
        
        next_btn = page.locator('.tab-pane#general button[data-href="#mode"]')
        print(f"Next button exists: {next_btn.count() > 0}")
        if next_btn.count() > 0:
            print(f"Next button HTML: {next_btn.first.inner_html()}")
            next_btn.first.click()
            time.sleep(0.5)
            mode_tab = page.locator('.tab-pane#mode')
            print(f"Mode tab visible after click: {mode_tab.is_visible()}")
            print(f"Mode tab has 'active' class: {'active' in (mode_tab.get_attribute('class') or '')}")
        
        print(f"\nConsole errors after Chinese switch: {len(console_errors)}")
        for err in console_errors:
            print(f"  {err}")
        
        # Take screenshot
        page.screenshot(path='/tmp/setup_final.png', full_page=True)
        print("\nScreenshot saved to /tmp/setup_final.png")
        
        browser.close()

if __name__ == "__main__":
    test_setup()