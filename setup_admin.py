#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""设置管理员账号"""
import sys
sys.path.insert(0, '/workspace')

from CTFd import create_app
from CTFd.models import Users, Admins, db

app = create_app()

with app.app_context():
    # 检查是否已存在root用户
    admin = Users.query.filter_by(name="root").first()
    
    if not admin:
        print("创建管理员账号...")
        admin = Users(
            name="root",
            email="root@ctfd.local",
            type="admin",
            verified=True
        )
        admin.password = "root"
        db.session.add(admin)
        db.session.commit()
        print("管理员账号创建成功！")
    else:
        print("管理员账号已存在")
        # 确保密码是root
        admin.password = "root"
        db.session.commit()
        print("管理员密码已更新")
    
    print(f"管理员账号: root")
    print(f"管理员密码: root")
    print(f"管理员邮箱: {admin.email}")
    print(f"管理员类型: {admin.type}")