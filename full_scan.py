"""Full project scan for untranslated strings in CTFd."""
import re, os, subprocess, sys

PO_PATH = '/workspace/CTFd/translations/zh_Hans_CN/LC_MESSAGES/messages.po'
PROJECT_ROOT = '/workspace/CTFd'

# --- Load PO msgids ---
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

print(f"Round start: {len(msgids)} PO entries")

# --- Find all source files ---
def find_files(exts, exclude_dirs):
    cmd = ['find', PROJECT_ROOT, '-type', 'f']
    name_args = []
    for e in exts:
        name_args.extend(['-o', '-name', f'*.{e}'])
    cmd.extend(['(', name_args[1], *name_args[2:], ')'])
    for d in exclude_dirs:
        cmd.extend(['-not', '-path', f'*/{d}/*'])
    return subprocess.check_output(cmd, text=True).strip().split('\n')

py_files = find_files(['py'], ['__pycache__', 'node_modules', '.pyenv'])
html_files = find_files(['html'], ['__pycache__', 'node_modules'])
js_files = find_files(['js', 'vue'], ['__pycache__', 'node_modules', 'static/assets', 'echarts'])

# Filter JS files
js_files = [f for f in js_files if not f.endswith('.min.js') and not f.endswith('.dev.js') and 'bundle' not in os.path.basename(f)]

missing = []

def add(s, fp, t):
    if not s or len(s) <= 2:
        return
    if s in msgids:
        return
    if s.startswith('{') or s.startswith('$') or s.startswith('#'):
        return
    # Skip single lowercase words (likely code identifiers)
    if re.match(r'^[a-z][a-z0-9_-]*$', s) and len(s) < 15:
        return
    # Skip known false positives
    blacklist = {'true', 'false', 'null', 'undefined', 'GET', 'POST', 'PUT', 'DELETE', 'PATCH',
                 'args', 'type', 'team_id', 'id', 'field', 'value', 'review', 'text', 'location',
                 'challenge_id', 'audience_id', ''}
    if s in blacklist:
        return
    # Skip CSS/HTML related
    if re.match(r'^(fa[sb]?\s|col-|btn-|text-|data-|role=|aria-|dropdown|modal|nav|tab|card|'
                r'list-|alert-|form-|custom-|float-|w-\d|p-\d|pt-|pb-|pr-|pl-|'
                r'm-\d|mt-|mb-|mr-|ml-|d-|justify-|align-|offset-|order-|bg-|border|'
                r'rounded|sr-only|no-|container|row$|col$|active$|show$|collapse$|fade$|'
                r'open$|close$|next$|prev$|page-item|page-link|input-group|form-control|'
                r'custom-select|custom-file|custom-checkbox|custom-radio|custom-sw|'
                r'custom-range|form-text|form-check|form-group|form-row|form-inline|'
                r'was-validated|invalid-feedback|valid-feedback)', s):
        return
    for existing in missing:
        if existing[1] == s:
            return
    missing.append((fp, s, t))

# --- Scan Python files ---
print(f"Scanning {len(py_files)} Python files...")
for fp in py_files:
    if not os.path.isfile(fp):
        continue
    try:
        with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except:
        continue

    # gettext("...")
    for m in re.finditer(r'gettext\("(.+?)"\)', content):
        add(m.group(1), fp, 'gettext')
    # ValidationError("...")
    for m in re.finditer(r'ValidationError\("(.+?)"\)', content):
        add(m.group(1), fp, 'ValidationError')
    # abort(N, "...")
    for m in re.finditer(r'abort\(\d+,\s*"(.+?)"\)', content):
        add(m.group(1), fp, 'abort')
    # flash("...")
    for m in re.finditer(r'flash\("(.+?)"\)', content):
        add(m.group(1), fp, 'flash')

    # jsonify errors: {"errors": {"key": ["string"]}}
    for m in re.finditer(r'"errors":\s*\{[^}]*"([^"]+)":\s*\["([^"]+)"\]', content):
        s = m.group(2)
        if s and s not in {'success', 'false', 'True', 'False', 'None', ''}:
            add(s, fp, 'jsonify')
    # jsonify errors: {"errors": {"key": "string"}}
    for m in re.finditer(r'"errors":\s*\{[^}]*"([^"]+)":\s*"([^"]+)"', content):
        s = m.group(2)
        if s and s not in {'success', 'false', 'True', 'False', 'None', ''}:
            add(s, fp, 'jsonify')

# --- Scan HTML templates ---
print(f"Scanning {len(html_files)} HTML templates...")
for fp in html_files:
    if not os.path.isfile(fp):
        continue
    try:
        with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except:
        continue

    # {% trans %}CONTENT{% endtrans %}
    for m in re.finditer(r'\{%\s*trans\s*%\}\s*(.+?)\s*\{%\s*endtrans\s*%\}', content, re.DOTALL):
        s = m.group(1).strip()
        s = re.sub(r'\s+', ' ', s)
        add(s, fp, 'trans_block')
    # {% trans "..." %}
    for m in re.finditer(r'\{%\s*trans\s+"(.+?)"\s*%\}', content):
        add(m.group(1), fp, 'trans_inline')

    # Hardcoded English in labels, alt text, placeholders OUTSIDE {% trans %} blocks
    cleaned = re.sub(r'\{%\s*trans\s*%\}.*?\{%\s*endtrans\s*%\}', '', content, flags=re.DOTALL)
    cleaned = re.sub(r'\{%\s*trans\s+".*?"\s*%\}', '', cleaned)
    cleaned = re.sub(r'\{\{.*?\}\}', '', cleaned)
    cleaned = re.sub(r'\{%\s*(?:if|for|block|set|with|extends|include|macro).*?%\}', '', cleaned)

    # label text: >English Text<
    for m in re.finditer(r'>([A-Z][a-z]+(?:\s+[A-Za-z]+){1,})<', cleaned):
        s = m.group(1).strip()
        if len(s) >= 4 and not re.match(r'^\d', s):
            skip = {'Submit', 'Update', 'Delete', 'Save', 'Edit', 'Create', 'Cancel', 'Back',
                    'Next', 'Previous', 'True', 'False', 'None', 'Search', 'Clear', 'Remove',
                    'Loading', 'Error', 'Success', 'Warning', 'Info', 'Draft', 'Published',
                    'Hidden', 'Visible', 'Static', 'Linear', 'Logarithmic', 'Case Sensitive',
                    'Case Insensitive', 'Build CSS', 'Required', 'Optional', 'Yes', 'No'}
            if s not in skip:
                add(s, fp, 'hardcoded_html')

    # placeholder="..."
    for m in re.finditer(r'placeholder="([^"]+)"', cleaned):
        s = m.group(1)
        if re.search(r'[A-Za-z]{3,}', s):
            add(s, fp, 'placeholder')

# --- Scan JS/Vue files ---
print(f"Scanning {len(js_files)} JS/Vue files...")
for fp in js_files:
    if not os.path.isfile(fp):
        continue
    try:
        with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except:
        continue

    # ezAlert/ezQuery/ezNotify/ezToast
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

# --- Results ---
# Remove duplicates
seen = set()
unique = []
for fp, s, t in missing:
    if s not in seen:
        seen.add(s)
        unique.append((fp, s, t))

print(f"\n=== MISSING: {len(unique)} ===")
for fp, s, t in unique:
    print(f"  [{t}] {os.path.basename(fp)}")
    print(f"    msgid: {s}")

sys.exit(0 if len(unique) == 0 else 1)
