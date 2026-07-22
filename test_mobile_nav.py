from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    # Simulate iPhone 12
    context = browser.new_context(
        viewport={'width': 390, 'height': 844},
        user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1'
    )
    page = context.new_page()
    page.goto('http://localhost:4000/')
    page.wait_for_load_state('networkidle')

    # Take screenshot of the page
    page.screenshot(path='/tmp/mobile_nav.png', full_page=False)

    # Inspect navbar-collapse computed styles
    styles = page.evaluate('''() => {
        var el = document.querySelector('.navbar-collapse');
        if (!el) return null;
        var cs = window.getComputedStyle(el);
        return {
            className: el.className,
            overflowX: cs.overflowX,
            overflowY: cs.overflowY,
            display: cs.display,
            flexWrap: cs.flexWrap,
            width: cs.width,
            scrollWidth: el.scrollWidth,
            clientWidth: el.clientWidth,
            scrollable: el.scrollWidth > el.clientWidth,
            navbarClass: document.querySelector('.navbar') ? document.querySelector('.navbar').className : null,
            bodyPadding: window.getComputedStyle(document.body).paddingTop,
        };
    }''')
    print('navbar-collapse styles:', styles)

    # Also check .navbar
    navbar_styles = page.evaluate('''() => {
        var el = document.querySelector('.navbar');
        if (!el) return null;
        var cs = window.getComputedStyle(el);
        return {
            overflow: cs.overflow,
            overflowX: cs.overflowX,
            display: cs.display,
            flexWrap: cs.flexWrap,
            width: cs.width,
        };
    }''')
    print('navbar styles:', navbar_styles)

    # Check .container inside navbar
    container_styles = page.evaluate('''() => {
        var el = document.querySelector('.navbar .container');
        if (!el) return null;
        var cs = window.getComputedStyle(el);
        return {
            overflow: cs.overflow,
            overflowX: cs.overflowX,
            display: cs.display,
            flexWrap: cs.flexWrap,
            width: cs.width,
            maxWidth: cs.maxWidth,
        };
    }''')
    print('container styles:', container_styles)

    # Check if navbar-toggler is visible (mobile menu)
    toggler = page.evaluate('''() => {
        var el = document.querySelector('.navbar-toggler');
        if (!el) return null;
        var cs = window.getComputedStyle(el);
        return { display: cs.display, visibility: cs.visibility };
    }''')
    print('toggler:', toggler)

    # List all nav-items
    nav_items = page.evaluate('''() => {
        var items = document.querySelectorAll('.navbar-nav .nav-item');
        return Array.from(items).map(function(el) {
            var cs = window.getComputedStyle(el);
            return {
                text: el.textContent.trim().substring(0, 30),
                display: cs.display,
                visibility: cs.visibility,
                opacity: cs.opacity,
                rect: el.getBoundingClientRect(),
            };
        });
    }''')
    print('nav-items:', nav_items)

    browser.close()
