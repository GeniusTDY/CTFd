#!/usr/bin/env python3
"""使用 Playwright + puppeteer chrome 测量移动端统计页面布局"""
import json
from playwright.sync_api import sync_playwright

CHROME_PATH = "/root/.cache/puppeteer/chrome/linux-151.0.7922.71/chrome-linux64/chrome"
URL = "http://localhost:4000/admin/statistics"

MEASURE_SCRIPT = r"""
(function(){
  function rect(el){
    if(!el) return null;
    var r = el.getBoundingClientRect();
    var docTop = r.top + window.pageYOffset;
    var docBottom = r.bottom + window.pageYOffset;
    return {
      top: Math.round(r.top),
      left: Math.round(r.left),
      width: Math.round(r.width),
      height: Math.round(r.height),
      bottom: Math.round(r.bottom),
      docTop: Math.round(docTop),
      docBottom: Math.round(docBottom)
    };
  }

  var keys = document.querySelector("#keys-pie-graph");
  var cat = document.querySelector("#categories-pie-graph");
  var pts = document.querySelector("#points-pie-graph");
  var sc = document.querySelector(".submission-counts");

  var keysCanvas = keys ? keys.querySelector("canvas") : null;
  var catCanvas = cat ? cat.querySelector("canvas") : null;
  var ptsCanvas = pts ? pts.querySelector("canvas") : null;

  // 上方 hr（container 内的最后一个 hr，在 container-fluid 之前）
  var keysContainerFluid = keys ? keys.closest(".container-fluid") : null;
  var prevHr = null;
  if(keysContainerFluid){
    var node = keysContainerFluid.previousElementSibling;
    while(node){
      if(node.tagName === "HR"){ prevHr = node; break; }
      node = node.previousElementSibling;
    }
  }

  var keysStyle = keys ? window.getComputedStyle(keys) : null;
  var catStyle = cat ? window.getComputedStyle(cat) : null;
  var scStyle = sc ? window.getComputedStyle(sc) : null;

  return JSON.stringify({
    windowWidth: window.innerWidth,
    matchMediaMobile: window.matchMedia("(max-width: 767.98px)").matches,
    prevHr: rect(prevHr),
    prevHrMarginBottom: prevHr ? window.getComputedStyle(prevHr).marginBottom : null,
    keysGraph: rect(keys),
    keysGraphMarginTop: keysStyle ? keysStyle.marginTop : null,
    keysCanvas: rect(keysCanvas),
    submissionCounts: rect(sc),
    submissionCountsMarginTop: scStyle ? scStyle.marginTop : null,
    categoriesGraph: rect(cat),
    categoriesGraphMarginTop: catStyle ? catStyle.marginTop : null,
    categoriesCanvas: rect(catCanvas),
    pointsGraph: rect(pts),
    pointsCanvas: rect(ptsCanvas),
    keysCol: rect(keys ? keys.closest(".col-md-4") : null),
    catCol: rect(cat ? cat.closest(".col-md-4") : null),
    ptsCol: rect(pts ? pts.closest(".col-md-4") : null),
    pieRow: rect(keys ? keys.closest(".row") : null)
  }, null, 2);
})()
"""

with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path=CHROME_PATH,
        headless=True,
        args=["--no-sandbox", "--disable-setuid-sandbox"]
    )
    # 移动端视口 iPhone SE
    context = browser.new_context(
        viewport={"width": 375, "height": 667},
        device_scale_factor=2,
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15"
    )
    page = context.new_page()

    # 登录
    page.goto("http://localhost:4000/login", wait_until="networkidle")
    page.fill('input[name="name"]', "root")
    page.fill('input[name="password"]', "root")
    page.click('button[type="submit"]')
    page.wait_for_timeout(2000)

    # 访问统计页
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(4000)  # 等 ECharts 渲染

    # 确认是移动端
    is_mobile = page.evaluate("window.matchMedia('(max-width: 767.98px)').matches")
    print(f"Is mobile viewport: {is_mobile}")
    print(f"Window width: {page.evaluate('window.innerWidth')}")

    # 测量
    result = page.evaluate(MEASURE_SCRIPT)
    print("\n=== Mobile Layout Measurement ===")
    print(result)

    # 截图
    page.screenshot(path="/workspace/_mobile_stats_full.png", full_page=True)
    print("\nScreenshot saved: /workspace/_mobile_stats_full.png")

    # 滚动到三个环形图区域截图
    page.evaluate("document.querySelector('#keys-pie-graph').scrollIntoView({block:'start'})")
    page.wait_for_timeout(1000)
    page.screenshot(path="/workspace/_mobile_stats_pie.png", full_page=False)
    print("Pie chart screenshot saved: /workspace/_mobile_stats_pie.png")

    browser.close()
