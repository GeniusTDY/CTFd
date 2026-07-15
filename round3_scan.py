#!/usr/bin/env python3.11
"""Round 3: Comprehensive scan for missing translations across ALL file types."""
import os
import re
import sys
from babel.messages.pofile import read_po

# Get existing msgids from PO file
po_path = '/workspace/CTFd/translations/zh_Hans_CN/LC_MESSAGES/messages.po'
with open(po_path, 'rb') as f:
    catalog = read_po(f)

existing_msgids = set()
for msg in catalog:
    mid = msg.id
    if isinstance(mid, tuple):
        mid = mid[0] if mid else ''
    if mid and isinstance(mid, str):
        existing_msgids.add(mid)

print(f"Existing PO entries: {len(existing_msgids)}")

CTFD = '/workspace/CTFd'
missing = []

# ============================================================
# 1. Scan Python files for gettext(), ValidationError(), abort(), flash(), jsonify() strings
# ============================================================
print("\n=== Scanning Python files ===")
py_patterns = [
    # gettext("..."), _("..."), gettext('...')
    re.compile(r'''(?:gettext|_)\(\s*['"]((?:[^'"\\]|\\.)*)['"]\s*'''),
    # ValidationError("...")
    re.compile(r'''ValidationError\(\s*['"]((?:[^'"\\]|\\.)*)['"]\s*'''),
    # abort(403, "..."), abort(400, "...")
    re.compile(r'''abort\(\s*\d+\s*,\s*['"]((?:[^'"\\]|\\.)*)['"]\s*'''),
    # flash("...")
    re.compile(r'''flash\(\s*['"]((?:[^'"\\]|\\.)*)['"]\s*'''),
    # jsonify({"message": "..."}) or jsonify(error="...")
    re.compile(r'''"message"\s*:\s*["']((?:[^"'\\]|\\.)*)['"]'''),
    # jsonify(error="..."), jsonify(msg="..."), jsonify(errors=[...])
    re.compile(r'jsonify\(\s*(?:error|msg|message)\s*=\s*"([^"\\]*(?:\\.[^"\\]*)*)"'),
]

py_count = 0
for root, dirs, files in os.walk(CTFD):
    # Skip unnecessary directories
    skip = ['/translations', '/.git', '/node_modules', '/static/assets', '/__pycache__', '/.venv', '/venv']
    if any(s in root for s in skip):
        continue
    for fname in files:
        if not fname.endswith('.py'):
            continue
        fpath = os.path.join(root, fname)
        try:
            with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except:
            continue
        for pat in py_patterns:
            for m in pat.finditer(content):
                text = m.group(1)
                if not text or len(text) < 2:
                    continue
                # Skip if it's a format string variable or code
                if text.startswith('%') or text.startswith('{'):
                    continue
                if text in existing_msgids:
                    continue
                # Check if it looks like a real English sentence/phrase
                if re.match(r'^[A-Z]', text) and len(text) > 3:
                    rel = os.path.relpath(fpath, CTFD)
                    missing.append(('python', rel, text))
                    py_count += 1

print(f"Python missing: {py_count}")

# ============================================================
# 2. Scan JS files for ezAlert/ezQuery/ezNotify/ezToast/dialog strings
# ============================================================
print("\n=== Scanning JS/Vue files for dialog strings ===")
js_patterns = [
    re.compile(r'ezAlert\(\s*\{[^}]*title:\s*"([^"]+)"'),
    re.compile(r'ezQuery\(\s*\{[^}]*title:\s*"([^"]+)"'),
    re.compile(r'ezNotify\(\s*\{[^}]*title:\s*"([^"]+)"'),
    re.compile(r'ezToast\(\s*\{[^}]*title:\s*"([^"]+)"'),
    re.compile(r'ezAlert\(\s*\{[^}]*body:\s*"([^"]+)"'),
    re.compile(r'ezQuery\(\s*\{[^}]*body:\s*"([^"]+)"'),
    re.compile(r'ezAlert\(\s*\{[^}]*button:\s*"([^"]+)"'),
    re.compile(r'ezQuery\(\s*\{[^}]*button:\s*"([^"]+)"'),
]

js_count = 0
for root, dirs, files in os.walk(CTFD):
    skip = ['/translations', '/.git', '/node_modules', '/static/assets', '/__pycache__']
    if any(s in root for s in skip):
        continue
    for fname in files:
        if not (fname.endswith('.js') or fname.endswith('.vue')):
            continue
        fpath = os.path.join(root, fname)
        try:
            with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except:
            continue
        for pat in js_patterns:
            for m in pat.finditer(content):
                text = m.group(1)
                if not text or len(text) < 2:
                    continue
                if text in existing_msgids:
                    continue
                rel = os.path.relpath(fpath, CTFD)
                missing.append(('js_dialog', rel, text))
                js_count += 1

print(f"JS/Vue dialog missing: {js_count}")

# ============================================================
# 3. Scan Vue .vue files for hardcoded English in <template> sections
# ============================================================
print("\n=== Scanning Vue component templates ===")
vue_count = 0
for root, dirs, files in os.walk(CTFD):
    skip = ['/translations', '/.git', '/node_modules', '/static/assets', '/__pycache__']
    if any(s in root for s in skip):
        continue
    for fname in files:
        if not fname.endswith('.vue'):
            continue
        fpath = os.path.join(root, fname)
        try:
            with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except:
            continue
        # Extract template section
        tmpl_match = re.search(r'<template>(.*?)</template>', content, re.DOTALL)
        if not tmpl_match:
            continue
        tmpl = tmpl_match.group(1)
        
        # Find text content in HTML elements that's not inside {{ }} or v- directives
        # Look for >English text< patterns
        for m in re.finditer(r'>([A-Z][a-zA-Z\s]{2,40})<', tmpl):
            text = m.group(1).strip()
            if not text or len(text) < 3:
                continue
            # Skip if it looks like a Vue variable or directive
            if '{{' in text or 'v-' in text:
                continue
            # Skip common false positives
            if text in ['div', 'span', 'template']:
                continue
            if text in existing_msgids:
                continue
            rel = os.path.relpath(fpath, CTFD)
            missing.append(('vue_template', rel, text))
            vue_count += 1
        
        # Look for placeholder="..." and title="..." attributes
        for m in re.finditer(r'(?:placeholder|title|label)=["\']([A-Z][^"\']{2,60})["\']', tmpl):
            text = m.group(1).strip()
            if not text or len(text) < 3:
                continue
            if '{{' in text:
                continue
            if text in existing_msgids:
                continue
            rel = os.path.relpath(fpath, CTFD)
            missing.append(('vue_attr', rel, text))
            vue_count += 1

print(f"Vue template missing: {vue_count}")

# ============================================================
# 4. Scan HTML templates for remaining hardcoded English text
# ============================================================
print("\n=== Scanning HTML templates for remaining hardcoded text ===")
html_count = 0
# Patterns for hardcoded English in HTML
html_patterns = [
    # <label>text</label> not containing {% trans %}
    re.compile(r'<label(?:\s[^>]*)?>([A-Z][a-zA-Z\s:]{2,80})</label>'),
    # <h1>-<h6>text</h1>-</h6>
    re.compile(r'<h[1-6](?:\s[^>]*)?>([A-Z][a-zA-Z\s]{2,80})</h[1-6]>'),
    # <small>text</small>
    re.compile(r'<small(?:\s[^>]*)?>([A-Z][a-zA-Z\s,.!?\'-]{2,120})</small>'),
    # <b>text</b>
    re.compile(r'<b>([A-Z][a-zA-Z\s]{2,40})</b>'),
    # <span>text</span> (only if it looks like a word/phrase)
    re.compile(r'<span(?:\s[^>]*)?>([A-Z][a-z]{3,20})</span>'),
    # <option>text</option>
    re.compile(r'<option(?:\s[^>]*)?>([A-Z][a-zA-Z\s()]{2,60})</option>'),
    # <button>text</button>
    re.compile(r'<button(?:\s[^>]*)?>([A-Z][a-zA-Z\s]{2,40})</button>'),
    # placeholder="text"
    re.compile(r'placeholder=["\']([A-Z][^"\']{2,60})["\']'),
    # value="text" (for submit buttons)
    re.compile(r'value=["\']([A-Z][a-zA-Z\s]{2,40})["\']'),
    # <legend>text</legend>
    re.compile(r'<legend(?:\s[^>]*)?>([A-Z][a-zA-Z\s]{2,60})</legend>'),
    # <abbr>text</abbr>
    re.compile(r'<abbr(?:\s[^>]*)?>([A-Z][a-zA-Z\s]{2,40})</abbr>'),
]

for root, dirs, files in os.walk(CTFD + '/themes'):
    skip = ['/static/assets', '/node_modules']
    if any(s in root for s in skip):
        continue
    for fname in files:
        if not fname.endswith('.html'):
            continue
        fpath = os.path.join(root, fname)
        try:
            with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except:
            continue
        
        # Remove {% trans %}...{% endtrans %} blocks to avoid matching inside them
        cleaned = re.sub(r'\{%\s*trans[^%]*%\}.*?\{%\s*endtrans\s*%\}', '', content, flags=re.DOTALL)
        # Also remove {{ ... }} Jinja expressions
        cleaned = re.sub(r'\{\{[^}]*\}\}', '', cleaned)
        # Remove HTML comments
        cleaned = re.sub(r'<!--.*?-->', '', cleaned, flags=re.DOTALL)
        # Remove Jinja comments
        cleaned = re.sub(r'\{#.*?#\}', '', cleaned, flags=re.DOTALL)
        
        for pat in html_patterns:
            for m in pat.finditer(cleaned):
                text = m.group(1).strip()
                if not text or len(text) < 2:
                    continue
                # Skip if text contains { or < (likely HTML)
                if '{' in text or '<' in text:
                    continue
                # Skip if it's just whitespace or entities
                if text.startswith('&') or text.startswith('/'):
                    continue
                if text in existing_msgids:
                    continue
                rel = os.path.relpath(fpath, CTFD)
                missing.append(('html', rel, text))
                html_count += 1

print(f"HTML remaining missing: {html_count}")

# ============================================================
# 5. Scan JS files for CTFd._.translations / ezAlert / ezQuery / ezNotify / ezToast
# ============================================================
print("\n=== Scanning JS files for untranslated dialog strings (deeper) ===")
js_deep_count = 0
# Look for strings passed to ezAlert/ezQuery/etc that are NOT CTFd._.t() calls
for root, dirs, files in os.walk(CTFD):
    skip = ['/translations', '/.git', '/node_modules', '/static/assets', '/__pycache__']
    if any(s in root for s in skip):
        continue
    for fname in files:
        if not (fname.endswith('.js') or fname.endswith('.vue')):
            continue
        fpath = os.path.join(root, fname)
        try:
            with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except:
            continue
        
        # Look for title: "..." or body: "..." or button: "..." in ez* calls
        for m in re.finditer(r'(?:title|body|button)\s*:\s*["\']([A-Z][^"\']{3,80})["\']', content):
            text = m.group(1).strip()
            if not text:
                continue
            # Skip if it uses translation function
            if 'CTFd._' in text or 'gettext' in text or 'lang' in text:
                continue
            if text in existing_msgids:
                continue
            rel = os.path.relpath(fpath, CTFD)
            missing.append(('js_dialog_deep', rel, text))
            js_deep_count += 1

print(f"JS dialog deep missing: {js_deep_count}")

# ============================================================
# Summary
# ============================================================
print(f"\n{'='*60}")
print(f"ROUND 3 TOTAL MISSING: {len(missing)}")
print(f"{'='*60}")

# Deduplicate
seen = set()
unique_missing = []
for category, filepath, text in missing:
    key = (filepath, text)
    if key not in seen:
        seen.add(key)
        unique_missing.append((category, filepath, text))

print(f"Unique missing: {len(unique_missing)}")
print()

for cat, fp, text in sorted(unique_missing):
    print(f"  [{cat}] {fp} - {text[:80]}")
