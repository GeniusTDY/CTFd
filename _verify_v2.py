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
    m_page.wait_for_timeout(15000)

    # 用 ECharts API 直接获取 Legend 的实际渲染位置
    info = m_page.evaluate('''async () => {
        const mod = await import('/themes/admin/static/assets/echarts.common-B4cbpQlJ.js');
        const echarts = mod.e;
        const out = {};
        for (const sel of ['#categories-pie-graph', '#points-pie-graph']) {
            const el = document.querySelector(sel);
            const inst = echarts.getInstanceByDom(el);
            const opt = inst.getOption();

            // 获取 Legend 的实际渲染位置
            // ECharts 内部 model 可以通过 inst.getModel() 获取
            const model = inst.getModel();
            const legendModel = model.getComponent('legend', 0);
            let legendRect = null;
            if (legendModel) {
                // legend 的位置信息
                const legendOpt = legendModel.option;
                out[sel] = {
                    legend_top_option: legendOpt.top,
                    legend_orient: legendOpt.orient,
                    legend_data: legendOpt.data
                };
            }

            // 通过 DOM 获取 Legend 的实际渲染位置
            // ECharts 渲染在 canvas 上，无法通过 DOM 获取
            // 但可以通过 inst.convertToPixel 获取坐标
            const width = el.offsetWidth;
            const height = el.offsetHeight;
            const center = opt.series[0].center;
            const radius = opt.series[0].radius;
            const minDim = Math.min(width, height);
            const outerR = parseFloat(radius[1]) / 100 * minDim;
            const cy = parseFloat(center[1]) / 100 * height;
            out[sel].ring_theoretical_bottom = cy + outerR;
            out[sel].ring_theoretical_top = cy - outerR;
            out[sel].container_h = height;
            out[sel].container_w = width;
        }
        return out;
    }''')

    # 截图并做像素分析
    m_page.screenshot(path='/workspace/_v56_v2.png', full_page=True)

    boxes = {}
    for sel in ['#categories-pie-graph', '#points-pie-graph']:
        el = m_page.query_selector(sel)
        boxes[sel] = el.bounding_box()

    m_context.close()
    browser.close()

print("ECharts API 报告的位置（容器内 CSS px）:")
for sel, d in info.items():
    print(f"\n{sel}:")
    print(f"  容器: {d['container_w']}x{d['container_h']}")
    print(f"  legend.top(option): {d['legend_top_option']}")
    print(f"  环形图理论 top: {d['ring_theoretical_top']:.1f}")
    print(f"  环形图理论 bottom: {d['ring_theoretical_bottom']:.1f}")
    print(f"  Legend top(option): {d['legend_top_option']}")
    print(f"  理论留白(Legend top - ring bottom): {d['legend_top_option'] - d['ring_theoretical_bottom']:.1f}")

# 像素分析 - 使用更精确的 Legend 识别
img = Image.open('/workspace/_v56_v2.png')
scale = img.size[0] / 375
img_array = np.array(img)

print(f"\n{'='*60}")
print("像素分析（精确识别 Legend）")
print(f"{'='*60}")

for label, sel in [('分类细分', '#categories-pie-graph'), ('积分细分', '#points-pie-graph')]:
    box = boxes[sel]
    x1 = int(box['x'] * scale)
    y1 = int(box['y'] * scale)
    x2 = int((box['x'] + box['width']) * scale)
    y2 = int((box['y'] + box['height']) * scale)
    crop = img_array[y1:y2, x1:x2]
    rgb = crop[:, :, :3]
    non_white = np.any(rgb < 240, axis=2)
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

    print(f"\n[{label}] 共 {len(groups)} 组:")
    for i, g in enumerate(groups):
        top_px = g[0] / scale
        bot_px = (g[-1] + 1) / scale
        seg = crop[g[0]:g[-1]+1, :, :3]
        color_mask = (np.max(seg, axis=2) - np.min(seg, axis=2)) > 30
        cc = int(np.sum(color_mask))
        print(f"  [{i}] top={top_px:.1f}, bottom={bot_px:.1f}, height={bot_px-top_px:.1f}, color={cc}, rows={int(np.sum(row_counts[g[0]:g[-1]+1]))}")
