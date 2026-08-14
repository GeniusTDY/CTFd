#!/usr/bin/env python3
"""
testall.py - 一键完成 CTFd 初始化设置 + 填充测试数据。
用法: python3.11 testall.py
管理员账号: root / root
"""

import datetime
import random
import re
import sys

import requests

random.seed(42)

BASE_URL = "http://127.0.0.1:4000"
ADMIN_USER = "root"
ADMIN_PASSWORD = "root"
ADMIN_EMAIL = "root@ctfd.local"

# ============================================================
# 第一阶段: 通过 HTTP 完成 CTFd Setup
# ============================================================

def setup_ctfd():
    """通过 HTTP 完成 CTFd 初始化设置，创建 root 管理员。"""
    sess = requests.Session()

    # 1. 获取 setup 页面，拿到 session cookie 和 state token
    print("[SETUP] 获取 setup 页面...")
    resp = sess.get(f"{BASE_URL}/setup", allow_redirects=False)

    # 如果 setup 已完成，会重定向到 /
    if resp.status_code == 302:
        print("  [INFO] CTFd 已完成初始化，跳过 setup 步骤。")
        return True

    if resp.status_code != 200:
        print(f"  [ERROR] 无法访问 setup 页面，HTTP {resp.status_code}")
        sys.exit(1)

    # 提取 state token (CTFd 3.x 使用 state 字段)
    match = re.search(r'name="state"[^>]*value="([^"]+)"', resp.text)
    if not match:
        print("  [ERROR] 无法从 setup 页面提取 state token")
        print(f"  页面内容: {resp.text[:500]}")
        sys.exit(1)
    state = match.group(1)
    print(f"  state token: {state[:20]}...")

    # 2. 提交 setup 表单
    form_data = {
        "ctf_name": "CTFd Demo",
        "ctf_description": "测试 CTF 平台",
        "user_mode": "teams",            # 团队模式
        "name": ADMIN_USER,
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD,
        "ctf_theme": "core",
        "challenge_visibility": "public",
        "account_visibility": "public",
        "score_visibility": "public",
        "registration_visibility": "public",
        "verify_emails": "false",
        "social_shares": "true",
        "state": state,
        "nonce": "",                      # CSRF nonce 在 session 中
        "submit": "Finish",
    }

    print("[SETUP] 提交初始化表单...")
    resp = sess.post(f"{BASE_URL}/setup", data=form_data, allow_redirects=True)
    if resp.status_code == 200 and "setup" in resp.url:
        print(f"  [ERROR] Setup 失败，可能 state 已过期")
        print(f"  页面片段: {resp.text[:1000]}")
        sys.exit(1)
    print(f"  [OK] Setup 完成，HTTP {resp.status_code}")

    # 3. 验证登录
    resp = sess.get(f"{BASE_URL}/login")
    if "nonce" in sess.cookies:
        csrf_nonce = sess.cookies.get("nonce", "")
        # 重新获取 login 页面拿 state
        match = re.search(r'name="nonce"\s+value="([^"]+)"', resp.text)
        nonce_val = match.group(1) if match else ""
    else:
        nonce_val = ""

    login_data = {
        "name": ADMIN_USER,
        "password": ADMIN_PASSWORD,
        "nonce": nonce_val,
        "submit": "Submit",
    }
    resp = sess.post(f"{BASE_URL}/login", data=login_data, allow_redirects=True)
    if "admin" in resp.url or resp.status_code == 200:
        print("  [OK] root 管理员登录成功")
    else:
        print(f"  [WARN] 登录验证异常，HTTP {resp.status_code}")
    return True


# ============================================================
# 第二阶段: 通过 CTFd 模型直接填充测试数据
# ============================================================

def populate_test_data():
    """使用 CTFd 模型创建测试数据（用户、队伍、题目、解题、错误提交、奖励、追踪）。"""
    import os
    os.environ.setdefault("FLASK_ENV", "development")
    sys.path.insert(0, "/workspace")

    from CTFd import create_app
    from CTFd.cache import clear_challenges, clear_config, clear_pages, clear_standings
    from CTFd.models import (
        Awards,
        Brackets,
        Challenges,
        Fails,
        Flags,
        Solves,
        Teams,
        Tracking,
        Users,
        db,
    )
    from CTFd.utils.security.passwords import hash_password

    app = create_app()

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

    with app.app_context():
        db = app.db

        # 1) 创建分组 (Brackets)
        print("[1/8] 创建分组...")
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
        print(f"   队伍分组: {team_brackets}, 用户分组: {user_brackets}")

        # 2) 创建题目（覆盖各种分值/分类，含 0 分题和隐藏题）
        print("[2/8] 创建题目...")
        challenges = []
        challenge_specs = [
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
            ("Hidden Service","Misc",     0,   "visible"),   # 0 分题
            ("Hard Misc",     "Misc",     600, "visible"),
            ("Future Challenge","Misc",  250, "hidden"),     # 隐藏题
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
        print(f"   创建了 {len(challenges)} 道题目")

        # 3) 创建队伍
        print("[3/8] 创建队伍...")
        teams = []
        for i, name in enumerate(TEAM_NAMES[:16]):
            t = Teams(name=name, password="password")
            t.affiliation = f"Org {i+1}"
            t.bracket_id = team_brackets[i % len(team_brackets)]
            db.session.add(t)
            db.session.flush()
            teams.append(t)
        # banned 队伍
        t_banned = Teams(name="BannedTeam", password="password")
        t_banned.banned = True
        t_banned.bracket_id = team_brackets[0]
        db.session.add(t_banned)
        db.session.flush()
        teams.append(t_banned)
        # hidden 队伍
        t_hidden = Teams(name="HiddenTeam", password="password")
        t_hidden.hidden = True
        t_hidden.bracket_id = team_brackets[1]
        db.session.add(t_hidden)
        db.session.flush()
        teams.append(t_hidden)
        db.session.commit()
        print(f"   创建了 {len(teams)} 支队伍（含 1 banned, 1 hidden）")

        # 4) 创建用户
        print("[4/8] 创建用户...")
        users = []
        user_idx = 0
        for i, team in enumerate(teams[:-2]):  # 正常队伍，每队 1-2 人
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
                if team.captain_id is None:
                    team.captain_id = u.id
        # banned 用户
        u_banned = Users(
            name="banneduser", email="banned@test.local",
            password=hash_password("password"),
            team_id=teams[-2].id, verified=True,
        )
        u_banned.banned = True
        db.session.add(u_banned)
        db.session.flush()
        users.append(u_banned)
        # hidden 用户
        u_hidden = Users(
            name="hiddenuser", email="hidden@test.local",
            password=hash_password("password"),
            team_id=teams[-1].id, verified=True,
        )
        u_hidden.hidden = True
        db.session.add(u_hidden)
        db.session.flush()
        users.append(u_hidden)
        db.session.commit()
        print(f"   创建了 {len(users)} 个用户（含 1 banned, 1 hidden）")

        # 5) 生成 Solves（解题记录）
        print("[5/8] 创建解题记录...")
        visible_challenges = [c for c in challenges if c.state == "visible" and c.value != 0]
        zero_value_chal = next(c for c in challenges if c.value == 0)
        hidden_chal = next(c for c in challenges if c.state == "hidden")

        solve_counter = 0
        for ti, team in enumerate(teams):
            members = [u for u in users if u.team_id == team.id]
            if not members:
                continue
            if team.banned or team.hidden:
                num_solves = 3
            else:
                num_solves = random.randint(5, min(12, len(visible_challenges)))
            chosen = random.sample(visible_challenges, num_solves)
            for ci, chal in enumerate(chosen):
                solver = random.choice(members)
                solve_time = BASE_TIME + datetime.timedelta(
                    days=ti % 3, hours=ci, minutes=random.randint(0, 59)
                )
                s = Solves(
                    user_id=solver.id,
                    team_id=team.id,
                    challenge_id=chal.id,
                    ip=f"10.0.{ti}.{ci}",
                    provided=f"flag{{{chal.name.replace(' ', '_').lower()}}}",
                    date=solve_time,
                )
                db.session.add(s)
                solve_counter += 1

        # 0 分题解题
        team_for_zero = teams[0]
        u_for_zero = next(u for u in users if u.team_id == team_for_zero.id)
        db.session.add(Solves(
            user_id=u_for_zero.id, team_id=team_for_zero.id,
            challenge_id=zero_value_chal.id,
            ip="10.0.0.99", provided="flag{zero}", date=BASE_TIME,
        ))
        solve_counter += 1

        # 隐藏题解题
        db.session.add(Solves(
            user_id=u_for_zero.id, team_id=team_for_zero.id,
            challenge_id=hidden_chal.id,
            ip="10.0.0.98", provided="flag{hidden}", date=BASE_TIME,
        ))
        solve_counter += 1
        db.session.commit()
        print(f"   创建了 {solve_counter} 条解题记录")

        # 6) 生成 Awards（奖励：正分、负分、0 分）
        print("[6/8] 创建奖励记录...")
        award_counter = 0
        for i, team in enumerate(teams[:12]):
            members = [u for u in users if u.team_id == team.id]
            if not members:
                continue
            db.session.add(Awards(
                user_id=members[0].id, team_id=team.id,
                name="first_blood_bonus", value=random.choice([20, 50, 100]),
                icon="shield", category="bonus",
                date=BASE_TIME + datetime.timedelta(hours=i),
            ))
            award_counter += 1
            if i % 3 == 0:
                db.session.add(Awards(
                    user_id=members[0].id, team_id=team.id,
                    name="hint_penalty", value=-random.choice([20, 50]),
                    icon="ban", category="penalty",
                    date=BASE_TIME + datetime.timedelta(hours=i + 1),
                ))
                award_counter += 1
            if i % 4 == 0:
                db.session.add(Awards(
                    user_id=members[0].id, team_id=team.id,
                    name="participation", value=0, icon="crown", category="bonus",
                    date=BASE_TIME + datetime.timedelta(hours=i + 2),
                ))
                award_counter += 1
        db.session.commit()
        print(f"   创建了 {award_counter} 条奖励记录")

        # 7) 生成 Fails（错误提交）
        print("[7/8] 创建错误提交记录...")
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
        print(f"   创建了 {fail_counter} 条错误提交记录")

        # 8) 生成 Tracking（IP 追踪）
        print("[8/8] 创建追踪记录...")
        track_counter = 0
        for u in users:
            for _ in range(random.randint(1, 3)):
                db.session.add(Tracking(
                    user_id=u.id,
                    ip=f"203.0.113.{random.randint(1, 254)}",
                    date=BASE_TIME + datetime.timedelta(hours=random.randint(0, 100)),
                ))
                track_counter += 1
            for chal_id in random.sample([c.id for c in challenges[:10]], random.randint(1, 5)):
                db.session.add(Tracking(
                    user_id=u.id, type="challenges.open",
                    target=chal_id, ip=f"203.0.113.{random.randint(1, 254)}",
                    date=BASE_TIME + datetime.timedelta(hours=random.randint(0, 100)),
                ))
                track_counter += 1
        db.session.commit()
        print(f"   创建了 {track_counter} 条追踪记录")

        # 清缓存
        clear_config()
        clear_standings()
        clear_challenges()
        clear_pages()
        print("\n========== 数据填充完成 ==========")
        print(f"队伍:     {Teams.query.count()}")
        print(f"用户:     {Users.query.count()}")
        print(f"题目:     {Challenges.query.count()}（visible: {Challenges.query.filter_by(state='visible').count()}）")
        print(f"解题:     {Solves.query.count()}")
        print(f"错误提交: {Fails.query.count()}")
        print(f"奖励:     {Awards.query.count()}")
        print(f"追踪:     {Tracking.query.count()}")
        print(f"分组:     {Brackets.query.count()}")
        print(f"独立IP:   {db.session.query(Tracking.ip).distinct().count()}")
        print("===================================")


# ============================================================
# 主入口
# ============================================================

if __name__ == "__main__":
    print("=" * 50)
    print("CTFd 测试数据填充脚本")
    print(f"管理员: {ADMIN_USER} / {ADMIN_PASSWORD}")
    print("=" * 50)

    # Phase 1: 完成 Setup
    setup_ctfd()

    # Phase 2: 填充测试数据
    print("\n--- 开始填充测试数据 ---\n")
    populate_test_data()

    print("\n[完成] 请访问 http://localhost:4000/admin 查看统计信息")