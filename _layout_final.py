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
    m_page.wait_for_timeout(8000)

    boxes = {}
    for sel in ['#keys-pie-graph', '#categories-pie-graph', '#points-pie-graph', '.submission-counts']:
        el = m_page.query_selector(sel)
        if el:
            boxes[sel] = el.bounding_box()

    # 获取 ECharts option 信息（确认 legend 类型）
    echart_info = m_page.evaluate('''async () => {
        const mod = await import('/themes/admin/static/assets/echarts.common-B4cbpQlJ.js');
        const echarts = mod.e;
        const out = {};
        for (const sel of ['#keys-pie-graph', '#categories-pie-graph', '#points-pie-graph']) {
            const el = document.querySelector(sel);
            const inst = echarts.getInstanceByDom(el);
            const opt = inst.getOption();
            out[sel] = {
                legend_orient: opt.legend[0].orient,
                legend_top: opt.legend[0].top,
                legend_right: opt.legend[0].right,
                series_center: opt.series[0].center,
                series_radius: opt.series[0].radius,
                legend_data: opt.legend[0].data
            };
        }
        return out;
    }''')

    m_page.screenshot(path='/workspace/_layout_final.png', full_page=True)
    m_context.close()
    browser.close()

img = Image.open('/workspace/_layout_final.png')
scale = img.size[0] / 375
img_array = np.array(img)

print("=" * 80)
print("移动端布局分析 (CSS px)")
print(f"视口: 375×667, device_scale_factor={scale}")
print("=" * 80)

print("\n[ECharts 配置信息]")
for sel, info in echart_info.items():
    print(f"  {sel}: orient={info['legend_orient']}, top={info['legend_top']}, right={info['legend_right']}, center={info['series_center']}, radius={info['series_radius']}, legend_data={info['legend_data']}")

def analyze_chart_elements(box, img_array, scale, legend_orient):
    """分析图表区域: 标题、环形图、Legend 位置"""
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
        return None

    groups = []
    cur = [sig[0]]
    for i in range(1, len(sig)):
        if sig[i] - sig[i-1] <= 8:
            cur.append(sig[i])
        else:
            groups.append(cur)
            cur = [sig[i]]
    groups.append(cur)

    out = []
    for g in groups:
        top_px = g[0] / scale
        bot_px = (g[-1] + 1) / scale
        height_px = bot_px - top_px
        # 用图表中心列附近分析彩色像素
        seg = crop[g[0]:g[-1]+1, :, :3]
        color_mask = (np.max(seg, axis=2) - np.min(seg, axis=2)) > 30
        color_count = int(np.sum(color_mask))
        out.append({
            'top': top_px,
            'bottom': bot_px,
            'height': height_px,
            'color_pixels': color_count,
            'row_pixels': int(np.sum(row_counts[g[0]:g[-1]+1]))
        })
    return out

elements = []

# 处理每个图表
chart_info = [
    ('#keys-pie-graph', '提交百分比', 'vertical'),
    ('#categories-pie-graph', '分类细分', 'horizontal'),
    ('#points-pie-graph', '积分细分', 'horizontal'),
]

for sel, label, legend_orient in chart_info:
    box = boxes.get(sel)
    if not box:
        continue
    print(f"\n[{label}] ({sel})")
    print(f"  容器: top={box['y']:.1f}, bottom={box['y']+box['height']:.1f}, height={box['height']:.1f}")

    groups = analyze_chart_elements(box, img_array, scale, legend_orient)
    if not groups:
        continue

    # 调试: 打印所有 groups
    print(f"  --- 所有内容分组 (共{len(groups)}组) ---")
    for i, g in enumerate(groups):
        print(f"    [{i}] top={g['top']:.1f}, bottom={g['bottom']:.1f}, height={g['height']:.1f}, color_pixels={g['color_pixels']}, row_pixels={g['row_pixels']}")

    # 标题: 第一组（在容器顶部，row_pixels适中，color_pixels少）
    title_g = groups[0]

    # 环形图: color_pixels 最多
    ring_g = max(groups, key=lambda g: g['color_pixels'])

    # Legend
    legend_g = None
    if legend_orient == 'horizontal':
        # 水平Legend在环形图下方，选 color_pixels 最多的一组（与 _verify_56.py 一致）
        max_color = 0
        for g in groups:
            if g['top'] > ring_g['bottom'] and g['color_pixels'] > max_color:
                max_color = g['color_pixels']
                legend_g = g
    else:
        # 垂直Legend在右侧，跳过(用户主要关心下方布局)
        legend_g = None

    title_top = box['y'] + title_g['top']
    title_bot = box['y'] + title_g['bottom']
    print(f"  标题: top={title_top:.1f}, bottom={title_bot:.1f}, height={title_g['height']:.1f}")
    elements.append({'label': f'{label}-文字块', 'top': title_top, 'bottom': title_bot, 'height': title_g['height']})

    ring_top = box['y'] + ring_g['top']
    ring_bot = box['y'] + ring_g['bottom']
    print(f"  环形图: top={ring_top:.1f}, bottom={ring_bot:.1f}, height={ring_g['height']:.1f}")
    elements.append({'label': f'{label}-环形图', 'top': ring_top, 'bottom': ring_bot, 'height': ring_g['height']})

    if legend_g:
        leg_top = box['y'] + legend_g['top']
        leg_bot = box['y'] + legend_g['bottom']
        print(f"  Legend: top={leg_top:.1f}, bottom={leg_bot:.1f}, height={legend_g['height']:.1f}")
        elements.append({'label': f'{label}-Legend', 'top': leg_top, 'bottom': leg_bot, 'height': legend_g['height']})

# 正确提交/错误提交文字块
sc_box = boxes.get('.submission-counts')
if sc_box:
    print(f"\n[正确提交/错误提交] (.submission-counts)")
    print(f"  容器: top={sc_box['y']:.1f}, bottom={sc_box['y']+sc_box['height']:.1f}, height={sc_box['height']:.1f}")
    elements.append({
        'label': '正确提交/错误提交',
        'top': sc_box['y'],
        'bottom': sc_box['y'] + sc_box['height'],
        'height': sc_box['height']
    })

# 按页面 y 位置排序
elements.sort(key=lambda x: x['top'])

print("\n" + "=" * 80)
print("最终元素列表（按页面 y 位置排序）")
print("=" * 80)
for i, e in enumerate(elements, 1):
    print(f"  {i}. [{e['label']}] top={e['top']:.1f}, bottom={e['bottom']:.1f}, height={e['height']:.1f}")

print("\n" + "=" * 80)
print("相邻元素间留白")
print("=" * 80)
for i in range(1, len(elements)):
    prev = elements[i-1]
    curr = elements[i]
    gap = curr['top'] - prev['bottom']
    print(f"  {i}. [{prev['label']}] → [{curr['label']}]: {gap:.1f}px")
