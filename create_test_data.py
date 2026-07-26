#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""创建测试数据用于展示统计信息"""
import sys
import os
sys.path.insert(0, '/workspace')

from CTFd import create_app
from CTFd.models import Challenges, Flags, Solves, Users, db
from CTFd.utils.user import get_current_user
import random
from datetime import datetime, timedelta

app = create_app()

with app.app_context():
    # 检查是否已经存在挑战
    challenges_count = Challenges.query.count()
    
    if challenges_count == 0:
        print("创建测试挑战...")
        # 创建几个挑战
        test_challenges = [
            {"name": "Web 初级挑战", "category": "Web", "value": 100, "description": "这是一个简单的Web挑战"},
            {"name": "Crypto 基础", "category": "Crypto", "value": 150, "description": "密码学入门题目"},
            {"name": "PWN 入门", "category": "PWN", "value": 200, "description": "二进制漏洞基础"},
            {"name": "Reverse 基础", "category": "Reverse", "value": 250, "description": "逆向工程入门"},
            {"name": "Misc 趣味题", "category": "Misc", "value": 50, "description": "杂项题目"},
        ]
        
        for idx, chal_data in enumerate(test_challenges):
            challenge = Challenges(
                name=chal_data["name"],
                category=chal_data["category"],
                value=chal_data["value"],
                description=chal_data["description"],
                state="visible"
            )
            db.session.add(challenge)
            db.session.flush()
            
            # 为每个挑战创建flag
            flag = Flags(
                challenge_id=challenge.id,
                type="static",
                content=f"flag{{test_{idx + 1}}}",
                data="case_insensitive"
            )
            db.session.add(flag)
        
        db.session.commit()
        print(f"已创建 {len(test_challenges)} 个挑战")
    else:
        print(f"已存在 {challenges_count} 个挑战")
    
    # 检查普通用户数量
    users_count = Users.query.filter_by(type="user", banned=False, hidden=False).count()
    
    if users_count < 10:
        print("创建测试用户...")
        # 创建一些测试用户
        test_users = [
            "alice", "bob", "charlie", "david", "eve",
            "frank", "grace", "henry", "ivan", "julia"
        ]
        
        for username in test_users:
            # 检查用户是否已存在
            if not Users.query.filter_by(name=username).first():
                user = Users(
                    name=username,
                    email=f"{username}@test.com",
                    type="user",
                    verified=True
                )
                user.password = "password123"
                db.session.add(user)
        
        db.session.commit()
        print(f"已创建 {len(test_users)} 个测试用户")
    
    # 检查解题记录数量
    solves_count = Solves.query.count()
    
    if solves_count == 0:
        print("创建解题记录...")
        # 获取所有挑战和用户
        challenges = Challenges.query.filter_by(state="visible").all()
        users = Users.query.filter_by(type="user", banned=False, hidden=False).all()
        
        if challenges and users:
            # 为每个用户随机解决几个挑战
            for user in users:
                # 每个用户随机解决2-4个挑战
                num_solves = random.randint(2, min(4, len(challenges)))
                solved_challenges = random.sample(challenges, num_solves)
                
                for challenge in solved_challenges:
                    # 随机生成提交时间（过去7天内）
                    days_ago = random.randint(0, 7)
                    hours_ago = random.randint(0, 23)
                    solve_time = datetime.now() - timedelta(days=days_ago, hours=hours_ago)
                    
                    solve = Solves(
                        user_id=user.id,
                        challenge_id=challenge.id,
                        ip="127.0.0.1",
                        provided=f"flag{{test_{challenge.id}}}"
                    )
                    solve.date = solve_time
                    db.session.add(solve)
            
            db.session.commit()
            print(f"已创建解题记录")
    
    # 统计信息
    total_challenges = Challenges.query.filter_by(state="visible").count()
    total_users = Users.query.filter_by(type="user", banned=False, hidden=False).count()
    total_solves = Solves.query.count()
    
    print("\n=== 统计信息 ===")
    print(f"总挑战数: {total_challenges}")
    print(f"总用户数: {total_users}")
    print(f"总解题数: {total_solves}")
    print("\n测试数据创建完成！")