#!/usr/bin/env python3
"""生成CTFd测试数据脚本"""
from CTFd import create_app
from CTFd.models import (
    db, Users, Teams, Challenges, Solves, Awards, Fails,
    Flags, Tags, Hints
)
from CTFd.utils import set_config
import random
from datetime import datetime, timedelta

def create_test_data():
    app = create_app()
    
    with app.app_context():
        # 检查管理员账号
        admin = Users.query.filter_by(name='root').first()
        if not admin:
            # 创建管理员账号 - 使用type='admin'
            admin = Users(
                name='root',
                email='root@ctfd.local',
                password='root',  # 密码会自动哈希
                type='admin',
                verified=True,
                hidden=False,
                banned=False
            )
            db.session.add(admin)
            print("创建管理员账号: root / root")
        else:
            # 更新管理员密码
            admin.password = 'root'
            print("管理员账号已存在，已更新密码")
        
        db.session.commit()
        
        # 获取admin用户ID
        admin = Users.query.filter_by(name='root').first()
        admin_id = admin.id
        
        # 创建用户
        users_data = [
            ('alice', 'alice@test.com', 'Alice'),
            ('bob', 'bob@test.com', 'Bob'),
            ('charlie', 'charlie@test.com', 'Charlie'),
            ('david', 'david@test.com', 'David'),
            ('emma', 'emma@test.com', 'Emma'),
        ]
        
        created_users = []
        for name, email, display_name in users_data:
            user = Users.query.filter_by(name=name).first()
            if not user:
                user = Users(
                    name=name,
                    email=email,
                    password='password123',  # 密码会自动哈希
                    type='user',
                    verified=True,
                    hidden=False,
                    banned=False
                )
                db.session.add(user)
                db.session.commit()
                created_users.append(user)
                print(f"创建用户: {name}")
            else:
                created_users.append(user)
                print(f"用户已存在: {name}")
        
        # 创建队伍
        teams_data = [
            ('Alpha_Team', 'Alpha Team - The First'),
            ('Beta_Squad', 'Beta Squad - The Second'),
            ('Cyber_Warriors', 'Cyber Warriors - Elite Hackers'),
        ]
        
        created_teams = []
        for name, description in teams_data:
            team = Teams.query.filter_by(name=name).first()
            if not team:
                team = Teams(
                    name=name,
                    password='team123',  # 密码会自动哈希
                    banned=False,
                    hidden=False
                )
                db.session.add(team)
                db.session.commit()
                created_teams.append(team)
                print(f"创建队伍: {name}")
            else:
                created_teams.append(team)
                print(f"队伍已存在: {name}")
        
        # 将用户分配到队伍
        if len(created_teams) >= 2 and len(created_users) >= 5:
            # Team 0: alice, bob
            team0_members = [created_users[0], created_users[1]]
            # Team 1: charlie, david
            team1_members = [created_users[2], created_users[3]]
            # Team 2: emma (单人)
            team2_members = [created_users[4]]
            
            for user in team0_members:
                if user.team_id is None:
                    user.team_id = created_teams[0].id
            for user in team1_members:
                if user.team_id is None:
                    user.team_id = created_teams[1].id
            for user in team2_members:
                if user.team_id is None:
                    user.team_id = created_teams[2].id
            
            db.session.commit()
            print("用户已分配到队伍")
        
        # 创建挑战题
        challenges_data = [
            ('Web入门1', '这是一个简单的Web题目', 'web', 100, 'flag{web_easy_1}'),
            ('Web入门2', '这是一个中等难度的Web题目', 'web', 200, 'flag{web_medium_2}'),
            ('Crypto基础', '密码学入门题目', 'crypto', 100, 'flag{crypto_basic}'),
            ('Crypto进阶', '密码学进阶题目', 'crypto', 300, 'flag{crypto_advanced}'),
            ('Pwn入门', '二进制漏洞基础题目', 'pwn', 150, 'flag{pwn_intro}'),
            ('Pwn挑战', '二进制漏洞进阶题目', 'pwn', 400, 'flag{pwn_challenge}'),
            ('Reverse Easy', '逆向工程入门', 'reverse', 100, 'flag{reverse_easy}'),
            ('Misc杂项', '杂项题目', 'misc', 50, 'flag{misc_fun}'),
            ('Web大师', 'Web高级挑战', 'web', 500, 'flag{web_master}'),
            ('算法思维', '算法编程题', 'misc', 200, 'flag{algorithm_fun}'),
        ]
        
        created_challenges = []
        for name, description, category, value, flag_content in challenges_data:
            challenge = Challenges.query.filter_by(name=name).first()
            if not challenge:
                challenge = Challenges(
                    name=name,
                    description=description,
                    value=value,
                    category=category,
                    state='visible',
                    type='standard'
                )
                db.session.add(challenge)
                db.session.commit()
                
                # 为题目添加flag
                flag = Flags(
                    challenge_id=challenge.id,
                    type='static',
                    content=flag_content,
                    data=''
                )
                db.session.add(flag)
                db.session.commit()
                
                created_challenges.append(challenge)
                print(f"创建题目: {name} ({category}, {value}分)")
            else:
                created_challenges.append(challenge)
                print(f"题目已存在: {name}")
        
        # 创建解题记录
        base_time = datetime.utcnow() - timedelta(days=7)
        
        # 在队伍模式下，每道题每个队伍只能解一次
        # 所以我们让不同队伍解不同的题目组合
        if len(created_teams) >= 3 and len(created_users) >= 5:
            # 为每个队伍分配不同的题目
            team_challenges = {
                created_teams[0].id: created_challenges[:6],  # Alpha Team解前6题
                created_teams[1].id: created_challenges[3:9],  # Beta Squad解中间6题
                created_teams[2].id: created_challenges[5:],   # Cyber Warriors解后5题
            }
            
            for user in created_users:
                # 获取用户所属队伍应该解的题目
                if user.team_id and user.team_id in team_challenges:
                    challenges_for_team = team_challenges[user.team_id]
                    
                    for challenge in challenges_for_team:
                        # 检查该队伍是否已经解过这道题
                        existing_solve = Solves.query.filter_by(
                            team_id=user.team_id,
                            challenge_id=challenge.id
                        ).first()
                        
                        if not existing_solve:
                            solve_time = base_time + timedelta(
                                days=random.randint(0, 6),
                                hours=random.randint(0, 23),
                                minutes=random.randint(0, 59)
                            )
                            
                            solve = Solves(
                                user_id=user.id,
                                team_id=user.team_id,
                                challenge_id=challenge.id,
                                ip='127.0.0.1',
                                provided=challenge.name + '_solved'
                            )
                            solve.date = solve_time
                            db.session.add(solve)
                            db.session.commit()
                            print(f"队伍 {user.team.name} 的用户 {user.name} 解出: {challenge.name}")
                            break  # 每道题只让一个用户解
        
        # 添加一些失败尝试记录
        for user in created_users[:3]:
            challenges = random.sample(created_challenges, min(3, len(created_challenges)))
            for challenge in challenges:
                fail = Fails(
                    user_id=user.id,
                    team_id=user.team_id,
                    challenge_id=challenge.id,
                    ip='127.0.0.1',
                    provided='wrong_flag'
                )
                fail.date = datetime.utcnow() - timedelta(
                    days=random.randint(0, 5),
                    hours=random.randint(0, 23)
                )
                db.session.add(fail)
                db.session.commit()
                print(f"用户 {user.name} 尝试解 {challenge.name} 失败")
        
        # 添加一些奖项/加分
        awards_data = [
            ('First Blood - Web入门1', 50),
            ('Best Team Spirit', 30),
            ('Early Bird', 20),
        ]
        
        for name, value in awards_data:
            award = Awards(
                user_id=random.choice(created_users).id,
                team_id=random.choice(created_teams).id,
                name=name,
                value=value
            )
            award.date = datetime.utcnow() - timedelta(days=random.randint(0, 3))
            db.session.add(award)
            db.session.commit()
            print(f"添加奖项: {name} (+{value}分)")
        
        # 设置一些配置
        set_config('ctf_name', 'CTFd 测试平台')
        set_config('ctf_description', '这是一个用于测试的CTF平台')
        set_config('user_mode', 'teams')  # 团队模式
        
        db.session.commit()
        
        print("\n" + "="*50)
        print("测试数据创建完成！")
        print("="*50)
        print(f"用户数: {Users.query.count()}")
        print(f"队伍数: {Teams.query.count()}")
        print(f"题目数: {Challenges.query.count()}")
        print(f"解题数: {Solves.query.count()}")
        print(f"失败尝试: {Fails.query.count()}")
        print(f"奖项数: {Awards.query.count()}")
        print("="*50)
        print("\n登录信息:")
        print("管理员: root / root")
        print("用户密码: password123")
        print("队伍密码: team123")

if __name__ == '__main__':
    create_test_data()