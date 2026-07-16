#!/usr/bin/env python3
"""Fix wrong fuzzy translations and remove fuzzy flags."""
import re

po_file = "/workspace/CTFd/translations/zh_Hans_CN/LC_MESSAGES/messages.po"

# Corrected translations for wrong fuzzy matches
corrections = {
    "Click Here to Confirm Email": "点击此处确认邮箱",
    "Please enter a valid email address": "请输入有效的邮箱地址",
    "Your user name cannot be an email address": "用户名不能是邮箱地址",
    "Please provide a shorter affiliation": "请提供较短的所属机构名称",
    "Scoreboard has been frozen": "记分板已冻结",
    "try": "次",
    "Email settings not configured": "邮箱设置未配置",
    "User Name or Email": "用户名或邮箱",
    "Search": "搜索",
    "Upload Files": "上传文件",
    "Team Creation": "创建团队",
    "Name Changes": "名称更改",
    "Control whether users and teams can change their names": "控制用户和团队是否可以更改名称",
    "lockout": "锁定",
    "Public": "公开",
    "Private": "私有",
    "Admins Only": "仅管理员",
    "Mail Server Port": "邮件服务器端口",
    "Use Mail Server Username and Password": "使用邮件服务器用户名和密码",
    "Body": "正文",
    "Subject line for account verification email": "账户验证邮件的主题行",
    "Subject line for new account details email": "新账户详情邮件的主题行",
    "Subject line for password reset request email": "密码重置请求邮件的主题行",
    "Subject line for password reset confirmation email": "密码重置确认邮件的主题行",
    "Notification Type": "通知类型",
    "Toast": "Toast提示",
    "Alert": "警告",
    "Format": "格式",
    "Target": "目标",
    "Current Page": "当前页面",
    "Page Type": "页面类型",
    "Language": "语言",
    "Usage Description": "使用说明",
    "Admin Username": "管理员用户名",
    "Your username for the administration account": "您的管理员账号用户名",
    "Theme Color": "主题颜色",
    "Provided": "已提供",
    "Account ID": "账户 ID",
    "Team Name": "队伍名称",
    "Team Password": "队伍密码",
    "Email account credentials to user": "将账号凭据发送至用户邮箱",
    "Hint %(id)d": "提示 %(id)d",
    "Correct": "正确",
    "Your access token is invalid": "您的访问令牌无效",
    "Your access token has expired": "您的访问令牌已过期",
}

with open(po_file, "r", encoding="utf-8") as f:
    lines = f.read().split("\n")

output = []
i = 0
fixed_count = 0
fuzzy_removed = 0
total = len(lines)

while i < total:
    line = lines[i]
    
    # Handle comment lines - remove fuzzy flag
    if line.startswith("#"):
        if "fuzzy" in line:
            # Handle "#, fuzzy" or "#, fuzzy, python-format" or "#, python-format, fuzzy"
            # Remove "fuzzy" and clean up
            new_line = line
            if new_line == "#, fuzzy":
                # Skip this entire line (remove fuzzy flag)
                i += 1
                fuzzy_removed += 1
                continue
            else:
                # Remove "fuzzy" from combined flags
                new_line = new_line.replace(", fuzzy", "")
                new_line = new_line.replace("fuzzy, ", "")
                new_line = new_line.replace("fuzzy", "")
                if new_line == "#, ":
                    i += 1
                    fuzzy_removed += 1
                    continue
                output.append(new_line)
                i += 1
                fuzzy_removed += 1
                continue
        else:
            output.append(line)
            i += 1
            continue
    
    if line.startswith("msgid "):
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
        
        # Handle msgstr
        if i < total and lines[i].startswith("msgstr "):
            msgstr_line = lines[i]
            i += 1
            msgstr_content = msgstr_line[len("msgstr "):].strip()
            
            # Collect any continuation lines
            continuation = []
            while i < total and lines[i].startswith('"'):
                continuation.append(lines[i])
                i += 1
            
            # If we have a correction, replace the translation
            if full_msgid in corrections:
                output.append('msgstr "' + corrections[full_msgid] + '"')
                fixed_count += 1
                print(f"Corrected: {full_msgid[:70]}")
            else:
                # Keep original
                output.append(msgstr_line)
                output.extend(continuation)
        continue
    else:
        output.append(line)
        i += 1

with open(po_file, "w", encoding="utf-8") as f:
    f.write("\n".join(output))

print(f"\nTotal corrections: {fixed_count}")
print(f"Fuzzy flags removed: {fuzzy_removed}")
