#!/usr/bin/env python3
"""
统合测试数据填充脚本（供管理面板统计信息页面使用）。
创建用户、队伍、题目、解题、错误提交、奖励、追踪记录，覆盖各种边界情况。
"""

import datetime
import random
import sys

random.seed(42)

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


def main():
    with app.app_context():
        db = app.db

        # 1) Brackets
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

        # 2) Challenges
        print("[2/8] Creating Challenges...")
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
            ("Hidden Service","Misc",     0,   "visible"),
            ("Hard Misc",     "Misc",     600, "visible"),
            ("Future Challenge","Misc",  250, "hidden"),
        ]
        for name, cat, val, state in challenge_specs:
            c = Challenges(
                name=name, description=f"Description for {name}.",
                attribution=f"Author {name.split()[0]}",
                value=val, category=cat, state=state,
            )
            db.session.add(c)
            db.session.flush()
            db.session.add(Flags(challenge_id=c.id, content=f"flag{{{name.replace(' ', '_').lower()}}}", type="static"))
            challenges.append(c)
        db.session.commit()
        print(f"   Created {len(challenges)} challenges")

        # 3) Teams
        print("[3/8] Creating Teams...")
        teams = []
        for i, name in enumerate(TEAM_NAMES[:16]):
            t = Teams(name=name, password="password", affiliation=f"Org {i+1}")
            t.bracket_id = team_brackets[i % len(team_brackets)]
            db.session.add(t)
            db.session.flush()
            teams.append(t)
        t_banned = Teams(name="BannedTeam", password="password", banned=True)
        t_banned.bracket_id = team_brackets[0]
        db.session.add(t_banned)
        db.session.flush()
        teams.append(t_banned)
        t_hidden = Teams(name="HiddenTeam", password="password", hidden=True)
        t_hidden.bracket_id = team_brackets[1]
        db.session.add(t_hidden)
        db.session.flush()
        teams.append(t_hidden)
        db.session.commit()
        print(f"   Created {len(teams)} teams (incl. 1 banned, 1 hidden)")

        # 4) Users
        print("[4/8] Creating Users...")
        users = []
        user_idx = 0
        for i, team in enumerate(teams[:-2]):
            num_members = random.choice([1, 2, 2])
            for _ in range(num_members):
                if user_idx >= len(USER_NAMES):
                    break
                uname = USER_NAMES[user_idx]
                user_idx += 1
                u = Users(
                    name=uname, email=f"{uname}@test.local",
                    password=hash_password("password"),
                    team_id=team.id, verified=True,
                    bracket_id=user_brackets[i % len(user_brackets)],
                )
                db.session.add(u)
                db.session.flush()
                users.append(u)
                if team.captain_id is None:
                    team.captain_id = u.id
        u_banned = Users(name="banneduser", email="banned@test.local",
                         password=hash_password("password"), team_id=teams[-2].id, verified=True, banned=True)
        db.session.add(u_banned)
        db.session.flush()
        users.append(u_banned)
        u_hidden = Users(name="hiddenuser", email="hidden@test.local",
                         password=hash_password("password"), team_id=teams[-1].id, verified=True, hidden=True)
        db.session.add(u_hidden)
        db.session.flush()
        users.append(u_hidden)
        db.session.commit()
        print(f"   Created {len(users)} users (incl. 1 banned, 1 hidden)")

        # 5) Solves
        print("[5/8] Creating Solves...")
        visible_challenges = [c for c in challenges if c.state == "visible" and c.value != 0]
        zero_value_chal = next(c for c in challenges if c.value == 0)
        hidden_chal = next(c for c in challenges if c.state == "hidden")
        solve_counter = 0
        for ti, team in enumerate(teams):
            members = [u for u in users if u.team_id == team.id]
            if not members:
                continue
            num_solves = 3 if (team.banned or team.hidden) else random.randint(5, min(12, len(visible_challenges)))
            chosen = random.sample(visible_challenges, num_solves)
            for ci, chal in enumerate(chosen):
                solver = random.choice(members)
                solve_time = BASE_TIME + datetime.timedelta(days=ti % 3, hours=ci, minutes=random.randint(0, 59))
                db.session.add(Solves(
                    user_id=solver.id, team_id=team.id, challenge_id=chal.id,
                    ip=f"10.0.{ti}.{ci}",
                    provided=f"flag{{{chal.name.replace(' ', '_').lower()}}}",
                    date=solve_time,
                ))
                solve_counter += 1
        team_for_zero = teams[0]
        u_for_zero = next(u for u in users if u.team_id == team_for_zero.id)
        db.session.add(Solves(user_id=u_for_zero.id, team_id=team_for_zero.id,
                              challenge_id=zero_value_chal.id, ip="10.0.0.99",
                              provided="flag{zero}", date=BASE_TIME))
        solve_counter += 1
        db.session.add(Solves(user_id=u_for_zero.id, team_id=team_for_zero.id,
                              challenge_id=hidden_chal.id, ip="10.0.0.98",
                              provided="flag{hidden}", date=BASE_TIME))
        solve_counter += 1
        db.session.commit()
        print(f"   Created {solve_counter} solves")

        # 6) Awards
        print("[6/8] Creating Awards...")
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
        print(f"   Created {award_counter} awards")

        # 7) Fails
        print("[7/8] Creating Fails...")
        fail_counter = 0
        for team in teams:
            members = [u for u in users if u.team_id == team.id]
            if not members:
                continue
            for _ in range(random.randint(2, 8)):
                chal = random.choice(challenges)
                db.session.add(Fails(
                    user_id=members[0].id, team_id=team.id,
                    challenge_id=chal.id, ip=f"10.1.{team.id}.x",
                    provided="wrong_flag_attempt",
                    date=BASE_TIME + datetime.timedelta(minutes=random.randint(1, 5000)),
                ))
                fail_counter += 1
        db.session.commit()
        print(f"   Created {fail_counter} fails")

        # 8) Tracking
        print("[8/8] Creating Tracking...")
        track_counter = 0
        for u in users:
            for _ in range(random.randint(1, 3)):
                db.session.add(Tracking(
                    user_id=u.id, ip=f"203.0.113.{random.randint(1, 254)}",
                    date=BASE_TIME + datetime.timedelta(hours=random.randint(0, 100)),
                ))
                track_counter += 1
            for chal_id in random.sample([c.id for c in challenges[:10]], random.randint(1, 5)):
                db.session.add(Tracking(
                    user_id=u.id, type="challenges.open", target=chal_id,
                    ip=f"203.0.113.{random.randint(1, 254)}",
                    date=BASE_TIME + datetime.timedelta(hours=random.randint(0, 100)),
                ))
                track_counter += 1
        db.session.commit()
        print(f"   Created {track_counter} tracking records")

        # Clear caches
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