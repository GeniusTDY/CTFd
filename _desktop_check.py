from playwright.sync_api import sync_playwright
import requests
import re
from PIL import Image
import numpy as np

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
    d_context = browser.new_context(viewport={'width': 1280, 'height': 800})
    d_context.add_cookies([{'name': 'session', 'value': session_cookie, 'domain': 'localhost', 'path': '/'}])
    d_page = d_context.new_page()
    d_page.goto('http://localhost:4000/admin/statistics', wait_until='domcontentloaded')
    d_page.wait_for_timeout(10000)

    # 1. 检查 ECharts option
    opt_info = d_page.evaluate('''async () => {
        const mod = await import('/themes/admin/static/assets/echarts.common-B4cbpQlJ.js');
        const echarts = mod.e;
        const out = {};
        for (const sel of ['#keys-pie-graph', '#categories-pie-graph', '#points-pie-graph']) {
            const el = document.querySelector(sel);
            const inst = echarts.getInstanceByDom(el);
            const opt = inst.getOption();
            out[sel] = {
                legend_top: opt.legend[0].top,
                legend_orient: opt.legend[0].orient,
                series_center: opt.series[0].center,
                series_radius: opt.series[0].radius
            };
        }
        return out;
    }''')

    # 2. 获取所有相关元素的 bounding box
    boxes = {}
    for sel in ['#keys-pie-graph', '#categories-pie-graph', '#points-pie-graph', '.submission-counts']:
        el = d_page.query_selector(sel)
        if el:
            boxes[sel] = el.bounding_box()

    # 3. 检查 .submission-counts 是否有 position:relative 和 top 偏移
    sub_style = d_page.evaluate('''() => {
        const el = document.querySelector('.submission-counts');
        if (!el) return null;
        const cs = window.getComputedStyle(el);
        const cat = document.querySelector('#categories-pie-graph');
        const cat_cs = cat ? window.getComputedStyle(cat) : null;
        return {
            submission_counts: {
                position: cs.position,
                top: cs.top,
                display: cs.display,
                marginTop: cs.marginTop
            },
            categories_pie: cat_cs ? {
                marginTop: cat_cs.marginTop
            } : null
        };
    }''')

    # 4. 截图
    d_page.screenshot(path='/workspace/_desktop_check.png', full_page=True)
    d_context.close()
    browser.close()

print("=" * 70)
print("桌面端验证 (视口 1280×800)")
print("=" * 70)

print("\n[1] ECharts 配置（应与原始一致）:")
for sel, info in opt_info.items():
    print(f"  {sel}:")
    print(f"    legend: orient={info['legend_orient']}, top={info['legend_top']}")
    print(f"    series: center={info['series_center']}, radius={info['series_radius']}")

print("\n[2] 元素 bounding box:")
for sel, box in boxes.items():
    print(f"  {sel}: x={box['x']:.1f}, y={box['y']:.1f}, w={box['width']:.1f}, h={box['height']:.1f}")

# 验证三个图表是否在同一行（桌面端 col-md-4 布局）
keys_box = boxes.get('#keys-pie-graph')
cat_box = boxes.get('#categories-pie-graph')
pt_box = boxes.get('#points-pie-graph')
if keys_box and cat_box and pt_box:
    print("\n[3] 三个图表同行验证:")
    print(f"  提交百分比 y={keys_box['y']:.1f}")
    print(f"  分类细分   y={cat_box['y']:.1f}")
    print(f"  积分细分   y={pt_box['y']:.1f}")
    same_row = abs(keys_box['y'] - cat_box['y']) < 5 and abs(cat_box['y'] - pt_box['y']) < 5
    print(f"  同行: {'是 ✓' if same_row else '否 ✗'}")

    # 水平间距
    print(f"\n[4] 水平间距:")
    print(f"  提交百分比 right={keys_box['x']+keys_box['width']:.1f} → 分类细分 left={cat_box['x']:.1f} = {cat_box['x']-(keys_box['x']+keys_box['width']):.1f}px")
    print(f"  分类细分   right={cat_box['x']+cat_box['width']:.1f} → 积分细分 left={pt_box['x']:.1f} = {pt_box['x']-(cat_box['x']+cat_box['width']):.1f}px")

print("\n[5] CSS 样式（桌面端应为默认值）:")
if sub_style:
    sc = sub_style['submission_counts']
    print(f"  .submission-counts: position={sc['position']}, top={sc['top']}, display={sc['display']}, margin-top={sc['marginTop']}")
    # 桌面端应: position=static, top=auto, display=block
    desktop_ok = sc['position'] == 'static' and sc['top'] == 'auto'
    print(f"  桌面端默认样式: {'正常 ✓' if desktop_ok else '异常 ✗'}")

    cat = sub_style['categories_pie']
    if cat:
        print(f"  #categories-pie-graph: margin-top={cat['marginTop']}")
        # 桌面端 margin-top 应为 0
        cat_ok = cat['marginTop'] == '0px'
        print(f"  分类细分 margin-top: {'正常 ✓ (0px)' if cat_ok else '异常 ✗'}")
