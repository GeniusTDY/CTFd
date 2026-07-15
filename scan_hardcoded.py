import re, os, subprocess

po_path = '/workspace/CTFd/translations/zh_Hans_CN/LC_MESSAGES/messages.po'
po = open(po_path, 'r').read()

msgids = set()
for m in re.finditer(r'^msgid "(.+?)"', po, re.MULTILINE):
    mid = m.group(1)
    if mid and len(mid) > 1:
        msgids.add(mid)

# Get all HTML templates
result = subprocess.check_output(
    ['find', '/workspace/CTFd/themes', '-name', '*.html', '-type', 'f'],
    text=True
).strip()
html_files = [f for f in result.split('\n') if f]

# Look for hardcoded English text in labels, placeholders, buttons, etc.
# that are NOT inside {% trans %} blocks
missing = {}
for fp in html_files:
    try:
        with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except:
        continue
    
    # Remove {% trans %}...{% endtrans %} blocks
    cleaned = re.sub(r'\{%\s*trans\s*%\}.*?\{%\s*endtrans\s*%\}', '', content, flags=re.DOTALL)
    
    # Look for English text in common HTML patterns
    # placeholder="..."
    for m in re.finditer(r'placeholder="([^"]+)"', cleaned):
        s = m.group(1)
        if re.search(r'[A-Za-z]{3,}', s) and s not in msgids and len(s) > 3:
            if '{' not in s and '{{' not in s and '{%' not in s:
                if s not in missing:
                    missing[s] = fp
    
    # value="..."  (for buttons)
    for m in re.finditer(r'value="([^"]+)"', cleaned):
        s = m.group(1)
        if re.search(r'[A-Za-z]{3,}', s) and s not in msgids and len(s) > 3:
            if '{' not in s and '{{' not in s and '{%' not in s:
                if s not in missing:
                    missing[s] = fp
    
    # title="..."
    for m in re.finditer(r'title="([^"]+)"', cleaned):
        s = m.group(1)
        if re.search(r'[A-Za-z]{3,}', s) and s not in msgids and len(s) > 3:
            if '{' not in s and '{{' not in s and '{%' not in s:
                if s not in missing:
                    missing[s] = fp
    
    # >Text< pattern (button/label text)
    for m in re.finditer(r'>([A-Z][a-z]+(?:\s+[A-Za-z]+){1,})<', cleaned):
        s = m.group(1).strip()
        if s not in msgids and len(s) > 3:
            if s not in ('True', 'False', 'None', 'Submit', 'Update', 'Delete', 'Save', 'Edit', 'Create', 'Cancel', 'Close', 'Back', 'Next', 'Previous'):
                if not re.match(r'^(fa[sb]?\s|col-|btn-|text-|data-|role=|aria-)', s):
                    if s not in missing and '{' not in s:
                        missing[s] = fp

print(f'Potential hardcoded English in HTML: {len(missing)}')
for s, fp in sorted(missing.items()):
    print(f'  [{os.path.basename(fp)}] {s}')
