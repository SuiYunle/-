from models import (db, RewardRecord, User, DailyCheckIn, UserAchievement,
                    BMIAssessment, ConstitutionAssessment, MentalAssessment)
from datetime import datetime, timedelta, date
from typing import List, Dict

# ==================== 积分规则配置 ====================
REWARD_RULES = {
    # 原有渠道
    "login": {"points": 5, "daily_limit": 1, "description": "每日登录奖励"},
    "chat": {"points": 2, "daily_limit": 20, "description": "对话互动"},
    "constitution_test": {"points": 20, "daily_limit": 1, "description": "完成体质辨识测试"},
    "mental_test": {"points": 15, "daily_limit": 1, "description": "完成心理状态测试"},
    "bmi_analysis": {"points": 5, "daily_limit": 3, "description": "BMI健康分析"},
    # 新增渠道
    "image_upload": {"points": 3, "daily_limit": 10, "description": "上传舌象/餐食图片"},
    "daily_checkin": {"points": 3, "daily_limit": 1, "description": "每日健康打卡"},
    "read_article": {"points": 1, "daily_limit": 5, "description": "阅读健康资讯"},
    "share_result": {"points": 5, "daily_limit": 3, "description": "分享测评结果"},
    "complete_profile": {"points": 10, "daily_limit": 1, "description": "完善个人资料"},
    "set_privacy": {"points": 5, "daily_limit": 1, "description": "设置隐私偏好"},
    "weekly_streak_3": {"points": 15, "daily_limit": 1, "description": "连续打卡3天"},
    "weekly_streak_7": {"points": 30, "daily_limit": 1, "description": "连续打卡7天"},
    "all_assessments": {"points": 50, "daily_limit": 1, "description": "完成全部三项测评"},
    "first_bmi": {"points": 10, "daily_limit": 1, "description": "首次BMI分析"},
    "first_constitution": {"points": 10, "daily_limit": 1, "description": "首次体质辨识"},
    "first_mental": {"points": 10, "daily_limit": 1, "description": "首次心理测评"},
}

# ==================== 成就系统 ====================
ACHIEVEMENTS = {
    "health_newbie": {"name": "健康新手", "icon": "fa-seedling", "color": "#10b981", "description": "完成首次健康测评"},
    "full_assessment": {"name": "全面评估", "icon": "fa-clipboard-check", "color": "#3b82f6", "description": "完成全部三项测评（体质+心理+BMI）"},
    "streak_3": {"name": "坚持达人", "icon": "fa-fire", "color": "#f97316", "description": "连续打卡3天"},
    "streak_7": {"name": "一周先锋", "icon": "fa-bolt", "color": "#f59e0b", "description": "连续打卡7天"},
    "active_user": {"name": "活跃用户", "icon": "fa-comments", "color": "#8b5cf6", "description": "累计对话100次"},
    "mental_expert": {"name": "心理达人", "icon": "fa-brain", "color": "#ec4899", "description": "心理测评得分85+分"},
    "constitution_expert": {"name": "体质专家", "icon": "fa-yin-yang", "color": "#0d9488", "description": "完成体质辨识测试"},
    "share_master": {"name": "分享达人", "icon": "fa-share-alt", "color": "#06b6d4", "description": "分享5次测评结果"},
    "reader": {"name": "资讯达人", "icon": "fa-book-reader", "color": "#a855f7", "description": "阅读20篇健康资讯"},
    "points_100": {"name": "百分勇士", "icon": "fa-star", "color": "#eab308", "description": "累计获得100积分"},
    "points_500": {"name": "积分富豪", "icon": "fa-gem", "color": "#6366f1", "description": "累计获得500积分"},
    "bmi_normal": {"name": "标准身材", "icon": "fa-heart", "color": "#ef4444", "description": "BMI处于正常范围"},
}


class RewardService:
    """激励积分服务"""

    def __init__(self, config=None):
        self.config = config

    def add_points(self, user_id: int, action_type: str, points: int = None, description: str = None) -> Dict:
        """增加积分"""
        user = User.query.get(user_id)
        if not user:
            return {'success': False, 'message': '用户不存在'}

        # 使用 REWARD_RULES 获取积分值
        rule = REWARD_RULES.get(action_type, {})
        if points is None:
            points = rule.get('points', 1)
        if description is None:
            description = rule.get('description', f'{action_type} 获得 {points} 积分')

        # 检查每日上限（基于该action_type的次数）
        daily_limit = rule.get('daily_limit')
        if daily_limit:
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            today_count = RewardRecord.query.filter(
                RewardRecord.user_id == user_id,
                RewardRecord.action_type == action_type,
                RewardRecord.created_at >= today_start
            ).count()
            if today_count >= daily_limit:
                return {'success': False, 'message': f'今日{action_type}次数已达上限({daily_limit}次)'}

        # 创建记录
        record = RewardRecord(
            user_id=user_id,
            action_type=action_type,
            points=points,
            description=description
        )

        user.total_points += points

        db.session.add(record)
        db.session.commit()

        return {
            'success': True,
            'points_added': points,
            'total_points': user.total_points,
            'description': record.description
        }

    def get_history(self, user_id: int, days: int = 30) -> List[Dict]:
        """获取积分历史"""
        start_date = datetime.utcnow() - timedelta(days=days)
        records = RewardRecord.query.filter(
            RewardRecord.user_id == user_id,
            RewardRecord.created_at >= start_date
        ).order_by(RewardRecord.created_at.desc()).all()

        return [r.to_dict() for r in records]

    def get_stats(self, user_id: int) -> Dict:
        """获取积分统计"""
        user = User.query.get(user_id)
        if not user:
            return {'success': False}

        # 今日积分
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_points = db.session.query(db.func.sum(RewardRecord.points)).filter(
            RewardRecord.user_id == user_id,
            RewardRecord.created_at >= today
        ).scalar() or 0

        # 本周积分
        week_start = today - timedelta(days=today.weekday())
        week_points = db.session.query(db.func.sum(RewardRecord.points)).filter(
            RewardRecord.user_id == user_id,
            RewardRecord.created_at >= week_start
        ).scalar() or 0

        return {
            'total_points': user.total_points,
            'today_points': int(today_points),
            'week_points': int(week_points),
            'max_daily': self.config.REWARD_MAX_DAILY if self.config else 50
        }

    def get_rewards_overview(self, user_id: int) -> Dict:
        """获取积分中心概览：积分、今日获取、可用渠道、成就"""
        user = User.query.get(user_id)
        if not user:
            return {'success': False}

        # 今日积分
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_records = RewardRecord.query.filter(
            RewardRecord.user_id == user_id,
            RewardRecord.created_at >= today
        ).all()
        today_points = sum(r.points for r in today_records if r.points > 0)

        # 构建可用渠道列表
        available_actions = []
        for action_key, rule in REWARD_RULES.items():
            today_count = len([r for r in today_records if r.action_type == action_key])
            available_actions.append({
                'key': action_key,
                'description': rule['description'],
                'points': rule['points'],
                'daily_limit': rule['daily_limit'],
                'completed_today': today_count,
                'remaining': max(0, rule['daily_limit'] - today_count),
            })

        # 成就状态
        achievements = self.get_achievement_status(user_id)

        # 打卡状态
        checkin_status = self.get_checkin_status(user_id)

        return {
            'success': True,
            'total_points': user.total_points,
            'today_points': today_points,
            'available_actions': available_actions,
            'achievements': achievements,
            'checkin': checkin_status,
        }

    def get_achievement_status(self, user_id: int) -> List[Dict]:
        """获取所有成就及解锁状态"""
        unlocked = UserAchievement.query.filter_by(user_id=user_id).all()
        unlocked_keys = {a.achievement_key for a in unlocked}

        # 获取用户统计数据用于进度计算
        chat_count = RewardRecord.query.filter_by(user_id=user_id, action_type='chat').count()
        share_count = RewardRecord.query.filter_by(user_id=user_id, action_type='share_result').count()
        read_count = RewardRecord.query.filter_by(user_id=user_id, action_type='read_article').count()

        user = User.query.get(user_id)
        total_points = (user.total_points or 0) if user else 0
        checkin_streak = (user.checkin_streak or 0) if user else 0

        has_bmi = BMIAssessment.query.filter_by(user_id=user_id).count() > 0
        has_constitution = ConstitutionAssessment.query.filter_by(user_id=user_id).count() > 0
        has_mental = MentalAssessment.query.filter_by(user_id=user_id).count() > 0

        # 最佳心理评分
        best_mental = MentalAssessment.query.filter_by(user_id=user_id).order_by(
            MentalAssessment.overall_score.desc()
        ).first()
        best_mental_score = (best_mental.overall_score or 0) if best_mental else 0

        # BMI是否正常
        bmi_normal = False
        latest_bmi = BMIAssessment.query.filter_by(user_id=user_id).order_by(
            BMIAssessment.created_at.desc()
        ).first()
        if latest_bmi and latest_bmi.bmi_category == 'normal':
            bmi_normal = True

        result = []
        for key, info in ACHIEVEMENTS.items():
            is_unlocked = key in unlocked_keys
            # 计算进度
            progress = 1.0 if is_unlocked else 0.0
            if not is_unlocked:
                if key == 'health_newbie':
                    progress = min(1.0, (1 if has_bmi or has_constitution or has_mental else 0))
                elif key == 'full_assessment':
                    done = sum([has_bmi, has_constitution, has_mental])
                    progress = done / 3.0
                elif key == 'streak_3':
                    progress = min(1.0, checkin_streak / 3.0)
                elif key == 'streak_7':
                    progress = min(1.0, checkin_streak / 7.0)
                elif key == 'active_user':
                    progress = min(1.0, chat_count / 100.0)
                elif key == 'mental_expert':
                    progress = min(1.0, best_mental_score / 85.0)
                elif key == 'constitution_expert':
                    progress = 1.0 if has_constitution else 0.0
                elif key == 'share_master':
                    progress = min(1.0, share_count / 5.0)
                elif key == 'reader':
                    progress = min(1.0, read_count / 20.0)
                elif key == 'points_100':
                    progress = min(1.0, total_points / 100.0)
                elif key == 'points_500':
                    progress = min(1.0, total_points / 500.0)
                elif key == 'bmi_normal':
                    progress = 1.0 if bmi_normal else 0.0

            result.append({
                'key': key,
                'name': info['name'],
                'icon': info['icon'],
                'color': info['color'],
                'description': info['description'],
                'unlocked': is_unlocked,
                'progress': round(progress * 100),
            })

        return result

    def get_checkin_status(self, user_id: int) -> Dict:
        """获取今日打卡状态"""
        user = User.query.get(user_id)
        today = date.today()
        today_checkin = DailyCheckIn.query.filter_by(
            user_id=user_id, checkin_date=today
        ).first()

        return {
            'checked_in_today': today_checkin is not None,
            'checkin': today_checkin.to_dict() if today_checkin else None,
            'streak': (user.checkin_streak or 0) if user else 0,
            'last_checkin': user.last_checkin_date.isoformat() if user and user.last_checkin_date else None,
        }

    def calculate_checkin_score(self, breakfast_done: bool, lunch_done: bool, dinner_done: bool,
                                exercise_minutes: int, water_cups: int, sleep_hours: float,
                                mood_score: int) -> int:
        """
        计算打卡得分（百分制）
        评分体系：
        - 三餐打卡：45分（每餐15分）
        - 运动打卡：20分
        - 饮水打卡：15分
        - 睡眠打卡：10分
        - 心情打卡：10分
        """
        score = 0

        # 三餐打卡（45分）
        if breakfast_done:
            score += 15
        if lunch_done:
            score += 15
        if dinner_done:
            score += 15

        # 运动打卡（20分）
        if exercise_minutes >= 30:
            score += 20
        elif exercise_minutes >= 15:
            score += 15
        elif exercise_minutes > 0:
            score += 10

        # 饮水打卡（15分）
        if water_cups >= 8:
            score += 15
        elif water_cups >= 5:
            score += 10
        elif water_cups > 0:
            score += 5

        # 睡眠打卡（10分）
        if 7 <= sleep_hours <= 9:
            score += 10
        elif 6 <= sleep_hours < 7 or 9 < sleep_hours <= 10:
            score += 8
        elif 5 <= sleep_hours < 6:
            score += 5
        elif sleep_hours > 0:
            score += 2

        # 心情打卡（10分）
        if mood_score >= 8:
            score += 10
        elif mood_score >= 6:
            score += 8
        elif mood_score >= 4:
            score += 5
        elif mood_score > 0:
            score += 2

        return min(score, 100)

    def perform_daily_checkin(self, user_id: int, 
                               breakfast_done: bool = None, lunch_done: bool = None,
                               dinner_done: bool = None, exercise_minutes: int = None,
                               water_cups: int = None, sleep_hours: float = None,
                               mood_score: int = None, notes: str = None) -> Dict:
        """执行每日打卡（多任务版）"""
        user = User.query.get(user_id)
        if not user:
            return {'success': False, 'message': '用户不存在'}

        today = date.today()
        existing = DailyCheckIn.query.filter_by(
            user_id=user_id, checkin_date=today
        ).first()

        if existing:
            # 已打卡，更新记录
            if breakfast_done is not None:
                existing.breakfast_done = breakfast_done
            if lunch_done is not None:
                existing.lunch_done = lunch_done
            if dinner_done is not None:
                existing.dinner_done = dinner_done
            if exercise_minutes is not None:
                existing.exercise_minutes = exercise_minutes
            if water_cups is not None:
                existing.water_cups = water_cups
            if sleep_hours is not None:
                existing.sleep_hours = sleep_hours
            if mood_score is not None:
                existing.mood_score = mood_score
            if notes is not None:
                existing.notes = notes
            
            # 重新计算得分
            existing.total_score = self.calculate_checkin_score(
                existing.breakfast_done, existing.lunch_done, existing.dinner_done,
                existing.exercise_minutes or 0, existing.water_cups or 0,
                existing.sleep_hours or 0, existing.mood_score or 5
            )
            db.session.commit()
            return {
                'success': True,
                'message': '今日打卡记录已更新',
                'checkin': existing.to_dict(),
                'streak': user.checkin_streak or 0,
                'points_awarded': 0
            }

        # 创建新打卡记录
        checkin = DailyCheckIn(
            user_id=user_id,
            checkin_date=today,
            breakfast_done=breakfast_done or False,
            lunch_done=lunch_done or False,
            dinner_done=dinner_done or False,
            exercise_minutes=exercise_minutes or 0,
            water_cups=water_cups or 0,
            sleep_hours=sleep_hours or 0,
            mood_score=mood_score or 5,
            notes=notes
        )

        # 计算得分
        checkin.total_score = self.calculate_checkin_score(
            checkin.breakfast_done, checkin.lunch_done, checkin.dinner_done,
            checkin.exercise_minutes, checkin.water_cups,
            checkin.sleep_hours, checkin.mood_score
        )

        db.session.add(checkin)

        # 计算连续打卡天数
        yesterday = today - timedelta(days=1)
        if user.last_checkin_date and user.last_checkin_date == yesterday:
            user.checkin_streak = (user.checkin_streak or 0) + 1
        else:
            user.checkin_streak = 1
        user.last_checkin_date = today

        # 基础打卡积分（根据得分比例）
        base_points = int(REWARD_RULES['daily_checkin']['points'] * checkin.total_score / 100)
        self.add_points(user_id, 'daily_checkin', points=max(base_points, 1),
                       description=f'每日健康打卡（得分{checkin.total_score}分）')

        # 连续打卡奖励
        points_awarded = max(base_points, 1)
        if user.checkin_streak == 3:
            self.add_points(user_id, 'weekly_streak_3', points=REWARD_RULES['weekly_streak_3']['points'],
                       description='连续打卡3天奖励')
            points_awarded += REWARD_RULES['weekly_streak_3']['points']
            self._check_and_unlock(user_id, 'streak_3')
        elif user.checkin_streak == 7:
            self.add_points(user_id, 'weekly_streak_7', points=REWARD_RULES['weekly_streak_7']['points'],
                       description='连续打卡7天奖励')
            points_awarded += REWARD_RULES['weekly_streak_7']['points']
            self._check_and_unlock(user_id, 'streak_7')

        # 检查成就解锁
        self._check_and_unlock(user_id, 'health_newbie')
        if user.total_points >= 100:
            self._check_and_unlock(user_id, 'points_100')
        if user.total_points >= 500:
            self._check_and_unlock(user_id, 'points_500')

        db.session.commit()

        return {
            'success': True,
            'message': f'打卡成功！得分{checkin.total_score}分，连续第{user.checkin_streak}天',
            'checkin': checkin.to_dict(),
            'streak': user.checkin_streak,
            'points_awarded': points_awarded,
            'total_points': user.total_points
        }

    def _check_and_unlock(self, user_id: int, achievement_key: str) -> bool:
        """检查并解锁成就"""
        existing = UserAchievement.query.filter_by(
            user_id=user_id, achievement_key=achievement_key
        ).first()
        if existing:
            return False

        if achievement_key not in ACHIEVEMENTS:
            return False

        achievement = UserAchievement(
            user_id=user_id,
            achievement_key=achievement_key
        )
        db.session.add(achievement)
        db.session.commit()
        print(f"[成就解锁] 用户{user_id}解锁成就: {ACHIEVEMENTS[achievement_key]['name']}")
        return True

    def check_assessment_achievements(self, user_id: int, assessment_type: str = None):
        """在完成测评后检查成就"""
        if assessment_type == 'bmi':
            if 'first_bmi' in ACHIEVEMENTS:
                self._check_and_unlock(user_id, 'first_bmi')
            # BMI正常成就
            latest = BMIAssessment.query.filter_by(user_id=user_id).order_by(
                BMIAssessment.created_at.desc()
            ).first()
            if latest and latest.bmi_category == 'normal':
                self._check_and_unlock(user_id, 'bmi_normal')
        elif assessment_type == 'constitution':
            self._check_and_unlock(user_id, 'constitution_expert')
            if 'first_constitution' in ACHIEVEMENTS:
                self._check_and_unlock(user_id, 'first_constitution')
        elif assessment_type == 'mental':
            if 'first_mental' in ACHIEVEMENTS:
                self._check_and_unlock(user_id, 'first_mental')
            best = MentalAssessment.query.filter_by(user_id=user_id).order_by(
                MentalAssessment.overall_score.desc()
            ).first()
            if best and (best.overall_score or 0) >= 85:
                self._check_and_unlock(user_id, 'mental_expert')

        # 检查全面评估成就
        has_bmi = BMIAssessment.query.filter_by(user_id=user_id).count() > 0
        has_con = ConstitutionAssessment.query.filter_by(user_id=user_id).count() > 0
        has_men = MentalAssessment.query.filter_by(user_id=user_id).count() > 0
        if has_bmi and has_con and has_men:
            self._check_and_unlock(user_id, 'full_assessment')
            self.add_points(user_id, 'all_assessments',
                          points=REWARD_RULES['all_assessments']['points'],
                          description='完成全部三项测评')

    def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        """获取积分排行榜"""
        users = User.query.order_by(User.total_points.desc()).limit(limit).all()
        return [
            {
                'student_id': u.student_id,
                'username': u.username,
                'total_points': u.total_points,
                'college': u.college
            }
            for u in users
        ]

    # 兑换商品配置
    EXCHANGE_ITEMS = [
        {"id": "wellness_tip", "name": "每日养生小贴士", "description": "解锁今日专属养生知识卡片", "cost": 10, "icon": "fa-lightbulb", "category": "数字"},
        {"id": "mental_guide", "name": "心理减压音频", "description": "解锁专属冥想放松音频指导", "cost": 30, "icon": "fa-headphones", "category": "数字"},
        {"id": "consult_vip", "name": "AI高级咨询特权", "description": "获得一次深度健康分析咨询", "cost": 50, "icon": "fa-user-md", "category": "服务"},
        {"id": "tcm_plan", "name": "中医调理方案", "description": "获取定制中医食疗+起居调理方案", "cost": 80, "icon": "fa-leaf", "category": "服务"},
        {"id": "health_report", "name": "个性化健康报告", "description": "生成个人专属健康分析报告", "cost": 100, "icon": "fa-file-medical", "category": "服务"},
        {"id": "sports_check", "name": "运动健康检测", "description": "校医院免费体测一次", "cost": 120, "icon": "fa-heart-pulse", "category": "服务"},
        {"id": "coupon_bookstore", "name": "书店8折优惠券", "description": "校内书店购书优惠", "cost": 150, "icon": "fa-book", "category": "实物"},
        {"id": "coupon_canteen", "name": "食堂5元代金券", "description": "校内食堂使用的代金券", "cost": 200, "icon": "fa-utensils", "category": "实物"},
        {"id": "badge_gold", "name": "健康达人徽章", "description": "专属虚拟徽章，展示在排行榜", "cost": 300, "icon": "fa-medal", "category": "虚拟"},
    ]

    def get_shop_items(self, user_id: int) -> list:
        """获取商城商品列表"""
        user = User.query.get(user_id)
        user_points = user.total_points if user else 0
        items = []
        for item in self.EXCHANGE_ITEMS:
            items.append({
                **item,
                'affordable': user_points >= item['cost'],
                'user_points': user_points
            })
        return items

    def exchange(self, user_id: int, item_id: str) -> Dict:
        """兑换商品"""
        user = User.query.get(user_id)
        if not user:
            return {'success': False, 'message': '用户不存在'}

        item = next((i for i in self.EXCHANGE_ITEMS if i['id'] == item_id), None)
        if not item:
            return {'success': False, 'message': '商品不存在'}

        if user.total_points < item['cost']:
            return {'success': False, 'message': f'积分不足，需要{item["cost"]}积分'}

        # 扣除积分
        user.total_points -= item['cost']

        # 记录兑换
        record = RewardRecord(
            user_id=user_id,
            action_type='exchange',
            points=-item['cost'],
            description=f'兑换：{item["name"]}'
        )
        db.session.add(record)
        db.session.commit()

        return {
            'success': True,
            'message': f'兑换成功！{item["name"]}',
            'item': item,
            'remaining_points': user.total_points
        }

    def get_exchange_history(self, user_id: int) -> list:
        """获取兑换记录"""
        records = RewardRecord.query.filter_by(
            user_id=user_id, action_type='exchange'
        ).order_by(RewardRecord.created_at.desc()).all()
        return [r.to_dict() for r in records]


# 单例
_reward_service = None

def get_reward_service(config=None):
    global _reward_service
    if _reward_service is None:
        _reward_service = RewardService(config)
    return _reward_service
