#!/usr/bin/env python3
"""
演示数据生成脚本 - 多任务打卡版
为测试账号(2024001)预存打卡记录
"""
import os
import sys
import random
from datetime import datetime, timedelta, date

sys.path.insert(0, os.path.dirname(__file__))

from app import app
from models import db, User, DailyCheckIn
from services.reward_service import get_reward_service

TEST_STUDENT_ID = "2024001"

def create_checkin_data():
    """创建多任务打卡演示数据"""
    with app.app_context():
        user = User.query.filter_by(student_id=TEST_STUDENT_ID).first()
        if not user:
            print(f"测试用户不存在，请先运行 seed_demo_data.py")
            return

        today = date.today()
        reward_service = get_reward_service(None)
        
        print("生成多任务打卡记录...")
        checkin_count = 0
        
        for i in range(30, 0, -1):
            checkin_date = today - timedelta(days=i)
            
            # 模拟打卡频率：约75%的天数有打卡
            if random.random() < 0.75:
                existing = DailyCheckIn.query.filter_by(
                    user_id=user.id, checkin_date=checkin_date
                ).first()
                
                if existing:
                    # 删除旧记录重新创建
                    db.session.delete(existing)
                    db.session.commit()
                
                # 生成随机打卡数据
                breakfast_done = random.random() < 0.85
                lunch_done = random.random() < 0.9
                dinner_done = random.random() < 0.8
                exercise_minutes = random.choice([0, 0, 15, 20, 30, 40, 45, 60])
                water_cups = random.randint(3, 10)
                sleep_hours = round(random.uniform(5.5, 9.0), 1)
                mood_score = random.randint(5, 10)
                
                # 计算得分
                total_score = reward_service.calculate_checkin_score(
                    breakfast_done, lunch_done, dinner_done,
                    exercise_minutes, water_cups, sleep_hours, mood_score
                )
                
                checkin = DailyCheckIn(
                    user_id=user.id,
                    checkin_date=checkin_date,
                    breakfast_done=breakfast_done,
                    lunch_done=lunch_done,
                    dinner_done=dinner_done,
                    exercise_minutes=exercise_minutes,
                    water_cups=water_cups,
                    sleep_hours=sleep_hours,
                    mood_score=mood_score,
                    total_score=total_score
                )
                db.session.add(checkin)
                checkin_count += 1
        
        # 今天的打卡记录
        existing_today = DailyCheckIn.query.filter_by(
            user_id=user.id, checkin_date=today
        ).first()
        if existing_today:
            db.session.delete(existing_today)
            db.session.commit()
        
        # 今天完成大部分任务
        today_checkin = DailyCheckIn(
            user_id=user.id,
            checkin_date=today,
            breakfast_done=True,
            lunch_done=True,
            dinner_done=False,
            exercise_minutes=35,
            water_cups=7,
            sleep_hours=7.5,
            mood_score=8,
            total_score=0  # 稍后计算
        )
        today_checkin.total_score = reward_service.calculate_checkin_score(
            today_checkin.breakfast_done, today_checkin.lunch_done, today_checkin.dinner_done,
            today_checkin.exercise_minutes, today_checkin.water_cups,
            today_checkin.sleep_hours, today_checkin.mood_score
        )
        db.session.add(today_checkin)
        checkin_count += 1
        
        # 更新用户打卡统计
        user.last_checkin_date = today
        user.checkin_streak = 5
        
        db.session.commit()
        
        print(f"\n===== 多任务打卡数据生成完成 =====")
        print(f"测试账号: {TEST_STUDENT_ID}")
        print(f"打卡记录: {checkin_count} 条")
        print(f"今日得分: {today_checkin.total_score} 分")
        print(f"连续打卡: 5 天")

if __name__ == "__main__":
    create_checkin_data()
