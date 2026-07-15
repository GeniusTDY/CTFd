#!/usr/bin/env python3.11
"""Comprehensive scan for ALL untranslated strings - Round 1.
Covers: Python (all user-facing strings), HTML, Vue, JS, Forms."""
import os
import re
import sys
from babel.messages.pofile import read_po

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
# 1. Python: ALL user-facing strings (abort, jsonify, flash, ValidationError, render_template strings)
# ============================================================
print("\n=== 1. Python user-facing strings ===")

# Patterns that indicate user-facing strings
py_patterns = [
    # abort(403, "message") or abort(403, 'message')
    (re.compile(r'abort\(\s*\d+\s*,\s*"([^"\\]*(?:\\.[^"\\]*)*)"'), 'abort'),
    (re.compile(r"abort\(\s*\d+\s*,\s*'([^'\\]*(?:\\.[^'\\]*)*)'"), 'abort'),
    # ValidationError("message")
    (re.compile(r'ValidationError\(\s*"([^"\\]*(?:\\.[^"\\]*)*)"'), 'validation'),
    (re.compile(r"ValidationError\(\s*'([^'\\]*(?:\\.[^'\\]*)*)'"), 'validation'),
    # flash("message")
    (re.compile(r'flash\(\s*"([^"\\]*(?:\\.[^"\\]*)*)"'), 'flash'),
    (re.compile(r"flash\(\s*'([^'\\]*(?:\\.[^'\\]*)*)'"), 'flash'),
    # jsonify(error="message"), jsonify(message="...")
    (re.compile(r'jsonify\(\s*(?:error|message|msg)\s*=\s*"([^"\\]*(?:\\.[^"\\]*)*)"'), 'jsonify'),
    (re.compile(r"jsonify\(\s*(?:error|message|msg)\s*=\s*'([^'\\]*(?:\\.[^'\\]*)*)'"), 'jsonify'),
    # "message": "..." in jsonify dict
    (re.compile(r'"message"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"'), 'jsonify_dict'),
    # gettext("...") - these are already translated, skip
    # _l("...") - lazy_gettext, already translated, skip
]

py_count = 0
for root, dirs, files in os.walk(CTFD):
    skip = ['/translations', '/.git', '/node_modules', '/static/assets', '/__pycache__', '/.venv', '/venv', '/site-packages']
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
        
        # Check if gettext/_l is used for this string by looking at context
        for pat, ptype in py_patterns:
            for m in pat.finditer(content):
                text = m.group(1)
                if not text or len(text) < 2:
                    continue
                # Skip format-only strings
                if text.startswith('%') or text.startswith('{') or text.startswith('<'):
                    continue
                # Check if already wrapped in gettext/_l by looking at preceding chars
                start = max(0, m.start() - 30)
                preceding = content[start:m.start()]
                if 'gettext(' in preceding or '_l(' in preceding or 'lazy_gettext(' in preceding:
                    continue
                # Must look like English text
                if not re.match(r'^[A-Z]', text):
                    continue
                if text in existing_msgids:
                    continue
                rel = os.path.relpath(fpath, CTFD)
                missing.append((ptype, rel, text))
                py_count += 1

print(f"Python missing: {py_count}")

# ============================================================
# 2. Forms: WTForms labels, validators, descriptions
# ============================================================
print("\n=== 2. WTForms labels and validators ===")
form_count = 0
for root, dirs, files in os.walk(CTFD + '/forms'):
    for fname in files:
        if not fname.endswith('.py'):
            continue
        fpath = os.path.join(root, fname)
        try:
            with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except:
            continue
        # Look for label="...", description="...", validators=[...]
        # Also look for _l("...") which is lazy_gettext - these ARE translated
        # Look for plain string labels not wrapped in _l()
        for m in re.finditer(r'label\s*=\s*"([^"]{2,80})"', content):
            text = m.group(1)
            if text in existing_msgids:
                continue
            if not re.match(r'^[A-Z]', text):
                continue
            rel = os.path.relpath(fpath, CTFD)
            missing.append(('form_label', rel, text))
            form_count += 1
        for m in re.finditer(r"description\s*=\s*\"([^\"]{2,120})\"", content):
            text = m.group(1)
            if text in existing_msgids:
                continue
            if not re.match(r'^[A-Z]', text):
                continue
            rel = os.path.relpath(fpath, CTFD)
            missing.append(('form_desc', rel, text))
            form_count += 1

print(f"Forms missing: {form_count}")

# ============================================================
# 3. HTML: ALL hardcoded English text (broader patterns)
# ============================================================
print("\n=== 3. HTML hardcoded text (broad) ===")
html_count = 0
html_patterns = [
    # <label>text</label>
    (re.compile(r'<label(?:\s[^>]*)?>([A-Z][a-zA-Z\s:,.\'()&;-]{1,100})</label>'), 'label'),
    # <h1-6>text</h1-6>
    (re.compile(r'<h[1-6](?:\s[^>]*)?>([A-Z][a-zA-Z\s:,.\'()-]{1,100})</h[1-6]>'), 'heading'),
    # <small>text</small>
    (re.compile(r'<small(?:\s[^>]*)?>([A-Z][a-zA-Z\s:,.\'()!?&;-]{1,150})</small>'), 'small'),
    # <b>text</b>
    (re.compile(r'<b(?:\s[^>]*)?>([A-Z][a-zA-Z\s:,.()&;-]{1,60})</b>'), 'b'),
    # <td>text</td> with bold
    (re.compile(r'<td(?:\s[^>]*)?><b>([A-Z][a-zA-Z\s:,.()&;-]{1,60})</b></td>'), 'td_b'),
    # <th>text</th>
    (re.compile(r'<th(?:\s[^>]*)?>([A-Z][a-zA-Z\s:,.()&;-]{1,60})</th>'), 'th'),
    # <span>text</span> - word only
    (re.compile(r'<span(?:\s[^>]*)?>([A-Z][a-z]{3,25})</span>'), 'span'),
    # <option>text</option>
    (re.compile(r'<option(?:\s[^>]*)?>([A-Z][a-zA-Z\s:,.()&;-]{1,80})</option>'), 'option'),
    # <button>text</button>
    (re.compile(r'<button(?:\s[^>]*)?>([A-Z][a-zA-Z\s:,.()&;-]{1,50})</button>'), 'button'),
    # <legend>text</legend>
    (re.compile(r'<legend(?:\s[^>]*)?>([A-Z][a-zA-Z\s:,.()&;-]{1,60})</legend>'), 'legend'),
    # <abbr title="text">
    (re.compile(r'<abbr(?:\s[^>]*)?>([A-Z][a-zA-Z\s:,.()&;-]{1,40})</abbr>'), 'abbr'),
    # placeholder="text"
    (re.compile(r'placeholder="([A-Z][^"]{2,80})"'), 'placeholder'),
    # title="text" in elements
    (re.compile(r'title="([A-Z][^"]{2,80})"'), 'title_attr'),
    # aria-label="text"
    (re.compile(r'aria-label="([A-Z][^"]{2,80})"'), 'aria_label'),
    # value="text" (submit buttons)
    (re.compile(r'value="([A-Z][a-zA-Z\s:,.()&;-]{2,50})"'), 'value'),
    # <p>text</p> - paragraphs
    (re.compile(r'<p(?:\s[^>]*)?>([A-Z][a-zA-Z\s:,.()\'!?&;-]{3,150})</p>'), 'paragraph'),
    # <a ...>text</a> link text
    (re.compile(r'<a\s[^>]*>([A-Z][a-zA-Z\s:,.()&;-]{2,60})</a>'), 'a_link'),
]

for root, dirs, files in os.walk(CTFD + '/themes'):
    skip = ['/static/assets', '/node_modules', '/static/js/']
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
        
        # Remove {% trans %}...{% endtrans %} blocks
        cleaned = re.sub(r'\{%\s*trans[^%]*%\}.*?\{%\s*endtrans\s*%\}', '', content, flags=re.DOTALL)
        # Remove {{ ... }} Jinja expressions
        cleaned = re.sub(r'\{\{[^}]*\}\}', '', cleaned)
        # Remove HTML comments
        cleaned = re.sub(r'<!--.*?-->', '', cleaned, flags=re.DOTALL)
        # Remove Jinja comments
        cleaned = re.sub(r'\{#.*?#\}', '', cleaned, flags=re.DOTALL)
        # Remove Jinja block tags {% ... %}
        cleaned = re.sub(r'\{%[^%]*%\}', '', cleaned)
        
        for pat, ptype in html_patterns:
            for m in pat.finditer(cleaned):
                text = m.group(1).strip()
                if not text or len(text) < 2:
                    continue
                # Skip if contains HTML/Jinja remnants
                if '{' in text or '<' in text or '&' in text:
                    # Allow &hellip; &amp; etc? No, skip to be safe
                    if text.startswith('&') or '<' in text:
                        continue
                if text.startswith('/'):
                    continue
                # Skip pure numbers
                if text.isdigit():
                    continue
                if text in existing_msgids:
                    continue
                rel = os.path.relpath(fpath, CTFD)
                missing.append((ptype, rel, text))
                html_count += 1

print(f"HTML missing: {html_count}")

# ============================================================
# 4. Vue components: template strings
# ============================================================
print("\n=== 4. Vue component templates ===")
vue_count = 0
for root, dirs, files in os.walk(CTFD):
    skip = ['/translations', '/.git', '/node_modules', '/static/assets', '/__pycache__', '/static/js/']
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
        
        # Remove {{ }} expressions
        cleaned = re.sub(r'\{\{[^}]*\}\}', '', tmpl)
        
        # >English text<
        for m in re.finditer(r'>([A-Z][a-zA-Z\s:,.()\'!?&;-]{2,60})<', cleaned):
            text = m.group(1).strip()
            if not text or len(text) < 3:
                continue
            if text in existing_msgids:
                continue
            rel = os.path.relpath(fpath, CTFD)
            missing.append(('vue_text', rel, text))
            vue_count += 1
        
        # placeholder="...", title="...", label="..."
        for m in re.finditer(r'(?:placeholder|title|label|aria-label)="([A-Z][^"]{2,80})"', cleaned):
            text = m.group(1).strip()
            if not text or len(text) < 3:
                continue
            if text in existing_msgids:
                continue
            rel = os.path.relpath(fpath, CTFD)
            missing.append(('vue_attr', rel, text))
            vue_count += 1

print(f"Vue missing: {vue_count}")

# ============================================================
# 5. JS: dialog strings (ezAlert, ezQuery, ezNotify, ezToast, confirm)
# ============================================================
print("\n=== 5. JS dialog strings ===")
js_count = 0
for root, dirs, files in os.walk(CTFD):
    skip = ['/translations', '/.git', '/node_modules', '/static/assets', '/__pycache__', '/static/js/']
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
        # title: "..." or body: "..." or button: "..." 
        for m in re.finditer(r'(?:title|body|button)\s*:\s*"([^"\\]{3,120})"', content):
            text = m.group(1).strip()
            if not text:
                continue
            if 'CTFd._' in text or 'gettext' in text:
                continue
            if text in existing_msgids:
                continue
            rel = os.path.relpath(fpath, CTFD)
            missing.append(('js_dialog', rel, text))
            js_count += 1
        # confirm("...")
        for m in re.finditer(r'confirm\(\s*"([^"\\]{5,120})"', content):
            text = m.group(1).strip()
            if not text:
                continue
            if text in existing_msgids:
                continue
            rel = os.path.relpath(fpath, CTFD)
            missing.append(('js_confirm', rel, text))
            js_count += 1

print(f"JS missing: {js_count}")

# ============================================================
# Summary
# ============================================================
print(f"\n{'='*60}")
print(f"ROUND 1 TOTAL: {len(missing)}")
print(f"{'='*60}")

# Deduplicate
seen = set()
unique = []
for cat, fp, text in missing:
    key = (fp, text)
    if key not in seen:
        seen.add(key)
        unique.append((cat, fp, text))

print(f"Unique: {len(unique)}")
print()
for cat, fp, text in sorted(unique):
    print(f"  [{cat}] {fp} - {text[:90]}")
