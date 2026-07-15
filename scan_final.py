import re, os, subprocess

po_path = '/workspace/CTFd/translations/zh_Hans_CN/LC_MESSAGES/messages.po'
po = open(po_path, 'r').read()

msgids = set()
for m in re.finditer(r'^msgid "(.+?)"', po, re.MULTILINE):
    mid = m.group(1)
    if mid and len(mid) > 1:
        msgids.add(mid)

blocks = po.split('\n\n')
for block in blocks:
    lines = block.strip().split('\n')
    parts = []
    in_msgid = False
    for l in lines:
        if l.startswith('msgid "'):
            parts = [l[7:-1]]
            in_msgid = True
        elif l.startswith('"') and in_msgid:
            parts.append(l[1:-1])
        elif l.startswith('msgstr'):
            if parts:
                msgids.add(''.join(parts))
            in_msgid = False
            break

print(f"PO entries: {len(msgids)}")

# Get ALL Python files
result = subprocess.check_output(
    ['find', '/workspace/CTFd', '-name', '*.py', '-type', 'f',
     '-not', '-path', '*__pycache__*',
     '-not', '-path', '*.pyenv*'],
    text=True
).strip()
py_files = [f for f in result.split('\n') if f]

missing = []

def add(s, fp, t):
    if not s or len(s) <= 2:
        return
    if s in msgids:
        return
    if s.startswith('{') or s.startswith('$'):
        return
    for existing in missing:
        if existing[1] == s:
            return
    missing.append((fp, s, t))

for fp in py_files:
    try:
        with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except:
        continue

    # gettext
    for m in re.finditer(r'gettext\("(.+?)"\)', content):
        add(m.group(1), fp, 'gettext')
    
    # ValidationError
    for m in re.finditer(r'ValidationError\("(.+?)"\)', content):
        add(m.group(1), fp, 'ValidationError')
    
    # abort
    for m in re.finditer(r'abort\(\d+,\s*"(.+?)"\)', content):
        add(m.group(1), fp, 'abort')
    
    # flash messages
    for m in re.finditer(r'flash\(\s*"(.+?)"', content):
        add(m.group(1), fp, 'flash')
    
    # jsonify error strings (comprehensive)
    for m in re.finditer(r'"errors":\s*\{[^}]*"([^"]+)":\s*\[[^\]]*"([^"]+)"[^\]]*\]', content):
        s = m.group(2)
        if s and s not in ('success', 'false', 'True', 'False', 'None', ''):
            add(s, fp, 'jsonify')
    
    # jsonify error strings (single string, not array)
    for m in re.finditer(r'"errors":\s*\{[^}]*"([^"]+)":\s*"([^"]+)"', content):
        s = m.group(2)
        if s and s not in ('success', 'false', 'True', 'False', 'None', ''):
            add(s, fp, 'jsonify')

# Get all HTML files
result = subprocess.check_output(
    ['find', '/workspace/CTFd/themes', '-name', '*.html', '-type', 'f'],
    text=True
).strip()
html_files = [f for f in result.split('\n') if f]

for fp in html_files:
    try:
        with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except:
        continue

    # {% trans %}...{% endtrans %}
    for m in re.finditer(r'\{%\s*trans\s*%\}\s*(.+?)\s*\{%\s*endtrans\s*%\}', content, re.DOTALL):
        s = m.group(1).strip()
        s = re.sub(r'\s+', ' ', s)
        add(s, fp, 'trans_block')
    
    # {% trans "..." %}
    for m in re.finditer(r'\{%\s*trans\s+"(.+?)"\s*%\}', content):
        add(m.group(1), fp, 'trans_inline')

# Get all JS/Vue files
result = subprocess.check_output(
    ['find', '/workspace/CTFd/themes', '-type', 'f', '(', '-name', '*.js', '-o', '-name', '*.vue', ')',
     '-not', '-path', '*static/assets*',
     '-not', '-path', '*echarts*',
     '-not', '-name', '*.min.js',
     '-not', '-name', '*.dev.js',
     '-not', '-name', '*bundle*'],
    text=True
).strip()
js_files = [f for f in result.split('\n') if f]

for fp in js_files:
    try:
        with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except:
        continue

    for m in re.finditer(r'(?:ezAlert|ezQuery|ezNotify|ezToast)\(\s*\{[^}]*?title:\s*["\']([^"\']+?)["\']', content):
        s = m.group(1)
        if '{' not in s and '$' not in s and '`' not in s:
            add(s, fp, 'ez_title')
    
    for m in re.finditer(r'(?:ezAlert|ezQuery|ezNotify|ezToast)\(\s*\{[^}]*?body:\s*["\']([^"\']+?)["\']', content):
        s = m.group(1)
        if '{' not in s and '$' not in s and '`' not in s:
            add(s, fp, 'ez_body')
    
    for m in re.finditer(r'(?:ezAlert|ezQuery|ezNotify|ezToast)\(\s*\{[^}]*?button:\s*["\']([^"\']+?)["\']', content):
        s = m.group(1)
        if '{' not in s and '$' not in s and '`' not in s:
            add(s, fp, 'ez_button')

# Filter out false positives
def is_real_string(s):
    if len(s) < 3:
        return False
    if re.match(r'^[a-z][a-z0-9_-]*$', s) and len(s) < 15:
        return False
    if s in ('true', 'false', 'null', 'undefined', 'GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'args', 'type', 'team_id', 'id', 'field', 'value', 'review', 'text', 'location', 'challenge_id', 'audience_id'):
        return False
    if re.match(r'^(fa[sb]?\s|col-|btn-|text-|data-|role=|aria-|dropdown|modal|nav|tab|card|list-|alert-|form-|custom-|float-|w-\d|p-\d|pt-|pb-|pr-|pl-|m-\d|mt-|mb-|mr-|ml-|d-|justify-|align-|offset-|order-|bg-|border|rounded|sr-only|no-|container|row$|col$|active$|show$|collapse$|fade$|open$|close$|next$|prev$|page-item|page-link|input-group|form-control|custom-select|custom-file|custom-checkbox|custom-radio|custom-switch|custom-range|form-text|form-check|form-group|form-row|form-inline|was-validated|invalid-feedback|valid-feedback)', s):
        return False
    return True

real_missing = [(fp, s, t) for fp, s, t in missing if is_real_string(s)]

# Remove duplicates
seen = set()
unique = []
for fp, s, t in real_missing:
    if s not in seen:
        seen.add(s)
        unique.append((fp, s, t))

print(f"\n=== FINAL MISSING ({len(unique)} found) ===")
for fp, s, t in unique:
    print(f"  [{t}] {fp}")
    print(f"    {s}")
    print()
