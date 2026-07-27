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

    # 通过JS获取所有元素的位置
    layout = m_page.evaluate('''async () => {
        const mod = await import('/themes/admin/static/assets/echarts.common-B4cbpQlJ.js');
        const echarts = mod.e;

        const result = {};

        // 获取卡片标题和图表元素
        // 找到所有包含 h5/h4 的卡片
        const cards = document.querySelectorAll('.card');
        const items = [];

        cards.forEach(card => {
            const headers = card.querySelectorAll('h5.card-title, h4.card-title, h5, h4');
            headers.forEach(h => {
                const text = h.textContent.trim();
                if (text && (
                    text.includes('提交百分比') ||
                    text.includes('Submission Percent') ||
                    text.includes('正确提交') ||
                    text.includes('Correct') ||
                    text.includes('分类细分') ||
                    text.includes('Category Breakdown') ||
                    text.includes('积分细分') ||
                    text.includes('Point Breakdown')
                )) {
                    const rect = h.getBoundingClientRect();
                    items.push({
                        text: text,
                        type: 'header',
                        x: rect.x,
                        y: rect.y,
                        width: rect.width,
                        height: rect.height,
                        bottom: rect.bottom
                    });
                }
            });
        });

        // 图表容器
        const charts = ['#keys-pie-graph', '#categories-pie-graph', '#points-pie-graph'];
        charts.forEach(sel => {
            const el = document.querySelector(sel);
            if (el) {
                const rect = el.getBoundingClientRect();
                const inst = echarts.getInstanceByDom(el);
                let legendTop = null, legendHeight = null;
                let ringInfo = null;
                if (inst) {
                    const opt = inst.getOption();
                    if (opt.legend && opt.legend[0]) {
                        legendTop = opt.legend[0].top;
                    }
                    // 获取系列中心点
                    if (opt.series && opt.series[0] && opt.series[0].center) {
                        ringInfo = {
                            center: opt.series[0].center,
                            radius: opt.series[0].radius,
                            legend_top: opt.legend[0].top
                        };
                    }
                }
                items.push({
                    text: sel,
                    type: 'chart',
                    x: rect.x,
                    y: rect.y,
                    width: rect.width,
                    height: rect.height,
                    bottom: rect.bottom,
                    legendTop: legendTop,
                    ringInfo: ringInfo
                });
            }
        });

        // "正确提交/错误提交" 文字块容器 .submission-counts
        const subCounts = document.querySelector('.submission-counts');
        if (subCounts) {
            const rect = subCounts.getBoundingClientRect();
            items.push({
                text: 'submission-counts',
                type: 'submission-counts',
                x: rect.x,
                y: rect.y,
                width: rect.width,
                height: rect.height,
                bottom: rect.bottom
            });
        }

        return items;
    }''')

    m_page.screenshot(path='/workspace/_layout_mobile.png', full_page=True)
    m_context.close()
    browser.close()

print("=" * 70)
print("移动端元素位置 (视口 375×667, device_scale_factor=2)")
print("=" * 70)
print(f"{'类型':<20} {'文本/选择器':<35} {'y':>8} {'h':>8} {'bottom':>8}")
print("-" * 70)
for item in layout:
    t = item['type']
    text = item['text'][:35]
    print(f"{t:<20} {text:<35} {item['y']:>8.1f} {item['height']:>8.1f} {item['bottom']:>8.1f}")

# 排序按 y 位置
sorted_items = sorted(layout, key=lambda x: x['y'])
print("\n" + "=" * 70)
print("按 y 排序 - 元素顺序与上下间距")
print("=" * 70)
prev_bottom = None
prev_text = None
for item in sorted_items:
    if prev_bottom is not None:
        gap = item['y'] - prev_bottom
        print(f"  [{prev_text}] 底部 {prev_bottom:.1f} → [{item['text'][:30]}] 顶部 {item['y']:.1f} = 间距 {gap:.1f}px")
    print(f"  [{item['type']}] {item['text'][:40]}: y={item['y']:.1f}, h={item['height']:.1f}, bottom={item['bottom']:.1f}")
    if item.get('legendTop') is not None:
        print(f"      legend.top (option): {item['legendTop']}")
    if item.get('ringInfo'):
        print(f"      series.center: {item['ringInfo']['center']}, radius: {item['ringInfo']['radius']}, legend_top: {item['ringInfo']['legend_top']}")
    prev_bottom = item['bottom']
    prev_text = item['text'][:30]
    print()
