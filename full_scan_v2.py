"""Full project scan for untranslated strings - v2 (accurate)"""
import re, os, subprocess, sys

PO_PATH = '/workspace/CTFd/translations/zh_Hans_CN/LC_MESSAGES/messages.po'
ROOT = '/workspace/CTFd'

with open(PO_PATH, 'r', encoding='utf-8') as f:
    po = f.read()

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

print(f"ROUND START - {len(msgids)} PO entries")

def find_files(exts):
    r = subprocess.run(['find', ROOT, '-type', 'f'] + sum([['-o', '-name', f'*.{e}'] for e in exts], [])[1:],
                       capture_output=True, text=True)
    if r.stdout.strip():
        return [f for f in r.stdout.strip().split('\n') if f and '__pycache__' not in f and 'node_modules' not in f and '.pyenv' not in f]
    return []

py_files = find_files(['py'])
html_files = find_files(['html'])
js_files = find_files(['js', 'vue'])

# Filter JS: exclude built/minified/bundled
js_files = [f for f in js_files if 'static/assets' not in f and 'echarts' not in f and not f.endswith('.min.js') and not f.endswith('.dev.js') and 'bundle' not in os.path.basename(f)]

missing = {}

def add(s, fp, t):
    if not s or len(s) <= 2:
        return
    if s in msgids:
        return
    # Skip template variables
    if '{{' in s or '{%' in s or '}}' in s or '%}' in s:
        return
    if s.startswith('{') or s.startswith('$') or s.startswith('#'):
        return
    # Skip single lowercase words
    if re.match(r'^[a-z][a-z0-9_-]*$', s) and len(s) < 15:
        return
    # Skip known non-translatable
    blacklist = {'true', 'false', 'null', 'undefined', 'GET', 'POST', 'PUT', 'DELETE', 'PATCH',
                 'args', 'type', 'team_id', 'id', 'field', 'value', 'review', 'text', 'location',
                 'challenge_id', 'audience_id', '', '', 'nonce'}
    if s.lower() in blacklist:
        return
    # Skip CSS/HTML classes
    if re.match(r'^(fa[sb]?\s|col-|btn-|text-|data-|role=|aria-|dropdown|modal|nav|tab|card|'
                r'list-|alert-|form-|custom-|float-|w-\d|p-\d|pt-|pb-|pr-|pl-|'
                r'm-\d|mt-|mb-|mr-|ml-|d-|justify-|align-|offset-|order-|bg-|border|'
                r'rounded|sr-only|no-|container|row$|col$|active$|show$|collapse$|fade$|'
                r'open$|close$|next$|prev$|page-item|page-link|input-group|form-control|'
                r'custom-select|custom-file|custom-checkbox|custom-radio|custom-sw|'
                r'custom-range|form-text|form-check|form-group|form-row|form-inline|'
                r'was-validated|invalid-feedback|valid-feedback)', s):
        return
    # Skip URLs
    if s.startswith('http') or s.startswith('api/'):
        return
    if s not in missing:
        missing[s] = (fp, t)

# 1. Python files
for fp in py_files:
    try:
        with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
            c = f.read()
    except:
        continue
    for m in re.finditer(r'gettext\("(.+?)"\)', c):
        add(m.group(1), fp, 'gettext')
    for m in re.finditer(r'ValidationError\("(.+?)"\)', c):
        add(m.group(1), fp, 'ValidationError')
    for m in re.finditer(r'abort\(\d+,\s*"(.+?)"\)', c):
        add(m.group(1), fp, 'ort')
    for m in re.finditer(r'flash\("(.+?)"\)', c):
        add(m.group(1), fp, 'flash')
    for m in re.finditer(r'"errors":\s*\{[^}]*"([^"]+)":\s*\["([^"]+)"\]', c):
        s = m.group(2)
        if s and s not in {'success', 'false', 'True', 'False', 'None', ''}:
            add(s, fp, 'jsonify')
    for m in re.finditer(r'"errors":\s*\{[^}]*"([^"]+)":\s*"([^"]+)"', c):
        s = m.group(2)
        if s and s not in {'success', 'false', 'True', 'False', 'None', ''}:
            add(s, fp, 'jsonify')

# 2. HTML templates
for fp in html_files:
    try:
        with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
            c = f.read()
    except:
        continue
    for m in re.finditer(r'\{%\s*trans\s*%\}\s*(.+?)\s*\{%\s*endtrans\s*%\}', c, re.DOTALL):
        s = m.group(1).strip()
        s = re.sub(r'\s+', ' ', s)
        add(s, fp, 'trans_block')
    for m in re.finditer(r'\{%\s*trans\s+"(.+?)"\s*%\}', c):
        add(m.group(1), fp, 'trans_inline')

# 3. JS/Vue files
for fp in js_files:
    try:
        with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
            c = f.read()
    except:
        continue
    for m in re.finditer(r'(?:ezAlert|ezQuery|ezNotify|ezToast)\(\s*\{[^}]*?title:\s*["\']([^"\']+?)["\']', c):
        s = m.group(1)
        if '{' not in s and '$' not in s and '`' not in s:
            add(s, fp, 'ez_title')
    for m in re.finditer(r'(?:ezAlert|ezQuery|ezNotify|ezToast)\(\s*\{[^}]*?body:\s*["\']([^"\']+?)["\']', c):
        s = m.group(1)
        if '{' not in s and '$' not in s and '`' not in s:
            add(s, fp, 'ez_body')
    for m in re.finditer(r'(?:ezAlert|ezQuery|ezNotify|ezToast)\(\s*\{[^}]*?button:\s*["\']([^"\']+?)["\']', c):
        s = m.group(1)
        if '{' not in s and '$' not in s and '`' not in s:
            add(s, fp, 'ez_button')

# Results
unique = list(missing.items())
print(f"MISSING COUNT: {len(unique)}")
for s, (fp, t) in sorted(unique, key=lambda x: x[1][1]):
    fname = os.path.basename(fp)
    print(f"  [{t}] {fname}")
    print(f"    msgid: {s}")
    print()

sys.exit(0 if len(unique) == 0 else 1)
