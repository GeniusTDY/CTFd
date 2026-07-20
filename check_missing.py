"""Extract strings from templates and generate messages.po with translations."""
import re
import os
import sys

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

# Load translations from the dictionary in gen_po.py
# We'll exec the gen_po.py to get the TRANSLATIONS dict
import importlib.util
spec = importlib.util.spec_from_file_location("gen_po", "/workspace/gen_po.py")
gen_po = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen_po)

TRANSLATIONS = gen_po.TRANSLATIONS

# Find missing translations
missing = []
for s in sorted(all_strings):
    if s not in TRANSLATIONS:
        missing.append(s)

print(f"Total strings in templates: {len(all_strings)}")
print(f"Translations provided: {len(TRANSLATIONS)}")
print(f"Missing translations: {len(missing)}")
if missing:
    print("\nMISSING STRINGS (need translation):")
    for s in missing:
        escaped = s.replace('\n', '\\n')
        print(f"  {repr(escaped)}")
