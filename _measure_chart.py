from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 400, "height": 800})
    page.goto('file:///workspace/_measure.html')
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(1000)  # Wait for ECharts to render
    
    output = page.locator('#output').text_content()
    print(output)
    
    browser.close()