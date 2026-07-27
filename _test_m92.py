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
    m_context = browser.new_context(viewport={'width': 375, 'height': 667}, device_scale_factor=2)
    m_context.add_cookies([{'name': 'session', 'value': session_cookie, 'domain': 'localhost', 'path': '/'}])
    m_page = m_context.new_page()
    m_page.goto('http://localhost:4000/admin/statistics', wait_until='domcontentloaded')
    m_page.wait_for_timeout(10000)

    boxes = {}
    for sel in ['#categories-pie-graph', '.submission-counts', '#points-pie-graph']:
        el = m_page.query_selector(sel)
        if el:
            boxes[sel] = el.bounding_box()

    opt_info = m_page.evaluate('''async () => {
        const mod = await import('/themes/admin/static/assets/echarts.common-B4cbpQlJ.js');
        const echarts = mod.e;
        const out = {};
        for (const sel of ['#categories-pie-graph', '#points-pie-graph']) {
            const el = document.querySelector(sel);
            const inst = echarts.getInstanceByDom(el);
            const opt = inst.getOption();
            out[sel] = {legend_top: opt.legend[0].top, center: opt.series[0].center, radius: opt.series[0].radius};
        }
        return out;
    }''')

    m_page.screenshot(path='/workspace/_test_m92.png', full_page=True)
    m_context.close()
    browser.close()

img = Image.open('/workspace/_test_m92.png')
scale = img.size[0] / 375
img_array = np.array(img)

# 1. submission-counts → 分类细分标题 留白
sc_box = boxes['.submission-counts']
cat_box = boxes['#categories-pie-graph']

# 分析分类细分容器内的标题位置
x1 = int(cat_box['x'] * scale)
y1 = int(cat_box['y'] * scale)
x2 = int((cat_box['x'] + cat_box['width']) * scale)
y2 = int((cat_box['y'] + cat_box['height']) * scale)
crop = img_array[y1:y2, x1:x2]
rgb = crop[:, :, :3]
non_white = np.any(rgb < 240, axis=2)
row_counts = np.sum(non_white, axis=1)
sig = np.where(row_counts > 3)[0]
title_top_in_container = sig[0] / scale if len(sig) > 0 else 0

title_top_page = cat_box['y'] + title_top_in_container
sc_bottom = sc_box['y'] + sc_box['height']
gap = title_top_page - sc_bottom

# 2. Legend 上留白
legend_gaps = {}
for label, sel in [('分类细分', '#categories-pie-graph'), ('积分细分', '#points-pie-graph')]:
    box = boxes[sel]
    x1 = int(box['x'] * scale)
    y1 = int(box['y'] * scale)
    x2 = int((box['x'] + box['width']) * scale)
    y2 = int((box['y'] + box['height']) * scale)
    crop = img_array[y1:y2, x1:x2]
    rgb = crop[:, :, :3]
    color_mask = (np.max(rgb, axis=2) - np.min(rgb, axis=2)) > 30
    color_row_counts = np.sum(color_mask, axis=1)
    color_sig = np.where(color_row_counts > 5)[0]
    if len(color_sig) == 0:
        continue

    groups = []
    cur = [color_sig[0]]
    for i in range(1, len(color_sig)):
        if color_sig[i] - color_sig[i-1] <= 8:
            cur.append(color_sig[i])
        else:
            groups.append(cur)
            cur = [color_sig[i]]
    groups.append(cur)

    max_color = 0
    ring_g = None
    for g in groups:
        if len(g) > max_color:
            max_color = len(g)
            ring_g = g

    legend_g = None
    if ring_g:
        ring_bot = ring_g[-1]
        for g in groups:
            if g[0] > ring_bot and len(g) > 5:
                legend_g = g
                break

    if ring_g and legend_g:
        ring_bottom_px = (ring_g[-1] + 1) / scale
        legend_top_px = legend_g[0] / scale
        legend_gaps[label] = legend_top_px - ring_bottom_px

print("=" * 60)
print("margin-top=92 验证结果")
print("=" * 60)
print(f"正确/错误提交 → 分类细分标题 留白: {gap:.1f}px (原103.0px, 目标97.0px)")
print(f"ECharts option: cat.legend.top={opt_info['#categories-pie-graph']['legend_top']}, pt.legend.top={opt_info['#points-pie-graph']['legend_top']}")
for label, g in legend_gaps.items():
    print(f"{label} Legend 上留白(彩色像素): {g:.1f}px")
print(f"\n留白变化: 103.0 → {gap:.1f} = 减少 {103.0 - gap:.1f}px")
