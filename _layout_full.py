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

    # 获取图表容器和 submission-counts 的位置
    boxes = {}
    for sel in ['#keys-pie-graph', '#categories-pie-graph', '#points-pie-graph', '.submission-counts']:
        el = m_page.query_selector(sel)
        if el:
            boxes[sel] = el.bounding_box()

    m_page.screenshot(path='/workspace/_layout_full.png', full_page=True)
    m_context.close()
    browser.close()

img = Image.open('/workspace/_layout_full.png')
scale = img.size[0] / 375  # device_scale_factor=2 → scale=2.0
img_array = np.array(img)

print(f"截图尺寸: {img.size}, scale={scale}")
print(f"device_scale_factor=2, 所以 img_y / 2 = css_y")
print()

def analyze_chart(label, box, img_array, scale):
    """分析图表区域内的元素: 标题文字、环形图、Legend"""
    x1 = int(box['x'] * scale)
    y1 = int(box['y'] * scale)
    x2 = int((box['x'] + box['width']) * scale)
    y2 = int((box['y'] + box['height']) * scale)
    crop = img_array[y1:y2, x1:x2]
    rgb = crop[:, :, :3]
    # 非白色像素（即有内容的像素）
    non_white = np.any(rgb < 240, axis=2)
    row_counts = np.sum(non_white, axis=1)
    sig = np.where(row_counts > 3)[0]
    if len(sig) == 0:
        return None

    # 把连续的行（间隔<=8px视为同组）分组
    groups = []
    cur = [sig[0]]
    for i in range(1, len(sig)):
        if sig[i] - sig[i-1] <= 8:
            cur.append(sig[i])
        else:
            groups.append(cur)
            cur = [sig[i]]
    groups.append(cur)

    # 找出主要分组
    # 标题: 第一组（顶部）
    # 环形图: 最大的一组（彩色像素最多）
    # Legend: 标题之后的彩色文字组
    result = {
        'groups_count': len(groups),
        'groups': []
    }
    for i, g in enumerate(groups):
        top_px = g[0] / scale  # 转回 CSS px
        bot_px = g[-1] / scale
        height_px = (g[-1] - g[0] + 1) / scale
        # 该组的彩色像素数（用于识别环形图）
        seg = crop[g[0]:g[-1]+1, :, :3]
        color_mask = (np.max(seg, axis=2) - np.min(seg, axis=2)) > 30
        color_count = int(np.sum(color_mask))
        result['groups'].append({
            'idx': i,
            'top': top_px,
            'bottom': bot_px,
            'height': height_px,
            'color_pixels': color_count,
            'row_pixels': int(np.sum(row_counts[g[0]:g[-1]+1]))
        })
    return result

print("=" * 80)
print("移动端布局像素分析 (CSS px)")
print("视口: 375×667, device_scale_factor=2")
print("=" * 80)

chart_labels = {
    '#keys-pie-graph': '提交百分比',
    '#categories-pie-graph': '分类细分',
    '#points-pie-graph': '积分细分',
    '.submission-counts': '正确提交/错误提交'
}

elements = []

for sel in ['#keys-pie-graph', '.submission-counts', '#categories-pie-graph', '#points-pie-graph']:
    box = boxes.get(sel)
    if not box:
        continue
    label = chart_labels[sel]
    print(f"\n[{label}] ({sel})")
    print(f"  容器: y={box['y']:.1f}, height={box['height']:.1f}, bottom={box['y']+box['height']:.1f}")

    if sel == '.submission-counts':
        # 文字块直接取其 bounding box
        elements.append({
            'label': label,
            'sel': sel,
            'top': box['y'],
            'bottom': box['y'] + box['height'],
            'height': box['height'],
            'kind': 'text-block'
        })
        continue

    # 分析图表内的元素
    res = analyze_chart(label, box, img_array, scale)
    if not res:
        continue

    # 识别标题、环形图、Legend
    # 标题: 第一组（在容器顶部附近，row_pixels较少但存在）
    # 环形图: color_pixels最多的一组
    # Legend: 环形图之后的彩色组
    title_g = None
    ring_g = None
    legend_g = None

    if len(res['groups']) >= 1:
        # 找标题：第一组中 color_pixels 较少的（文字）
        # 但通常第一组是标题
        title_g = res['groups'][0]

    # 找环形图：color_pixels最多的组
    max_color = 0
    for g in res['groups']:
        if g['color_pixels'] > max_color:
            max_color = g['color_pixels']
            ring_g = g

    # 找Legend：环形图之后的、color_pixels较多的组
    if ring_g:
        for g in res['groups']:
            if g['top'] > ring_g['bottom'] and g['color_pixels'] > 30:
                legend_g = g
                break

    if title_g:
        # 标题位置（相对页面）
        title_top = box['y'] + title_g['top']
        title_bottom = box['y'] + title_g['bottom']
        print(f"  标题: top={title_top:.1f}, bottom={title_bottom:.1f}, height={title_g['height']:.1f}")
        elements.append({
            'label': f'{label}-标题',
            'sel': sel,
            'top': title_top,
            'bottom': title_bottom,
            'height': title_g['height'],
            'kind': 'title'
        })

    if ring_g:
        ring_top = box['y'] + ring_g['top']
        ring_bottom = box['y'] + ring_g['bottom']
        print(f"  环形图: top={ring_top:.1f}, bottom={ring_bottom:.1f}, height={ring_g['height']:.1f}")
        elements.append({
            'label': f'{label}-环形图',
            'sel': sel,
            'top': ring_top,
            'bottom': ring_bottom,
            'height': ring_g['height'],
            'kind': 'ring'
        })

    if legend_g:
        legend_top = box['y'] + legend_g['top']
        legend_bottom = box['y'] + legend_g['bottom']
        print(f"  Legend: top={legend_top:.1f}, bottom={legend_bottom:.1f}, height={legend_g['height']:.1f}")
        elements.append({
            'label': f'{label}-Legend',
            'sel': sel,
            'top': legend_top,
            'bottom': legend_bottom,
            'height': legend_g['height'],
            'kind': 'legend'
        })

# 按页面 y 位置排序
elements.sort(key=lambda x: x['top'])

print("\n" + "=" * 80)
print("按页面 y 位置排序的元素列表")
print("=" * 80)
for e in elements:
    print(f"  [{e['label']}] top={e['top']:.1f}, bottom={e['bottom']:.1f}, height={e['height']:.1f}")

print("\n" + "=" * 80)
print("相邻元素间留白 (gap = 下一元素top - 上一元素bottom)")
print("=" * 80)
for i in range(1, len(elements)):
    prev = elements[i-1]
    curr = elements[i]
    gap = curr['top'] - prev['bottom']
    print(f"  [{prev['label']}] → [{curr['label']}]: gap = {gap:.1f}px")
