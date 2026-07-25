from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8000"

# CSS that reverts my fix back to the ORIGINAL layout (mx-4 gaps, 400px charts,
# 150px sticky name, 32px jumbotron) so we can screenshot the "before" state
# without rebuilding the project.
REVERT_CSS = """
<style id="revert-fix">
.jumbotron { padding: 2rem 1rem !important; margin-bottom: 2rem !important; }
.jumbotron h1 { font-size: 2.5rem !important; letter-spacing: 2px !important; }
.stats-counters { row-gap: 0 !important; column-gap: 0 !important; }
.stats-counters > div { margin-left: 1.5rem !important; margin-right: 1.5rem !important; }
.stats-counters h5 { font-size: 1.25rem !important; white-space: normal !important; }
.stats-highlights { row-gap: 0 !important; column-gap: 0 !important; }
.stats-highlights > div { margin-left: 1.5rem !important; margin-right: 1.5rem !important; }
#solves-graph { height: 350px !important; }
#keys-pie-graph, #categories-pie-graph, #points-pie-graph,
#solve-percentages-graph, #score-distribution-graph { min-height: 400px !important; }
.filter-col { height: 400px !important; }
.sticky-col-place { left: 0 !important; min-width: 50px !important; max-width: 50px !important; }
.sticky-col-name { left: 50px !important; min-width: 150px !important; max-width: 150px !important; }
.sticky-col-score { left: 200px !important; min-width: 80px !important; max-width: 80px !important; }
#matrix-scoreboard { font-size: 11px !important; }
</style>
"""

def login(page):
    page.goto(f"{BASE}/login", wait_until="domcontentloaded")
    page.fill('input[name="name"]', "admin")
    page.fill('input[name="password"]', "password123")
    page.click('.btn-primary')
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(1500)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    # iPhone SE 375px - the most common small mobile
    context = browser.new_context(
        viewport={"width": 375, "height": 667},
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
    )
    page = context.new_page()
    login(page)
    page.goto(f"{BASE}/admin/statistics", wait_until="domcontentloaded")
    page.wait_for_timeout(5000)

    # ---- AFTER (with fix) ----
    page.screenshot(path="/tmp/compare_after_top.png", full_page=False)
    page.screenshot(path="/tmp/compare_after_full.png", full_page=True)
    after = page.evaluate("""() => {
        const sc=document.querySelector('.stats-counters');
        const items=sc.querySelectorAll('div');
        const rows={};
        items.forEach(it=>{const t=Math.round(it.getBoundingClientRect().top); rows[t]=(rows[t]||0)+1;});
        return {itemsPerRow:Object.values(rows), scrollW:document.body.scrollWidth, innerW:window.innerWidth};
    }""")

    # ---- BEFORE (revert fix via injected CSS) ----
    page.evaluate(f'() => document.head.insertAdjacentHTML("beforeend", {REVERT_CSS!r})')
    page.wait_for_timeout(800)
    page.screenshot(path="/tmp/compare_before_top.png", full_page=False)
    page.screenshot(path="/tmp/compare_before_full.png", full_page=True)
    before = page.evaluate("""() => {
        const sc=document.querySelector('.stats-counters');
        const items=sc.querySelectorAll('div');
        const rows={};
        items.forEach(it=>{const t=Math.round(it.getBoundingClientRect().top); rows[t]=(rows[t]||0)+1;});
        return {itemsPerRow:Object.values(rows), scrollW:document.body.scrollWidth, innerW:window.innerWidth};
    }""")

    print("BEFORE (original layout, 375px):")
    print("  ", before)
    print("AFTER (with fix, 375px):")
    print("  ", after)
    browser.close()
    print("\nScreenshots: /tmp/compare_before_*.png and /tmp/compare_after_*.png")
