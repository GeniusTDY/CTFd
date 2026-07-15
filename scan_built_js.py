import re, os, subprocess

po_path = '/workspace/CTFd/translations/zh_Hans_CN/LC_MESSAGES/messages.po'
po = open(po_path, 'r').read()

msgids = set()
for m in re.finditer(r'^msgid "(.+?)"', po, re.MULTILINE):
    mid = m.group(1)
    if mid and len(mid) > 1:
        msgids.add(mid)

result = subprocess.check_output(
    ['find', '/workspace/CTFd/themes/admin/static/assets', '/workspace/CTFd/themes/core/static/assets',
     '-name', '*.js', '-type', 'f'],
    text=True
).strip()
js_files = [f for f in result.split('\n') if f and 'echarts' not in f]

missing = {}
for fp in js_files:
    try:
        with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except:
        continue
    
    # ezAlert/ezQuery/ezNotify/ezToast
    for m in re.finditer(r'ez(?:Alert|Query|Notify|Toast)\(\s*\{[^}]*?title:\s*"([^"]+)"', content):
        s = m.group(1)
        if s not in msgids and '{' not in s and '$' not in s and len(s) > 2:
            if s not in missing:
                missing[s] = fp
    
    for m in re.finditer(r'ez(?:Alert|Query|Notify|Toast)\(\s*\{[^}]*?body:\s*"([^"]+)"', content):
        s = m.group(1)
        if s not in msgids and '{' not in s and '$' not in s and len(s) > 2:
            if s not in missing:
                missing[s] = fp
    
    for m in re.finditer(r'ez(?:Alert|Query|Notify|Toast)\(\s*\{[^}]*?button:\s*"([^"]+)"', content):
        s = m.group(1)
        if s not in msgids and '{' not in s and '$' not in s and len(s) > 2:
            if s not in missing:
                missing[s] = fp

print(f'Missing from built JS: {len(missing)}')
for s, fp in sorted(missing.items()):
    print(f'  [{os.path.basename(fp)}] {s}')
