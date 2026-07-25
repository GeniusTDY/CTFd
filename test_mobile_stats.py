from playwright.sync_api import sync_playwright
import re

BASE = "http://127.0.0.1:8000"

def login(page):
    page.goto(f"{BASE}/login", wait_until="domcontentloaded")
    page.fill('input[name="name"]', "admin")
    page.fill('input[name="password"]', "password123")
    page.click('.btn-primary')
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(1500)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    for name, width, height in [
        ("iphone-se-375", 375, 667),
        ("iphone-12-390", 390, 844),
        ("small-360", 360, 640),
    ]:
        context = browser.new_context(
            viewport={"width": width, "height": height},
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
        )
        page = context.new_page()
        login(page)
        page.goto(f"{BASE}/admin/statistics", wait_until="domcontentloaded")
        page.wait_for_timeout(5000)

        page.screenshot(path=f"/tmp/stats_mobile_{name}_full.png", full_page=True)
        page.screenshot(path=f"/tmp/stats_mobile_{name}_top.png", full_page=False)

        info = page.evaluate("""() => {
            const out = {};
            const j = document.querySelector('.jumbotron');
            if (j) { const r=j.getBoundingClientRect(); const cs=getComputedStyle(j);
                out.jumbotron={h:r.height, padding:cs.paddingTop+' '+cs.paddingBottom};
                const h1=j.querySelector('h1');
                if(h1) out.h1={fontSize:getComputedStyle(h1).fontSize, letterSpacing:getComputedStyle(h1).letterSpacing};
            }
            const sc=document.querySelector('.stats-counters');
            if(sc){ const cs=getComputedStyle(sc);
                out.counters={gap:cs.rowGap+' / '+cs.columnGap, display:cs.display};
                const first=sc.querySelector('div');
                if(first) out.firstItem={ml:getComputedStyle(first).marginLeft, mr:getComputedStyle(first).marginRight};
                const h5=sc.querySelector('h5');
                if(h5) out.h5={fontSize:getComputedStyle(h5).fontSize, whiteSpace:getComputedStyle(h5).whiteSpace};
            }
            const sh=document.querySelector('.stats-highlights');
            if(sh){ const cs=getComputedStyle(sh); out.highlights={gap:cs.rowGap+' / '+cs.columnGap}; }
            // measure how many counters per row (top row width)
            if(sc){
                const items=sc.querySelectorAll('div');
                const rows={};
                items.forEach(it=>{const t=Math.round(it.getBoundingClientRect().top); rows[t]=(rows[t]||0)+1;});
                out.itemsPerRow=Object.values(rows);
                out.itemCount=items.length;
            }
            const solvesG=document.querySelector('#solves-graph');
            if(solvesG) out.solvesGraphH=getComputedStyle(solvesG).height;
            const pie=document.querySelector('#keys-pie-graph');
            if(pie) out.pieMinH=getComputedStyle(pie).minHeight;
            const fc=document.querySelector('.filter-col');
            if(fc) out.filterColH=getComputedStyle(fc).height;
            const cn=document.querySelector('.sticky-col-name');
            if(cn) out.stickyNameW=getComputedStyle(cn).width;
            out.hasHScroll=document.body.scrollWidth>window.innerWidth;
            out.scrollW=document.body.scrollWidth;
            out.innerW=window.innerWidth;
            return out;
        }""")
        print(f"=== {name} ({width}x{height}) ===")
        for k,v in info.items():
            print(f"  {k}: {v}")
        context.close()

    # Desktop comparison
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    page = context.new_page()
    login(page)
    page.goto(f"{BASE}/admin/statistics", wait_until="domcontentloaded")
    page.wait_for_timeout(5000)
    page.screenshot(path="/tmp/stats_desktop_full.png", full_page=True)
    page.screenshot(path="/tmp/stats_desktop_top.png", full_page=False)
    info = page.evaluate("""() => {
        const sc=document.querySelector('.stats-counters');
        const first=sc.querySelector('div');
        return {firstItemML:getComputedStyle(first).marginLeft, h5FS:getComputedStyle(sc.querySelector('h5')).fontSize};
    }""")
    print("=== desktop ===")
    print("  ", info)

    browser.close()
    print("\nDone. Screenshots in /tmp/stats_*.png")
