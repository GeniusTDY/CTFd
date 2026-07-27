import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch
import matplotlib.font_manager as fm

# 找一个中文字体
import os
font_paths = [
    '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
    '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
    '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
    '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
]
font_path = None
for fp in font_paths:
    if os.path.exists(fp):
        font_path = fp
        break

if font_path:
    cn_font = fm.FontProperties(fname=font_path)
    plt.rcParams['font.family'] = cn_font.get_name()
else:
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 元素数据 (按页面 y 排序)
# (label, top, bottom, color, kind)
elements = [
    ("提交百分比\n文字块",     1990.0, 2012.0, "#4A90E2", "title"),
    ("提交百分比\n环形图",     2071.0, 2243.5, "#7BB3F0", "ring"),
    ("正确提交/错误提交\n文字块", 2303.5, 2359.5, "#F5A623", "text"),
    ("分类细分\n文字块",       2469.0, 2491.0, "#9B59B6", "title"),
    ("分类细分\n环形图",       2544.5, 2722.5, "#C39BD3", "ring"),
    ("分类细分\nLegend",       2778.0, 2792.0, "#8E44AD", "legend"),
    ("积分细分\n文字块",       2869.0, 2891.0, "#27AE60", "title"),
    ("积分细分\n环形图",       2930.0, 3125.5, "#58D68D", "ring"),
    ("积分细分\nLegend",       3181.0, 3195.0, "#1E8449", "legend"),
]

# 留白 (上方元素, 下方元素, gap)
gaps = [
    ("提交百分比\n文字块", "提交百分比\n环形图", 59.0),
    ("提交百分比\n环形图", "正确提交/错误提交\n文字块", 60.0),
    ("正确提交/错误提交\n文字块", "分类细分\n文字块", 109.5),
    ("分类细分\n文字块", "分类细分\n环形图", 53.5),
    ("分类细分\n环形图", "分类细分\nLegend", 55.5),
    ("分类细分\nLegend", "积分细分\n文字块", 77.0),
    ("积分细分\n文字块", "积分细分\n环形图", 39.0),
    ("积分细分\n环形图", "积分细分\nLegend", 55.5),
]

# 构建 label 到 bottom/top 的映射
label_to_bottom = {e[0]: e[2] for e in elements}
label_to_top = {e[0]: e[1] for e in elements}

fig, ax = plt.subplots(figsize=(11, 13))

# 画布参数
LEFT_X = 200      # 元素左边 x
ELEM_W = 280      # 元素宽度
GAP_X = LEFT_X + ELEM_W + 40  # 留白标注 x

# 颜色分组背景
section_colors = {
    "提交百分比": "#E8F1FB",
    "正确提交/错误提交": "#FDF1DC",
    "分类细分": "#F4ECF7",
    "积分细分": "#E8F8EF",
}

# 画元素
for label, top, bottom, color, kind in elements:
    h = bottom - top
    # 圆角矩形
    box = FancyBboxPatch(
        (LEFT_X, top), ELEM_W, h,
        boxstyle="round,pad=0.3,rounding_size=4",
        linewidth=1.5, edgecolor=color, facecolor=color, alpha=0.85
    )
    ax.add_patch(box)
    # 文字
    ax.text(LEFT_X + ELEM_W/2, (top+bottom)/2, label,
            ha='center', va='center', fontsize=10, fontweight='bold',
            color='white' if kind != 'legend' else 'white')
    # 右侧标注 height
    ax.text(LEFT_X + ELEM_W + 12, (top+bottom)/2, f"h={h:.1f}",
            ha='left', va='center', fontsize=8, color='#555',
            fontstyle='italic')

# 画留白标注
for upper, lower, gap in gaps:
    y_upper = label_to_bottom[upper]
    y_lower = label_to_top[lower]
    y_mid = (y_upper + y_lower) / 2

    # 双向箭头
    ax.annotate('', xy=(GAP_X, y_lower), xytext=(GAP_X, y_upper),
                arrowprops=dict(arrowstyle='<->', color='#C0392B', lw=1.5))
    # 留白数值
    ax.text(GAP_X + 15, y_mid, f"{gap:.1f}px",
            ha='left', va='center', fontsize=9, color='#C0392B',
            fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#FDEDEC',
                      edgecolor='#C0392B', linewidth=0.8))

# 画 section 背景分组（淡淡的色块标识三个图表分组）
sections = [
    ("提交百分比", 1990.0, 2388.5, "#4A90E2"),
    ("分类细分", 2469.0, 2867.5, "#9B59B6"),
    ("积分细分", 2869.0, 3267.5, "#27AE60"),
]
for name, top, bottom, color in sections:
    ax.text(LEFT_X - 15, (top+bottom)/2, name,
            ha='right', va='center', fontsize=11, color=color,
            fontweight='bold', rotation=90)

# 在最右侧画一条总轴
TOTAL_TOP = elements[0][1]
TOTAL_BOT = elements[-1][2]
ax.annotate('', xy=(GAP_X + 100, TOTAL_BOT), xytext=(GAP_X + 100, TOTAL_TOP),
            arrowprops=dict(arrowstyle='<->', color='#2C3E50', lw=2))
ax.text(GAP_X + 115, (TOTAL_TOP+TOTAL_BOT)/2,
        f"总区域\n{TOTAL_TOP:.0f} → {TOTAL_BOT:.0f}\n高度 {TOTAL_BOT-TOTAL_TOP:.1f}px",
        ha='left', va='center', fontsize=9, color='#2C3E50',
        fontweight='bold')

# 标题与说明
ax.set_title("移动端布局与留白示意图\n(视口 375×667, CSS px)",
             fontsize=14, fontweight='bold', pad=15)

# 图例说明
legend_y = TOTAL_BOT + 80
ax.text(LEFT_X, legend_y, "图例：", fontsize=10, fontweight='bold')
legend_items = [
    ("文字块/标题", "#4A90E2"),
    ("环形图", "#7BB3F0"),
    ("正确/错误提交", "#F5A623"),
    ("Legend", "#8E44AD"),
]
for i, (name, color) in enumerate(legend_items):
    x = LEFT_X + 70 + i * 110
    box = FancyBboxPatch((x, legend_y), 14, 14,
                         boxstyle="round,pad=0.1,rounding_size=2",
                         linewidth=1, edgecolor=color, facecolor=color)
    ax.add_patch(box)
    ax.text(x + 20, legend_y + 7, name, ha='left', va='center', fontsize=8)

# 备注
note_y = legend_y + 40
ax.text(LEFT_X, note_y,
        "备注：\n"
        "— 提交百分比的 Legend 为 orient=vertical, top=middle, right=0（在容器右侧垂直居中），不在下方布局中\n"
        "— 分类细分/积分细分的 Legend 上留白均已统一为 56px（实测 55.5px，像素分组边界 ±0.5px 误差）",
        ha='left', va='top', fontsize=8, color='#555',
        fontstyle='italic')

# 坐标轴设置
ax.set_xlim(80, GAP_X + 250)
ax.set_ylim(TOTAL_BOT + 120, TOTAL_TOP - 30)  # y 轴反转
ax.set_xlabel("页面 x 位置 (CSS px)", fontsize=10)
ax.set_ylabel("页面 y 位置 (CSS px)", fontsize=10)
ax.grid(True, alpha=0.2, linestyle='--')
ax.set_aspect('equal')

plt.tight_layout()
plt.savefig('/workspace/mobile_layout.png', dpi=150, bbox_inches='tight',
            facecolor='white')
print("已保存: /workspace/mobile_layout.png")
