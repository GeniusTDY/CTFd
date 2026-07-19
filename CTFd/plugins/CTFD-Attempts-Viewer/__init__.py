import json
import os
from flask import Blueprint, render_template, jsonify, request, make_response
from flask_babel import gettext, lazy_gettext
from CTFd.plugins import register_plugin_assets_directory, register_plugin_script
from CTFd.models import db
from CTFd.utils.decorators import authed_only, admins_only
from CTFd.utils.plugins import (
    get_menubar_plugins as _original_get_menubar_plugins,
    get_configurable_plugins as _original_get_configurable_plugins,
)
from CTFd.utils.user import get_current_user, get_current_team
from CTFd.models import Challenges, Submissions, Users

def _translated_get_menubar_plugins():
    # Wrap each plugin's name with gettext so the sidebar entry under
    # the "Plugins" dropdown can be translated without touching CTFd core.
    plugins = _original_get_menubar_plugins()
    return [p._replace(name=gettext(p.name)) for p in plugins]


def _translated_get_configurable_plugins():
    # Wrap each plugin's name with gettext so the entry under the admin
    # Config page sidebar ("Plugins" section) can be translated without
    # touching CTFd core. This complements _translated_get_menubar_plugins,
    # which only covers the top-nav "Plugins" dropdown.
    plugins = _original_get_configurable_plugins()
    return [p._replace(name=gettext(p.name)) for p in plugins]


class AttemptsViewerSettings(db.Model):
    __tablename__ = "attempts_viewer_settings"
    id = db.Column(db.Integer, primary_key=True)
    show_main_button = db.Column(db.Boolean, default=False)


def load(app):
    # Register plugin translations directory
    plugin_translations = os.path.join(os.path.dirname(__file__), "translations")
    current = app.config.get("BABEL_TRANSLATION_DIRECTORIES", "translations")
    if plugin_translations not in current:
        app.config["BABEL_TRANSLATION_DIRECTORIES"] = f"{current};{plugin_translations}"

    # Override the Jinja2 globals so the "Plugins" entries — both the
    # top-nav dropdown (get_menubar_plugins) and the admin Config page
    # sidebar (get_configurable_plugins) — are rendered through gettext
    # (no CTFd core template change).
    app.jinja_env.globals.update(
        get_menubar_plugins=_translated_get_menubar_plugins,
        get_configurable_plugins=_translated_get_configurable_plugins,
    )

    viewer_bp = Blueprint(
        "ctfd_attempts_viewer",
        __name__,
        template_folder="templates",
        static_folder="assets",
        url_prefix="/plugins/ctfd-attempts-viewer",
    )

    # --- JS translations dict ---
    JS_I18N = {
        "attempts_history": lazy_gettext("Your attempts history"),
        "my_attempts": lazy_gettext("My attempts"),
        "close": lazy_gettext("Close"),
        "loading": lazy_gettext("Loading..."),
        "attempts": lazy_gettext("Attempts"),
        "cannot_find_challenge_id": lazy_gettext("Cannot find current challenge ID."),
        "no_attempts": lazy_gettext("No attempts for this challenge."),
        "filter_by_player": lazy_gettext("Filter by player:"),
        "all": lazy_gettext("All"),
        "player": lazy_gettext("Player"),
        "challenge": lazy_gettext("Challenge"),
        "answer_tried": lazy_gettext("Submission"),
        "correct": lazy_gettext("Correct"),
        "incorrect": lazy_gettext("Incorrect"),
        "correct_answer": lazy_gettext("Correct?"),
        "type": lazy_gettext("Status"),
        "date": lazy_gettext("Date"),
        "copy": lazy_gettext("Copy"),
        "error_loading": lazy_gettext("Error retrieving attempts."),
        "network_error": lazy_gettext("Network or server error."),
        "settings_saved": lazy_gettext("Settings saved!"),
        "error_saving": lazy_gettext("Error saving settings."),
    }

    @viewer_bp.context_processor
    def inject_i18n():
        return {"js_i18n": JS_I18N}

    @viewer_bp.route("/assets/i18n.js")
    def i18n_js():
        i18n_dict = {k: str(v) for k, v in JS_I18N.items()}
        js_content = "window.AT_I18N = " + json.dumps(
            i18n_dict, ensure_ascii=False
        ) + ";"
        response = make_response(js_content)
        response.headers["Content-Type"] = "application/javascript"
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        return response

    # --- Initialisation table et config par défaut ---
    with app.app_context():
        db.create_all()
        settings = AttemptsViewerSettings.query.first()
        if not settings:
            settings = AttemptsViewerSettings(show_main_button=False)
            db.session.add(settings)
            db.session.commit()

    @viewer_bp.route("/admin")
    @admins_only
    def admin_page():
        return render_template("ctfd_attempts_viewer_admin.html")

    @viewer_bp.route("/admin/save", methods=["POST"])
    @admins_only
    def save_admin_settings():
        data = request.get_json()
        settings = AttemptsViewerSettings.query.first()
        if not settings:
            settings = AttemptsViewerSettings()
        settings.show_main_button = data.get("show_main_button", False)
        db.session.add(settings)
        db.session.commit()
        return jsonify({"success": True})

    @viewer_bp.route("/api/settings", methods=["GET"])
    @authed_only
    def get_settings():
        # Public read-only setting for logged-in users so the client-side
        # script on /challenges can decide whether to render the button.
        settings = AttemptsViewerSettings.query.first()
        if not settings:
            return jsonify({"show_main_button": False})
        return jsonify({"show_main_button": settings.show_main_button})

    @viewer_bp.route("/attempts")
    @authed_only
    def attempts_page():
        return render_template("ctfd_attempts_viewer_attempts.html")

    @viewer_bp.route("/api/my-team-submissions")
    @authed_only
    def team_submissions():
        user = get_current_user()
        team = get_current_team()

        if not user:
            return (
                jsonify(
                    {
                        "success": False,
                        "data": [],
                        "error": gettext("User not connected"),
                    }
                ),
                403,
            )

        if team:
            filter_condition = Submissions.team_id == team.id
        else:
            filter_condition = Submissions.user_id == user.id

        rows = (
            db.session.query(
                Submissions.challenge_id,
                Submissions.provided,
                Submissions.type,
                Submissions.date,
                Challenges.name.label("challenge_name"),
                Users.name.label("user_name"),
            )
            .join(Challenges, Submissions.challenge_id == Challenges.id)
            .join(Users, Submissions.user_id == Users.id)
            .filter(filter_condition)
            .all()
        )

        data = [
            {
                "challenge_id": row.challenge_id,
                "challenge_name": row.challenge_name,
                "submission": row.provided,
                "type": row.type,
                "date": row.date.isoformat() + "Z",
                "user_name": row.user_name,
            }
            for row in rows
        ]

        response = jsonify({"success": True, "data": data})
        response.headers["Cache-Control"] = (
            "no-store, no-cache, must-revalidate, private"
        )
        return response

    # Plugin registration
    app.register_blueprint(viewer_bp)

    register_plugin_assets_directory(
        app, base_path="/plugins/ctfd-attempts-viewer/assets"
    )
    register_plugin_script("/plugins/ctfd-attempts-viewer/assets/i18n.js")
    register_plugin_script("/plugins/ctfd-attempts-viewer/assets/settings.js")