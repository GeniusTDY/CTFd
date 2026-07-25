from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:4000"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    # Mobile viewport (iPhone SE-like)
    context = browser.new_context(
        viewport={"width": 375, "height": 667},
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15",
    )
    page = context.new_page()

    # Login
    page.goto(f"{BASE}/login")
    page.fill('input[name="name"]', "admin")
    page.fill('input[name="password"]', "Admin@12345")
    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")

    # Go to statistics
    page.goto(f"{BASE}/admin/statistics")
    page.wait_for_load_state("networkidle")
    # Wait for the matrix table to render (Vue loads it async)
    page.wait_for_selector("#matrix-scoreboard thead tr th", timeout=15000)
    page.wait_for_timeout(2000)  # let recomputeStickyOffsets run

    # Read the 3 header cells' rendered widths
    widths = page.evaluate("""() => {
      const ths = document.querySelectorAll('#matrix-scoreboard thead tr:first-child th');
      return Array.from(ths).slice(0, 3).map(th => ({
        text: th.textContent.trim().split('\\n')[0],
        width: Math.round(th.getBoundingClientRect().width),
        left: th.style.left || getComputedStyle(th).left,
        minWidth: getComputedStyle(th).minWidth,
        maxWidth: getComputedStyle(th).maxWidth,
      }));
    }""")
    print("MOBILE (375px) - Place/Team/Score column widths:")
    for w in widths:
        print(f"  {w['text']!r}: width={w['width']}px, left={w['left']}, min={w['minWidth']}, max={w['maxWidth']}")

    # Screenshot the matrix area
    page.screenshot(path="/tmp/stats_mobile.png", full_page=False)
    print("\nScreenshot saved to /tmp/stats_mobile.png")

    # Also test desktop to confirm no regression
    context2 = browser.new_context(viewport={"width": 1280, "height": 800})
    page2 = context2.new_page()
    page2.goto(f"{BASE}/login")
    page2.fill('input[name="name"]', "admin")
    page2.fill('input[name="password"]', "Admin@12345")
    page2.click('button[type="submit"]')
    page2.wait_for_load_state("networkidle")
    page2.goto(f"{BASE}/admin/statistics")
    page2.wait_for_load_state("networkidle")
    page2.wait_for_selector("#matrix-scoreboard thead tr th", timeout=15000)
    page2.wait_for_timeout(1000)
    widths_d = page2.evaluate("""() => {
      const ths = document.querySelectorAll('#matrix-scoreboard thead tr:first-child th');
      return Array.from(ths).slice(0, 3).map(th => ({
        text: th.textContent.trim().split('\\n')[0],
        width: Math.round(th.getBoundingClientRect().width),
      }));
    }""")
    print("\nDESKTOP (1280px) - Place/Team/Score column widths:")
    for w in widths_d:
        print(f"  {w['text']!r}: width={w['width']}px")

    browser.close()
