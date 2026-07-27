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

    # 移动端
    m_context = browser.new_context(viewport={'width': 375, 'height': 667}, device_scale_factor=2)
    m_context.add_cookies([{'name': 'session', 'value': session_cookie, 'domain': 'localhost', 'path': '/'}])
    m_page = m_context.new_page()
    m_page.goto('http://localhost:4000/admin/statistics', wait_until='domcontentloaded')
    m_page.wait_for_timeout(8000)

    # 确认 option 值
    info = m_page.evaluate('''async () => {
        const mod = await import('/themes/admin/static/assets/echarts.common-B4cbpQlJ.js');
        const echarts = mod.e;
        const results = {};
        for (const [name, sel] of [['cat', '#categories-pie-graph'], ['pt', '#points-pie-graph']]) {
            const el = document.querySelector(sel);
            const inst = echarts.getInstanceByDom(el);
            const opt = inst.getOption();
            results[name] = {legend_top: opt.legend[0].top};
        }
        return results;
    }''')
    print("Option legend.top:")
    for name, d in info.items():
        print(f"  {name}: {d['legend_top']}")

    m_page.screenshot(path='/workspace/_v56.png', full_page=True)
    boxes = {}
    for name, sel in [('cat', '#categories-pie-graph'), ('pt', '#points-pie-graph')]:
        el = m_page.query_selector(sel)
        boxes[name] = el.bounding_box() if el else None
    m_context.close()

    # 桌面端
    d_context = browser.new_context(viewport={'width': 1280, 'height': 800})
    d_context.add_cookies([{'name': 'session', 'value': session_cookie, 'domain': 'localhost', 'path': '/'}])
    d_page = d_context.new_page()
    d_page.goto('http://localhost:4000/admin/statistics', wait_until='domcontentloaded')
    d_page.wait_for_timeout(8000)
    cat_box = d_page.query_selector('#categories-pie-graph').bounding_box()
    pt_box = d_page.query_selector('#points-pie-graph').bounding_box()
    d_context.close()
    browser.close()

img = Image.open('/workspace/_v56.png')
scale = img.size[0] / 375
img_array = np.array(img)

print("\n" + "=" * 60)
print("移动端 Legend 上留白验证")
print("=" * 60)

for label, key in [('分类细分', 'cat'), ('积分细分', 'pt')]:
    box = boxes.get(key)
    if not box:
        continue
    x1 = int(box['x'] * scale)
    y1 = int(box['y'] * scale)
    x2 = int((box['x'] + box['width']) * scale)
    y2 = int((box['y'] + box['height']) * scale)
    crop = img_array[y1:y2, x1:x2]
    rgb = crop[:, :, :3]
    non_white = np.any(rgb < 250, axis=2)
    row_counts = np.sum(non_white, axis=1)
    sig = np.where(row_counts > 3)[0]
    if len(sig) == 0:
        continue
    groups = []
    cur = [sig[0]]
    for i in range(1, len(sig)):
        if sig[i] - sig[i-1] <= 8:
            cur.append(sig[i])
        else:
            groups.append(cur)
            cur = [sig[i]]
    groups.append(cur)

    print(f"\n[{label}]")
    if len(groups) >= 3:
        ring_bot = groups[1][-1]/scale
        legend_idx = None
        max_color = 0
        for i in range(2, len(groups)):
            gt = int(groups[i][0])
            gb = int(groups[i][-1])
            seg = crop[gt:gb, :, :3]
            color_mask = (np.max(seg, axis=2) - np.min(seg, axis=2)) > 30
            cc = np.sum(color_mask)
            if cc > max_color:
                max_color = cc
                legend_idx = i
        if legend_idx is not None:
            legend_top = groups[legend_idx][0]/scale
            gap = legend_top - ring_bot
            print(f"  环形图底部(相对): {ring_bot:.1f}")
            print(f"  Legend 顶部(相对): {legend_top:.1f}")
            print(f"  Legend 上留白: {gap:.1f}px")

print("\n" + "=" * 60)
print("桌面端验证（不应受影响）")
print("=" * 60)
print(f"  分类细分 y={cat_box['y']:.1f}")
print(f"  积分细分 y={pt_box['y']:.1f}")
print(f"  同行: {'是' if abs(cat_box['y'] - pt_box['y']) < 5 else '否'}")
