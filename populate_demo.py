"""
演示数据填充脚本（不修改 CTFd 核心文件）。
用于在管理面板统计页面展示完整数据：用户、队伍、题目、解题、失败、奖励。

运行方式：
    . .venv/bin/activate && python populate_demo.py
"""
import datetime
import random

from CTFd import create_app

random.seed(42)

# 时间跨度：过去 5 天，让统计图表有数据
NOW = datetime.datetime.utcnow()
def ts(days_ago, hour=0, minute=0):
    return NOW - datetime.timedelta(days=days_ago, hours=hour, minutes=minute)


def main():
    app = create_app()
    with app.app_context():
        from CTFd.models import (
            Awards,
            Challenges,
            Fails,
            Flags,
            Solves,
            Teams,
            Users,
        )
        from CTFd.cache import clear_challenges, clear_standings

        db = app.db

        # 1. 创建题目（不同分类、不同分值、不同状态）
        challenge_specs = [
            ("Sign-in",         "Misc",      50,  "visible", "flag{welcome_to_ctfd}"),
            ("Base64 101",      "Crypto",   100,  "visible", "flag{b64_is_easy}"),
            ("SQLi Baby",       "Web",      150,  "visible", "flag{sqli_injection_baby}"),
            ("Buffer Overflow", "Pwn",      300,  "visible", "flag{bof_pwned}"),
            ("Simple RE",       "Reverse",  250,  "visible", "flag{reverse_engineering}"),
            ("Network Forensics","Forensics",200,"visible", "flag{pcap_analysis}"),
            ("Hard Crypto",     "Crypto",   500,  "hidden",  "flag{rsa_hard_mode}"),
        ]
        challenges = {}
        for name, category, value, state, flag in challenge_specs:
            chal = Challenges(
                name=name,
                description=f"Demo challenge: {name}",
                value=value,
                category=category,
                type="standard",
                state=state,
            )
            db.session.add(chal)
            db.session.commit()
            db.session.add(Flags(challenge_id=chal.id, content=flag, type="static"))
            db.session.commit()
            challenges[name] = (chal, flag)
            print(f"[+] Challenge: {name} (id={chal.id}, value={value}, state={state})")

        clear_challenges()

        # 2. 创建队伍 + 成员（user_mode=teams）
        team_specs = [
            ("BlackHat",   ["alice", "bob",     "carol"]),
            ("WhiteHat",   ["dave",  "eve",     "frank", "grace"]),
            ("0xDEADBEEF", ["heidi", "ivan"]),
            ("PwnStars",   ["judy",  "mallory", "oscar"]),
            ("CryptoKids", ["trent", "wendy"]),
        ]
        teams = {}
        for tname, members in team_specs:
            team = Teams(name=tname, email=f"{tname.lower()}@example.com", password="password")
            db.session.add(team)
            db.session.commit()
            for i, uname in enumerate(members):
                user = Users(
                    name=uname,
                    email=f"{uname}@example.com",
                    password="password",
                    team_id=team.id,
                    verified=True,
                )
                if i == 0:
                    team.captain_id = None  # 稍后设置
                db.session.add(user)
                db.session.commit()
                team.members.append(user)
            # 设置队长为第一个成员
            team.captain_id = team.members[0].id
            db.session.commit()
            teams[tname] = team
            print(f"[+] Team: {tname} ({len(members)} members)")

        # 3. 创建解题记录（按时间分散，每个队伍解不同题）
        # (team_name, challenge_name, days_ago, hour, minute)
        solve_plan = [
            # BlackHat 队 - 强队，解了 5 题
            ("BlackHat", "Sign-in",          4, 10, 15),
            ("BlackHat", "Base64 101",       4, 11, 30),
            ("BlackHat", "SQLi Baby",        3, 14, 22),
            ("BlackHat", "Network Forensics",3, 16, 45),
            ("BlackHat", "Simple RE",        2,  9, 10),
            ("BlackHat", "Buffer Overflow",  1, 20,  5),

            # WhiteHat 队 - 中等，解了 4 题
            ("WhiteHat", "Sign-in",          4,  9,  0),
            ("WhiteHat", "Base64 101",       3, 10, 30),
            ("WhiteHat", "Simple RE",        2, 15, 20),
            ("WhiteHat", "Network Forensics",1, 11, 50),

            # 0xDEADBEEF 队 - 解了 3 题
            ("0xDEADBEEF", "Sign-in",        3, 13,  0),
            ("0xDEADBEEF", "SQLi Baby",      2, 18, 30),
            ("0xDEADBEEF", "Base64 101",     1, 10, 15),

            # PwnStars 队 - 解了 4 题（含 Pwn 难题）
            ("PwnStars", "Sign-in",          4, 14,  0),
            ("PwnStars", "Buffer Overflow",  2, 21, 30),
            ("PwnStars", "Simple RE",        1, 12, 45),
            ("PwnStars", "Base64 101",       0,  9, 20),

            # CryptoKids 队 - 较弱，解了 2 题
            ("CryptoKids", "Sign-in",        3, 16,  0),
            ("CryptoKids", "Base64 101",     1, 14, 30),
        ]

        for tname, cname, d, h, m in solve_plan:
            team = teams[tname]
            chal, flag = challenges[cname]
            # 队伍里随机一个成员作为提交者
            solver = random.choice(team.members)
            solve = Solves(
                user_id=solver.id,
                team_id=team.id,
                challenge_id=chal.id,
                ip="127.0.0.1",
                provided=flag,
            )
            solve.date = ts(d, h, m)
            db.session.add(solve)
            db.session.commit()
            print(f"[+] Solve: {tname}/{solver.name} -> {cname} at {solve.date}")

        # 4. 创建失败提交记录（让统计有 fail 数据）
        fail_plan = [
            ("BlackHat",    "Buffer Overflow",  3, 19,  5),
            ("BlackHat",    "Simple RE",        2,  8, 50),
            ("WhiteHat",    "Buffer Overflow",  3, 10, 15),
            ("WhiteHat",    "SQLi Baby",        2, 11, 30),
            ("0xDEADBEEF",  "Simple RE",        2, 17,  0),
            ("0xDEADBEEF",  "Network Forensics",1, 14, 30),
            ("PwnStars",    "Hard Crypto",      1, 22,  0),  # hidden 题，他们尝试了
            ("PwnStars",    "Network Forensics",2, 13, 15),
            ("CryptoKids",  "SQLi Baby",        2, 10,  0),
            ("CryptoKids",  "Simple RE",        1, 16, 45),
        ]
        for tname, cname, d, h, m in fail_plan:
            team = teams[tname]
            chal, _ = challenges[cname]
            submitter = random.choice(team.members)
            fail = Fails(
                user_id=submitter.id,
                team_id=team.id,
                challenge_id=chal.id,
                ip="127.0.0.1",
                provided="flag{wrong_guess}",
            )
            fail.date = ts(d, h, m)
            db.session.add(fail)
            db.session.commit()
            print(f"[-] Fail: {tname}/{submitter.name} -> {cname} at {fail.date}")

        # 5. 创建奖励（award）- 让分数有额外变化
        award_plan = [
            ("BlackHat",   "First Blood - SQLi Baby",   50, 3, 14, 23),
            ("PwnStars",   "First Blood - Buffer Overflow", 100, 2, 21, 31),
            ("WhiteHat",   "Best Writeup",               30, 1, 18,  0),
        ]
        for tname, desc, value, d, h, m in award_plan:
            team = teams[tname]
            award = Awards(
                user_id=team.members[0].id,
                team_id=team.id,
                name=desc,
                value=value,
            )
            award.date = ts(d, h, m)
            db.session.add(award)
            db.session.commit()
            print(f"[★] Award: {tname} -> {desc} (+{value})")

        clear_standings()
        clear_challenges()

        # 6. 总结
        print("\n" + "=" * 60)
        print("Demo data population complete!")
        print("=" * 60)
        print(f"Challenges : {Challenges.query.count()}")
        print(f"Teams      : {Teams.query.count()}")
        print(f"Users      : {Users.query.count()}")
        print(f"Solves     : {Solves.query.count()}")
        print(f"Fails      : {Fails.query.count()}")
        print(f"Awards     : {Awards.query.count()}")
        print("=" * 60)
        print("\nLogin as admin:")
        print("  Username: root")
        print("  Password: root")
        print("  Statistics page: http://localhost:4000/admin/statistics")


if __name__ == "__main__":
    main()
