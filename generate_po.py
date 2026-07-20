"""Generate the final messages.po file."""
import os
import sys

# Import translations from gen_po.py
sys.path.insert(0, '/workspace')
from gen_po import TRANSLATIONS

header = '''msgid ""
msgstr ""
"Project-Id-Version: CTFd Remote Desktop Plugin 1.0\\n"
"POT-Creation-Date: 2026-07-20 00:00+0800\\n"
"Language: zh_Hans_CN\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
"Plural-Forms: nplurals=1; plural=0;\\n"

'''

def escape(s):
    """Escape string for .po format."""
    return s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\t', '\\t')

# Only include translations that are actually used in templates
# Import the extract function
import importlib.util
spec = importlib.util.spec_from_file_location("check_missing", "/workspace/check_missing.py")
check_missing = importlib.util.module_from_spec(spec)
# Don't exec - we just need the extract function

# Re-import extract function directly
import re
TEMPLATES = [
    '/workspace/CTFd/plugins/ctfd-remote-desktop/src/templates/remote_desktop.html',
    '/workspace/CTFd/plugins/ctfd-remote-desktop/src/templates/remote_desktop_config.html',
    '/workspace/CTFd/plugins/ctfd-remote-desktop/src/templates/remote_desktop_dashboard.html',
]
TRANS_RE = re.compile(r'\{%\s*trans\s*%\}(.*?)\{%\s*endtrans\s*%\}', re.DOTALL)

def extract_from_underscore(text):
    results = set()
    i = 0
    while i < len(text):
        idx = text.find('_(', i)
        if idx == -1:
            break
        j = idx + 2
        while j < len(text) and text[j] in ' \t\n':
            j += 1
        if j >= len(text) or text[j] not in ('"', "'"):
            i = idx + 2
            continue
        quote = text[j]
        k = j + 1
        s = []
        while k < len(text):
            c = text[k]
            if c == '\\' and k + 1 < len(text):
                next_c = text[k+1]
                if next_c == 'n':
                    s.append('\n')
                elif next_c == 't':
                    s.append('\t')
                elif next_c == 'r':
                    s.append('\r')
                elif next_c == '\\':
                    s.append('\\')
                elif next_c == quote:
                    s.append(quote)
                else:
                    s.append(next_c)
                k += 2
            elif c == quote:
                break
            else:
                s.append(c)
                k += 1
        if k < len(text):
            results.add(''.join(s))
        i = k + 1
    return results

all_strings = set()
for tpl_path in TEMPLATES:
    with open(tpl_path, 'r') as f:
        content = f.read()
    for m in TRANS_RE.finditer(content):
        s = m.group(1).strip()
        if s:
            all_strings.add(s)
    strs = extract_from_underscore(content)
    all_strings.update(strs)

# Generate .po file with only used strings
lines = [header]
for en in sorted(all_strings, key=str.lower):
    if en in TRANSLATIONS:
        zh = TRANSLATIONS[en]
    else:
        zh = en  # Fallback to English if missing
    lines.append(f'msgid "{escape(en)}"')
    lines.append(f'msgstr "{escape(zh)}"')
    lines.append('')

content = '\n'.join(lines)

# Write the .po file
po_path = '/workspace/CTFd/plugins/ctfd-remote-desktop/translations/zh_Hans_CN/LC_MESSAGES/messages.po'
os.makedirs(os.path.dirname(po_path), exist_ok=True)
with open(po_path, 'w') as f:
    f.write(content)

print(f"Generated {len(all_strings)} translation entries")
print(f"Written to: {po_path}")
print(f"File size: {len(content)} chars")
