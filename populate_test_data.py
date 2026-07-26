"""
Populate CTFd with test data for the admin statistics page.

This script:
1. Sets up the admin account (root/root) with user_mode=teams (only if not already set up)
2. Creates brackets
3. Creates challenges across multiple categories with positions
4. Creates teams with brackets
5. Creates users assigned to teams
6. Creates solves, fails, and tracking opens to populate the matrix scoreboard

Logic notes (from get_standings / progression matrix):
- Score = sum(challenge.value for solved) + sum(award.value)
- Challenges/awards with value == 0 are filtered out for tie-breaking
- Ranking order: score DESC, max(solve.date) ASC, max(solve.id) ASC
- Matrix cell colors:
    green  = solved
    yellow = attempted (Fails) but not solved
    cyan   = opened (Tracking type="challenges.open") but no submission
    gray   = nothing
- For teams mode, opens are aggregated from team members' Tracking rows
- Solves/Fails use account_id == team_id in teams mode
- get_standings is cached for 60s; we clear the cache at the end
"""

import datetime
import os
import sys

# Ensure gevent is not monkey-patching here (we're a separate process)
os.environ.setdefault("DISABLE_GEVENT", "1")

from CTFd import create_app
from CTFd.models import (
    Awards,
    Brackets,
    Challenges,
    Configs,
    Fails,
    Flags,
    Solves,
    Teams,
    Tracking,
    Users,
    db,
)
from CTFd.utils import set_config
from CTFd.utils.config import is_setup
from CTFd.cache import cache


def ensure_setup():
    """Set up the admin account (root/root) if CTFd is not yet set up."""
    if is_setup():
        print("[*] CTFd is already set up; skipping setup.")
        return

    # Set required config values
    set_config("ctf_name", "CTFd Stats Test")
    set_config("ctf_description", "Test instance for admin statistics page")
    set_config("user_mode", "teams")
    set_config("challenge_visibility", "private")
    set_config("account_visibility", "public")
    set_config("score_visibility", "public")
    set_config("registration_visibility", "public")
    set_config("verify_emails", "false")
    set_config("start", "")
    set_config("end", "")
    set_config("freeze", None)
    set_config("ctf_theme", "core")
    set_config("setup", "true")

    admin = Users(
        name="root",
        email="root@example.com",
        password="root",
        type="admin",
        verified=True,
    )
    db.session.add(admin)
    db.session.commit()
    print("[+] Created admin user 'root' (password: 'root').")


def create_brackets():
    """Create two brackets: High School and University."""
    if Brackets.query.count() > 0:
        print("[*] Brackets already exist; skipping.")
        return {b.name: b.id for b in Brackets.query.all()}

    hs = Brackets(name="High School", description="High School students", type="teams")
    uni = Brackets(name="University", description="University students", type="teams")
    db.session.add_all([hs, uni])
    db.session.commit()
    print(f"[+] Created brackets: High School(id={hs.id}), University(id={uni.id})")
    return {"High School": hs.id, "University": uni.id}


def create_challenges():
    """Create 8 challenges across 3 categories with explicit positions and varied points."""
    if Challenges.query.count() > 0:
        print("[*] Challenges already exist; skipping.")
        return {c.name: c.id for c in Challenges.query.all()}

    specs = [
        # name, category, value, position, description
        ("Welcome",       "Misc",      10,   1, "Welcome challenge"),
        ("Base64 101",    "Crypto",    50,   2, "Decode a base64 string"),
        ("Caesar Cipher", "Crypto",   100,   3, "Classic Caesar cipher"),
        ("SQLi Login",    "Web",      150,   4, "SQL injection login bypass"),
        ("XSS Stealer",   "Web",      200,   5, "Cross-site scripting"),
        ("Buffer Overflow","Pwn",     300,   6, "Classic stack buffer overflow"),
        ("ROP Chain",     "Pwn",      400,   7, "Return-oriented programming"),
        ("Reverse Me",    "Reverse",  250,   8, "Simple reversing"),
        ("Forensics 1",   "Forensics",100,   9, "Analyze a pcap"),
        ("Zero Point",    "Misc",       0,  10, "Zero-value challenge (filtered in tie-break)"),
    ]

    chals = []
    for name, category, value, position, desc in specs:
        c = Challenges(
            name=name,
            description=desc,
            value=value,
            category=category,
            type="standard",
            state="visible",
            position=position,
        )
        chals.append(c)
        # Add a static flag so the challenge is solvable in theory
        db.session.add(c)
        db.session.flush()
        flag = Flags(challenge_id=c.id, type="static", content=f"flag{{{name.lower().replace(' ', '_')}}}")
        db.session.add(flag)

    db.session.commit()
    for c in chals:
        print(f"[+] Challenge: {c.name} ({c.category}, {c.value}pt, pos={c.position}, id={c.id})")
    return {c.name: c.id for c in Challenges.query.all()}


def create_teams(brackets):
    """Create 6 teams across the two brackets."""
    if Teams.query.count() > 0:
        print("[*] Teams already exist; skipping.")
        return {t.name: t.id for t in Teams.query.all()}

    specs = [
        # name, email, bracket, hidden, banned
        ("Alpha Squad",  "alpha@example.com",  "High School", False, False),
        ("Beta Team",    "beta@example.com",   "High School", False, False),
        ("Gamma Force",  "gamma@example.com",  "University",  False, False),
        ("Delta Ops",    "delta@example.com",  "University",  False, False),
        ("Epsilon Ghost","epsilon@example.com","University",  True,  False),  # hidden
        ("Zeta Banned",  "zeta@example.com",   "High School", False, True),   # banned
    ]

    teams = []
    for name, email, bracket_name, hidden, banned in specs:
        t = Teams(
            name=name,
            email=email,
            password="password",
            bracket_id=brackets[bracket_name],
            hidden=hidden,
            banned=banned,
        )
        db.session.add(t)
        teams.append(t)

    db.session.commit()
    for t in teams:
        print(f"[+] Team: {t.name} (bracket_id={t.bracket_id}, id={t.id}, hidden={t.hidden}, banned={t.banned})")
    return {t.name: t.id for t in Teams.query.all()}


def create_users(teams):
    """Create users and assign them to teams. Each team gets a captain + 1-2 members."""
    if Users.query.filter(Users.type != "admin").count() > 0:
        print("[*] Non-admin users already exist; skipping.")
        return

    # (username, email, team_name, bracket follows team)
    specs = [
        ("alice",  "alice@example.com",  "Alpha Squad"),
        ("bob",    "bob@example.com",    "Alpha Squad"),
        ("carol",  "carol@example.com",  "Beta Team"),
        ("dave",   "dave@example.com",   "Beta Team"),
        ("eve",    "eve@example.com",    "Gamma Force"),
        ("frank",  "frank@example.com",  "Gamma Force"),
        ("grace",  "grace@example.com",  "Gamma Force"),
        ("heidi",  "heidi@example.com",  "Delta Ops"),
        ("ivan",   "ivan@example.com",   "Delta Ops"),
        ("judy",   "judy@example.com",   "Epsilon Ghost"),
        ("mallory","mallory@example.com","Zeta Banned"),
    ]

    team_objs = {t.name: t for t in Teams.query.all()}
    for username, email, team_name in specs:
        team = team_objs[team_name]
        u = Users(
            name=username,
            email=email,
            password="password",
            team_id=team.id,
            bracket_id=team.bracket_id,
            verified=True,
            hidden=team.hidden,
            banned=team.banned,
        )
        db.session.add(u)
        db.session.flush()
        # Set first member as captain
        if team.captain_id is None:
            team.captain_id = u.id

    db.session.commit()
    print(f"[+] Created {len(specs)} users across teams.")


def _utc_now_minus(seconds):
    return datetime.datetime.utcnow() - datetime.timedelta(seconds=seconds)


def create_submissions_and_tracking(chals, teams):
    """
    Create solves, fails, and tracking opens to populate the matrix.

    Matrix behavior we want to demonstrate:
      - green  (solved)
      - yellow (attempted/fail but not solved)
      - cyan   (opened but no submission)
      - gray   (nothing)

    Score / ranking:
      - Alpha Squad: solves Welcome + Base64 + Caesar + SQLi = 10+50+100+150 = 310
      - Beta Team:   solves Welcome + Base64 + XSS (200) = 10+50+200 = 260
      - Gamma Force: solves Welcome + Caesar + Buffer Overflow + ROP = 10+100+300+400 = 810  (highest)
      - Delta Ops:   solves Welcome + Reverse Me + Forensics = 10+250+100 = 360
      - Epsilon Ghost: solves Base64 + SQLi = 50+150 = 200 (hidden team — admin can still see)
      - Zeta Banned: solves Welcome = 10 (banned — admin sees, public doesn't)

    Tie-break check:
      - Alpha (310) and Delta (360) are distinct, but we want to ensure date-based tie-break works.
      - We deliberately make Gamma the highest with the earliest solve date to lock #1.

    Fails / opens:
      - Alpha: fail on XSS (yellow), open ROP (cyan, no submission)
      - Beta:  fail on Caesar (yellow), open Buffer Overflow (cyan)
      - Gamma: open Welcome (cyan) -- but solved too, so green wins
      - Delta: fail on ROP (yellow), open XSS (cyan)
      - Epsilon: open Caesar (cyan)
      - Zeta:   open Base64 (cyan)
    """
    if Solves.query.count() > 0 or Fails.query.count() > 0:
        print("[*] Submissions already exist; skipping.")
        return

    team_objs = {t.name: t for t in Teams.query.all()}
    # captain of each team is the first user; we'll attribute submissions to captains
    captain_ids = {t.name: t.captain_id for t in Teams.query.all()}

    # base time offsets (seconds ago). Earlier solve = smaller offset = earlier date.
    # Gamma solves first (largest negative offset / earliest), then Delta, then Alpha, then Beta.

    # (team_name, challenge_name, type: solve/fail/open, seconds_ago)
    plan = [
        # ---- Solves (correct) ----
        # Gamma Force — earliest solver, highest score
        ("Gamma Force", "Welcome",         "solve", 100000),
        ("Gamma Force", "Caesar Cipher",   "solve",  95000),
        ("Gamma Force", "Buffer Overflow", "solve",  90000),
        ("Gamma Force", "ROP Chain",       "solve",  85000),

        # Delta Ops
        ("Delta Ops",   "Welcome",         "solve",  80000),
        ("Delta Ops",   "Reverse Me",      "solve",  78000),
        ("Delta Ops",   "Forensics 1",     "solve",  76000),

        # Alpha Squad
        ("Alpha Squad", "Welcome",         "solve",  70000),
        ("Alpha Squad", "Base64 101",      "solve",  68000),
        ("Alpha Squad", "Caesar Cipher",   "solve",  66000),
        ("Alpha Squad", "SQLi Login",      "solve",  64000),

        # Beta Team
        ("Beta Team",   "Welcome",         "solve",  60000),
        ("Beta Team",   "Base64 101",      "solve",  58000),
        ("Beta Team",   "XSS Stealer",     "solve",  56000),

        # Epsilon Ghost (hidden)
        ("Epsilon Ghost","Base64 101",     "solve",  50000),
        ("Epsilon Ghost","SQLi Login",     "solve",  48000),

        # Zeta Banned
        ("Zeta Banned", "Welcome",         "solve",  40000),

        # ---- Fails (incorrect) - yellow cells ----
        ("Alpha Squad", "XSS Stealer",     "fail",   62000),
        ("Beta Team",   "Caesar Cipher",   "fail",   57000),
        ("Delta Ops",   "ROP Chain",       "fail",   75000),
        ("Gamma Force", "Reverse Me",      "fail",   88000),  # Gamma tried but didn't solve

        # ---- Opens (Tracking type="challenges.open") - cyan cells ----
        # These create cyan cells ONLY where there's no solve and no fail for that (team, challenge)
        ("Alpha Squad", "ROP Chain",       "open",   63000),
        ("Beta Team",   "Buffer Overflow", "open",   59000),
        ("Delta Ops",   "XSS Stealer",     "open",   77000),
        ("Epsilon Ghost","Caesar Cipher",  "open",   49000),
        ("Zeta Banned", "Base64 101",      "open",   39000),
        # Gamma opens Welcome but already solved -> still green
        ("Gamma Force", "Welcome",         "open",  101000),
    ]

    for team_name, chal_name, kind, secs_ago in plan:
        team = team_objs[team_name]
        chal_id = chals[chal_name]
        user_id = captain_ids[team_name]
        date = _utc_now_minus(secs_ago)

        if kind == "solve":
            # Avoid duplicate solves (unique constraint on challenge_id+team_id)
            existing = Solves.query.filter_by(challenge_id=chal_id, team_id=team.id).first()
            if existing:
                continue
            s = Solves(
                challenge_id=chal_id,
                user_id=user_id,
                team_id=team.id,
                ip="127.0.0.1",
                provided=f"flag{{{chal_name.lower().replace(' ', '_')}}}",
                date=date,
            )
            db.session.add(s)
        elif kind == "fail":
            f = Fails(
                challenge_id=chal_id,
                user_id=user_id,
                team_id=team.id,
                ip="127.0.0.1",
                provided="wrong_attempt",
                date=date,
            )
            db.session.add(f)
        elif kind == "open":
            t = Tracking(
                type="challenges.open",
                ip="127.0.0.1",
                target=chal_id,
                user_id=user_id,
                date=date,
            )
            db.session.add(t)

    db.session.commit()
    print(f"[+] Created submissions/opens: {Solves.query.count()} solves, {Fails.query.count()} fails, "
          f"{Tracking.query.filter_by(type='challenges.open').count()} opens.")


def create_awards(teams):
    """Add a couple of awards to verify the awards branch of get_standings."""
    if Awards.query.count() > 0:
        print("[*] Awards already exist; skipping.")
        return

    team_objs = {t.name: t for t in Teams.query.all()}
    captain_ids = {t.name: t.captain_id for t in Teams.query.all()}

    # Alpha gets a +50 "First Blood" style bonus; Beta gets -20 penalty
    a1 = Awards(
        user_id=captain_ids["Alpha Squad"],
        team_id=team_objs["Alpha Squad"].id,
        name="First Solve Bonus",
        description="Bonus for first solve",
        value=50,
        category="bonus",
        date=_utc_now_minus(69000),
    )
    a2 = Awards(
        user_id=captain_ids["Beta Team"],
        team_id=team_objs["Beta Team"].id,
        name="Hint Penalty",
        description="Hint unlock penalty",
        value=-20,
        category="penalty",
        date=_utc_now_minus(57000),
    )
    db.session.add_all([a1, a2])
    db.session.commit()
    print("[+] Created 2 awards (Alpha +50, Beta -20).")


def clear_cache():
    """Clear the memoize cache so get_standings picks up the new data immediately."""
    try:
        cache.clear()
        print("[+] Cache cleared.")
    except Exception as e:
        print(f"[!] Could not clear cache: {e}")


def print_summary():
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Users:    {Users.query.count()}")
    print(f"Teams:    {Teams.query.count()}")
    print(f"Challenges: {Challenges.query.count()} (visible: {Challenges.query.filter_by(state='visible').count()})")
    print(f"Brackets: {Brackets.query.count()}")
    print(f"Solves:   {Solves.query.count()}")
    print(f"Fails:    {Fails.query.count()}")
    print(f"Opens:    {Tracking.query.filter_by(type='challenges.open').count()}")
    print(f"Awards:   {Awards.query.count()}")

    print("\nExpected team scores (solves + awards):")
    expected = {
        "Gamma Force":   10 + 100 + 300 + 400,           # 810
        "Delta Ops":     10 + 250 + 100,                 # 360
        "Alpha Squad":   10 + 50 + 100 + 150 + 50,       # 360 (with +50 award)
        "Beta Team":     10 + 50 + 200 - 20,             # 240 (with -20 award)
        "Epsilon Ghost": 50 + 150,                       # 200
        "Zeta Banned":   10,                             # 10
    }
    for name, score in sorted(expected.items(), key=lambda x: -x[1]):
        print(f"  {name:<16} -> {score}")
    print("\nNote: Alpha Squad & Delta Ops tie at 360. Tie-breaker = max(solve.date) ASC.")
    print("Delta's latest solve (Forensics 1, ~76000s ago) is earlier than Alpha's latest (SQLi, ~64000s ago),")
    print("so Delta should rank above Alpha.")
    print("=" * 60)


def main():
    app = create_app()
    with app.app_context():
        ensure_setup()
        brackets = create_brackets()
        chals = create_challenges()
        teams = create_teams(brackets)
        create_users(teams)
        create_submissions_and_tracking(chals, teams)
        create_awards(teams)
        clear_cache()
        print_summary()


if __name__ == "__main__":
    main()
