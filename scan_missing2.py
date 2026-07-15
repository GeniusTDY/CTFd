import re, os, subprocess

po_file = '/workspace/CTFd/translations/zh_Hans_CN/LC_MESSAGES/messages.po'
with open(po_file, 'r', encoding='utf-8') as f:
    po_content = f.read()

msgids = set()
for m in re.finditer(r'^msgid "(.+?)"', po_content, re.MULTILINE):
    mid = m.group(1)
    if mid and len(mid) > 1:
        msgids.add(mid)

blocks = po_content.split('\n\n')
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

print(f"Total PO msgids: {len(msgids)}")

# Get ALL Python source files + built JS files
result = subprocess.check_output(
    ['find', '/workspace/CTFd', '-type', 'f',
     '(', '-name', '*.py', '-o', '-name', '*.html', '-o', '-name', '*.js', '-o', '-name', '*.vue', ')',
     '-not', '-path', '*__pycache__*',
     '-not', '-path', '*node_modules*',
     '-not', '-path', '*.pyenv*',
     '-not', '-path', '*echarts*',
     '-not', '-name', '*.min.js',
     '-not', '-name', '*.dev.js',
     '-not', '-name', '*bundle*'],
    text=True
).strip()
all_files = [f for f in result.split('\n') if f]

print(f"Total source files: {len(all_files)}")

missing = []

def add_string(fp, s, source_type):
    if not s or len(s) <= 2:
        return
    if s in msgids:
        return
    if s.startswith('{') or s.startswith('$') or s.startswith('#'):
        return
    if re.match(r'^[a-z][a-z0-9_-]*$', s) and len(s) < 15:
        return
    if s in ('true', 'false', 'null', 'undefined', 'GET', 'POST', 'PUT', 'DELETE', 'PATCH'):
        return
    if re.match(r'^(fa[sb]?\s|col-|btn-|text-|data-|role=|aria-|dropdown|modal|nav|tab|card|list-|alert-|form-|custom-|float-|w-\d|p-\d|pt-|pb-|pr-|pl-|m-\d|mt-|mb-|mr-|ml-|d-|justify-|align-|offset-|order-|bg-|border|rounded|sr-only|no-|container|row$|col$|active$|show$|collapse$|fade$|open$|close$|next$|prev$|page-item|page-link|input-group|form-control|custom-select|custom-file|custom-checkbox|custom-radio|custom-sw|custom-range|form-text|form-check|form-group|form-row|form-inline|was-validated|invalid-feedback|valid-feedback)', s):
        return
    for existing in missing:
        if existing[1] == s:
            return
    missing.append((fp, s, source_type))

for fp in all_files:
    if not os.path.isfile(fp):
        continue
    try:
        with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except:
        continue

    ext = os.path.splitext(fp)[1]
    
    if ext == '.py':
        for m in re.finditer(r'gettext\("(.+?)"\)', content):
            add_string(fp, m.group(1), 'gettext')
        for m in re.finditer(r'ValidationError\("(.+?)"\)', content):
            add_string(fp, m.group(1), 'ValidationError')
        for m in re.finditer(r'abort\(\d+,\s*"(.+?)"\)', content):
            add_string(fp, m.group(1), 'abort')
        # jsonify errors - various patterns
        for m in re.finditer(r'"errors":\s*\{[^}]*"([^"]+)":\s*\[([^\[\]]+)\]', content):
            val = m.group(2).strip()
            # Extract the string from the list
            for s_match in re.finditer(r'"([^"]+)"', val):
                add_string(fp, s_match.group(1), 'jsonify_error')
        # Also check for direct jsonify with errors
        for m in re.finditer(r'"errors":\s*\{[^}]*"([^"]+)":\s*"([^"]+)"', content):
            add_string(fp, m.group(2), 'jsonify_error')
    
    elif ext == '.html':
        for m in re.finditer(r'\{%\s*trans\s*%\}\s*(.+?)\s*\{%\s*endtrans\s*%\}', content, re.DOTALL):
            s = m.group(1).strip()
            s = re.sub(r'\s+', ' ', s)
            add_string(fp, s, 'trans_block')
        for m in re.finditer(r'\{%\s*trans\s+"(.+?)"\s*%\}', content):
            add_string(fp, m.group(1), 'trans_inline')
    
    elif ext in ('.js', '.vue'):
        for m in re.finditer(r'(?:ezAlert|ezQuery|ezNotify|ezToast)\(\s*\{[^}]*?title:\s*["\']([^"\']+?)["\']', content):
            s = m.group(1)
            if '{' not in s and '$' not in s and '`' not in s:
                add_string(fp, s, 'ez_title')
        for m in re.finditer(r'(?:ezAlert|ezQuery|ezNotify|ezToast)\(\s*\{[^}]*?body:\s*["\']([^"\']+?)["\']', content):
            s = m.group(1)
            if '{' not in s and '$' not in s and '`' not in s:
                add_string(fp, s, 'ez_body')
        for m in re.finditer(r'(?:ezAlert|ezQuery|ezNotify|ezToast)\(\s*\{[^}]*?button:\s*["\']([^"\']+?)["\']', content):
            s = m.group(1)
            if '{' not in s and '$' not in s and '`' not in s:
                add_string(fp, s, 'ez_button')

seen = set()
unique = []
for fp, s, t in missing:
    if s not in seen:
        seen.add(s)
        unique.append((fp, s, t))

unique.sort(key=lambda x: (x[2], x[1]))

print(f"\n=== MISSING TRANSLATIONS ({len(unique)} found) ===")
for fp, s, t in unique:
    print(f"  [{t}] {fp}")
    print(f"    msgid: {s}")
    print()
