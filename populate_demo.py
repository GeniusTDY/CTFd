"""
Populate demo data for CTFd admin statistics page.

This script does NOT modify any CTFd core files. It only uses CTFd's
public app context, models and cache utilities to insert demo data:
  - Completes the initial setup (admin account + index page)
  - Creates several challenges with flags
  - Creates several users / teams
  - Creates some solves and fails so the statistics page is populated

Run with the same python3.11 interpreter used to run CTFd:
    python3.11 populate_demo.py
"""

import datetime
import random

from CTFd import create_app
from CTFd.cache import cache
from CTFd.models import (
    Admins,
    Challenges,
    Fails,
    Flags,
    Pages,
    Solves,
    Teams,
    Users,
    db,
)
from CTFd.utils import set_config
from CTFd.utils.config import is_setup


def now_minus(days, hours=0):
    return datetime.datetime.utcnow() - datetime.timedelta(days=days, hours=hours)


def main():
    app = create_app()
    with app.app_context():
        # ----- 1. Complete setup if not done yet -----
        if not is_setup():
            # Set the basic config values that the setup wizard would set
            set_config("ctf_name", "Demo CTF")
            set_config("ctf_description", "Demo CTF for admin statistics preview")
            set_config("user_mode", "users")
            set_config("challenge_visibility", "private")
            set_config("registration_visibility", "public")
            set_config("score_visibility", "public")
            set_config("account_visibility", "public")
            set_config("verify_emails", "false")
            set_config("social_shares", "true")
            set_config("team_size", 0)
            set_config("ctf_theme", "core")
            set_config("start", None)
            set_config("end", None)
            set_config("freeze", None)
            set_config("setup", True)

            admin = Admins(
                name="admin",
                email="admin@demo.ctf",
                password="admin123456",
                type="admin",
                hidden=True,
            )
            db.session.add(admin)

            index_page = Pages(
                title="Demo CTF", route="index", content="Welcome to Demo CTF", draft=False
            )
            db.session.add(index_page)
            db.session.commit()
            print("[setup] admin created: admin / admin123456")
        else:
            print("[setup] already completed, skipping")

        # ----- 2. Create challenges -----
        challenge_specs = [
            ("Base64 Warmup", "Crypto", 100, "flag{base64_is_easy}"),
            ("Caesar Cipher", "Crypto", 150, "flag{et_tu_brute}"),
            ("SQL Injection 101", "Web", 200, "flag{sql_injection_master}"),
            ("XSS Playground", "Web", 250, "flag{xss_hunter}"),
            ("Buffer Overflow", "Pwn", 300, "flag{pwned_the_stack}"),
            ("Reverse Me", "Reverse", 350, "flag{reversed_engineering}"),
            ("Hidden Flag", "Misc", 100, "flag{look_in_the_source}"),
            ("Stego Image", "Misc", 200, "flag{stego_is_fun}"),
            ("Forensic Disk", "Forensics", 400, "flag{disk_forensics_pro}"),
            ("Network Capture", "Forensics", 300, "flag{pcap_analyzed}"),
        ]

        existing = Challenges.query.count()
        if existing == 0:
            for i, (name, category, value, flag) in enumerate(challenge_specs):
                chal = Challenges(
                    name=name,
                    description=f"Demo challenge: {name}. Category: {category}.",
                    value=value,
                    category=category,
                    type="standard",
                    state="visible",
                    position=i,
                )
                db.session.add(chal)
                db.session.flush()
                db.session.add(
                    Flags(challenge_id=chal.id, type="static", content=flag, data="")
                )
            db.session.commit()
            print(f"[challenges] created {len(challenge_specs)} challenges")
        else:
            print(f"[challenges] already {existing} challenges exist, skipping")

        challenges = Challenges.query.all()

        # ----- 3. Create users -----
        user_specs = [
            ("alice", "alice@demo.ctf"),
            ("bob", "bob@demo.ctf"),
            ("charlie", "charlie@demo.ctf"),
            ("diana", "diana@demo.ctf"),
            ("eve", "eve@demo.ctf"),
            ("frank", "frank@demo.ctf"),
        ]
        existing_users = Users.query.filter(Users.type == "user").count()
        if existing_users == 0:
            for name, email in user_specs:
                db.session.add(
                    Users(
                        name=name,
                        email=email,
                        password="password123",
                        type="user",
                        verified=True,
                        country="CN",
                    )
                )
            db.session.commit()
            print(f"[users] created {len(user_specs)} users")
        else:
            print(f"[users] already {existing_users} users exist, skipping")

        users = Users.query.filter(Users.type == "user").all()

        # ----- 4. Create solves & fails -----
        existing_solves = Solves.query.count()
        if existing_solves == 0:
            random.seed(42)
            for chal in challenges:
                # Each challenge is solved by a random subset of users
                solvers = random.sample(users, k=random.randint(1, len(users)))
                for u in solvers:
                    solve = Solves(
                        challenge_id=chal.id,
                        user_id=u.id,
                        team_id=None,
                        ip="127.0.0.1",
                        provided="flag{...}",
                        date=now_minus(days=random.randint(0, 3), hours=random.randint(0, 12)),
                    )
                    db.session.add(solve)

                # Add a few wrong submissions per challenge
                failers = [u for u in users if u not in solvers]
                for u in random.sample(failers, k=min(len(failers), random.randint(0, 3))):
                    db.session.add(
                        Fails(
                            challenge_id=chal.id,
                            user_id=u.id,
                            team_id=None,
                            ip="127.0.0.1",
                            provided="wrong_flag",
                            date=now_minus(days=random.randint(0, 3)),
                        )
                    )
            db.session.commit()
            print("[submissions] created solves & fails")
        else:
            print(f"[submissions] already {existing_solves} solves exist, skipping")

        db.session.close()
        cache.clear()
        print("[done] demo data populated")


if __name__ == "__main__":
    main()
