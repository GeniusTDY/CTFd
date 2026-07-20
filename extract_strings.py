"""Extract all strings wrapped with _() and {% trans %} from plugin templates."""
import re
import os
import sys

TEMPLATES = [
    '/workspace/CTFd/plugins/ctfd-remote-desktop/src/templates/remote_desktop.html',
    '/workspace/CTFd/plugins/ctfd-remote-desktop/src/templates/remote_desktop_config.html',
    '/workspace/CTFd/plugins/ctfd-remote-desktop/src/templates/remote_desktop_dashboard.html',
]

# Patterns to extract translatable strings
# 1. {% trans %}TEXT{% endtrans %}
TRANS_RE = re.compile(r'\{%\s*trans\s*%\}(.*?)\{%\s*endtrans\s*%\}', re.DOTALL)
# 2. {{ _('TEXT') }} and _( 'TEXT' ) in JS — handle single, double quotes, and escaped quotes
# We need to handle: _('...'), _("..."), {{ _('...') }}, _('...\'...')
def extract_from_underscore(text):
    """Extract strings from _() calls, handling escaped quotes."""
    results = set()
    i = 0
    while i < len(text):
        # Find _(
        idx = text.find('_(', i)
        if idx == -1:
            break
        # Find the opening quote
        j = idx + 2
        # Skip whitespace
        while j < len(text) and text[j] in ' \t\n':
            j += 1
        if j >= len(text) or text[j] not in ('"', "'"):
            i = idx + 2
            continue
        quote = text[j]
        # Find closing quote, handling escapes
        k = j + 1
        s = []
        while k < len(text):
            c = text[k]
            if c == '\\' and k + 1 < len(text):
                # Escape sequence
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
    # Extract {% trans %} blocks
    for m in TRANS_RE.finditer(content):
        s = m.group(1).strip()
        if s:
            all_strings.add(s)
    # Extract _() calls
    strs = extract_from_underscore(content)
    all_strings.update(strs)

print(f"Total unique strings: {len(all_strings)}")
print()

# Sort and print
for s in sorted(all_strings):
    # Show with escapes for visibility
    escaped = s.replace('\n', '\\n').replace('\t', '\\t')
    print(repr(escaped))
