#!/usr/bin/env python3
"""
独立测试数据填充脚本（不修改 CTFd 核心文件）。
创建 15+ 队伍、用户、题目、解题、错误提交、奖励，覆盖 admin 统计与排名表格的所有边界情况：

边界情况覆盖：
- 名次得分 = sum(已解题分值 != 0) + sum(奖励分值 != 0)
- 同分时按 max(date) ASC, max(id) ASC 排序
- 0 分题目/0 分奖励会被计分逻辑过滤（但仍计入 challenge_count 统计）
- banned / hidden 队伍在 admin 视图中可见
- 不同分组的队伍
- 不同分类的题目
- 错误提交（Fails）影响 wrong_count 统计
- Tracking 记录影响 ip_count 统计
- Awards 包含正/负分值
"""

import datetime
import random
import sys

random.seed(42)  # 固定随机种子以便复现

from CTFd import create_app
from CTFd.cache import clear_challenges, clear_config, clear_pages, clear_standings
from CTFd.models import (
    Awards,
    Brackets,
    Challenges,
    ChallengeFiles,
    Fails,
    Flags,
    Hints,
    Solves,
    Teams,
    Tracking,
    Users,
    db,
)
from CTFd.utils.security.passwords import hash_password

app = create_app()

# ---- 基础常量 ----
CATEGORIES = ["Web", "Pwn", "Crypto", "Reverse", "Misc", "Forensics"]
TEAM_NAMES = [
    "BlackHats", "PHDays", "r3kap1t", "Wormble", "Pixie", "Balsn",
    "BlueWater", "StarBugs", "0xRyzen", "Krypto", "N0PS", "PwnMe",
    "ShellDredd", "ZenPwn", "VulnHub", "HackSmith", "CyberKnight", "NullByte",
]
USER_NAMES = [
    "alice", "bob", "carol", "dave", "eve", "frank", "grace", "heidi",
    "ivan", "judy", "karl", "leo", "mallory", "nina", "oscar", "peggy",
    "quinn", "rupert", "sybil", "trent", "uma", "victor", "wendy", "xavier",
    "yara", "zach", "abby", "billy", "cody", "demi",
]

BASE_TIME = datetime.datetime.utcnow() - datetime.timedelta(days=7)


def main():
    with app.app_context():
        db = app.db

        # 1) 创建分组 (Brackets)
        print("[1/8] Creating Brackets...")
        brackets_data = [
            ("高校组", "学生队伍", "teams"),
            ("社会组", "社会队伍", "teams"),
            ("个人组", "用户分组", "users"),
        ]
        team_brackets = []
        user_brackets = []
        for name, desc, btype in brackets_data:
            b = Brackets(name=name, description=desc, type=btype)
            db.session.add(b)
            db.session.flush()
            if btype == "teams":
                team_brackets.append(b.id)
            else:
                user_brackets.append(b.id)
        db.session.commit()
        print(f"   team_brackets={team_brackets}, user_brackets={user_brackets}")

        # 2) 创建题目（覆盖各种分值/分类，含 0 分题）
        print("[2/8] Creating Challenges...")
        challenges = []
        challenge_specs = [
            # (name, category, value, state)
            ("Easy Web",      "Web",      100, "visible"),
            ("SQLi Basic",    "Web",      200, "visible"),
            ("XSS Filter",    "Web",      300, "visible"),
            ("RCE Playground","Web",      500, "visible"),
            ("Stack Overflow","Pwn",      100, "visible"),
            ("Format String", "Pwn",      250, "visible"),
            ("Heap Exploit",  "Pwn",      500, "visible"),
            ("RSA Warmup",    "Crypto",   100, "visible"),
            ("AES-CBC",       "Crypto",   300, "visible"),
            ("ECC Signature", "Crypto",   450, "visible"),
            ("Baby Rev",      "Reverse",  150, "visible"),
            ("Obfuscated Bin","Reverse",  400, "visible"),
            ("Stego PNG",     "Misc",     100, "visible"),
            ("PCAP Analysis", "Forensics",250, "visible"),
            ("Log Forensics", "Forensics",350, "visible"),
            ("Hidden Service","Misc",     0,   "visible"),  # 0 分题（应被计分过滤）
            ("Hard Misc",     "Misc",     600, "visible"),
            ("Future Challenge","Misc",  250, "hidden"),    # 隐藏题
        ]
        for name, cat, val, state in challenge_specs:
            c = Challenges(
                name=name,
                description=f"Description for {name}.",
                attribution=f"Author {name.split()[0]}",
                value=val,
                category=cat,
                state=state,
            )
            db.session.add(c)
            db.session.flush()
            flag_content = f"flag{{{name.replace(' ', '_').lower()}}}"
            db.session.add(Flags(challenge_id=c.id, content=flag_content, type="static"))
            challenges.append(c)
        db.session.commit()
        print(f"   Created {len(challenges)} challenges (incl. 0-value and hidden)")

        # 3) 创建队伍（覆盖 banned / hidden / 不同 bracket）
        print("[3/8] Creating Teams...")
        teams = []
        # 16 支可见正常队伍
        for i, name in enumerate(TEAM_NAMES[:16]):
            t = Teams(name=name, password="password")
            t.affiliation = f"Org {i+1}"
            t.bracket_id = team_brackets[i % len(team_brackets)]
            db.session.add(t)
            db.session.flush()
            teams.append(t)
        # 1 支 banned 队伍
        t_banned = Teams(name="BannedTeam", password="password")
        t_banned.banned = True
        t_banned.bracket_id = team_brackets[0]
        db.session.add(t_banned)
        db.session.flush()
        teams.append(t_banned)
        # 1 支 hidden 队伍
        t_hidden = Teams(name="HiddenTeam", password="password")
        t_hidden.hidden = True
        t_hidden.bracket_id = team_brackets[1]
        db.session.add(t_hidden)
        db.session.flush()
        teams.append(t_hidden)
        db.session.commit()
        print(f"   Created {len(teams)} teams (incl. 1 banned, 1 hidden)")

        # 4) 创建用户（每队 1-2 个；含 banned / hidden 用户）
        print("[4/8] Creating Users...")
        users = []
        user_idx = 0
        for i, team in enumerate(teams[:-2]):  # 正常队伍
            num_members = random.choice([1, 2, 2])
            for _ in range(num_members):
                if user_idx >= len(USER_NAMES):
                    break
                uname = USER_NAMES[user_idx]
                user_idx += 1
                u = Users(
                    name=uname,
                    email=f"{uname}@test.local",
                    password=hash_password("password"),
                    team_id=team.id,
                    verified=True,
                    bracket_id=user_brackets[i % len(user_brackets)],
                )
                db.session.add(u)
                db.session.flush()
                users.append(u)
                # 队长 = 第一个成员
                if team.captain_id is None:
                    team.captain_id = u.id
        # banned 用户
        u_banned = Users(
            name="banneduser",
            email="banned@test.local",
            password=hash_password("password"),
            team_id=teams[-2].id,
            verified=True,
        )
        u_banned.banned = True
        db.session.add(u_banned)
        db.session.flush()
        users.append(u_banned)
        # hidden 用户
        u_hidden = Users(
            name="hiddenuser",
            email="hidden@test.local",
            password=hash_password("password"),
            team_id=teams[-1].id,
            verified=True,
        )
        u_hidden.hidden = True
        db.session.add(u_hidden)
        db.session.flush()
        users.append(u_hidden)
        db.session.commit()
        print(f"   Created {len(users)} users (incl. 1 banned, 1 hidden)")

        # 5) 生成 Solves（覆盖：不同分值、同分时按时间/ID 排序）
        print("[5/8] Creating Solves...")
        visible_challenges = [c for c in challenges if c.state == "visible" and c.value != 0]
        zero_value_chal = next(c for c in challenges if c.value == 0)
        hidden_chal = next(c for c in challenges if c.state == "hidden")

        solve_counter = 0
        # 让正常队伍按不同强度解题
        for ti, team in enumerate(teams):
            members = [u for u in users if u.team_id == team.id]
            if not members:
                continue
            # 每队解 5 ~ 12 道（banned/hidden 队伍解少一点 3 道）
            if team.banned or team.hidden:
                num_solves = 3
            else:
                num_solves = random.randint(5, min(12, len(visible_challenges)))
            chosen = random.sample(visible_challenges, num_solves)
            for ci, chal in enumerate(chosen):
                solver = random.choice(members)
                # 时间递增（越后解越晚）
                solve_time = BASE_TIME + datetime.timedelta(
                    days=ti % 3, hours=ci, minutes=random.randint(0, 59)
                )
                s = Solves(
                    user_id=solver.id,
                    team_id=team.id,
                    challenge_id=chal.id,
                    # account_id is auto-derived from team_id in teams mode
                    ip=f"10.0.{ti}.{ci}",
                    provided=f"flag{{{chal.name.replace(' ', '_').lower()}}}",
                    date=solve_time,
                )
                db.session.add(s)
                solve_counter += 1

        # 让某些队伍解 0 分题（应被计分过滤）
        team_for_zero = teams[0]
        u_for_zero = next(u for u in users if u.team_id == team_for_zero.id)
        db.session.add(Solves(
            user_id=u_for_zero.id, team_id=team_for_zero.id,
            challenge_id=zero_value_chal.id,
            ip="10.0.0.99", provided="flag{zero}", date=BASE_TIME,
        ))
        solve_counter += 1

        # 让某些队伍解隐藏题（不计入 visible challenge_count，但会产生 solve）
        db.session.add(Solves(
            user_id=u_for_zero.id, team_id=team_for_zero.id,
            challenge_id=hidden_chal.id,
            ip="10.0.0.98", provided="flag{hidden}", date=BASE_TIME,
        ))
        solve_counter += 1
        db.session.commit()
        print(f"   Created {solve_counter} solves (incl. zero-value and hidden challenge solves)")

        # 6) 生成 Awards（正分 + 负分 + 0 分）
        print("[6/8] Creating Awards...")
        award_counter = 0
        for i, team in enumerate(teams[:12]):
            members = [u for u in users if u.team_id == team.id]
            if not members:
                continue
            # 1 个正分奖励
            db.session.add(Awards(
                user_id=members[0].id, team_id=team.id,
                name="first_blood_bonus",
                value=random.choice([20, 50, 100]),
                icon="shield", category="bonus",
                date=BASE_TIME + datetime.timedelta(hours=i),
            ))
            award_counter += 1
            # 偶尔有负分奖励
            if i % 3 == 0:
                db.session.add(Awards(
                    user_id=members[0].id, team_id=team.id,
                    name="hint_penalty",
                    value=-random.choice([20, 50]),
                    icon="ban", category="penalty",
                    date=BASE_TIME + datetime.timedelta(hours=i + 1),
                ))
                award_counter += 1
            # 偶尔有 0 分奖励（应被计分过滤）
            if i % 4 == 0:
                db.session.add(Awards(
                    user_id=members[0].id, team_id=team.id,
                    name="participation",
                    value=0, icon="crown", category="bonus",
                    date=BASE_TIME + datetime.timedelta(hours=i + 2),
                ))
                award_counter += 1
        db.session.commit()
        print(f"   Created {award_counter} awards (incl. negative and zero-value)")

        # 7) 生成 Fails（错误提交）
        print("[7/8] Creating Fails...")
        fail_counter = 0
        for team in teams:
            members = [u for u in users if u.team_id == team.id]
            if not members:
                continue
            num_fails = random.randint(2, 8)
            for _ in range(num_fails):
                chal = random.choice(challenges)
                db.session.add(Fails(
                    user_id=members[0].id, team_id=team.id,
                    challenge_id=chal.id,
                    ip=f"10.1.{team.id}.x",
                    provided="wrong_flag_attempt",
                    date=BASE_TIME + datetime.timedelta(minutes=random.randint(1, 5000)),
                ))
                fail_counter += 1
        db.session.commit()
        print(f"   Created {fail_counter} fails")

        # 8) 生成 Tracking（IP 统计）
        print("[8/8] Creating Tracking...")
        track_counter = 0
        for u in users:
            # 每个用户 1-3 条登录 IP 追踪
            for _ in range(random.randint(1, 3)):
                db.session.add(Tracking(
                    user_id=u.id,
                    ip=f"203.0.113.{random.randint(1, 254)}",
                    date=BASE_TIME + datetime.timedelta(hours=random.randint(0, 100)),
                ))
                track_counter += 1
            # 给一些用户加 challenge.open 事件
            for chal_id in random.sample([c.id for c in challenges[:10]], random.randint(1, 5)):
                db.session.add(Tracking(
                    user_id=u.id, type="challenges.open",
                    target=chal_id, ip=f"203.0.113.{random.randint(1, 254)}",
                    date=BASE_TIME + datetime.timedelta(hours=random.randint(0, 100)),
                ))
                track_counter += 1
        db.session.commit()
        print(f"   Created {track_counter} tracking records")

        # 清缓存让排行榜生效
        clear_config()
        clear_standings()
        clear_challenges()
        clear_pages()
        print("\n=== Done. Summary ===")
        print(f"Teams:        {Teams.query.count()}")
        print(f"Users:        {Users.query.count()}")
        print(f"Challenges:   {Challenges.query.count()} (visible: {Challenges.query.filter_by(state='visible').count()})")
        print(f"Solves:       {Solves.query.count()}")
        print(f"Fails:        {Fails.query.count()}")
        print(f"Awards:       {Awards.query.count()}")
        print(f"Tracking:     {Tracking.query.count()}")
        print(f"Brackets:     {Brackets.query.count()}")
        print(f"Distinct IPs: {db.session.query(Tracking.ip).distinct().count()}")


if __name__ == "__main__":
    main()
