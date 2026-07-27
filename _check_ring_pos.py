from playwright.sync_api import sync_playwright
import requests
import re

s = requests.Session()
r = s.get('http://localhost:4000/login')
nonce_match = re.search(r'value="([a-f0-9]{64})"', r.text)
nonce = nonce_match.group(1) if nonce_match else ''
data = {'nonce': nonce, 'name': 'root', 'password': 'root'}
r = s.post('http://localhost:4000/login', data=data, allow_redirects=False)
session_cookie = s.cookies.get('session')

CHROME_PATH = "/root/.cache/ms-playwright/chromium-1187/chrome-linux/chrome"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, executable_path=CHROME_PATH)
    m_context = browser.new_context(viewport={'width': 375, 'height': 667}, device_scale_factor=2)
    m_context.add_cookies([{'name': 'session', 'value': session_cookie, 'domain': 'localhost', 'path': '/'}])
    m_page = m_context.new_page()
    m_page.goto('http://localhost:4000/admin/statistics', wait_until='domcontentloaded')
    m_page.wait_for_timeout(8000)

    info = m_page.evaluate('''async () => {
        const mod = await import('/themes/admin/static/assets/echarts.common-B4cbpQlJ.js');
        const echarts = mod.e;
        const out = {};
        for (const sel of ['#keys-pie-graph', '#categories-pie-graph', '#points-pie-graph']) {
            const el = document.querySelector(sel);
            const inst = echarts.getInstanceByDom(el);
            const opt = inst.getOption();

            // 通过 model 获取实际渲染的环形图位置
            // 获取 chart 实例的内部坐标信息
            const width = el.offsetWidth;
            const height = el.offsetHeight;

            // series.center ["50%", "42.06%"]
            // series.radius ["30%", "50%"]
            const center = opt.series[0].center;
            const radius = opt.series[0].radius;

            // 半径相对短边
            const minDim = Math.min(width, height);
            const outerR = parseFloat(radius[1]) / 100 * minDim;
            const innerR = parseFloat(radius[0]) / 100 * minDim;

            // center 实际坐标
            const cx = parseFloat(center[0]) / 100 * width;
            const cy = parseFloat(center[1]) / 100 * height;

            // 标题位置（title.text）
            // ECharts title 默认 padding 5px, 顶部对齐 left:center
            // 实际 title 顶部位置: padding (5px), title height 约 22px (font-size 14px + line-height)
            // 标题底部 = 5(padding) + ~17(text) = ~22

            out[sel] = {
                container: {w: width, h: height},
                center_pct: center,
                radius_pct: radius,
                center_actual: {x: cx, y: cy},
                outer_r: outerR,
                inner_r: innerR,
                ring_top: cy - outerR,
                ring_bottom: cy + outerR,
                ring_height: outerR * 2,
                legend_top: opt.legend[0].top,
                legend_orient: opt.legend[0].orient,
                legend_data: opt.legend[0].data
            };
        }
        return out;
    }''')

    m_context.close()
    browser.close()

print("=" * 80)
print("ECharts 实际渲染位置 (基于 API 计算, CSS px)")
print("=" * 80)
for sel, d in info.items():
    print(f"\n{sel}:")
    print(f"  容器: {d['container']['w']}x{d['container']['h']}")
    print(f"  center(实际): ({d['center_actual']['x']:.1f}, {d['center_actual']['y']:.1f})")
    print(f"  outerR: {d['outer_r']:.1f}, innerR: {d['inner_r']:.1f}")
    print(f"  环形图: top={d['ring_top']:.1f}, bottom={d['ring_bottom']:.1f}, height={d['ring_height']:.1f}")
    print(f"  legend: orient={d['legend_orient']}, top={d['legend_top']}")
    print(f"  legend_data: {d['legend_data']}")
