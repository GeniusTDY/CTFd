#!/usr/bin/env python3
"""Extract all fuzzy translations for review using simple line parsing."""

po_file = "/workspace/CTFd/translations/zh_Hans_CN/LC_MESSAGES/messages.po"

with open(po_file, "r", encoding="utf-8") as f:
    lines = f.read().split("\n")

entries = []
current = None
state = None  # 'msgid', 'msgstr', 'comments'
in_fuzzy = False
msgid_lines = []
msgstr_lines = []

i = 0
while i < len(lines):
    line = lines[i]
    
    # Track fuzzy flag in comments
    if line.startswith("#"):
        if "fuzzy" in line:
            in_fuzzy = True
        i += 1
        continue
    
    if line.startswith("msgid "):
        # Start of new entry
        # Save previous if any
        if current is not None and in_fuzzy:
            msgid = "".join(msgid_lines)
            msgstr = "".join(msgstr_lines)
            if msgid:  # skip empty header
                entries.append((msgid, msgstr))
        
        # Reset for new entry
        in_fuzzy = False
        msgid_lines = []
        msgstr_lines = []
        
        # Extract first line content
        content = line[len("msgid "):].strip()
        if content.startswith('"') and content.endswith('"'):
            msgid_lines.append(content[1:-1])
        
        i += 1
        # Collect continuation lines
        while i < len(lines) and lines[i].startswith('"'):
            c = lines[i].strip()
            if c.startswith('"') and c.endswith('"'):
                msgid_lines.append(c[1:-1])
            i += 1
        current = "msgid"
        continue
    
    if line.startswith("msgstr "):
        content = line[len("msgstr "):].strip()
        if content.startswith('"') and content.endswith('"'):
            msgstr_lines.append(content[1:-1])
        
        i += 1
        # Collect continuation lines
        while i < len(lines) and lines[i].startswith('"'):
            c = lines[i].strip()
            if c.startswith('"') and c.endswith('"'):
                msgstr_lines.append(c[1:-1])
            i += 1
        continue
    
    i += 1

# Save last entry
if current is not None and in_fuzzy:
    msgid = "".join(msgid_lines)
    msgstr = "".join(msgstr_lines)
    if msgid:
        entries.append((msgid, msgstr))

print(f"Total fuzzy entries: {len(entries)}\n")
for idx, (msgid, msgstr) in enumerate(entries, 1):
    print(f"{idx}. MSGID: {msgid[:120]}")
    print(f"   MSGSTR: {msgstr[:120]}")
    print()
