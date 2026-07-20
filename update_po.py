#!/usr/bin/env python3
"""Update messages.po to replace concatenated i18n fragments with single placeholder strings."""
import re
from pathlib import Path

PO = Path("/workspace/CTFd/plugins/ctfd-remote-desktop/translations/zh_Hans_CN/LC_MESSAGES/messages.po")
text = PO.read_text(encoding="utf-8")

OLD_ENTRIES_TO_REMOVE = [
    '" command logs"',
    '" is reachable and the configured image was found"',
    '" sessions, "',
    '"\\"?"',
    '". Consider rebuilding."',
    '": "',
    '": request failed, check the logs for details"',
    '"Cleared "',
    '"Delete context \\""',
    '"Docker contexts detected from"',
    '"Error: "',
    '"is mounted and contexts are created with"',
    '"Last scanned: "',
    '"Make sure"',
    '"MB ("',
    '"MB but the newest build is "',
    '"MB difference). Built "',
    '"MB) is consistent with the newest build ("',
    '"MB). Built "',
    '"MB, built "',
    '"Newest build found across contexts. "',
    '"Possibly outdated. This image is "',
    '"on this host. Set the public hostname for each context you want to use, this is the address users connect to for VNC sessions. You can adjust weight and other settings after importing."',
]

for old in OLD_ENTRIES_TO_REMOVE:
    pattern = re.compile(r'^msgid ' + re.escape(old) + r'\nmsgstr ".*"\n\n', re.MULTILINE)
    new_text, n = pattern.subn('', text)
    if n == 0:
        print(f'WARNING: did not find msgid {old!r}')
    else:
        text = new_text
        print(f'removed: {old!r}')

NEW_ENTRIES = [
    ('"{name} is reachable and the configured image was found"',
     '"{name} 可连接且找到了配置的镜像"'),
    ('"{name}: {error}"',
     '"{name}：{error}"'),
    ('"{name}: request failed, check the logs for details"',
     '"{name}：请求失败，请查看日志了解详情"'),
    ('"Delete context \\"{name}\\"?"',
     '"删除上下文\\"{name}\\"？"'),
    ('"Cleared {sessions} sessions, {commands} command logs"',
     '"已清除 {sessions} 个会话、{commands} 条命令日志"'),
    ('"Last scanned: {date}"',
     '"上次扫描：{date}"'),
    ('"Error: {message}"',
     '"错误：{message}"'),
    ('"Newest build found across contexts. {size}MB, built {created}"',
     '"在所有上下文中找到的最新构建。{size}MB，构建于 {created}"'),
    ('"Possibly outdated. This image is {cur}MB but the newest build is {ref}MB ({diff}MB difference). Built {created}. Consider rebuilding."',
     '"可能已过时。此镜像为 {cur}MB，但最新构建为 {ref}MB（差异 {diff}MB）。构建于 {created}。建议重新构建。"'),
    ('"Size ({cur}MB) is consistent with the newest build ({ref}MB). Built {created}"',
     '"大小（{cur}MB）与最新构建一致（{ref}MB）。构建于 {created}"'),
    ('"Docker contexts detected from <code>~/.docker/contexts</code> on this host. Set the public hostname for each context you want to use, this is the address users connect to for VNC sessions. You can adjust weight and other settings after importing."',
     '"在此主机上的 <code>~/.docker/contexts</code> 检测到 Docker 上下文。为每个要使用的上下文设置公开主机名，这是用户连接 VNC 会话使用的地址。导入后可以调整权重和其他设置。"'),
    ('"Make sure <code>~/.docker</code> is mounted and contexts are created with <code>docker context create</code>"',
     '"请确保已挂载 <code>~/.docker</code>，且使用 <code>docker context create</code> 创建上下文"'),
]

entry_pattern = re.compile(r'^msgid (".*")\nmsgstr (".*")\n', re.MULTILINE)
entries = []
for m in entry_pattern.finditer(text):
    entries.append((m.group(1), m.group(2)))

for msgid, msgstr in NEW_ENTRIES:
    entries.append((msgid, msgstr))

def sort_key(e):
    msgid = e[0]
    if msgid == '""':
        return ''
    return msgid.lower()

entries.sort(key=sort_key)

header_end = text.find('\n\n') + 2
header = text[:header_end]

body = []
for msgid, msgstr in entries:
    if msgid == '""':
        continue
    body.append(f'msgid {msgid}\nmsgstr {msgstr}\n')

new_text = header + '\n'.join(body)
PO.write_text(new_text, encoding="utf-8")
print(f'\nFinal file: {len(entries)} entries, {len(new_text)} bytes')
