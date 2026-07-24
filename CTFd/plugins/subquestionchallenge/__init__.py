import datetime
import json
import os
from flask import Blueprint, Response
from flask_babel import gettext

from CTFd.models import Challenges, db, Flags, Solves
from CTFd.plugins import (
    register_plugin_assets_directory,
    register_plugin_script,
    register_admin_plugin_script,
)
from CTFd.plugins.challenges import CHALLENGE_CLASSES, BaseChallenge
from CTFd.plugins.flags import get_flag_class
from CTFd.plugins.migrations import upgrade


# Server-side translated strings exposed to JavaScript.
# Keys are the English source strings used throughout the plugin's JS code;
# values are gettext-translated at request time (resolved per-locale).
_PLUGIN_TRANSLATION_KEYS = [
    "Multi Question Challenge",
    "Score Acquired",
    "Questions Completed",
    "Questions Remaining",
    "Question",
    "points",
    "Completed",
    "Unsolved",
    "Select a question to answer:",
    "Enter the flag for the selected question",
    "Congratulations on completing all questions!",
    "You have successfully solved all questions in this multi-question challenge.",
    "Challenge Completed",
    "All Completed",
    "Hint",
    "All questions have been completed! Congratulations on finishing this challenge.",
    "Please select a question",
    "Error",
    "Please use the multi-question interface to submit",
    "Wait",
    "Question %(num)s",
    "Flag %(num)s",
    "Enter question text",
    "Enter flag",
    "Points",
    "Add Question",
    "Remove Last Question",
    "Please fill out the challenge name and category",
    "Please fill out at least one question and its corresponding flag",
    "Failed to create challenge. Please check all fields are filled correctly.",
    "An error occurred while creating the challenge",
]


def _get_plugin_translations():
    """Return a dict of {english_key: translated_value} for the current locale."""
    return {key: gettext(key) for key in _PLUGIN_TRANSLATION_KEYS}


class SubQuestionChallengeModel(Challenges):
    __mapper_args__ = {"polymorphic_identity": "subquestionchallenge"}
    
    # 不需要額外的 id 欄位，因為我們繼承自 Challenges
    # 也不需要額外的表格
    
    def __init__(self, *args, **kwargs):
        super(SubQuestionChallengeModel, self).__init__(**kwargs)


class SubQuestionItem(db.Model):
    __tablename__ = "subquestion_items"
    
    id = db.Column(db.Integer, primary_key=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenges.id', ondelete="CASCADE"))
    question_num = db.Column(db.Integer)
    question_text = db.Column(db.Text)
    points = db.Column(db.Integer, default=100)
    flag_id = db.Column(db.Integer, db.ForeignKey('flags.id', ondelete="CASCADE"))
    
    challenge = db.relationship("Challenges", foreign_keys="SubQuestionItem.challenge_id")
    flag = db.relationship("Flags", foreign_keys="SubQuestionItem.flag_id")

    def __init__(self, challenge_id, question_num, question_text, points, flag_id):
        self.challenge_id = challenge_id
        self.question_num = question_num
        self.question_text = question_text
        self.points = points
        self.flag_id = flag_id


class SubQuestionPartialSolve(db.Model):
    __tablename__ = "subquestion_partial_solves"
    __table_args__ = (db.UniqueConstraint('challenge_id', 'team_id', 'user_id', 'question_num'), {})
    
    id = db.Column(db.Integer, primary_key=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenges.id'))
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    question_num = db.Column(db.Integer)
    ip = db.Column(db.String(46))
    provided = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __init__(self, challenge_id, team_id, user_id, question_num, ip, provided):
        self.challenge_id = challenge_id
        self.team_id = team_id
        self.user_id = user_id
        self.question_num = question_num
        self.ip = ip
        self.provided = provided


class SubQuestionChallengeType(BaseChallenge):
    id = "subquestionchallenge"  # Unique identifier used to register challenges
    name = "Sub Question Challenge"  # Name of a challenge type
    templates = {  # Templates used for each aspect of challenge editing & viewing
        "create": "/plugins/subquestionchallenge/assets/create.html",
        "update": "/plugins/subquestionchallenge/assets/update.html",
        "view": "/plugins/subquestionchallenge/assets/view.html",
    }
    scripts = {  # Scripts that are loaded when a template is loaded
        "create": "/plugins/subquestionchallenge/assets/create.js",
        "update": "/plugins/subquestionchallenge/assets/update.js",
        "view": "/plugins/subquestionchallenge/assets/view.js",
    }
    # Route at which files are accessible. This must be registered using register_plugin_assets_directory()
    route = "/plugins/subquestionchallenge/assets/"
    # Blueprint used to access the static_folder directory.
    blueprint = Blueprint(
        "subquestionchallenge",
        __name__,
        template_folder="templates",
        static_folder="assets",
    )
    challenge_model = SubQuestionChallengeModel

    @classmethod
    def create(cls, request):
        """
        This method is used to process the challenge creation request.
        """
        data = request.form or request.get_json()
        
        # Separate challenge data from flag data
        challenge_data = {}
        questions = {}  # question_num -> {text, points, flag_content}
        
        # Valid challenge fields based on the Challenges model
        valid_challenge_fields = {
            'name', 'description', 'connection_info', 'next_id', 
            'max_attempts', 'value', 'category', 'type', 'state', 'requirements'
        }
        
        for key, value in data.items():
            if key in valid_challenge_fields:
                challenge_data[key] = value
                continue

            parts = key.split('_')
            if len(parts) != 2 or not parts[1].isdigit():
                continue

            question_num = int(parts[1])
            
            if key.startswith('flag_') and value:
                if question_num not in questions:
                    questions[question_num] = {}
                questions[question_num]['flag_content'] = value
            elif key.startswith('question_') and value:
                if question_num not in questions:
                    questions[question_num] = {}
                questions[question_num]['text'] = value
            elif key.startswith('points_') and value:
                if question_num not in questions:
                    questions[question_num] = {}
                questions[question_num]['points'] = int(value)
        
        # Calculate total value from all questions and override the challenge value
        total_value = sum(q.get('points', 0) for q in questions.values())
        challenge_data['value'] = total_value
        
        # Ensure 'state' is correctly passed, default to 'hidden' if not present
        if 'state' not in challenge_data:
            challenge_data['state'] = 'hidden'

        # Create the basic challenge
        challenge = cls.challenge_model(**challenge_data)
        db.session.add(challenge)
        db.session.commit()
        
        # Create flags and question items
        for question_num, question_info in questions.items():
            if 'flag_content' in question_info and 'text' in question_info:
                # Create flag
                flag = Flags(
                    challenge_id=challenge.id,
                    content=question_info['flag_content'],
                    type='static'
                )
                db.session.add(flag)
                db.session.flush()  # Get the flag ID
                
                # Create question item
                question_item = SubQuestionItem(
                    challenge_id=challenge.id,
                    question_num=question_num,
                    question_text=question_info['text'],
                    points=question_info.get('points', 100),
                    flag_id=flag.id
                )
                db.session.add(question_item)
        
        db.session.commit()
        return challenge

    @classmethod
    def read(cls, challenge):
        """
        This method is used to access the data of a challenge in a format processable by the front end.
        """
        challenge = cls.challenge_model.query.filter_by(id=challenge.id).first()
        
        # Get all question items for this challenge
        question_items = SubQuestionItem.query.filter_by(challenge_id=challenge.id).order_by(SubQuestionItem.question_num).all()
        
        # Get user's solved questions
        from CTFd.utils.user import get_current_user, get_current_team
        solved_questions = set()
        user = get_current_user()
        team = get_current_team()
        
        if user:
            partial_solves = SubQuestionPartialSolve.query.filter_by(
                challenge_id=challenge.id,
                team_id=team.id if team else None,
                user_id=user.id
            ).all()
            solved_questions = {ps.question_num for ps in partial_solves}
        
        # Format questions data
        questions = []
        for item in question_items:
            questions.append({
                'num': item.question_num,
                'text': item.question_text,
                'points': item.points,
                'flag_id': item.flag_id,
                'solved': item.question_num in solved_questions
            })
        
        data = {
            "id": challenge.id,
            "name": challenge.name,
            "value": challenge.value,
            "description": challenge.description,
            "connection_info": challenge.connection_info,
            "next_id": challenge.next_id,
            "category": challenge.category,
            "state": challenge.state,
            "max_attempts": challenge.max_attempts,
            "type": challenge.type,
            "questions": questions,
            "translations": _get_plugin_translations(),
            "type_data": {
                "id": cls.id,
                "name": cls.name,
                "templates": cls.templates,
                "scripts": cls.scripts,
            },
        }
        return data

    @classmethod
    def update(cls, challenge, request):
        """
        This method is used to update the information associated with a challenge.
        """
        data = request.form or request.get_json()
        
        for attr, value in data.items():
            # Skip fields that shouldn't be updated directly
            if attr in ("submit", "type"):
                continue
            setattr(challenge, attr, value)
        
        db.session.commit()
        return challenge

    @classmethod
    def attempt(cls, challenge, request):
        """
        This method is used to check whether a given input is right or wrong.
        """
        data = request.form or request.get_json()
        provided = data.get("submission", "").strip()
        question_num = data.get("question_num")

        # Immediately reject requests without question_num to prevent duplicate submissions
        if not question_num:
            return False, gettext("Multi-question challenges must be submitted via the question selection interface")

        try:
            question_num = int(question_num)
        except (ValueError, TypeError):
            return False, gettext("Invalid question number")

        # Get the specific question item
        question_item = SubQuestionItem.query.filter_by(
            challenge_id=challenge.id,
            question_num=question_num
        ).first()

        if not question_item:
            return False, gettext("Question %(num)s does not exist") % {"num": question_num}

        # Get the flag for this specific question
        flag = Flags.query.filter_by(id=question_item.flag_id).first()

        if not flag:
            return False, gettext("This question has no flag set")
        
        # Check if the provided answer matches this question's flag
        flag_class = get_flag_class(flag.type)
        if flag_class.compare(flag, provided):
            # Record partial solve but don't mark challenge as complete yet
            from CTFd.utils.user import get_current_user, get_current_team
            user = get_current_user()
            team = get_current_team()
            
            # Check if this question was already solved
            existing_partial = SubQuestionPartialSolve.query.filter_by(
                challenge_id=challenge.id,
                team_id=team.id if team else None,
                user_id=user.id,
                question_num=question_num
            ).first()
            
            if not existing_partial:
                # Record this partial solve
                from CTFd.utils.user import get_ip
                partial_solve = SubQuestionPartialSolve(
                    challenge_id=challenge.id,
                    team_id=team.id if team else None,
                    user_id=user.id,
                    question_num=question_num,
                    ip=get_ip(request),
                    provided=provided
                )
                db.session.add(partial_solve)
                db.session.commit()
            
            # Check if all questions are now solved
            total_questions = SubQuestionItem.query.filter_by(challenge_id=challenge.id).count()
            solved_questions = SubQuestionPartialSolve.query.filter_by(
                challenge_id=challenge.id,
                team_id=team.id if team else None,
                user_id=user.id
            ).count()
            
            if solved_questions >= total_questions:
                return True, gettext(
                    "Congratulations! You have completed all %(total)s questions!"
                ) % {"total": total_questions}
            else:
                return "partial", gettext(
                    "Question %(num)s correct! %(solved)s/%(total)s questions completed"
                ) % {
                    "num": question_num,
                    "solved": solved_questions,
                    "total": total_questions,
                }

        return False, gettext("Question %(num)s is incorrect") % {"num": question_num}

    @classmethod
    def solve(cls, user, team, challenge, request):
        """
        This method is used to insert Solves into the database.
        Only create solve record if ALL questions are completed.
        """
        # Double-check that all questions are indeed solved
        total_questions = SubQuestionItem.query.filter_by(challenge_id=challenge.id).count()
        solved_questions = SubQuestionPartialSolve.query.filter_by(
            challenge_id=challenge.id,
            team_id=team.id if team else None,
            user_id=user.id
        ).count()
        
        if solved_questions >= total_questions:
            # All questions solved, proceed with normal solve
            super().solve(user, team, challenge, request)

    @classmethod
    def delete(cls, challenge):
        """
        This method is used to delete the information associated with a challenge.
        """
        # Delete all question items first
        SubQuestionItem.query.filter_by(challenge_id=challenge.id).delete()
        
        # Delete partial solves
        SubQuestionPartialSolve.query.filter_by(challenge_id=challenge.id).delete()
        
        # Delete the challenge itself
        Challenges.query.filter_by(id=challenge.id).delete()
        
        # Delete solves for the parent challenge
        Solves.query.filter_by(challenge_id=challenge.id).delete()

        db.session.commit()

    @classmethod
    def fail(cls, user, team, challenge, request):
        """
        This method is used to insert wrong submissions into the database.
        """
        pass


@SubQuestionChallengeType.blueprint.route("/plugins/subquestionchallenge/i18n.js")
def plugin_i18n_js():
    """
    Server-rendered JavaScript that injects Flask-Babel translated strings
    into CTFd.translations. This avoids client-side async translation loading
    (which caused UI flicker) and makes translations available immediately
    on page load for both admin and user-facing pages.

    Also patches the admin challenge-type card label on /admin/challenges/new,
    where CTFd core renders the raw type id ("subquestionchallenge") instead
    of a human-readable name.
    """
    translations = _get_plugin_translations()
    translations_json = json.dumps(translations, ensure_ascii=False)
    js = f"""(function() {{
    if (typeof window.CTFd === 'undefined') window.CTFd = {{}};
    if (typeof CTFd.translations === 'undefined') CTFd.translations = {{}};
    Object.assign(CTFd.translations, {translations_json});

    function patchTypeLabel() {{
        if (!window.location.pathname.endsWith('/admin/challenges/new')) return;
        var labels = document.querySelectorAll('#create-chals-select .form-check-label');
        labels.forEach(function(el) {{
            var text = (el.textContent || '').trim();
            if (text === 'subquestionchallenge') {{
                var translated = CTFd.translations['Multi Question Challenge'];
                if (translated && typeof translated === 'string') {{
                    el.textContent = translated;
                }}
            }}
        }});
    }}

    if (document.readyState === 'loading') {{
        document.addEventListener('DOMContentLoaded', patchTypeLabel);
    }} else {{
        patchTypeLabel();
    }}

    // CTFd core renders the type list asynchronously, so observe DOM mutations
    var observer = new MutationObserver(function() {{ patchTypeLabel(); }});
    if (document.body) {{
        observer.observe(document.body, {{ childList: true, subtree: true }});
        setTimeout(function() {{ observer.disconnect(); }}, 10000);
    }}
}})();
"""
    return Response(js, mimetype="application/javascript")


def load(app):
    # Register plugin translations directory for Flask-Babel
    plugin_translations = os.path.join(os.path.dirname(__file__), "translations")
    current = app.config.get("BABEL_TRANSLATION_DIRECTORIES", "translations")
    if plugin_translations not in current:
        app.config["BABEL_TRANSLATION_DIRECTORIES"] = f"{current};{plugin_translations}"

    upgrade(plugin_name="subquestionchallenge")
    app.register_blueprint(SubQuestionChallengeType.blueprint)
    CHALLENGE_CLASSES["subquestionchallenge"] = SubQuestionChallengeType
    register_plugin_assets_directory(
        app, base_path="/plugins/subquestionchallenge/assets/"
    )
    # Server-rendered i18n script: injects Flask-Babel translated strings
    # into CTFd.translations and patches the admin challenge-type card label.
    # Loaded on every admin page so translations are available immediately
    # (no async fetch, no UI flicker).
    register_admin_plugin_script("/plugins/subquestionchallenge/i18n.js")
    # Also register for user-facing pages so CTFd.translations is populated
    # for any plugin scripts that run on the challenge view.
    register_plugin_script("/plugins/subquestionchallenge/i18n.js")