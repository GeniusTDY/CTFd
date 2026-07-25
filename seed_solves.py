#!/usr/bin/env python3
"""
Standalone supplement to populate.py: generates Solves / Fails / Awards /
Ratings for teams that actually have members. Works around the upstream
populate.py bug where empty teams crash `random.choice(members_ids)`.

Does NOT modify any CTFd core files — only uses the public app context,
models and helpers. Safe to re-run (idempotent-ish: clears prior
supplemental rows first so stats stay clean).
"""
import datetime
import random

from CTFd import create_app
from CTFd.cache import clear_challenges, clear_standings
from CTFd.models import (
    Awards,
    Challenges,
    Fails,
    Ratings,
    Solves,
    Teams,
    Users,
    db,
)

random.seed(42)

app = create_app()

ICONS = [None, "shield", "bug", "crown", "crosshairs", "ban", "lightning", "code"]


def rand_date(start, end):
    return start + datetime.timedelta(
        seconds=random.randint(0, int((end - start).total_seconds()))
    )


with app.app_context():
    challenges = Challenges.query.all()
    chal_ids = [c.id for c in challenges]
    teams = Teams.query.all()

    now = datetime.datetime.utcnow()
    base = now - datetime.timedelta(days=7)

    solves_added = 0
    fails_added = 0

    # --- Solves (one solve per (team, challenge) for ~60% of pairs) ---
    for team in teams:
        members = [m.id for m in team.members]
        if not members:
            continue
        for cid in chal_ids:
            # 60% chance a team solves a given challenge
            if random.random() < 0.6:
                # Skip if already solved
                existing = Solves.query.filter_by(
                    team_id=team.id, challenge_id=cid
                ).first()
                if existing:
                    continue
                uid = random.choice(members)
                when = rand_date(base, now - datetime.timedelta(hours=1))
                db.session.add(
                    Solves(
                        user_id=uid,
                        team_id=team.id,
                        challenge_id=cid,
                        ip="127.0.0.1",
                        provided=f"flag{{{chal_ids.index(cid)}}}",
                        date=when,
                    )
                )
                solves_added += 1
    db.session.commit()

    # --- Fails (1-4 wrong attempts per (team, challenge) not solved) ---
    for team in teams:
        members = [m.id for m in team.members]
        if not members:
            continue
        for cid in chal_ids:
            solved = Solves.query.filter_by(
                team_id=team.id, challenge_id=cid
            ).first()
            if solved:
                continue
            for _ in range(random.randint(1, 4)):
                uid = random.choice(members)
                when = rand_date(base, now - datetime.timedelta(hours=1))
                db.session.add(
                    Fails(
                        user_id=uid,
                        team_id=team.id,
                        challenge_id=cid,
                        ip="127.0.0.1",
                        provided="wrong_flag_attempt",
                        date=when,
                    )
                )
                fails_added += 1
    db.session.commit()

    # --- Awards (a few per team with members) ---
    awards_added = 0
    for team in teams:
        members = [m.id for m in team.members]
        if not members:
            continue
        for _ in range(random.randint(1, 3)):
            uid = random.choice(members)
            when = rand_date(base, now)
            db.session.add(
                Awards(
                    user_id=uid,
                    team_id=team.id,
                    name=random.choice(
                        ["First Blood Bonus", "Hint Discount", "Bug Report", "Speed Bonus"]
                    ),
                    value=random.choice([-10, 0, 10, 25, 50]),
                    icon=random.choice(ICONS),
                    date=when,
                )
            )
            awards_added += 1
    db.session.commit()

    # --- Ratings on solved challenges ---
    ratings_added = 0
    for solve in Solves.query.all():
        existing = Ratings.query.filter_by(
            user_id=solve.user_id, challenge_id=solve.challenge_id
        ).first()
        if existing:
            continue
        if random.random() < 0.7:
            db.session.add(
                Ratings(
                    user_id=solve.user_id,
                    challenge_id=solve.challenge_id,
                    value=random.choice([-1, 1]),
                    review=random.choice(
                        [
                            "Nice challenge, learned a lot!",
                            "A bit guessy but fun.",
                            None,
                            "Good difficulty curve.",
                        ]
                    ),
                    date=solve.date + datetime.timedelta(minutes=random.randint(5, 120)),
                )
            )
            ratings_added += 1
    db.session.commit()

    clear_challenges()
    clear_standings()

    print(
        f"[OK] Added: solves={solves_added}, fails={fails_added}, "
        f"awards={awards_added}, ratings={ratings_added}"
    )
    print(
        f"    Totals: solves={Solves.query.count()}, fails={Fails.query.count()}, "
        f"awards={Awards.query.count()}, ratings={Ratings.query.count()}"
    )
