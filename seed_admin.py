#!/usr/bin/env python3
"""
Standalone bootstrap script: takes CTFd out of /setup mode and creates an
administrator account + an index page. Does NOT modify any CTFd core files —
it only uses CTFd's public app context, models and helpers.

Run after `python3.11 serve.py` has created the SQLite DB at least once.
"""
from CTFd import create_app
from CTFd.cache import clear_config, clear_pages
from CTFd.models import Admins, Pages, db
from CTFd.utils import set_config

ADMIN_NAME = "admin"
ADMIN_EMAIL = "admin@ctfd.local"
ADMIN_PASSWORD = "Admin@123456"
CTF_NAME = "CTFd i18n Preview"

app = create_app()

with app.app_context():
    # Mark setup complete + minimal config (mirrors official /setup POST flow)
    set_config("ctf_name", CTF_NAME)
    set_config("ctf_description", "i18n/zh-cn-setup-translation branch preview deployment")
    set_config("user_mode", "teams")
    set_config("challenge_visibility", "private")
    set_config("registration_visibility", "public")
    set_config("score_visibility", "public")
    set_config("account_visibility", "public")
    set_config("verify_emails", "False")
    set_config("social_shares", "False")
    set_config("team_size", 0)
    set_config("mail_server", None)
    set_config("mail_port", None)
    set_config("mail_tls", None)
    set_config("mail_ssl", None)
    set_config("mail_username", None)
    set_config("mail_password", None)
    set_config("mail_useauth", None)
    set_config("start", None)
    set_config("end", None)
    set_config("freeze", None)
    set_config("setup", True)

    # Admin account (Admins.password @validates auto-hashes plaintext)
    existing = Admins.query.filter_by(email=ADMIN_EMAIL).first()
    if existing is None:
        admin = Admins(
            name=ADMIN_NAME,
            email=ADMIN_EMAIL,
            password=ADMIN_PASSWORD,  # model auto-hashes via @validates
            type="admin",
            hidden=True,
        )
        db.session.add(admin)
        db.session.commit()
        print(f"[+] Created admin: {ADMIN_NAME} <{ADMIN_EMAIL}> / {ADMIN_PASSWORD}")
    else:
        # Fix the double-hashed password from the earlier run
        existing.password = ADMIN_PASSWORD
        db.session.commit()
        print(f"[=] Admin already exists; password reset: {ADMIN_EMAIL}")

    # Index page so the home page renders
    page = Pages.query.filter_by(route="index").first()
    if page is None:
        page = Pages(title=CTF_NAME, route="index", content="", draft=False)
        db.session.add(page)
        db.session.commit()
        print("[+] Created index page")
    else:
        print("[=] Index page already exists")

    clear_config()
    clear_pages()
    print("[OK] Setup complete — CTFd is now out of /setup mode")
