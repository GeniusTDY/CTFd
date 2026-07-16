#!/usr/bin/env python3
"""Add missing Chinese translations to the .po file."""
import re

po_file = "/workspace/CTFd/translations/zh_Hans_CN/LC_MESSAGES/messages.po"

translations = {
    "Not accepted. Try again in %(seconds)d seconds": "不接受。请在 %(seconds)d 秒后重试",
    "Not accepted. You have 0 tries remaining": "不接受。您还剩 0 次尝试机会",
    "You're submitting flags too fast. Try again in %(seconds)d seconds.": "您提交 flag 的速度太快。请在 %(seconds)d 秒后重试。",
    "%(message)s but you already solved this": "%(message)s 但您已经解出了此题目",
    "%(message)s You have %(num)d %(tries)s remaining.": "%(message)s 您还剩 %(num)d %(tries)s。",
    " Try again in %(seconds)d seconds": " 请在 %(seconds)d 秒后重试",
    "Require password change on next login": "下次登录时需要修改密码",
    "Message from {ctf_name}": "来自 {ctf_name} 的消息",
    "%(error)s exception occured while handling your request": "处理您的请求时发生 %(error)s 异常",
    "Mailgun settings are incorrect": "Mailgun 设置不正确",
    "SMTP server connection timed out": "SMTP 服务器连接超时",
}

with open(po_file, "r", encoding="utf-8") as f:
    lines = f.read().split("\n")

output = []
i = 0
fixed_count = 0
total = len(lines)
while i < total:
    line = lines[i]

    if line.startswith("msgid "):
        # Collect full msgid block (comments + msgid lines)
        block_start = len(output)
        msgid_lines = [line]
        first_str = line[len("msgid "):].strip()
        i += 1

        if first_str == '""':
            while i < total and lines[i].startswith('"'):
                msgid_lines.append(lines[i])
                i += 1

        # Reconstruct full msgid
        full_msgid = ""
        for ml in msgid_lines:
            stripped = ml.strip()
            if stripped.startswith("msgid "):
                inner = stripped[len("msgid "):].strip()
            else:
                inner = stripped
            if inner.startswith('"') and inner.endswith('"'):
                full_msgid += inner[1:-1]

        output.extend(msgid_lines)

        # Now handle msgstr
        if i < total and lines[i].startswith("msgstr "):
            msgstr_line = lines[i]
            i += 1
            msgstr_content = msgstr_line[len("msgstr "):].strip()

            if msgstr_content == '""':
                # Collect any continuation lines
                continuation = []
                while i < total and lines[i].startswith('"'):
                    continuation.append(lines[i])
                    i += 1

                if not continuation:
                    # Truly empty - translate if we have it
                    if full_msgid in translations:
                        output.append('msgstr "' + translations[full_msgid] + '"')
                        fixed_count += 1
                        print(f"Fixed: {full_msgid[:70]}")
                    else:
                        output.append(msgstr_line)
                else:
                    # Has translation already
                    output.append(msgstr_line)
                    output.extend(continuation)
            else:
                output.append(msgstr_line)
        continue
    else:
        output.append(line)
        i += 1

with open(po_file, "w", encoding="utf-8") as f:
    f.write("\n".join(output))

print(f"\nTotal fixed: {fixed_count}")
