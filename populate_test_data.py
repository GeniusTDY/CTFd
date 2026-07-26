"""
Generate test data for CTFd admin statistics page.
Does NOT modify CTFd core files - only inserts data via the models.
"""
import datetime
import random

from CTFd import create_app
from CTFd.models import (
    db,
    Users,
    Teams,
    Challenges,
    Flags,
    Solves,
    Fails,
    Awards,
)
from CTFd.utils.crypto import hash_password


def main():
    app = create_app()
    with app.app_context():
        # ---- Teams ----
        teams_data = [
            ("Alpha Squad", "alpha@team.ctfd", "CN"),
            ("Beta Crew", "beta@team.ctfd", "US"),
            ("Gamma Force", "gamma@team.ctfd", "JP"),
            ("Delta Unit", "delta@team.ctfd", "DE"),
            ("Echo Team", "echo@team.ctfd", "GB"),
        ]
        teams = []
        for name, email, country in teams_data:
            t = Teams(
                name=name,
                email=email,
                password="password",
                country=country,
                captain_id=None,
            )
            db.session.add(t)
            db.session.flush()
            teams.append(t)

        # ---- Users ----
        users_data = [
            ("alice", "alice@user.ctfd", "CN", teams[0].id),
            ("bob", "bob@user.ctfd", "CN", teams[0].id),
            ("carol", "carol@user.ctfd", "US", teams[1].id),
            ("dave", "dave@user.ctfd", "US", teams[1].id),
            ("eve", "eve@user.ctfd", "JP", teams[2].id),
            ("frank", "frank@user.ctfd", "JP", teams[2].id),
            ("grace", "grace@user.ctfd", "DE", teams[3].id),
            ("heidi", "heidi@user.ctfd", "DE", teams[3].id),
            ("ivan", "ivan@user.ctfd", "GB", teams[4].id),
            ("judy", "judy@user.ctfd", "GB", teams[4].id),
        ]
        users = []
        for name, email, country, team_id in users_data:
            u = Users(
                name=name,
                email=email,
                password="password",
                country=country,
                team_id=team_id,
                verified=True,
            )
            db.session.add(u)
            db.session.flush()
            users.append(u)

        # Set captains
        for t, captain in zip(teams, users[::2]):
            t.captain_id = captain.id
        db.session.flush()

        # ---- Challenges ----
        challenges_data = [
            ("Base64 Decode", "Decode the base64 string.", 100, "Crypto", "standard"),
            ("SQL Injection", "Find the flag via SQL injection.", 200, "Web", "standard"),
            ("Buffer Overflow", "Exploit the buffer overflow.", 300, "Pwn", "standard"),
            ("Reverse Me", "Reverse the binary to get the flag.", 250, "Reverse", "standard"),
            ("Hidden Flag", "Find the hidden flag in the image.", 150, "Misc", "standard"),
            ("RSA Challenge", "Crack the weak RSA.", 350, "Crypto", "standard"),
            ("XSS Filter Bypass", "Bypass the XSS filter.", 225, "Web", "standard"),
            ("Forensics 101", "Analyze the pcap file.", 175, "Forensics", "standard"),
            ("Format String", "Exploit format string vulnerability.", 400, "Pwn", "standard"),
            ("Stego Hidden", "Extract hidden data from audio.", 125, "Misc", "standard"),
        ]
        challenges = []
        for name, desc, value, category, ctype in challenges_data:
            c = Challenges(
                name=name,
                description=desc,
                value=value,
                category=category,
                type=ctype,
                state="visible",
            )
            db.session.add(c)
            db.session.flush()
            challenges.append(c)
            # Add a static flag for each challenge
            f = Flags(
                challenge_id=c.id,
                content=f"flag{{{name.lower().replace(' ', '_')}}}",
                type="static",
                data="",
            )
            db.session.add(f)

        db.session.flush()

        # ---- Solves ----
        # Each team solves a random subset of challenges at random times
        base_time = datetime.datetime.utcnow() - datetime.timedelta(days=3)
        solve_count = 0
        for team in teams:
            # Each team solves 4-8 challenges
            num_solves = random.randint(4, 8)
            solved_challenges = random.sample(challenges, num_solves)
            for chal in solved_challenges:
                # Pick a member from the team to be the solver
                team_members = [u for u in users if u.team_id == team.id]
                solver = random.choice(team_members)
                solve_time = base_time + datetime.timedelta(
                    hours=random.randint(1, 70)
                )
                s = Solves(
                    challenge_id=chal.id,
                    user_id=solver.id,
                    team_id=team.id,
                    ip="127.0.0.1",
                    provided=f"flag{{{chal.name.lower().replace(' ', '_')}}}",
                    date=solve_time,
                )
                db.session.add(s)
                solve_count += 1

        # ---- Fails ----
        fail_count = 0
        for team in teams:
            # Each team has some failed attempts
            num_fails = random.randint(3, 10)
            for _ in range(num_fails):
                chal = random.choice(challenges)
                team_members = [u for u in users if u.team_id == team.id]
                solver = random.choice(team_members)
                fail_time = base_time + datetime.timedelta(
                    hours=random.randint(1, 70)
                )
                f = Fails(
                    challenge_id=chal.id,
                    user_id=solver.id,
                    team_id=team.id,
                    ip="127.0.0.1",
                    provided="wrong_flag",
                    date=fail_time,
                )
                db.session.add(f)
                fail_count += 1

        # ---- Awards (bonus points) ----
        award_count = 0
        for team in teams:
            if random.random() > 0.4:
                team_members = [u for u in users if u.team_id == team.id]
                awardee = random.choice(team_members)
                a = Awards(
                    user_id=awardee.id,
                    team_id=team.id,
                    type="standard",
                    name="First Blood Bonus",
                    value=random.choice([50, 100, 150]),
                    category="bonus",
                    description="First to solve a challenge",
                    date=base_time + datetime.timedelta(hours=random.randint(1, 70)),
                )
                db.session.add(a)
                award_count += 1

        db.session.commit()

        print("=" * 50)
        print("Test data created successfully:")
        print(f"  Teams:    {len(teams)}")
        print(f"  Users:    {len(users)}")
        print(f"  Challenges: {len(challenges)}")
        print(f"  Solves:   {solve_count}")
        print(f"  Fails:    {fail_count}")
        print(f"  Awards:   {award_count}")
        print("=" * 50)


if __name__ == "__main__":
    main()
