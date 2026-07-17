#!/usr/bin/env python3
"""Apply Chinese translations for the 86 untranslated Vue component entries."""

import polib

PO_PATH = "/workspace/CTFd/translations/zh_Hans_CN/LC_MESSAGES/messages.po"

# Translation mapping: msgid -> msgstr
TRANSLATIONS = {
    # CommentBox.vue
    "Add comment": "添加评论",
    "Comment": "评论",
    "of": "共",
    "comments": "条评论",
    # Bracket.vue / BracketList.vue
    "Bracket Name": "分组名称",
    'Bracket name (e.g. "Students", "Interns", "Engineers")':
        '分组名称（例如"学生"、"实习生"、"工程师"）',
    "Bracket Description": "分组描述",
    "Bracket Type": "分组类型",
    "If you are using Team Mode and would like the bracket to apply to entire teams instead of individuals, select Teams.":
        "如果你使用团队模式，并希望分组应用于整个团队而非个人，请选择团队。",
    "Add New Bracket": "添加新分组",
    # Field.vue / FieldList.vue
    "Field Type": "字段类型",
    "Text Field": "文本字段",
    "Checkbox": "复选框",
    "Type of field shown to the user": "向用户显示的字段类型",
    "Field Name": "字段名称",
    "Field name": "字段名称",
    "Field Description": "字段描述",
    "Editable by user in profile": "用户可在资料中编辑",
    "Required on registration": "注册时必填",
    "Shown on public profile": "在公开资料中显示",
    "Add New Field": "添加新字段",
    # ChallengeFilesList.vue / MediaLibrary.vue
    "File": "文件",
    "SHA1:": "SHA1：",
    "Media Details": "媒体详情",
    "Link:": "链接：",
    "Insert": "插入",
    "Insert link into editor": "将链接插入编辑器",
    "Download file": "下载文件",
    "Delete file": "删除文件",
    "Upload File Location": "上传文件位置",
    "Location": "位置",
    "Route where file will be accessible (if not provided a random folder will be used).":
        "文件可访问的路径（如未提供，将使用随机文件夹）。",
    "Provide as": "提供方式",
    # FlagCreationForm.vue / FlagList.vue / FlagEditForm.vue
    "Create Flag": "创建 Flag",
    "Choose Flag Type": "选择 Flag 类型",
    "--": "--",
    "Edit Flag": "编辑 Flag",
    # HintCreationForm.vue / HintEditForm.vue / HintsList.vue
    "Hint": "提示",
    "Content displayed before hint unlocking": "提示解锁前显示的内容",
    "Markdown & HTML are supported": "支持 Markdown 和 HTML",
    "Cost": "消耗",
    "How many points it costs to see your hint.": "查看提示所需的积分。",
    "Hints that must be unlocked before unlocking this hint":
        "解锁此提示前必须先解锁的提示",
    "Create Hint": "创建提示",
    # NextChallenge.vue
    "Challenge to recommend after solving this challenge":
        "解决此题目后推荐的题目",
    # RatingsViewer.vue
    "Loading ratings...": "正在加载评分...",
    "No ratings yet": "暂无评分",
    "Total:": "总计：",
    "Previous": "上一页",
    # Requirements.vue
    "Behavior if not unlocked": "未解锁时的行为",
    "Anonymized": "匿名化",
    # SolutionEditor.vue
    "Controls who can view this solution": "控制谁可以查看此题解",
    "Loading...": "加载中...",
    # ScoreboardMatrix.vue
    "Filter Matrix Data": "筛选矩阵数据",
    "Filters": "筛选器",
    "Reset All": "全部重置",
    "Select All": "全选",
    "Filter Categories": "筛选分类",
    "Search categories...": "搜索分类...",
    "Filter Challenges": "筛选题目",
    "Search challenges...": "搜索题目...",
    "Sort By": "排序方式",
    "Position (Default)": "位置（默认）",
    "ID (Ascending)": "ID（升序）",
    "ID (Descending)": "ID（降序）",
    "Alphabetical (Ascending: A-Z)": "字母升序（A-Z）",
    "Alphabetical (Descending: Z-A)": "字母降序（Z-A）",
    "Points (Ascending)": "分数（升序）",
    "Points (Descending)": "分数（降序）",
    "Filter Brackets": "筛选分组",
    "Search brackets...": "搜索分组...",
    "Attempted": "已尝试",
    "Opened": "已打开",
    "Filter Teams": "筛选团队",
    "Filter Users": "筛选用户",
    "Search teams...": "搜索团队...",
    "Search users...": "搜索用户...",
    # TagsList.vue
    "Tag": "标签",
    "Type tag and press Enter": "输入标签并按回车键",
    # UserAddForm.vue
    "Search Users": "搜索用户",
    "Search for users": "搜索用户",
    "No users found": "未找到用户",
    "already in a team": "已在团队中",
    "Add Users": "添加用户",
    # TopicsList.vue
    "Topic": "主题",
    "Type topic and press Enter": "输入主题并按回车键",
}


def main():
    po = polib.pofile(PO_PATH)
    applied = 0
    missing = []
    for entry in po:
        if entry.msgid in TRANSLATIONS:
            if not entry.translated():
                entry.msgstr = TRANSLATIONS[entry.msgid]
                # Remove fuzzy flag if present
                if "fuzzy" in entry.flags:
                    entry.flags.remove("fuzzy")
                applied += 1
            else:
                # Already translated, skip (could be from another source)
                pass
    # Check which translations from our map were not found
    po_msgids = {e.msgid for e in po}
    for msgid in TRANSLATIONS:
        if msgid not in po_msgids:
            missing.append(msgid)

    # Save with metadata preservation
    po.save(PO_PATH)
    print(f"Applied {applied} translations")
    if missing:
        print(f"WARNING: {len(missing)} msgids from map not found in PO file:")
        for m in missing:
            print(f"  - {repr(m)}")
    else:
        print("All msgids from map were found in PO file")


if __name__ == "__main__":
    main()
