from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    # 移动端视口（iPhone SE 宽度 375px，触发 < 767.98px 的移动端样式）
    context = browser.new_context(
        viewport={"width": 375, "height": 667},
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15",
    )
    page = context.new_page()

    # 登录
    page.goto("http://127.0.0.1:4000/login", wait_until="networkidle")
    page.fill('input[name="name"]', "root")
    page.fill('input[name="password"]', "Admin@12345")
    page.click('button[type="submit"], input[type="submit"]')
    page.wait_for_load_state("networkidle")

    # 访问 admin 配置页
    page.goto("http://127.0.0.1:4000/admin/config", wait_until="networkidle")
    try:
        page.click('a[href="#email"]', timeout=5000)
        page.wait_for_timeout(800)
    except Exception as e:
        print("click #email warning:", e)

    labels = ["Mail Server", "Registration", "Verification", "Account Details", "Password Reset"]
    for lbl in labels:
        count = page.locator(f'a.nav-link:has-text("{lbl}")').count()
        print(f"  tab '{lbl}' count={count}")

    cls = page.locator("ul.email-tabs-nav").count()
    print("email-tabs-nav ul count:", cls)

    box = page.locator("ul.email-tabs-nav").bounding_box()
    print("ul.email-tabs-nav bbox:", box)

    items = page.locator("ul.email-tabs-nav > li").all()
    print("nav-item count:", len(items))
    total_w = 0
    for it in items:
        b = it.bounding_box()
        total_w += b["width"] if b else 0
    print(f"sum of nav-item widths: {total_w:.1f}px (viewport width: 375px)")

    page.screenshot(path="/workspace/CTFd/logs/email_tabs_mobile.png", full_page=False)
    page.screenshot(path="/workspace/CTFd/logs/email_tabs_mobile_full.png", full_page=True)
    print("screenshots saved")

    browser.close()
