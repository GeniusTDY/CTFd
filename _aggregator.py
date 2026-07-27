from flask import Flask, send_file

app = Flask(__name__)

LAYOUT_IMG = "/workspace/mobile_layout.png"

# 分屏页面：iframe 直接引用各端口
SPLIT_PAGE = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>CTFd + 布局图 分屏</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
html,body{height:100%;font-family:sans-serif;background:#1a1a1a;color:#eee}
.toolbar{height:34px;background:#2c3e50;display:flex;align-items:center;padding:0 12px;font-size:12px;border-bottom:1px solid #34495e;gap:8px}
.toolbar a{color:#3b82f6;text-decoration:none;margin-left:6px}
.content{display:flex;height:calc(100% - 34px)}
.frame{flex:1;border-right:2px solid #34495e;display:flex;flex-direction:column;min-width:0}
.frame:last-child{border-right:none}
.frame-title{height:24px;background:#34495e;display:flex;align-items:center;padding:0 10px;font-size:11px;color:#ecf0f1;justify-content:space-between}
.frame-title .port{color:#1abc9c;font-family:monospace}
.frame iframe{flex:1;border:none;width:100%;background:#fff}
</style></head>
<body>
<div class="toolbar">
  <span>聚合预览</span>
  <a href="http://localhost:4001" target="_blank">CTFd 原始(:4001)</a>
  <a href="http://localhost:8899/mobile_layout.png" target="_blank">布局图原始(:8899)</a>
</div>
<div class="content">
  <div class="frame">
    <div class="frame-title"><span>CTFd 管理后台</span><span class="port">:4001</span></div>
    <iframe src="http://localhost:4001/"></iframe>
  </div>
  <div class="frame">
    <div class="frame-title"><span>移动端布局示意图</span><span class="port">:8899</span></div>
    <iframe src="http://localhost:8899/mobile_layout.png"></iframe>
  </div>
</div>
</body></html>"""


@app.route("/")
def index():
    return SPLIT_PAGE


@app.route("/layout.png")
def layout_png():
    return send_file(LAYOUT_IMG, mimetype="image/png")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4000, debug=False)
