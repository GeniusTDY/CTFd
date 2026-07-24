from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8000"
OUT = "/workspace"


def login(page):
    page.goto(f"{BASE}/login")
    page.wait_for_load_state("networkidle")
    page.fill("input[name='name']", "admin")
    page.fill("input[name='password']", "Admin@12345")
    page.locator("input[name='password']").press("Enter")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(800)


def open_theme_tab(page):
    page.goto(f"{BASE}/admin/config")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(500)
    page.locator("a[href='#theme']").first.click()
    page.wait_for_timeout(600)


def measure(page, label):
    picker = page.locator("#config-color-picker")
    button = page.locator("#config-color-update")
    actions = page.locator(".color-picker-actions")
    p_box = picker.bounding_box()
    b_box = button.bounding_box()
    a_box = actions.bounding_box()
    print(f"[{label}] picker: x={p_box['x']:.0f} y={p_box['y']:.0f} w={p_box['width']:.0f} h={p_box['height']:.0f}")
    print(f"[{label}] button: x={b_box['x']:.0f} y={b_box['y']:.0f} w={b_box['width']:.0f} h={b_box['height']:.0f}")
    print(f"[{label}] actions: x={a_box['x']:.0f} y={a_box['y']:.0f} w={a_box['width']:.0f} h={a_box['height']:.0f}")
    same_row = abs(p_box["y"] - b_box["y"]) <= 2
    height_diff = abs(p_box["height"] - b_box["height"])
    print(f"[{label}] same row (y within 2px): {same_row}")
    print(f"[{label}] height difference: {height_diff:.1f}px")
    return same_row, height_diff


def clip_row(page, name):
    p_box = page.locator("#config-color-picker").bounding_box()
    b_box = page.locator("#config-color-update").bounding_box()
    x0 = min(p_box["x"], b_box["x"]) - 12
    y0 = min(p_box["y"], b_box["y"]) - 12
    x1 = max(p_box["x"] + p_box["width"], b_box["x"] + b_box["width"]) + 12
    y1 = max(p_box["y"] + p_box["height"], b_box["y"] + b_box["height"]) + 12
    page.screenshot(
        path=f"{OUT}/{name}",
        clip={"x": x0, "y": y0, "width": x1 - x0, "height": y1 - y0},
    )


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        ctx_m = browser.new_context(viewport={"width": 375, "height": 812})
        page_m = ctx_m.new_page()
        login(page_m)
        open_theme_tab(page_m)
        page_m.locator("#config-color-picker").evaluate(
            "el => el.closest('.form-group').scrollIntoView({block:'center'})"
        )
        page_m.wait_for_timeout(200)
        page_m.screenshot(path=f"{OUT}/mobile_full.png", full_page=False)
        clip_row(page_m, "mobile_picker_row.png")
        print("=== MOBILE (375x812) ===")
        m_same_row, m_hdiff = measure(page_m, "mobile")

        ctx_d = browser.new_context(viewport={"width": 1280, "height": 800})
        page_d = ctx_d.new_page()
        login(page_d)
        open_theme_tab(page_d)
        page_d.locator("#config-color-picker").evaluate(
            "el => el.closest('.form-group').scrollIntoView({block:'center'})"
        )
        page_d.wait_for_timeout(200)
        clip_row(page_d, "desktop_picker_row.png")
        print("=== DESKTOP (1280x800) ===")
        d_same_row, d_hdiff = measure(page_d, "desktop")

        print("\n=== SUMMARY ===")
        print(f"mobile:  same_row={m_same_row} height_diff={m_hdiff:.1f}px")
        print(f"desktop: same_row={d_same_row} height_diff={d_hdiff:.1f}px")
        browser.close()


if __name__ == "__main__":
    main()
