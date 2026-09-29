from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class User(db.Model):
    """用户表"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    username = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='student')  # student/counselor/admin
    class_name = db.Column(db.String(100))
    college = db.Column(db.String(100))
    grade = db.Column(db.String(20))
    gender = db.Column(db.String(10))
    birth_date = db.Column(db.Date)
    phone = db.Column(db.String(20))
    emergency_contact = db.Column(db.String(20))
    
    # 隐私设置
    privacy_settings = db.Column(db.Text, default='{}')  # JSON格式
    alert_enabled = db.Column(db.Boolean, default=False)  # 是否开启心理预警
    counselor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # 密码状态：是否已通过注册设置密码（演示模式自动创建的用户为False）
    password_set = db.Column(db.Boolean, default=False)

    # 心理状态评分（0-100，NULL表示"未测评"）
    mental_score = db.Column(db.Integer, nullable=True)
    mental_score_source = db.Column(db.String(20), nullable=True)  # ai_chat/manual
    mental_score_updated_at = db.Column(db.DateTime, nullable=True)  # 最后更新时间

    # 积分
    total_points = db.Column(db.Integer, default=0)
    

    # 健康档案扩展
    height = db.Column(db.Float)  # 身高(cm)
    weight = db.Column(db.Float)  # 体重(kg)
    preferred_name = db.Column(db.String(100))  # 昵称
    avatar_url = db.Column(db.String(500))  # 头像URL

    # 打卡系统
    last_checkin_date = db.Column(db.Date)  # 最后打卡日期
    checkin_streak = db.Column(db.Integer, default=0)  # 连续打卡天数

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # 关系
    health_records = db.relationship('HealthRecord', backref='user', lazy=True, cascade='all, delete-orphan')
    mental_assessments = db.relationship('MentalAssessment', backref='user', lazy=True, cascade='all, delete-orphan')
    conversations = db.relationship('Conversation', backref='user', lazy=True, cascade='all, delete-orphan')
    rewards = db.relationship('RewardRecord', backref='user', lazy=True, cascade='all, delete-orphan')
    alerts = db.relationship('AlertRecord', backref='user', lazy=True, cascade='all, delete-orphan', foreign_keys='AlertRecord.user_id')
    bmi_assessments = db.relationship('BMIAssessment', backref='user', lazy=True, cascade='all, delete-orphan')
    constitution_assessments = db.relationship('ConstitutionAssessment', backref='user', lazy=True, cascade='all, delete-orphan')
    daily_checkins = db.relationship('DailyCheckIn', backref='user', lazy=True, cascade='all, delete-orphan')
    achievements = db.relationship('UserAchievement', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self, include_private=False):
        data = {
            'id': self.id,
            'student_id': self.student_id,
            'username': self.username,
            'role': self.role,
            'class_name': self.class_name,
            'college': self.college,
            'grade': self.grade,
            'gender': self.gender,
            'total_points': self.total_points,
            'alert_enabled': self.alert_enabled,
            'password_set': self.password_set if self.password_set is not None else False,
            'mental_score': self.mental_score,
            'mental_score_source': self.mental_score_source,
            'mental_score_updated_at': self.mental_score_updated_at.isoformat() if self.mental_score_updated_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'height': self.height,
            'weight': self.weight,
            'preferred_name': self.preferred_name,
            'avatar_url': self.avatar_url,
            'last_checkin_date': self.last_checkin_date.isoformat() if self.last_checkin_date else None,
            'checkin_streak': self.checkin_streak or 0,
        }
        if include_private:
            data['phone'] = self.phone
            data['emergency_contact'] = self.emergency_contact
            data['privacy_settings'] = json.loads(self.privacy_settings or '{}')
        return data

class HealthRecord(db.Model):
    """健康档案表 - 累积4年健康数据"""
    __tablename__ = 'health_records'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    record_type = db.Column(db.String(50), nullable=False)  # bmi/diet/sleep/exercise/physical_exam/tongue/etc
    record_date = db.Column(db.Date, nullable=False, index=True)
    
    # 加密存储的敏感数据
    data_hash = db.Column(db.String(64))  # 数据完整性校验
    encrypted_data = db.Column(db.Text)  # 加密后的JSON数据
    
    # 非敏感索引字段（用于快速筛选）
    bmi_value = db.Column(db.Float)
    constitution = db.Column(db.String(50))  # 体质类型
    tags = db.Column(db.String(200))  # 标签，逗号分隔
    
    # 医案溯源
    case_reference = db.Column(db.String(100))  # 关联的医案编号
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self, decrypt_fn=None):
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'record_type': self.record_type,
            'record_date': self.record_date.isoformat() if self.record_date else None,
            'constitution': self.constitution,
            'tags': self.tags,
            'case_reference': self.case_reference,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        if decrypt_fn and self.encrypted_data:
            try:
                decrypted = decrypt_fn(self.encrypted_data)
                data['details'] = json.loads(decrypted)
            except Exception:
                data['details'] = None
        return data

class MentalAssessment(db.Model):
    """心理评估表"""
    __tablename__ = 'mental_assessments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    assessment_date = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # 评估维度（0-100分）
    overall_score = db.Column(db.Integer, nullable=False)  # 总分
    anxiety_score = db.Column(db.Integer)  # 焦虑维度
    depression_score = db.Column(db.Integer)  # 抑郁维度
    stress_score = db.Column(db.Integer)  # 压力维度
    sleep_score = db.Column(db.Integer)  # 睡眠维度
    social_score = db.Column(db.Integer)  # 社交维度
    
    # 评估来源
    source = db.Column(db.String(50), default='ai_chat')  # ai_chat/scale/self_report
    
    # 原始对话摘要（加密存储）
    encrypted_summary = db.Column(db.Text)
    
    # 预警状态
    alert_triggered = db.Column(db.Boolean, default=False)
    alert_sent = db.Column(db.Boolean, default=False)
    alert_time = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self, decrypt_fn=None):
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'assessment_date': self.assessment_date.isoformat() if self.assessment_date else None,
            'overall_score': self.overall_score,
            'anxiety_score': self.anxiety_score,
            'depression_score': self.depression_score,
            'stress_score': self.stress_score,
            'sleep_score': self.sleep_score,
            'social_score': self.social_score,
            'source': self.source,
            'alert_triggered': self.alert_triggered,
            'alert_sent': self.alert_sent,
        }
        if decrypt_fn and self.encrypted_summary:
            try:
                data['summary'] = decrypt_fn(self.encrypted_summary)
            except Exception:
                data['summary'] = None
        return data

class Conversation(db.Model):
    """对话记录表 - 长期记忆"""
    __tablename__ = 'conversations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    session_id = db.Column(db.String(100), nullable=False, index=True)
    
    role = db.Column(db.String(20), nullable=False)  # user/assistant/system
    content = db.Column(db.Text, nullable=False)
    
    # 消息类型
    msg_type = db.Column(db.String(50), default='text')  # text/image/audio
    image_path = db.Column(db.String(500))  # 图片路径
    
    # 向量嵌入（用于语义检索）
    embedding = db.Column(db.BLOB)
    
    # 意图分类
    intent = db.Column(db.String(50))  # tcm/mental/diagnosis/general
    
    # 关联的医案
    case_reference = db.Column(db.String(100))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'role': self.role,
            'content': self.content,
            'msg_type': self.msg_type,
            'image_path': self.image_path,
            'intent': self.intent,
            'case_reference': self.case_reference,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

class RewardRecord(db.Model):
    """积分记录表"""
    __tablename__ = 'reward_records'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    action_type = db.Column(db.String(50), nullable=False)  # chat/diary/login/checkin/exchange
    points = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(200))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action_type': self.action_type,
            'points': self.points,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

class AlertRecord(db.Model):
    """预警记录表"""
    __tablename__ = 'alert_records'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    alert_type = db.Column(db.String(50), nullable=False)  # mental/physical
    severity = db.Column(db.String(20), default='medium')  # low/medium/high
    
    # 脱敏后的摘要
    summary = db.Column(db.Text)
    
    # 处理状态
    status = db.Column(db.String(20), default='pending')  # pending/processing/resolved
    handled_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    handled_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'alert_type': self.alert_type,
            'severity': self.severity,
            'summary': self.summary,
            'status': self.status,
            'handled_by': self.handled_by,
            'handled_at': self.handled_at.isoformat() if self.handled_at else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

class ImageAnalysis(db.Model):
    """图像分析记录表 - 多模态"""
    __tablename__ = 'image_analyses'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    image_type = db.Column(db.String(50), nullable=False)  # tongue/meal/skin/other
    image_path = db.Column(db.String(500), nullable=False)
    
    # 分析结果
    analysis_result = db.Column(db.Text)  # JSON格式
    
    # 关联医案
    case_reference = db.Column(db.String(100))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'image_type': self.image_type,
            'image_path': self.image_path,
            'analysis_result': json.loads(self.analysis_result) if self.analysis_result else None,
            'case_reference': self.case_reference,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }



class BMIAssessment(db.Model):
    """BMI评估记录表"""
    __tablename__ = 'bmi_assessments'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    gender = db.Column(db.String(10))
    height = db.Column(db.Float)
    weight = db.Column(db.Float)
    bmi_value = db.Column(db.Float, nullable=False)
    bmi_category = db.Column(db.String(50))
    bmi_category_label = db.Column(db.String(50))
    color = db.Column(db.String(20))

    diet_tip = db.Column(db.Text)
    exercise_tip = db.Column(db.Text)
    lifestyle_tip = db.Column(db.Text)

    encrypted_summary = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self, decrypt_fn=None):
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'gender': self.gender,
            'height': self.height,
            'weight': self.weight,
            'bmi_value': self.bmi_value,
            'bmi_category': self.bmi_category,
            'bmi_category_label': self.bmi_category_label,
            'color': self.color,
            'diet_tip': self.diet_tip,
            'exercise_tip': self.exercise_tip,
            'lifestyle_tip': self.lifestyle_tip,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        if decrypt_fn and self.encrypted_summary:
            try:
                data['summary'] = decrypt_fn(self.encrypted_summary)
            except Exception:
                data['summary'] = None
        return data


class ConstitutionAssessment(db.Model):
    """体质辨识记录表"""
    __tablename__ = 'constitution_assessments'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    primary_type = db.Column(db.String(50), nullable=False)
    primary_type_label = db.Column(db.String(100))
    percentages = db.Column(db.Text)  # JSON格式的体质百分比

    description = db.Column(db.Text)
    diet_tip = db.Column(db.Text)
    exercise_tip = db.Column(db.Text)
    lifestyle_tip = db.Column(db.Text)

    encrypted_summary = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self, decrypt_fn=None):
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'primary_type': self.primary_type,
            'primary_type_label': self.primary_type_label,
            'percentages': json.loads(self.percentages) if self.percentages else {},
            'description': self.description,
            'diet_tip': self.diet_tip,
            'exercise_tip': self.exercise_tip,
            'lifestyle_tip': self.lifestyle_tip,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        if decrypt_fn and self.encrypted_summary:
            try:
                data['summary'] = decrypt_fn(self.encrypted_summary)
            except Exception:
                data['summary'] = None
        return data


class DailyCheckIn(db.Model):
    """每日健康打卡表 - 多任务打卡系统"""
    __tablename__ = 'daily_checkins'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    checkin_date = db.Column(db.Date, nullable=False, index=True)

    # 三餐打卡（完成=1，未完成=0）
    breakfast_done = db.Column(db.Boolean, default=False)
    lunch_done = db.Column(db.Boolean, default=False)
    dinner_done = db.Column(db.Boolean, default=False)

    # 运动打卡（分钟，0=未运动）
    exercise_minutes = db.Column(db.Integer, default=0)

    # 饮水打卡（杯数）
    water_cups = db.Column(db.Integer, default=0)

    # 睡眠打卡（小时）
    sleep_hours = db.Column(db.Float, default=0)

    # 心情打卡（1-10分）
    mood_score = db.Column(db.Integer, default=5)

    # 总得分（0-100）
    total_score = db.Column(db.Integer, default=0)

    # 备注
    notes = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 唯一约束：每天只能打卡一次
    __table_args__ = (db.UniqueConstraint('user_id', 'checkin_date', name='unique_daily_checkin'),)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'checkin_date': self.checkin_date.isoformat() if self.checkin_date else None,
            'breakfast_done': self.breakfast_done,
            'lunch_done': self.lunch_done,
            'dinner_done': self.dinner_done,
            'exercise_minutes': self.exercise_minutes,
            'water_cups': self.water_cups,
            'sleep_hours': self.sleep_hours,
            'mood_score': self.mood_score,
            'total_score': self.total_score,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class UserAchievement(db.Model):
    """用户成就表"""
    __tablename__ = 'user_achievements'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    achievement_key = db.Column(db.String(50), nullable=False)
    unlocked_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('user_id', 'achievement_key', name='unique_user_achievement'),)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'achievement_key': self.achievement_key,
            'unlocked_at': self.unlocked_at.isoformat() if self.unlocked_at else None,
        }


class MedicalCase(db.Model):
    """医案库表 - 支持溯源"""
    __tablename__ = 'medical_cases'
    
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    
    source = db.Column(db.String(200), nullable=False)  # 来源文献
    source_url = db.Column(db.String(500))
    
    category = db.Column(db.String(100))  # 内科/妇科/ etc
    disease = db.Column(db.String(100))
    syndrome = db.Column(db.String(100))
    
    content = db.Column(db.Text, nullable=False)  # 完整医案内容
    
    # 向量嵌入
    embedding = db.Column(db.BLOB)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'case_id': self.case_id,
            'source': self.source,
            'source_url': self.source_url,
            'category': self.category,
            'disease': self.disease,
            'syndrome': self.syndrome,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class FoodCategory(db.Model):
    """食物分类表"""
    __tablename__ = 'food_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)  # 主食/荤菜/素菜/汤羹/饮品/水果/零食
    display_name = db.Column(db.String(50))  # 显示名称
    sort_order = db.Column(db.Integer, default=0)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
        }


class FoodItem(db.Model):
    """食物/菜肴基础数据表"""
    __tablename__ = 'food_items'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # 菜名/食材名
    category_id = db.Column(db.Integer, db.ForeignKey('food_categories.id'), nullable=False)
    
    # 营养成分 (每100g/每份)
    calories = db.Column(db.Float, default=0)  # 热量(kcal)
    protein = db.Column(db.Float, default=0)  # 蛋白质(g)
    fat = db.Column(db.Float, default=0)  # 脂肪(g)
    carbs = db.Column(db.Float, default=0)  # 碳水化合物(g)
    fiber = db.Column(db.Float, default=0)  # 膳食纤维(g)
    
    # 中医属性
    tcm_nature = db.Column(db.String(20))  # 寒/凉/平/温/热
    tcm_flavor = db.Column(db.String(50))  # 酸/苦/甘/辛/咸
    tcm_meridian = db.Column(db.String(100))  # 归经
    tcm_function = db.Column(db.String(200))  # 功效
    
    # 适用场景标签
    tags = db.Column(db.String(200))  # 减肥/消暑/温养/补气/补血/健脾等，逗号分隔
    suitable_constitutions = db.Column(db.String(200))  # 适用体质
    avoid_constitutions = db.Column(db.String(200))  # 忌用体质
    
    # 推荐餐次
    meal_types = db.Column(db.String(50))  # breakfast/lunch/dinner/snack，逗号分隔
    
    # 份量信息
    serving_size = db.Column(db.Float, default=100)  # 标准份量(g)
    serving_unit = db.Column(db.String(20), default='g')  # 单位
    
    # 图片/描述
    image_url = db.Column(db.String(500))
    description = db.Column(db.Text)
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category_id': self.category_id,
            'calories': self.calories,
            'protein': self.protein,
            'fat': self.fat,
            'carbs': self.carbs,
            'fiber': self.fiber,
            'tcm_nature': self.tcm_nature,
            'tcm_flavor': self.tcm_flavor,
            'tcm_meridian': self.tcm_meridian,
            'tcm_function': self.tcm_function,
            'tags': self.tags.split(',') if self.tags else [],
            'suitable_constitutions': self.suitable_constitutions.split(',') if self.suitable_constitutions else [],
            'avoid_constitutions': self.avoid_constitutions.split(',') if self.avoid_constitutions else [],
            'meal_types': self.meal_types.split(',') if self.meal_types else [],
            'serving_size': self.serving_size,
            'serving_unit': self.serving_unit,
            'image_url': self.image_url,
            'description': self.description,
        }


class DietRecommendation(db.Model):
    """膳食推荐记录表"""
    __tablename__ = 'diet_recommendations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # 用户基础数据（快照）
    gender = db.Column(db.String(10))
    height = db.Column(db.Float)
    weight = db.Column(db.Float)
    bmi = db.Column(db.Float)
    bmi_category = db.Column(db.String(20))
    constitution = db.Column(db.String(50))  # 体质类型
    
    # 计算结果
    daily_calories = db.Column(db.Float)  # 每日总热量
    target_calories = db.Column(db.Float)  # 目标热量(减肥/增重调整后)
    
    # 三餐分配
    breakfast_calories = db.Column(db.Float)
    lunch_calories = db.Column(db.Float)
    dinner_calories = db.Column(db.Float)
    snack_calories = db.Column(db.Float)
    
    # 宏量营养素目标
    target_protein = db.Column(db.Float)
    target_fat = db.Column(db.Float)
    target_carbs = db.Column(db.Float)
    
    # 推荐菜单 (JSON)
    breakfast_items = db.Column(db.Text)  # JSON数组
    lunch_items = db.Column(db.Text)
    dinner_items = db.Column(db.Text)
    snack_items = db.Column(db.Text)
    
    # 用户需求
    user_goal = db.Column(db.String(50))  # maintain/lose_weight/gain_muscle/heat_relief/warming/etc
    user_notes = db.Column(db.Text)  # 用户额外需求
    
    # 推荐类型
    recommendation_type = db.Column(db.String(20), default='algorithm')  # algorithm/ai
    
    # AI精细推荐结果
    ai_recommendation = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'gender': self.gender,
            'height': self.height,
            'weight': self.weight,
            'bmi': self.bmi,
            'bmi_category': self.bmi_category,
            'constitution': self.constitution,
            'daily_calories': self.daily_calories,
            'target_calories': self.target_calories,
            'breakfast_calories': self.breakfast_calories,
            'lunch_calories': self.lunch_calories,
            'dinner_calories': self.dinner_calories,
            'snack_calories': self.snack_calories,
            'target_protein': self.target_protein,
            'target_fat': self.target_fat,
            'target_carbs': self.target_carbs,
            'breakfast_items': json.loads(self.breakfast_items) if self.breakfast_items else [],
            'lunch_items': json.loads(self.lunch_items) if self.lunch_items else [],
            'dinner_items': json.loads(self.dinner_items) if self.dinner_items else [],
            'snack_items': json.loads(self.snack_items) if self.snack_items else [],
            'user_goal': self.user_goal,
            'user_notes': self.user_notes,
            'recommendation_type': self.recommendation_type,
            'ai_recommendation': self.ai_recommendation,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class DietLog(db.Model):
    """饮食记录表 - 用户每日饮食记录"""
    __tablename__ = 'diet_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # 记录时间
    log_date = db.Column(db.Date, nullable=False, index=True)
    log_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # 餐次类型: breakfast/lunch/dinner/snack
    meal_type = db.Column(db.String(20), nullable=False)
    
    # 食物信息
    food_name = db.Column(db.String(100), nullable=False)
    food_item_id = db.Column(db.Integer, db.ForeignKey('food_items.id'), nullable=True)
    
    # 份量信息
    serving_size = db.Column(db.Float, default=100)  # 份量(g)
    serving_count = db.Column(db.Float, default=1)  # 份数
    
    # 营养信息（实际摄入）
    calories = db.Column(db.Float, default=0)  # 热量(kcal)
    protein = db.Column(db.Float, default=0)  # 蛋白质(g)
    fat = db.Column(db.Float, default=0)  # 脂肪(g)
    carbs = db.Column(db.Float, default=0)  # 碳水化合物(g)
    fiber = db.Column(db.Float, default=0)  # 膳食纤维(g)
    
    # 是否为夜宵（21:00后）
    is_late_night = db.Column(db.Boolean, default=False)
    
    # 备注
    notes = db.Column(db.Text)
    
    # 图片路径（可选）
    image_path = db.Column(db.String(500))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    food_item = db.relationship('FoodItem', backref='diet_logs', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'log_date': self.log_date.isoformat() if self.log_date else None,
            'log_time': self.log_time.isoformat() if self.log_time else None,
            'meal_type': self.meal_type,
            'food_name': self.food_name,
            'food_item_id': self.food_item_id,
            'serving_size': self.serving_size,
            'serving_count': self.serving_count,
            'calories': self.calories,
            'protein': self.protein,
            'fat': self.fat,
            'carbs': self.carbs,
            'fiber': self.fiber,
            'is_late_night': self.is_late_night,
            'notes': self.notes,
            'image_path': self.image_path,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class DailyDietSummary(db.Model):
    """每日饮食汇总表"""
    __tablename__ = 'daily_diet_summaries'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    summary_date = db.Column(db.Date, nullable=False, index=True)
    
    # 每日总摄入
    total_calories = db.Column(db.Float, default=0)  # 总热量(kcal)
    total_protein = db.Column(db.Float, default=0)  # 总蛋白质(g)
    total_fat = db.Column(db.Float, default=0)  # 总脂肪(g)
    total_carbs = db.Column(db.Float, default=0)  # 总碳水(g)
    total_fiber = db.Column(db.Float, default=0)  # 总膳食纤维(g)
    
    # 各餐热量
    breakfast_calories = db.Column(db.Float, default=0)
    lunch_calories = db.Column(db.Float, default=0)
    dinner_calories = db.Column(db.Float, default=0)
    snack_calories = db.Column(db.Float, default=0)
    
    # 夜宵统计
    late_night_count = db.Column(db.Integer, default=0)  # 夜宵次数
    late_night_calories = db.Column(db.Float, default=0)  # 夜宵热量
    
    # 餐次记录数
    breakfast_count = db.Column(db.Integer, default=0)
    lunch_count = db.Column(db.Integer, default=0)
    dinner_count = db.Column(db.Integer, default=0)
    snack_count = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'summary_date': self.summary_date.isoformat() if self.summary_date else None,
            'total_calories': self.total_calories,
            'total_protein': self.total_protein,
            'total_fat': self.total_fat,
            'total_carbs': self.total_carbs,
            'total_fiber': self.total_fiber,
            'breakfast_calories': self.breakfast_calories,
            'lunch_calories': self.lunch_calories,
            'dinner_calories': self.dinner_calories,
            'snack_calories': self.snack_calories,
            'late_night_count': self.late_night_count,
            'late_night_calories': self.late_night_calories,
            'breakfast_count': self.breakfast_count,
            'lunch_count': self.lunch_count,
            'dinner_count': self.dinner_count,
            'snack_count': self.snack_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


# 初始化数据库
def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()
        _migrate_db()

def _migrate_db():
    """数据库迁移：为已存在的表添加新列（兼容旧版SQLite数据库）"""
    from sqlalchemy import inspect, text
    inspector = inspect(db.engine)

    # 仅处理已存在的表
    table_names = inspector.get_table_names()
    if 'users' not in table_names:
        return

    existing_columns = [col['name'] for col in inspector.get_columns('users')]

    # 需要迁移的新列：(列名, SQL类型)
    new_columns = [
        ('password_set', 'BOOLEAN'),
        ('mental_score', 'INTEGER'),
        ('mental_score_source', 'VARCHAR(20)'),
        ('mental_score_updated_at', 'DATETIME'),
    ]

    for col_name, col_type in new_columns:
        if col_name not in existing_columns:
            try:
                db.session.execute(
                    text(f'ALTER TABLE users ADD COLUMN {col_name} {col_type}')
                )
                print(f'[数据库迁移] 已添加列: users.{col_name}')
            except Exception as e:
                print(f'[数据库迁移] 添加列失败 users.{col_name}: {e}')

    # 新增字段迁移
    new_columns_v2 = [
        ('height', 'FLOAT'),
        ('weight', 'FLOAT'),
        ('preferred_name', 'VARCHAR(100)'),
        ('avatar_url', 'VARCHAR(500)'),
        ('last_checkin_date', 'DATE'),
        ('checkin_streak', 'INTEGER'),
    ]
    for col_name, col_type in new_columns_v2:
        if col_name not in existing_columns:
            try:
                db.session.execute(
                    text(f'ALTER TABLE users ADD COLUMN {col_name} {col_type}')
                )
                print(f'[数据库迁移] 已添加列: users.{col_name}')
            except Exception as e:
                print(f'[数据库迁移] 添加列失败 users.{col_name}: {e}')

    db.session.commit()
