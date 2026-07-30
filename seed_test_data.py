#!/usr/bin/env python3.11
"""为 CTFd 统计页创建测试数据（独立脚本，不修改 CTFd 核心文件）。
覆盖：用户/队伍/题目/正确提交/错误提交/题目打开追踪。
矩阵设计覆盖全部四态：已解出 / 已尝试 / 已打开 / 空。
"""
import datetime
from CTFd import create_app
from CTFd.models import db, Users, Teams, Challenges, Flags, Solves, Fails, Tracking, Configs

app = create_app()
with app.app_context():
    # ---- 0. 清理旧的测试数据（幂等）----
    test_emails = [
        "alice@test.ctfd", "bob@test.ctfd", "carol@test.ctfd", "dave@test.ctfd",
    ]
    team_emails = [
        "alpha@test.ctfd", "bravo@test.ctfd", "charlie@test.ctfd", "delta@test.ctfd",
    ]
    test_chal_names = ["Web-100", "Web-200", "Web-300", "Crypto-100", "Crypto-200", "Misc-150"]

    Tracking.query.filter(Tracking.user_id.in_(
        [u.id for u in Users.query.filter(Users.email.in_(test_emails)).all()]
    )).delete(synchronize_session=False)
    Solves.query.filter(Solves.challenge_id.in_(
        [c.id for c in Challenges.query.filter(Challenges.name.in_(test_chal_names)).all()]
    )).delete(synchronize_session=False)
    Fails.query.filter(Fails.challenge_id.in_(
        [c.id for c in Challenges.query.filter(Challenges.name.in_(test_chal_names)).all()]
    )).delete(synchronize_session=False)
    Flags.query.filter(Flags.challenge_id.in_(
        [c.id for c in Challenges.query.filter(Challenges.name.in_(test_chal_names)).all()]
    )).delete(synchronize_session=False)
    Challenges.query.filter(Challenges.name.in_(test_chal_names)).delete(synchronize_session=False)
    for u in Users.query.filter(Users.email.in_(test_emails)).all():
        db.session.delete(u)
    for t in Teams.query.filter(Teams.email.in_(team_emails)).all():
        db.session.delete(t)
    db.session.commit()

    # ---- 1. 设置 user_mode = teams（让统计页显示 teams 计数，矩阵以队伍为单位）----
    cfg = Configs.query.filter_by(key="user_mode").first()
    if cfg:
        cfg.value = "teams"
    else:
        db.session.add(Configs(key="user_mode", value="teams"))

    # ---- 2. 创建 4 个队伍 ----
    teams_info = [
        ("Alpha", "alpha@test.ctfd", "alpha_pass"),
        ("Bravo", "bravo@test.ctfd", "bravo_pass"),
        ("Charlie", "charlie@test.ctfd", "charlie_pass"),
        ("Delta", "delta@test.ctfd", "delta_pass"),
    ]
    teams = {}
    for name, email, pwd in teams_info:
        t = Teams(name=name, email=email, password=pwd)
        db.session.add(t)
        db.session.flush()
        teams[name] = t

    # ---- 3. 创建 4 个用户（每队一个，作为队长）----
    users_info = [
        ("alice", "alice@test.ctfd", "alice_pass", "Alpha"),
        ("bob", "bob@test.ctfd", "bob_pass", "Bravo"),
        ("carol", "carol@test.ctfd", "carol_pass", "Charlie"),
        ("dave", "dave@test.ctfd", "dave_pass", "Delta"),
    ]
    users = {}
    for name, email, pwd, team_name in users_info:
        t = teams[team_name]
        u = Users(name=name, email=email, password=pwd, team_id=t.id, verified=True)
        db.session.add(u)
        db.session.flush()
        t.captain_id = u.id
        users[name] = u
    db.session.commit()

    # ---- 4. 创建 6 个题目（3 分类，不同分值，全部 visible）----
    chals_info = [
        ("Web-100", 100, "Web", "flag{web100}"),
        ("Web-200", 200, "Web", "flag{web200}"),
        ("Web-300", 300, "Web", "flag{web300}"),
        ("Crypto-100", 100, "Crypto", "flag{crypto100}"),
        ("Crypto-200", 200, "Crypto", "flag{crypto200}"),
        ("Misc-150", 150, "Misc", "flag{misc150}"),
    ]
    chals = {}
    for name, value, cat, flag_text in chals_info:
        c = Challenges(
            name=name, description="测试题目 - " + name,
            value=value, category=cat, state="visible", type="standard",
        )
        db.session.add(c)
        db.session.flush()
        f = Flags(challenge_id=c.id, type="static", content=flag_text)
        db.session.add(f)
        chals[name] = c
    db.session.commit()

    # ---- 5. 创建 Solves（正确提交）----
    # account_id = team_id, user_id = 解题者
    now = datetime.datetime.utcnow()
    solves_plan = [
        # (team_name, user_name, chal_name)
        ("Alpha", "alice", "Web-100"),
        ("Alpha", "alice", "Web-200"),
        ("Alpha", "alice", "Crypto-100"),
        ("Bravo", "bob", "Web-100"),
        ("Bravo", "bob", "Crypto-200"),
        ("Charlie", "carol", "Web-100"),
        ("Charlie", "carol", "Crypto-100"),
        ("Delta", "dave", "Misc-150"),
    ]
    for i, (tn, un, cn) in enumerate(solves_plan):
        s = Solves(
            team_id=teams[tn].id, user_id=users[un].id,
            challenge_id=chals[cn].id, ip="127.0.0.1",
            provided="flag{%s}" % cn.lower().replace("-", ""),
            date=now - datetime.timedelta(hours=len(solves_plan) - i),
        )
        db.session.add(s)
    db.session.commit()

    # ---- 6. 创建 Fails（错误提交，仅对未解出的题目）----
    fails_plan = [
        ("Bravo", "bob", "Web-200"),
        ("Charlie", "carol", "Crypto-200"),
        ("Delta", "dave", "Web-100"),
    ]
    for tn, un, cn in fails_plan:
        f = Fails(
            team_id=teams[tn].id, user_id=users[un].id,
            challenge_id=chals[cn].id, ip="127.0.0.1",
            provided="flag{wrong_attempt}",
        )
        db.session.add(f)
    db.session.commit()

    # ---- 7. 创建 Tracking（challenges.open，产生"已打开"状态）----
    # user_id = 打开题目的用户；矩阵在 teams 模式下通过 user_id → team_id 关联
    opens_plan = [
        # (user_name, [chal_names])
        ("alice", ["Web-300", "Crypto-200", "Misc-150"]),
        ("bob", ["Web-300", "Crypto-100", "Misc-150"]),
        ("carol", ["Web-200", "Web-300", "Misc-150"]),
        ("dave", ["Web-200", "Web-300", "Crypto-200"]),
    ]
    for un, cn_list in opens_plan:
        for cn in cn_list:
            tr = Tracking(
                type="challenges.open", ip="127.0.0.1",
                target=chals[cn].id, user_id=users[un].id,
            )
            db.session.add(tr)
    db.session.commit()

    # ---- 8. 清除计分板缓存，确保统计页读取最新数据 ----
    try:
        from CTFd.utils.dates import unix_time_to_utc
        from CTFd.cache import cache
        cache.delete_mixed("view:scoreboard")
        cache.delete_mixed("view:scoreboard-top-10")
        cache.delete_mixed("standings")
    except Exception as e:
        print("cache clear (non-fatal):", e)

    # ---- 汇总 ----
    print("=== 测试数据创建完成 ===")
    print("user_mode:", Configs.query.filter_by(key="user_mode").first().value)
    print("队伍数:", Teams.query.count(), "(含 root 所属)")
    print("用户数:", Users.query.count())
    print("题目数:", Challenges.query.count())
    print("Flag数:", Flags.query.count())
    print("Solves数:", Solves.query.count())
    print("Fails数:", Fails.query.count())
    print("Tracking(challenges.open)数:",
          Tracking.query.filter_by(type="challenges.open").count())
    print()
    print("=== 各队伍得分 ===")
    for tname in ["Alpha", "Bravo", "Charlie", "Delta"]:
        t = teams[tname]
        score = db.session.query(db.func.sum(Challenges.value)).join(
            Solves, Solves.challenge_id == Challenges.id
        ).filter(Solves.team_id == t.id).scalar() or 0
        print(f"  {tname}: {score} 分")
