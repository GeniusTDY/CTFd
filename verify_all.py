"""Verify all translations are working in the rendered pages."""
import subprocess
import re

# Login first
print("Logging in as admin...")
subprocess.run([
    'curl', '-s', '-c', '/tmp/cookies.txt',
    'http://127.0.0.1:8000/login',
    '-o', '/tmp/login_page.html'
], capture_output=True, text=True)
with open('/tmp/login_page.html', 'r') as f:
    login_html = f.read()
m = re.search(r"csrfNonce':\s*\"([^\"]+)\"", login_html)
nonce = m.group(1) if m else ''
print(f"Got nonce: {nonce[:20]}...")

result = subprocess.run([
    'curl', '-s', '-c', '/tmp/cookies.txt', '-b', '/tmp/cookies.txt',
    '-X', 'POST', 'http://127.0.0.1:8000/login',
    '-H', 'Content-Type: application/x-www-form-urlencoded',
    '-H', 'Referer: http://127.0.0.1:8000/login',
    '--data', f'name=admin&password=admin123&nonce={nonce}',
    '-o', '/dev/null', '-w', '%{http_code}'
], capture_output=True, text=True)
print(f"Login HTTP: {result.stdout}")

# Test each page
pages = [
    ('/remote-desktop', 'Remote Desktop User Page', [
        '启动远程桌面', '远程桌面', '桌面', '终端',
        '无活动会话', '启动一个预装工具', '避免登录任何敏感账户或系统',
    ]),
    ('/admin/config', 'Admin Config Page', [
        '启用远程桌面', 'Docker 上下文', '镜像可用性',
        '危险区域', '清除会话历史',
    ]),
    ('/remote-desktop/dashboard', 'Admin Dashboard', [
        '远程桌面仪表盘', '当前活动', '总会话数', '活动会话',
        '活动', '报告', '使用热力图', '用户排行',
        '会话时长分布', '会话结束原因', '按主机分布', '命令日志',
        '总命令数', '独立工具数', '命令流', '按用户统计命令',
        '热门工具', '命令活动',
    ]),
]

total_pass = 0
total_fail = 0

for url, name, expected_strings in pages:
    print()
    print(f"=== {name} ({url}) ===")
    result = subprocess.run([
        'curl', '-s', '-b', '/tmp/cookies.txt',
        f'http://127.0.0.1:8000{url}'
    ], capture_output=True, text=True)
    content = result.stdout
    for s in expected_strings:
        if s in content:
            print(f"  ✓ Found: '{s}'")
            total_pass += 1
        else:
            print(f"  ✗ Missing: '{s}'")
            total_fail += 1

print()
print(f"=== SUMMARY ===")
print(f"Passed: {total_pass}")
print(f"Failed: {total_fail}")
print(f"Total: {total_pass + total_fail}")
