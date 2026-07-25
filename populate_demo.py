"""
Demo data population for CTFd - uses CTFd's app context + models directly.
Does NOT modify any CTFd core files. Run with: python3.11 /workspace/populate_demo.py
"""
import sys
import os
from datetime import datetime, timedelta, timezone

os.environ.setdefault("PYTHONPATH", "/workspace")
sys.path.insert(0, "/workspace")

from CTFd import create_app
from CTFd.models import (
    db, Users, Teams, Challenges, Flags, Solves, Submissions,
    Awards, Notifications, Pages,
)
# NOTE: The Users/Teams models have a @validates("password") hook that
# automatically hashes any plaintext assigned to `.password`. So we pass the
# PLAINTEXT password to the model and let the validator hash it.
generate_password = lambda plaintext: plaintext  # identity - validator will hash

app = create_app()


def clear_existing_demo():
    """Wipe solves/submissions/awards/challenges/teams/users so the run is idempotent."""
    with app.app_context():
        print("[*] Clearing existing demo data...")
        # Order matters: children first to avoid FK violations.
        db.session.query(Solves).delete()
        db.session.query(Submissions).delete()
        db.session.query(Awards).delete()
        db.session.query(Notifications).delete()
        db.session.query(Pages).delete()
        db.session.query(Flags).delete()
        db.session.query(Challenges).delete()
        # Detach admin from any team + clear team captain before deleting teams/users
        admin = db.session.query(Users).filter_by(id=1).first()
        if admin:
            admin.team_id = None
        db.session.query(Teams).update({"captain_id": None})
        db.session.query(Users).filter(Users.id != 1).delete()
        db.session.query(Teams).delete()
        db.session.commit()
        print("    [+] Cleared")


def make_challenge(name, category, description, value, flag, state="visible"):
    chal = Challenges(
        name=name,
        category=category,
        description=description,
        value=value,
        state=state,
        type="standard",
        max_attempts=0,
    )
    db.session.add(chal)
    db.session.flush()
    flag_obj = Flags(
        challenge_id=chal.id,
        content=flag,
        type="static",
        data="",
    )
    db.session.add(flag_obj)
    return chal


def make_team(name):
    team = Teams(name=name, banned=False, hidden=False)
    db.session.add(team)
    db.session.flush()
    return team


def make_user(username, email, password, team=None, is_admin=False):
    user = Users(
        name=username,
        email=email,
        password=generate_password(password),
        team_id=team.id if team else None,
        type="admin" if is_admin else "user",
        verified=True,
        hidden=False,
        banned=False,
    )
    db.session.add(user)
    db.session.flush()
    return user


def make_solve(user, team, challenge, flag, days_ago=0):
    now = datetime.utcnow() - timedelta(days=days_ago, hours=0)
    # Create the solve record (correct submission)
    solve = Solves(
        user_id=user.id,
        team_id=team.id if team else None,
        challenge_id=challenge.id,
        provided=flag,
        ip="127.0.0.1",
        date=now,
    )
    db.session.add(solve)
    # Also record the submission attempt (so the admin "Submissions" stat has data)
    sub = Submissions(
        user_id=user.id,
        team_id=team.id if team else None,
        challenge_id=challenge.id,
        provided=flag,
        type="correct",
        ip="127.0.0.1",
        date=now,
    )
    db.session.add(sub)
    return solve


def make_award(team, user, name, value, days_ago=0):
    now = datetime.utcnow() - timedelta(days=days_ago)
    award = Awards(
        team_id=team.id if team else None,
        user_id=user.id if user else None,
        name=name,
        value=value,
        category="bonus",
        icon="shield",
        date=now,
    )
    db.session.add(award)


def main():
    with app.app_context():
        clear_existing_demo()

        # Make sure admin exists and is on a team
        admin = db.session.query(Users).filter_by(id=1).first()
        if not admin:
            admin = make_user("admin", "admin@democtf.local", "Admin@12345",
                              team=None, is_admin=True)
        else:
            admin.password = generate_password("Admin@12345")
            admin.verified = True

        # 1. Create challenges (8 of them across categories + varied difficulty)
        print("[*] Creating challenges...")
        challenges = [
            make_challenge("Base64 Basics",     "Crypto",   "Decode this: `Q1RGezRiMDNlX2I0czYzfQ==`", 100, "CTF{4b03e_b4s63}"),
            make_challenge("SQL Injection 101", "Web",     "Bypass the login form to retrieve the admin password.", 200, "CTF{sql_1nj3ct10n_m4st3r}"),
            make_challenge("Hidden in Plain Sight", "Misc", "The flag is hidden somewhere on this very page.", 150, "CTF{h1dd3n_1n_pl41n_s1ght}"),
            make_challenge("Stack Smash",       "Pwn",      "Overflow the buffer and redirect execution to win.", 300, "CTF{b0f_0v3rfl0w_w1ns}"),
            make_challenge("RSA Decrypt",       "Crypto",   "Given n, e, c — factor n and recover the plaintext.", 250, "CTF{rs4_sm4ll_pr1m3_f4ct0r5}"),
            make_challenge("Packet Hunt",       "Forensics","A packet capture hides the secret. Find it.", 200, "CTF{pc4p_f0r3ns1cs_tr4c3}"),
            make_challenge("Reverse Me",        "Reversing","Reverse the binary to find the flag-check logic.", 350, "CTF{r3v3rs3_3ng1n33r1ng}"),
            make_challenge("Stego Hideout",     "Stego",    "A picture is worth a thousand flags.", 175, "CTF{st3g0_ls6_h1d3out}"),
        ]
        db.session.commit()
        print(f"    [+] Created {len(challenges)} challenges")

        # 2. Create teams
        print("[*] Creating teams...")
        teams_data = [
            ("Team Alpha",   [("alice", "alice@democtf.local", "AlicePass1")]),
            ("Team Bravo",   [("bob",   "bob@democtf.local",   "BobPass22")]),
            ("Team Charlie", [("carol", "carol@democtf.local", "CarolPass3")]),
            ("Team Delta",   [("dave",  "dave@democtf.local",   "DavePass44")]),
            ("Team Echo",    [("eve",   "eve@democtf.local",    "EvePass555")]),
        ]
        teams = []
        users = []
        for tname, members in teams_data:
            team = make_team(tname)
            teams.append(team)
            for uname, email, pwd in members:
                user = make_user(uname, email, pwd, team=team)
                users.append((user, team))
        # Put admin on a team too (Team Admin)
        admin_team = make_team("Team Admin")
        admin.team_id = admin_team.id
        teams.append(admin_team)
        db.session.commit()
        print(f"    [+] Created {len(teams)} teams and {len(users)} users")

        # 3. Create solves (spread across teams & challenges & time)
        print("[*] Creating solves...")
        chal_by_idx = {i: c for i, c in enumerate(challenges)}
        user_by_name = {u.name: (u, t) for u, t in users}

        solve_plan = [
            # alice / Team Alpha - solves 5
            ("alice", 0), ("alice", 1), ("alice", 2), ("alice", 4), ("alice", 7),
            # bob / Team Bravo - solves 4
            ("bob", 0), ("bob", 2), ("bob", 3), ("bob", 5),
            # carol / Team Charlie - solves 3
            ("carol", 0), ("carol", 4), ("carol", 6),
            # dave / Team Delta - solves 2
            ("dave", 1), ("dave", 5),
            # eve / Team Echo - solves 1
            ("eve", 0),
        ]
        for i, (uname, chal_idx) in enumerate(solve_plan):
            user, team = user_by_name[uname]
            chal = chal_by_idx[chal_idx]
            flag = chal_by_idx[chal_idx].name  # placeholder, we set real flag below
            # Re-fetch the real flag from the challenge
            flag_obj = db.session.query(Flags).filter_by(challenge_id=chal.id).first()
            real_flag = flag_obj.content if flag_obj else f"CTF{{{chal.name}}}"
            # Spread solves across the last 7 days
            days_ago = (i % 7)
            make_solve(user, team, chal, real_flag, days_ago=days_ago)
        db.session.commit()
        print(f"    [+] Created {len(solve_plan)} solves")

        # 4. Add a few awards (bonus points / hints)
        print("[*] Creating awards...")
        make_award(teams[0], users[0][0], "First Blood Bonus", 50, days_ago=6)  # Team Alpha
        make_award(teams[1], users[1][0], "Speed Run Bonus",   25, days_ago=5)  # Team Bravo
        make_award(teams[2], users[2][0], "Crypto Whiz",       30, days_ago=4)  # Team Charlie
        db.session.commit()
        print("    [+] Created 3 awards")

        # 5. Add a notification and a page (so admin panels show more content)
        print("[*] Creating notification & page...")
        notif = Notifications(
            title="Welcome to Demo CTF 2026!",
            content="The competition has begun. Good luck, have fun!",
            date=datetime.utcnow() - timedelta(days=7),
        )
        db.session.add(notif)
        page = Pages(
            title="About",
            route="about",
            content="# About\n\nThis is a demo CTF instance showing the admin statistics panel.",
            draft=False,
            hidden=False,
            auth_required=False,
            format="markdown",
        )
        db.session.add(page)
        db.session.commit()
        print("    [+] Created notification + page")

        # 6. Summary
        print("\n" + "=" * 55)
        print("DEMO DATA SUMMARY")
        print("=" * 55)
        n_chals = db.session.query(Challenges).count()
        n_users = db.session.query(Users).filter(Users.type != "admin").count()
        n_teams = db.session.query(Teams).count()
        n_solves = db.session.query(Solves).count()
        n_subs = db.session.query(Submissions).count()
        n_awards = db.session.query(Awards).count()
        print(f"  Challenges: {n_chals}")
        print(f"  Users:      {n_users} (+1 admin)")
        print(f"  Teams:      {n_teams}")
        print(f"  Solves:     {n_solves}")
        print(f"  Submissions:{n_subs}")
        print(f"  Awards:    {n_awards}")
        print("=" * 55)
        print("\n[+] Admin login: admin / Admin@12345")
        print("[+] View admin stats at: http://localhost:4000/admin/statistics")


if __name__ == "__main__":
    main()
