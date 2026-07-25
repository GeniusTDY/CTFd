from playwright.sync_api import sync_playwright

CTFD_URL = "http://localhost:4000"
MOBILE_VIEWPORT = {"width": 375, "height": 812}  # iPhone X-like


def setup_ctfd(page):
    """首次访问 CTFd 时完成 setup 向导。"""
    page.goto(CTFD_URL + "/setup")
    page.wait_for_load_state("networkidle")

    if "/setup" not in page.url:
        print("Already set up, URL:", page.url)
        return

    # 填写 setup 表单
    page.fill('input[name="ctf_name"]', "Test CTF")
    page.fill('input[name="ctf_description"]', "Test description")
    page.fill('input[name="name"]', "admin")
    page.fill('input[name="email"]', "admin@example.com")
    page.fill('input[name="password"]', "AdminPass123!")
    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")
    print("Setup complete, URL:", page.url)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        ctx = browser.new_context()
        page = ctx.new_page()
        setup_ctfd(page)
        ctx.storage_state(path="/tmp/ctfd_state.json")
        ctx.close()

        mctx = browser.new_context(
            viewport=MOBILE_VIEWPORT,
            storage_state="/tmp/ctfd_state.json",
            user_agent=(
                "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 "
                "Mobile/15E148 Safari/604.1"
            ),
        )
        mpage = mctx.new_page()
        mpage.on("console", lambda msg: print(f"[console.{msg.type}]", msg.text))
        mpage.on("pageerror", lambda err: print("[pageerror]", err))

        mpage.goto(CTFD_URL + "/admin/statistics")
        mpage.wait_for_load_state("networkidle")
        try:
            mpage.wait_for_selector("#matrix-scoreboard tbody tr", timeout=15000)
        except Exception as e:
            print("Wait for matrix rows failed:", e)

        mpage.wait_for_timeout(2000)

        widths = mpage.evaluate(
            """() => {
              const ths = document.querySelectorAll('#matrix-scoreboard thead th');
              const tds = document.querySelectorAll('#matrix-scoreboard tbody tr:first-child td');
              const result = {};
              if (ths.length >= 3) {
                result.place_th = ths[0].getBoundingClientRect().width;
                result.name_th = ths[1].getBoundingClientRect().width;
                result.score_th = ths[2].getBoundingClientRect().width;
              }
              if (tds.length >= 3) {
                result.place_td = tds[0].getBoundingClientRect().width;
                result.name_td = tds[1].getBoundingClientRect().width;
                result.score_td = tds[2].getBoundingClientRect().width;
              }
              const styles = getComputedStyle(document.querySelector('#matrix-scoreboard'));
              result.place_left = styles.getPropertyValue('--matrix-col-place-left');
              result.name_left = styles.getPropertyValue('--matrix-col-name-left');
              result.score_left = styles.getPropertyValue('--matrix-col-score-left');
              result.viewport = window.innerWidth;
              result.media_matches = window.matchMedia('(max-width: 767.98px)').matches;
              return result;
            }"""
        )
        print("=== Measurement Results ===")
        for k, v in widths.items():
            print(f"  {k}: {v}")

        mpage.screenshot(path="/tmp/admin_statistics_mobile.png", full_page=True)
        print("Screenshot saved: /tmp/admin_statistics_mobile.png")

        mctx.close()
        browser.close()


if __name__ == "__main__":
    main()
