# -*- coding: utf-8 -*-
"""
统计页测试数据填充脚本（独立辅助脚本，非 CTFd 核心文件）。

用途：
  - 完成 CTFd 初始化（管理员 root/root，user_mode=teams）
  - 创建 2 个组别（Brackets）、5 支队伍、5 名队员、6 道题目（可见、分值非 0）
  - 创建解题（Solves）/ 错误提交（Fails）/ 题目打开记录（Tracking），
    使管理面板“统计信息”页的“名次/队伍/得分”矩阵表格出现：
    已解出（绿✓）/ 已尝试（黄）/ 已打开（青）/ 未触碰（灰）四种状态。

设计要点（与 /api/v1/statistics/progression/matrix 逻辑严格对齐）：
  1. get_standings 使用 INNER JOIN sumscores 且 Challenges.value != 0，
     → 题目分值必须非 0，且队伍必须有至少一条解题才会出现在矩阵中。
  2. 队伍模式下 account_id = team_id；Solves/Fails 写 team_id，Tracking 写 user_id（队员）。
  3. 单元格状态优先级：solved > attempted > opened > untouched。
"""
import datetime
import os
import sys

sys.path.insert(0, "/workspace")

from CTFd import create_app  # noqa: E402
from CTFd.cache import cache  # noqa: E402
from CTFd.constants.config import (  # noqa: E402
    AccountVisibilityTypes,
    ChallengeVisibilityTypes,
    RegistrationVisibilityTypes,
    ScoreVisibilityTypes,
)
from CTFd.constants.themes import DEFAULT_THEME  # noqa: E402
from CTFd.models import (  # noqa: E402
    Admins,
    Brackets,
    Challenges,
    Configs,
    Fails,
    Flags,
    Pages,
    Solves,
    Teams,
    Tracking,
    Users,
    db,
)
from CTFd.utils import get_config, set_config  # noqa: E402

app = create_app()


def do_setup():
    """复刻 views.setup 的关键逻辑：创建管理员、写入配置、创建首页。"""
    if get_config("setup"):
        print("[setup] already done, skip.")
        return

    set_config("ctf_name", "统计页测试 CTF")
    set_config("ctf_description", "用于测试管理面板统计页矩阵表格")
    set_config("user_mode", "teams")

    set_config("challenge_visibility", ChallengeVisibilityTypes.PRIVATE)
    set_config("account_visibility", AccountVisibilityTypes.PUBLIC)
    set_config("score_visibility", ScoreVisibilityTypes.PUBLIC)
    set_config("registration_visibility", RegistrationVisibilityTypes.PUBLIC)
    set_config("verify_emails", "false")
    set_config("social_shares", "true")
    set_config("team_size", 0)

    set_config("ctf_theme", DEFAULT_THEME)
    set_config("start", None)
    set_config("end", None)
    set_config("freeze", None)

    for k in (
        "mail_server",
        "mail_port",
        "mail_tls",
        "mail_ssl",
        "mail_username",
        "mail_password",
        "mail_useauth",
    ):
        set_config(k, None)

    # 管理员账号 root / root
    admin = Admins.query.filter_by(name="root").first()
    if not admin:
        admin = Admins(
            name="root",
            email="root@ctfd.local",
            password="root",
            type="admin",
            hidden=True,
        )
        db.session.add(admin)
        db.session.commit()

    # 首页
    if not Pages.query.filter_by(route="index").first():
        page = Pages(title="统计页测试 CTF", route="index", content="", draft=False)
        db.session.add(page)
        db.session.commit()

    set_config("setup", True)
    cache.clear()
    print("[setup] done. admin=root/root, user_mode=teams")


def seed():
    if get_config("seeded_stats_test"):
        print("[seed] already seeded, skip. (unset config 'seeded_stats_test' to re-run)")
        return

    now = datetime.datetime.utcnow()

    # ---------- 组别（Brackets，type=teams 适用于队伍）----------
    bracket_hs = Brackets.query.filter_by(name="高校组", type="teams").first()
    if not bracket_hs:
        bracket_hs = Brackets(name="高校组", description="高校参赛队伍", type="teams")
        db.session.add(bracket_hs)
    bracket_soc = Brackets.query.filter_by(name="社会组", type="teams").first()
    if not bracket_soc:
        bracket_soc = Brackets(name="社会组", description="社会参赛队伍", type="teams")
        db.session.add(bracket_soc)
    db.session.commit()

    # ---------- 队伍 ----------
    teams_spec = [
        ("Alpha战队", bracket_hs),
        ("Beta战队", bracket_hs),
        ("Gamma战队", bracket_soc),
        ("Delta战队", bracket_soc),
        ("Omega战队", None),  # 无组别 → 矩阵会出现“(无组别)”
    ]
    teams = {}
    for name, br in teams_spec:
        t = Teams.query.filter_by(name=name).first()
        if not t:
            t = Teams(
                name=name,
                email=name + "@ctfd.local",
                password="x",  # 队伍密码占位
                bracket_id=br.id if br else None,
            )
            db.session.add(t)
            db.session.commit()
        teams[name] = t

    # ---------- 队员（每队 1 名，加入队伍）----------
    members_spec = [
        ("alice", teams["Alpha战队"]),
        ("bob", teams["Beta战队"]),
        ("carol", teams["Gamma战队"]),
        ("dave", teams["Delta战队"]),
        ("eve", teams["Omega战队"]),
    ]
    users = {}
    for uname, team in members_spec:
        u = Users.query.filter_by(name=uname).first()
        if not u:
            u = Users(
                name=uname,
                email=uname + "@ctfd.local",
                password="x",
                team_id=team.id,
                verified=True,
            )
            db.session.add(u)
            db.session.commit()
        users[uname] = u

    # ---------- 题目（全部 visible，分值非 0）----------
    chals_spec = [
        ("签到题", "Misc", 100, 1, "flag{c1_signin}"),
        ("SQL注入", "Web", 200, 2, "flag{c2_sqli}"),
        ("RSA破解", "Crypto", 300, 3, "flag{c3_rsa}"),
        ("栈溢出", "Pwn", 400, 4, "flag{c4_bof}"),
        ("流量分析", "Misc", 500, 5, "flag{c5_pcap}"),
        ("隐写术", "Misc", 100, 6, "flag{c6_stego}"),
    ]
    chals = {}
    for name, cat, val, pos, flag in chals_spec:
        c = Challenges.query.filter_by(name=name).first()
        if not c:
            c = Challenges(
                name=name,
                description=name + " 描述",
                value=val,
                category=cat,
                type="standard",
                state="visible",
                position=pos,
            )
            db.session.add(c)
            db.session.commit()
        chals[name] = c
        # 静态 flag
        if not Flags.query.filter_by(challenge_id=c.id, type="static").first():
            db.session.add(Flags(challenge_id=c.id, type="static", content=flag))
            db.session.commit()

    c = {k: chals[k] for k in ["签到题", "SQL注入", "RSA破解", "栈溢出", "流量分析", "隐写术"]}
    cid = {k: c[k].id for k in c}

    # ---------- 解题（Solves）：决定名次/得分 ----------
    # 用递增 date 保证 tie-break 确定性（分数各不相同，仅作稳健性）
    base = now - datetime.timedelta(hours=10)

    def add_solve(uname, team, chal_key, order):
        existing = Solves.query.filter_by(
            challenge_id=cid[chal_key], team_id=team.id
        ).first()
        if existing:
            return
        s = Solves(
            challenge_id=cid[chal_key],
            user_id=users[uname].id,
            team_id=team.id,
            ip="127.0.0.1",
            provided="flag{" + chal_key + "}",
            type="correct",
            date=base + datetime.timedelta(minutes=order),
        )
        db.session.add(s)

    # 期望名次（分数降序）：
    # 1) Gamma 1000  2) Alpha 600  3) Beta 300  4) Omega 200  5) Delta 100
    add_solve("alice", teams["Alpha战队"], "签到题", 1)
    add_solve("alice", teams["Alpha战队"], "SQL注入", 2)
    add_solve("alice", teams["Alpha战队"], "RSA破解", 3)  # 600

    add_solve("bob", teams["Beta战队"], "签到题", 4)
    add_solve("bob", teams["Beta战队"], "SQL注入", 5)  # 300

    add_solve("carol", teams["Gamma战队"], "签到题", 6)
    add_solve("carol", teams["Gamma战队"], "栈溢出", 7)
    add_solve("carol", teams["Gamma战队"], "流量分析", 8)  # 1000

    add_solve("dave", teams["Delta战队"], "签到题", 9)  # 100

    add_solve("eve", teams["Omega战队"], "签到题", 10)
    add_solve("eve", teams["Omega战队"], "隐写术", 11)  # 200
    db.session.commit()

    # ---------- 错误提交（Fails）：黄色“已尝试” ----------
    def add_fail(uname, team, chal_key):
        f = Fails(
            challenge_id=cid[chal_key],
            user_id=users[uname].id,
            team_id=team.id,
            ip="127.0.0.1",
            provided="wrong_attempt",
            type="incorrect",
            date=now - datetime.timedelta(minutes=5),
        )
        db.session.add(f)

    # 仅对该队“未解出”的题目制造失败，使其呈现黄色而非绿色
    add_fail("alice", teams["Alpha战队"], "栈溢出")  # Alpha 未解 c4
    add_fail("bob", teams["Beta战队"], "RSA破解")  # Beta 未解 c3
    add_fail("dave", teams["Delta战队"], "SQL注入")  # Delta 未解 c2
    db.session.commit()

    # ---------- 打开记录（Tracking challenges.open）：青色“已打开” ----------
    # 仅对该队“未解出且未失败”的题目制造打开记录，使其呈现青色
    def add_open(uname, chal_key):
        # 去重：每个 user 对每道题只记一次
        if Tracking.query.filter_by(
            type="challenges.open",
            user_id=users[uname].id,
            target=cid[chal_key],
        ).first():
            return
        db.session.add(
            Tracking(
                type="challenges.open",
                ip="127.0.0.1",
                target=cid[chal_key],
                user_id=users[uname].id,
                date=now - datetime.timedelta(minutes=3),
            )
        )

    add_open("alice", "流量分析")  # Alpha 未解/未失败 c5
    add_open("dave", "RSA破解")  # Delta 未解/未失败 c3
    add_open("eve", "SQL注入")  # Omega 未解/未失败 c2
    db.session.commit()

    set_config("seeded_stats_test", "True")
    cache.clear()

    # ---------- 打印设计期望 ----------
    print("\n========== 期望矩阵（名次/队伍/得分 + 6 题）==========")
    print("题目(列): 签到题(c1,100) SQL注入(c2,200) RSA破解(c3,300) 栈溢出(c4,400) 流量分析(c5,500) 隐写术(c6,100)")
    rows = [
        ("Gamma战队", 1, 1000, ["✓", "-", "-", "✓", "✓", "-"]),
        ("Alpha战队", 2, 600, ["✓", "✓", "✓", "黄(试)", "青(开)", "-"]),
        ("Beta战队", 3, 300, ["✓", "✓", "黄(试)", "-", "-", "-"]),
        ("Omega战队", 4, 200, ["✓", "青(开)", "-", "-", "-", "✓"]),
        ("Delta战队", 5, 100, ["✓", "黄(试)", "青(开)", "-", "-", "-"]),
    ]
    for name, place, score, cells in rows:
        print(f"  {place}. {name} ({score}): " + " | ".join(cells))
    print("图例: ✓=已解出(绿)  黄(试)=已尝试(黄)  青(开)=已打开(青)  -=未触碰(灰)")
    print("======================================================\n")
    print("[seed] done.")


def report():
    print("---------- DB 概览 ----------")
    print("users   :", Users.query.count())
    print("teams   :", Teams.query.count())
    print("challs  :", Challenges.query.count())
    print("solves  :", Solves.query.count())
    print("fails   :", Fails.query.count())
    print("opens   :", Tracking.query.filter_by(type="challenges.open").count())
    print("brackets:", Brackets.query.count())
    print("-----------------------------")


if __name__ == "__main__":
    with app.app_context():
        do_setup()
        seed()
        report()
