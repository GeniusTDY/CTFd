"""Setup CTFd with admin user and configure for zh_CN."""
import sys
sys.path.insert(0, '/workspace')
from CTFd import create_app
from CTFd.models import db, Users
from CTFd.utils import set_config
from CTFd.utils.crypto import hash_password
from CTFd.cache import cache
from CTFd.utils import get_config

app = create_app()

with app.app_context():
    # Check if already set up
    setup_completed = get_config('setup_complete')
    print(f'Setup completed: {setup_completed}')

    if not setup_completed:
        # Create admin user
        admin = Users(
            name='admin',
            email='admin@example.com',
            password='admin123',  # @validates will hash it
            type='admin',
            verified=True,
            hidden=False,
            banned=False,
        )
        db.session.add(admin)
        db.session.commit()
        print(f'Created admin user: {admin.name} (id={admin.id})')

        # Mark setup as complete
        set_config('setup_complete', True)
        set_config('mailfrom_addr', 'noreply@example.com')
        set_config('user_mode', 'users')
        db.session.commit()
        print('Setup marked as complete')

    # Set default language to zh_CN for admin
    admin = Users.query.filter_by(name='admin').first()
    if admin:
        admin.language = 'zh_CN'
        db.session.commit()
        print(f'Admin language set to: {admin.language}')

    # Set default language for new users
    set_config('default_locale', 'zh_CN')
    db.session.commit()

    # Clear cache
    cache.clear()

    # Enable remote_desktop_enabled in plugin settings using direct DB
    import sqlite3
    db_path = '/workspace/CTFd/ctfd.db'
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    # Check if remote_desktop_enabled exists
    cur.execute("SELECT value FROM desktop_settings WHERE key='remote_desktop_enabled'")
    row = cur.fetchone()
    if row:
        print(f'remote_desktop_enabled (before): {row[0]}')
        cur.execute("UPDATE desktop_settings SET value='True' WHERE key='remote_desktop_enabled'")
    else:
        cur.execute("INSERT INTO desktop_settings (key, value) VALUES ('remote_desktop_enabled', 'True')")
    conn.commit()
    cur.execute("SELECT value FROM desktop_settings WHERE key='remote_desktop_enabled'")
    row = cur.fetchone()
    print(f'remote_desktop_enabled (after): {row[0] if row else "NOT SET"}')
    conn.close()

    # Verify setup
    admin = Users.query.filter_by(name='admin').first()
    print(f'\nFinal admin: name={admin.name}, type={admin.type}, language={admin.language}')
    print(f'Password verify: {admin.verify_password("admin123")}')
    print('Setup complete!')
