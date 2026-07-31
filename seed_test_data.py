#!/usr/bin/env python3.11
"""为 CTFd 管理端统计页创建完整测试数据（独立脚本，不修改 CTFd 核心文件）。

设计目标：
- 12 支队伍、16 个用户（每队 1 队长 + 4 个队伍多 1 成员）、9 道题（5 个分类）。
- 矩阵（Player Progression）覆盖全部 4 态：solved(绿)/attempted(黄)/opened(青)/empty(灰)。
  优先级 solved > attempted > opened > empty（前端 ScoreboardMatrix.vue 判定）。
- 每支队伍至少 1 个 Solves(value≠0)，确保全部 12 队进入 Top 100 矩阵。
- 6 个图表均有数据：解题数/得分分布/各题解题百分比/提交百分比(正确vs错误)/分类细分/积分细分。
- 幂等：按 email 域 @test.ctfd 与题目名前缀清理旧数据。
"""
import datetime
from CTFd import create_app
from CTFd.models import (
    db, Users, Teams, Challenges, Flags, Solves, Fails, Tracking, Configs,
    Awards, Brackets,
)

app = create_app()

# ---- 数据设计（确定性，无随机） ----
# 9 道题：(name, value, category, flag)
CHALS = [
    ("Web-100",        100, "Web",        "flag{web100}"),
    ("Web-250",        250, "Web",        "flag{web250}"),
    ("Web-500",        500, "Web",        "flag{web500}"),
    ("Crypto-100",     100, "Crypto",     "flag{crypto100}"),
    ("Crypto-300",     300, "Crypto",     "flag{crypto300}"),
    ("Misc-150",       150, "Misc",       "flag{misc150}"),
    ("Misc-400",       400, "Misc",       "flag{misc400}"),
    ("Reversing-200",  200, "Reversing",  "flag{rev200}"),
    ("Forensics-350",  350, "Forensics",  "flag{for350}"),
]
# 题目下标 0..8 对应上面 CHALS

# 12 支队伍的解题集合（题目下标）；每队至少 1 题
TEAM_SOLVES = {
    1:  [0, 1, 3, 4, 5, 6, 7, 8],   # 8 题
    2:  [0, 1, 2, 3, 5, 7, 8],      # 7 题
    3:  [0, 1, 3, 5, 7, 8],         # 6 题
    4:  [0, 2, 3, 4, 5, 6],         # 6 题
    5:  [0, 1, 3, 4, 5, 7],         # 6 题
    6:  [0, 3, 5],                  # 3 题
    7:  [0, 1, 6, 7],               # 4 题
    8:  [0, 3],                     # 2 题
    9:  [0, 4, 8],                  # 3 题
    10: [1, 3, 5],                  # 3 题
    11: [0],                        # 1 题
    12: [5],                        # 1 题
}

# 错误提交 (team_idx 1-12, chal_idx 0-8)；均针对该队"未解出"的题目 → attempted 态
FAILS = [
    (1, 2), (1, 2),
    (2, 4),
    (3, 2), (3, 4),
    (4, 1),
    (5, 2), (5, 8),
    (6, 1), (6, 7), (6, 4),
    (7, 2), (7, 4),
    (8, 5), (8, 1),
    (9, 2), (9, 5),
    (10, 0), (10, 2),
    (11, 5), (11, 1),
    (12, 0), (12, 3),
]

# 题目打开追踪 (team_idx, chal_idx)；针对"未解出且未错误提交"的题目 → opened 态
OPENS = [
    (2, 6),
    (3, 6),
    (4, 7),
    (5, 6),
    (6, 2), (6, 6), (6, 8),
    (7, 3), (7, 5),
    (8, 2), (8, 4), (8, 7),
    (9, 1), (9, 3),
    (10, 4), (10, 6),
    (11, 2), (11, 3),
    (12, 1), (12, 2),
]

# 奖励/扣分 (team_idx, name, value, icon) → 影响得分分布与排名
AWARDS = [
    (6,  "First Blood Bonus", 50,   "crown"),
    (8,  "Time Penalty",      -30,  "ban"),
    (11, "Participation",     25,   "star"),
]

# 分组（brackets）：2 个队伍分组，用于矩阵筛选下拉
BRACKETS = [
    ("高校组", "高校参赛队伍"),
    ("社会组", "社会参赛队伍"),
]


def main():
    with app.app_context():
        # ---- 0. 清理旧测试数据（幂等）----
        print("清理旧测试数据...")
        test_user_ids = [u.id for u in Users.query.filter(Users.email.like("%@test.ctfd")).all()]
        test_team_ids = [t.id for t in Teams.query.filter(Teams.email.like("%@test.ctfd")).all()]
        test_chal_ids = [c.id for c in Challenges.query.filter(Challenges.name.like("Web-%"))
                         .union(Challenges.query.filter(Challenges.name.like("Crypto-%")),
                                Challenges.query.filter(Challenges.name.like("Misc-%")),
                                Challenges.query.filter(Challenges.name.like("Reversing-%")),
                                Challenges.query.filter(Challenges.name.like("Forensics-%"))).all()]
        if test_user_ids:
            Tracking.query.filter(Tracking.user_id.in_(test_user_ids)).delete(synchronize_session=False)
            Awards.query.filter(Awards.user_id.in_(test_user_ids)).delete(synchronize_session=False)
        if test_chal_ids:
            Solves.query.filter(Solves.challenge_id.in_(test_chal_ids)).delete(synchronize_session=False)
            Fails.query.filter(Fails.challenge_id.in_(test_chal_ids)).delete(synchronize_session=False)
            Flags.query.filter(Flags.challenge_id.in_(test_chal_ids)).delete(synchronize_session=False)
        if test_team_ids:
            Solves.query.filter(Solves.team_id.in_(test_team_ids)).delete(synchronize_session=False)
            Fails.query.filter(Fails.team_id.in_(test_team_ids)).delete(synchronize_session=False)
            Awards.query.filter(Awards.team_id.in_(test_team_ids)).delete(synchronize_session=False)
        Challenges.query.filter(Challenges.id.in_(test_chal_ids)).delete(synchronize_session=False)
        # 清理旧测试 brackets
        Brackets.query.filter(Brackets.name.in_(["高校组", "社会组"])).delete(synchronize_session=False)
        for u in Users.query.filter(Users.email.like("%@test.ctfd")).all():
            db.session.delete(u)
        for t in Teams.query.filter(Teams.email.like("%@test.ctfd")).all():
            db.session.delete(t)
        db.session.commit()

        # ---- 1. 确保 user_mode = teams（矩阵以队伍为单位）----
        cfg = Configs.query.filter_by(key="user_mode").first()
        if cfg:
            cfg.value = "teams"
        else:
            db.session.add(Configs(key="user_mode", value="teams"))
        db.session.commit()

        # ---- 2. 创建分组 ----
        brackets = {}
        for name, desc in BRACKETS:
            b = Brackets(name=name, description=desc, type="teams")
            db.session.add(b)
            db.session.flush()
            brackets[name] = b
        db.session.commit()

        # ---- 3. 创建 12 支队伍（交替分配到两个分组）----
        teams = {}
        for i in range(1, 13):
            name = "Team%02d" % i
            email = "team%02d@test.ctfd" % i
            t = Teams(name=name, email=email, password="team_pass")
            t.bracket_id = brackets["高校组" if i % 2 == 1 else "社会组"].id
            db.session.add(t)
            db.session.flush()
            teams[i] = t
        db.session.commit()

        # ---- 4. 创建 16 个用户（12 队长 + 4 个额外成员分到 T1/T2/T3/T4）----
        users = {}
        # 12 个队长
        for i in range(1, 13):
            uname = "player%02d" % i
            u = Users(name=uname, email="%s@test.ctfd" % uname,
                      password="player_pass", team_id=teams[i].id, verified=True)
            db.session.add(u)
            db.session.flush()
            teams[i].captain_id = u.id
            users[("captain", i)] = u
        # 4 个额外成员（T1/T2/T3/T4 各 1）
        extra_map = {13: 1, 14: 2, 15: 3, 16: 4}
        for uid in range(13, 17):
            ti = extra_map[uid]
            uname = "player%02d" % uid
            u = Users(name=uname, email="%s@test.ctfd" % uname,
                      password="player_pass", team_id=teams[ti].id, verified=True)
            db.session.add(u)
            db.session.flush()
            users[("member", uid)] = u
        db.session.commit()

        # ---- 5. 创建 9 道题 + flags ----
        chals = {}
        for idx, (name, value, cat, flag_text) in enumerate(CHALS):
            c = Challenges(name=name, description="测试题目 - " + name,
                           value=value, category=cat, state="visible", type="standard")
            db.session.add(c)
            db.session.flush()
            f = Flags(challenge_id=c.id, type="static", content=flag_text)
            db.session.add(f)
            chals[idx] = c
        db.session.commit()

        # ---- 6. 创建 Solves（正确提交）----
        # 解题者：前 4 队的部分题目由额外成员提交，其余由队长提交
        base = datetime.datetime.utcnow() - datetime.timedelta(hours=48)
        solve_count = 0
        for ti, chal_idxs in TEAM_SOLVES.items():
            for k, ci in enumerate(chal_idxs):
                # T1-T4 的第 k>=4 题由额外成员提交
                if ti in (1, 2, 3, 4) and k >= 4:
                    uid = 12 + ti  # extra member id
                    solver = users[("member", uid)]
                else:
                    solver = users[("captain", ti)]
                s = Solves(
                    team_id=teams[ti].id, user_id=solver.id,
                    challenge_id=chals[ci].id, ip="127.0.0.1",
                    provided=CHALS[ci][3],
                    date=base + datetime.timedelta(minutes=k * 3 + ti),
                )
                db.session.add(s)
                solve_count += 1
        db.session.commit()

        # ---- 7. 创建 Fails（错误提交）----
        fail_count = 0
        for ti, ci in FAILS:
            solver = users[("captain", ti)]
            f = Fails(
                team_id=teams[ti].id, user_id=solver.id,
                challenge_id=chals[ci].id, ip="127.0.0.1",
                provided="flag{wrong_%d_%d}" % (ti, ci),
                date=base + datetime.timedelta(minutes=ti * 5 + ci),
            )
            db.session.add(f)
            fail_count += 1
        db.session.commit()

        # ---- 8. 创建 Tracking(challenges.open) → opened 态 ----
        open_count = 0
        for ti, ci in OPENS:
            solver = users[("captain", ti)]
            tr = Tracking(
                type="challenges.open", ip="127.0.0.1",
                target=chals[ci].id, user_id=solver.id,
                date=base + datetime.timedelta(minutes=ti * 2 + ci),
            )
            db.session.add(tr)
            open_count += 1
        db.session.commit()

        # ---- 9. 创建 Awards（影响得分）----
        for ti, name, value, icon in AWARDS:
            solver = users[("captain", ti)]
            a = Awards(
                team_id=teams[ti].id, user_id=solver.id,
                name=name, value=value, icon=icon,
                date=base + datetime.timedelta(hours=ti),
            )
            db.session.add(a)
        db.session.commit()

        # ---- 10. 清除计分板/统计缓存 ----
        try:
            from CTFd.cache import clear_standings, clear_challenges, clear_config
            clear_standings()
            clear_challenges()
            clear_config()
        except Exception as e:
            print("缓存清理(非致命):", e)

        # ---- 汇总 ----
        print("\n=== 测试数据创建完成 ===")
        print("user_mode:", Configs.query.filter_by(key="user_mode").first().value)
        print("分组数:", Brackets.query.count())
        print("队伍数:", Teams.query.count())
        print("用户数:", Users.query.count())
        print("题目数:", Challenges.query.count())
        print("Flag数:", Flags.query.count())
        print("Solves数:", Solves.query.count(), "(预期 %d)" % solve_count)
        print("Fails数:", Fails.query.count(), "(预期 %d)" % fail_count)
        print("Tracking(challenges.open)数:",
              Tracking.query.filter_by(type="challenges.open").count(), "(预期 %d)" % open_count)
        print("Awards数:", Awards.query.count())
        print()
        print("=== 各队伍得分与排名 ===")
        rows = []
        for ti in range(1, 13):
            t = teams[ti]
            score = (db.session.query(db.func.sum(Challenges.value))
                     .join(Solves, Solves.challenge_id == Challenges.id)
                     .filter(Solves.team_id == t.id).scalar() or 0)
            award_val = (db.session.query(db.func.sum(Awards.value))
                         .filter(Awards.team_id == t.id).scalar() or 0)
            total = score + award_val
            rows.append((ti, t.name, score, award_val, total, len(TEAM_SOLVES[ti])))
        rows.sort(key=lambda r: -r[4])
        print("排名 | 队伍    | 解题分 | 奖励 | 总分 | 解题数")
        for rank, (ti, name, sc, aw, tot, ns) in enumerate(rows, 1):
            print("  %2d | %s | %5d | %+4d | %5d | %d" % (rank, name, sc, aw, tot, ns))
        print()
        print("=== 各题目解题次数 ===")
        for ci, (name, value, cat, _) in enumerate(CHALS):
            cnt = Solves.query.filter_by(challenge_id=chals[ci].id).count()
            print("  %-15s (%s, %d分): %d 次解出" % (name, cat, value, cnt))


if __name__ == "__main__":
    main()
