#!/usr/bin/env python3
"""
演示数据生成脚本
为测试账号(2024001)预存打卡记录和饮食记录，便于展示效果
"""
import os
import sys
import random
from datetime import datetime, timedelta, date

sys.path.insert(0, os.path.dirname(__file__))

from app import app
from models import db, User, DailyCheckIn, DietLog, DailyDietSummary

# 测试账号学号
TEST_STUDENT_ID = "2024001"

# 常见食物数据 (名称, 热量, 蛋白质, 脂肪, 碳水)
FOODS = {
    "breakfast": [
        ("白米粥", 46, 1.1, 0.1, 10.2),
        ("小米粥", 46, 1.4, 0.7, 8.4),
        ("豆浆", 31, 2.9, 1.6, 1.2),
        ("油条", 386, 6.9, 17.6, 51.0),
        ("包子(肉)", 226, 7.8, 8.5, 29.2),
        ("包子(素)", 198, 6.2, 5.8, 28.6),
        ("鸡蛋", 144, 13.3, 8.8, 2.8),
        ("牛奶", 54, 3.0, 3.2, 3.4),
        ("馒头", 221, 7.0, 1.1, 44.2),
        ("煎饼果子", 235, 8.5, 9.2, 28.8),
        ("茶叶蛋", 144, 13.3, 8.8, 2.8),
        ("八宝粥", 62, 2.1, 0.8, 11.5),
    ],
    "lunch": [
        ("米饭", 116, 2.6, 0.3, 25.9),
        ("红烧肉", 435, 18.5, 38.2, 5.6),
        ("番茄炒蛋", 98, 4.2, 6.5, 6.8),
        ("清炒白菜", 23, 1.2, 0.2, 4.2),
        ("宫保鸡丁", 162, 12.5, 9.8, 7.2),
        ("鱼香肉丝", 145, 8.2, 9.5, 8.6),
        ("麻婆豆腐", 125, 8.5, 8.2, 4.8),
        ("炒青菜", 28, 1.5, 0.3, 5.2),
        ("糖醋排骨", 245, 12.8, 15.2, 16.5),
        ("可乐鸡翅", 195, 11.2, 9.8, 15.6),
        ("蛋花汤", 18, 1.2, 0.8, 1.5),
        ("紫菜汤", 12, 0.8, 0.2, 1.8),
    ],
    "dinner": [
        ("米饭", 116, 2.6, 0.3, 25.9),
        ("清蒸鱼", 105, 18.5, 3.2, 0.8),
        ("炒时蔬", 35, 1.8, 0.5, 6.2),
        ("红烧豆腐", 128, 8.2, 8.5, 5.2),
        ("青椒肉丝", 135, 9.5, 8.8, 6.5),
        ("蒜蓉西兰花", 34, 2.8, 0.4, 5.8),
        ("酸辣汤", 45, 2.5, 1.8, 4.8),
        ("凉拌黄瓜", 22, 0.8, 0.2, 4.5),
        ("饺子", 215, 8.2, 6.5, 28.2),
        ("面条", 142, 5.2, 3.8, 20.8),
    ],
    "snack": [
        ("苹果", 52, 0.2, 0.2, 13.5),
        ("香蕉", 89, 1.1, 0.3, 22.8),
        ("橙子", 47, 0.9, 0.1, 11.8),
        ("酸奶", 72, 3.5, 2.7, 9.3),
        ("坚果(30g)", 175, 5.2, 15.8, 6.2),
        ("饼干", 465, 7.5, 18.2, 68.5),
        ("蛋糕", 348, 7.2, 15.5, 46.8),
        ("薯片", 536, 7.0, 34.6, 50.8),
        ("巧克力", 550, 5.0, 32.0, 58.0),
        ("葡萄", 43, 0.5, 0.2, 10.3),
        ("西瓜", 30, 0.6, 0.1, 7.5),
        ("梨", 50, 0.4, 0.1, 13.0),
    ],
}

def create_demo_data():
    """创建演示数据"""
    with app.app_context():
        # 获取或创建测试用户
        user = User.query.filter_by(student_id=TEST_STUDENT_ID).first()
        if not user:
            user = User(
                student_id=TEST_STUDENT_ID,
                username="演示用户",
                password_hash="demo"
            )
            db.session.add(user)
            db.session.commit()
            print(f"已创建测试用户: {TEST_STUDENT_ID}")
        else:
            print(f"测试用户已存在: {TEST_STUDENT_ID}")

        today = date.today()
        
        # ============ 生成30天的打卡记录 ============
        print("生成打卡记录...")
        checkin_count = 0
        streak = 0
        
        for i in range(30, 0, -1):
            checkin_date = today - timedelta(days=i)
            
            # 模拟打卡频率：约70%的天数有打卡
            if random.random() < 0.7:
                existing = DailyCheckIn.query.filter_by(
                    user_id=user.id, checkin_date=checkin_date
                ).first()
                
                if not existing:
                    checkin = DailyCheckIn(
                        user_id=user.id,
                        checkin_date=checkin_date,
                        mood_score=random.randint(5, 9),
                        sleep_hours=round(random.uniform(5.5, 8.5), 1),
                        exercise_minutes=random.randint(0, 60),
                        water_cups=random.randint(4, 10),
                        notes=random.choice(["状态不错", "有点累", "睡眠不好", "精神很好", ""])
                    )
                    db.session.add(checkin)
                    checkin_count += 1
        
        # 今天也打卡
        today_checkin = DailyCheckIn.query.filter_by(
            user_id=user.id, checkin_date=today
        ).first()
        if not today_checkin:
            checkin = DailyCheckIn(
                user_id=user.id,
                checkin_date=today,
                mood_score=8,
                sleep_hours=7.5,
                exercise_minutes=30,
                water_cups=8,
                notes="今天状态很好"
            )
            db.session.add(checkin)
            checkin_count += 1
        
        # 更新用户打卡统计
        user.last_checkin_date = today
        user.checkin_streak = 5  # 模拟连续5天打卡
        
        db.session.commit()
        print(f"已创建 {checkin_count} 条打卡记录")

        # ============ 生成7天的饮食记录 ============
        print("生成饮食记录...")
        diet_count = 0
        
        for i in range(7, 0, -1):
            log_date = today - timedelta(days=i)
            
            # 早餐
            breakfast_foods = random.sample(FOODS["breakfast"], random.randint(1, 3))
            for food_name, cal, protein, fat, carbs in breakfast_foods:
                serving = random.choice([100, 150, 200, 250])
                ratio = serving / 100
                log = DietLog(
                    user_id=user.id,
                    log_date=log_date,
                    log_time=datetime(log_date.year, log_date.month, log_date.day, 
                                     random.randint(7, 9), random.randint(0, 59)),
                    meal_type="breakfast",
                    food_name=food_name,
                    serving_size=serving,
                    serving_count=1,
                    calories=round(cal * ratio, 1),
                    protein=round(protein * ratio, 1),
                    fat=round(fat * ratio, 1),
                    carbs=round(carbs * ratio, 1),
                    is_late_night=False
                )
                db.session.add(log)
                diet_count += 1
            
            # 午餐
            lunch_foods = random.sample(FOODS["lunch"], random.randint(2, 4))
            for food_name, cal, protein, fat, carbs in lunch_foods:
                serving = random.choice([100, 150, 200, 250, 300])
                ratio = serving / 100
                log = DietLog(
                    user_id=user.id,
                    log_date=log_date,
                    log_time=datetime(log_date.year, log_date.month, log_date.day,
                                     random.randint(11, 13), random.randint(0, 59)),
                    meal_type="lunch",
                    food_name=food_name,
                    serving_size=serving,
                    serving_count=1,
                    calories=round(cal * ratio, 1),
                    protein=round(protein * ratio, 1),
                    fat=round(fat * ratio, 1),
                    carbs=round(carbs * ratio, 1),
                    is_late_night=False
                )
                db.session.add(log)
                diet_count += 1
            
            # 晚餐
            dinner_foods = random.sample(FOODS["dinner"], random.randint(2, 4))
            for food_name, cal, protein, fat, carbs in dinner_foods:
                serving = random.choice([100, 150, 200, 250])
                ratio = serving / 100
                log = DietLog(
                    user_id=user.id,
                    log_date=log_date,
                    log_time=datetime(log_date.year, log_date.month, log_date.day,
                                     random.randint(17, 19), random.randint(0, 59)),
                    meal_type="dinner",
                    food_name=food_name,
                    serving_size=serving,
                    serving_count=1,
                    calories=round(cal * ratio, 1),
                    protein=round(protein * ratio, 1),
                    fat=round(fat * ratio, 1),
                    carbs=round(carbs * ratio, 1),
                    is_late_night=False
                )
                db.session.add(log)
                diet_count += 1
            
            # 加餐/零食（50%概率）
            if random.random() < 0.5:
                snack_foods = random.sample(FOODS["snack"], random.randint(1, 2))
                for food_name, cal, protein, fat, carbs in snack_foods:
                    serving = random.choice([50, 100, 150])
                    ratio = serving / 100
                    hour = random.choice([10, 15, 16, 20, 21, 22])
                    is_late = hour >= 21
                    log = DietLog(
                        user_id=user.id,
                        log_date=log_date,
                        log_time=datetime(log_date.year, log_date.month, log_date.day,
                                         hour, random.randint(0, 59)),
                        meal_type="snack",
                        food_name=food_name,
                        serving_size=serving,
                        serving_count=1,
                        calories=round(cal * ratio, 1),
                        protein=round(protein * ratio, 1),
                        fat=round(fat * ratio, 1),
                        carbs=round(carbs * ratio, 1),
                        is_late_night=is_late
                    )
                    db.session.add(log)
                    diet_count += 1

        # 今天的饮食记录（更丰富一些）
        today_foods_breakfast = [("牛奶", 54, 3.0, 3.2, 3.4), ("鸡蛋", 144, 13.3, 8.8, 2.8), ("馒头", 221, 7.0, 1.1, 44.2)]
        for food_name, cal, protein, fat, carbs in today_foods_breakfast:
            log = DietLog(
                user_id=user.id,
                log_date=today,
                log_time=datetime(today.year, today.month, today.day, 8, 15),
                meal_type="breakfast",
                food_name=food_name,
                serving_size=150,
                serving_count=1,
                calories=cal,
                protein=protein,
                fat=fat,
                carbs=carbs,
                is_late_night=False
            )
            db.session.add(log)
            diet_count += 1

        today_foods_lunch = [("米饭", 116, 2.6, 0.3, 25.9), ("番茄炒蛋", 98, 4.2, 6.5, 6.8), ("清炒白菜", 23, 1.2, 0.2, 4.2)]
        for food_name, cal, protein, fat, carbs in today_foods_lunch:
            serving = 200
            ratio = serving / 100
            log = DietLog(
                user_id=user.id,
                log_date=today,
                log_time=datetime(today.year, today.month, today.day, 12, 30),
                meal_type="lunch",
                food_name=food_name,
                serving_size=serving,
                serving_count=1,
                calories=round(cal * ratio, 1),
                protein=round(protein * ratio, 1),
                fat=round(fat * ratio, 1),
                carbs=round(carbs * ratio, 1),
                is_late_night=False
            )
            db.session.add(log)
            diet_count += 1

        today_foods_dinner = [("米饭", 116, 2.6, 0.3, 25.9), ("清蒸鱼", 105, 18.5, 3.2, 0.8), ("炒青菜", 28, 1.5, 0.3, 5.2)]
        for food_name, cal, protein, fat, carbs in today_foods_dinner:
            serving = 150
            ratio = serving / 100
            log = DietLog(
                user_id=user.id,
                log_date=today,
                log_time=datetime(today.year, today.month, today.day, 18, 30),
                meal_type="dinner",
                food_name=food_name,
                serving_size=serving,
                serving_count=1,
                calories=round(cal * ratio, 1),
                protein=round(protein * ratio, 1),
                fat=round(fat * ratio, 1),
                carbs=round(carbs * ratio, 1),
                is_late_night=False
            )
            db.session.add(log)
            diet_count += 1

        db.session.commit()
        print(f"已创建 {diet_count} 条饮食记录")

        # ============ 添加一些夜宵记录（21:00-03:00） ============
        print("添加夜宵记录...")
        night_snack_foods = [
            ("泡面", 473, 9.5, 21.2, 61.6),
            ("烧烤", 280, 18.5, 22.0, 5.8),
            ("炸鸡", 279, 17.2, 18.5, 12.6),
            ("奶茶", 180, 3.2, 5.8, 30.5),
            ("薯片", 536, 7.0, 34.6, 50.8),
            ("面包", 312, 8.5, 10.2, 48.5),
            ("水果沙拉", 85, 1.2, 0.5, 19.8),
        ]
        
        for i in range(5, 0, -1):
            night_date = today - timedelta(days=i)
            # 每隔一天加一次夜宵
            if i % 2 == 0:
                food = random.choice(night_snack_foods)
                food_name, cal, protein, fat, carbs = food
                hour = random.choice([21, 22, 23, 0, 1, 2])
                log = DietLog(
                    user_id=user.id,
                    log_date=night_date,
                    log_time=datetime(night_date.year, night_date.month, night_date.day, hour, random.randint(0, 59)),
                    meal_type="snack",
                    food_name=food_name,
                    serving_size=100,
                    serving_count=1,
                    calories=cal,
                    protein=protein,
                    fat=fat,
                    carbs=carbs,
                    is_late_night=True,
                    notes="夜宵"
                )
                db.session.add(log)
                diet_count += 1
        
        db.session.commit()
        print(f"夜宵记录已添加，总计 {diet_count} 条饮食记录")

        # ============ 更新每日汇总 ============
        print("更新每日汇总...")
        from app import _update_daily_summary
        
        for i in range(7, -1, -1):
            summary_date = today - timedelta(days=i)
            _update_daily_summary(user.id, summary_date)
        
        db.session.commit()
        print("每日汇总已更新")

        print("\n===== 演示数据生成完成 =====")
        print(f"测试账号: {TEST_STUDENT_ID}")
        print(f"打卡记录: {checkin_count} 条 (含今天)")
        print(f"饮食记录: {diet_count} 条")
        print(f"连续打卡: 5 天")
        print(f"最后打卡: {today.isoformat()}")

if __name__ == "__main__":
    create_demo_data()
