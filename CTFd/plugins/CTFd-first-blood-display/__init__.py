import os
from flask import Blueprint, jsonify
from CTFd.models import Solves, Users, Teams, Challenges
from CTFd.utils import get_config
from CTFd.utils.user import is_admin
from CTFd.cache import cache


PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))

PLUGIN_SLUG = "CTFd-first-blood-display"

first_blood_bp = Blueprint(
    "first_blood_display",
    __name__,
    static_folder=os.path.join(PLUGIN_DIR, "assets"),
    static_url_path=f"/plugins/{PLUGIN_SLUG}/assets",
)


@cache.memoize(timeout=30)
def _get_first_blood(challenge_id):
    # find the first eligible solver, skipping hidden/banned users and teams
    all_solves = (
        Solves.query
        .filter_by(challenge_id=int(challenge_id))
        .order_by(Solves.date.asc())
        .all()
    )

    is_team_mode = get_config("user_mode") == "teams"

    for solve in all_solves:
        user = Users.query.filter_by(id=solve.user_id).first()
        if user is None:
            continue

        # cheaters and ghosts don't get glory
        if user.hidden or user.banned:
            continue

        # in team mode, skip users whose team is hidden/banned
        if is_team_mode and user.team_id:
            team = Teams.query.filter_by(id=user.team_id).first()
            if team and (team.hidden or team.banned):
                continue

        # found an eligible first blood
        result = {
            "user_id": user.id,
            "user_name": user.name,
            "solve_time": solve.date.isoformat() + "Z",
            "challenge_id": int(challenge_id),
        }

        if is_team_mode and user.team_id:
            team = Teams.query.filter_by(id=user.team_id).first()
            if team and not team.hidden and not team.banned:
                result["team_id"] = team.id
                result["team_name"] = team.name

        return result

    return None


@first_blood_bp.route("/api/v1/first_blood/<int:challenge_id>")
def get_first_blood(challenge_id):
    # you don't get to enumerate hidden challenges, nice try
    challenge = Challenges.query.filter_by(id=challenge_id).first_or_404()

    if challenge.state == "hidden" and not is_admin():
        return jsonify({"success": False, "data": None}), 404

    if challenge.state == "locked" and not is_admin():
        return jsonify({"success": False, "data": None}), 403

    data = _get_first_blood(challenge_id)
    return jsonify({"success": True, "data": data})


@first_blood_bp.route("/api/v1/first_bloods")
def get_all_first_bloods():
    if is_admin():
        challenges = Challenges.query.all()
    else:
        challenges = Challenges.query.filter(
            Challenges.state != "hidden",
            Challenges.state != "locked",
        ).all()

    result = {}
    for chal in challenges:
        fb = _get_first_blood(chal.id)
        if fb:
            result[str(chal.id)] = fb

    return jsonify({"success": True, "data": result})


# no render_template_string, no jinja, no SSTI, just raw html like animals
INJECT_HTML = (
    f'<link rel="stylesheet" href="/plugins/{PLUGIN_SLUG}/assets/first-blood.css">'
    f'<script defer src="/plugins/{PLUGIN_SLUG}/assets/first-blood.js"></script>'
)


def load(app):
    app.register_blueprint(first_blood_bp)

    @app.after_request
    def _inject_fb_assets(response):
        if response.direct_passthrough:
            return response
        if not response.content_type or "text/html" not in response.content_type:
            return response
        try:
            html = response.get_data(as_text=True)
            if "</head>" in html:
                html = html.replace("</head>", INJECT_HTML + "</head>", 1)
                response.set_data(html)
        except Exception:
            # if this breaks, the CTF still runs. priorities.
            pass
        return response

    print(" * [FirstBloodDisplay] loaded. time to see who scripted their way to glory")
