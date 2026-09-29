from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
import os
import sys
import uuid
import base64
import json
from datetime import datetime
from werkzeug.utils import secure_filename

from config import Config
from models import (db, init_db, User, HealthRecord, MentalAssessment, AlertRecord,
                    Conversation, BMIAssessment, ConstitutionAssessment, DailyCheckIn, UserAchievement,
                    FoodCategory, FoodItem, DietRecommendation, MedicalCase, DietLog, DailyDietSummary)
from services.llm_service import get_llm_service
from services.privacy_service import get_privacy_service
from services.memory_service import get_memory_service
from services.reward_service import get_reward_service
from services.image_service import get_image_service
from services.diet_service import get_diet_service
from agents.coordinator import CoordinatorAgent
from agents.tcm_agent import TCMAgent
from agents.mental_agent import MentalHealthAgent
from agents.diagnosis_agent import DiagnosisAgent

# 创建Flask应用
app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# 初始化数据库
init_db(app)

# 初始化服务
llm_service = get_llm_service(Config)
privacy_service = get_privacy_service(Config.ENCRYPTION_KEY)
memory_service = get_memory_service(llm_service)
reward_service = get_reward_service(Config)
image_service = get_image_service(llm_service)
diet_service = get_diet_service()

# 初始化Agent
coordinator = CoordinatorAgent(llm_service, memory_service, privacy_service, Config)
tcm_agent = TCMAgent(llm_service, memory_service, privacy_service, Config, image_service)
mental_agent = MentalHealthAgent(llm_service, memory_service, privacy_service, Config)
diagnosis_agent = DiagnosisAgent(llm_service, memory_service, privacy_service, Config)

# 注册Agent
coordinator.register_agent('tcm', tcm_agent)
coordinator.register_agent('mental', mental_agent)
coordinator.register_agent('diagnosis', diagnosis_agent)

# ==================== 工具函数 ====================

def get_or_create_user(student_id, username="用户"):
    """获取或创建用户"""
    user = User.query.filter_by(student_id=student_id).first()
    if not user:
        user = User(student_id=student_id, username=username, password_hash="demo")
        db.session.add(user)
        db.session.commit()
    return user

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

def get_data_dir():
    """获取数据目录路径"""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')

# ==================== 认证路由 ====================

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    student_id = data.get('student_id')
    password = data.get('password')
    
    is_new_user = False
    user = User.query.filter_by(student_id=student_id).first()
    if not user:
        # 演示模式：自动创建用户
        user = get_or_create_user(student_id, data.get('username', f'用户{student_id}'))
        is_new_user = True
    
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    # 登录奖励
    reward_service.add_points(user.id, 'login', description='每日登录奖励')
    
    # 新用户欢迎积分
    if is_new_user:
        welcome_bonus = getattr(Config, 'REWARD_WELCOME_BONUS', 30)
        reward_service.add_points(user.id, 'welcome', points=welcome_bonus, description='新用户欢迎积分')
    
    return jsonify({
        'success': True,
        'user': user.to_dict(include_private=True),
        'token': f'demo-token-{user.id}'
    })

@app.route('/api/auth/profile', methods=['GET'])
def get_profile():
    student_id = request.args.get('student_id')
    user = User.query.filter_by(student_id=student_id).first()
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    return jsonify({'user': user.to_dict(include_private=True)})

@app.route('/api/auth/privacy', methods=['POST'])
def update_privacy():
    data = request.json
    student_id = data.get('student_id')
    user = User.query.filter_by(student_id=student_id).first()
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    user.alert_enabled = data.get('alert_enabled', user.alert_enabled)
    if 'privacy_settings' in data:
        user.privacy_settings = json.dumps(data['privacy_settings'])
    
    db.session.commit()
    return jsonify({'success': True, 'user': user.to_dict(include_private=True)})

@app.route('/api/auth/delete', methods=['POST'])
def delete_account():
    """删除用户所有数据（符合数据隐私合规要求）"""
    data = request.json
    student_id = data.get('student_id')
    user = User.query.filter_by(student_id=student_id).first()
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    # 级联删除所有关联数据
    Conversation.query.filter_by(user_id=user.id).delete()
    HealthRecord.query.filter_by(user_id=user.id).delete()
    MentalAssessment.query.filter_by(user_id=user.id).delete()
    BMIAssessment.query.filter_by(user_id=user.id).delete()
    ConstitutionAssessment.query.filter_by(user_id=user.id).delete()
    DailyCheckIn.query.filter_by(user_id=user.id).delete()
    UserAchievement.query.filter_by(user_id=user.id).delete()
    from models import RewardRecord, ImageAnalysis
    RewardRecord.query.filter_by(user_id=user.id).delete()
    AlertRecord.query.filter_by(user_id=user.id).delete()
    ImageAnalysis.query.filter_by(user_id=user.id).delete()
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({'success': True, 'message': '账户数据已永久删除'})

# ==================== 核心对话路由 ====================

@app.route('/api/chat', methods=['POST'])
def chat():
    """主对话接口 - 数字人小艺

    设计要点：
      - AI 调用失败时返回 HTTP 200 + {error: ..., content: 兜底回复}
        这样前端 fetch 不会走 catch，能正常显示错误信息，避免"网络错误"误判
      - LLM 错误透传到 content 字段（带 [LLM错误] 前缀），用户能直接看到原因
    """
    data = request.get_json(silent=True) or {}
    student_id = data.get('student_id')
    message = data.get('message')
    # 兜底 session_id：前端可能传 null/undefined/空字符串，都生成新 uuid
    session_id = data.get('session_id') or str(uuid.uuid4())

    if not student_id or not message:
        return jsonify({'error': '缺少参数 student_id 或 message',
                        'content': '请先登录后再发消息～'}), 400

    user = get_or_create_user(student_id)

    # 获取长期记忆摘要
    health_summary = memory_service.get_health_summary(user.id)

    # 通过协调 Agent 处理（coordinator 内部会保存用户消息）
    force_intent = data.get('force_intent')
    try:
        response = coordinator.process(user.id, session_id, message,
                                       force_intent=force_intent)
    except Exception as e:
        # 协调 Agent 出错也要返回 200，给用户友好提示
        print(f"[chat] coordinator.process 异常: {type(e).__name__}: {e}")
        import traceback; traceback.print_exc()
        return jsonify({
            'content': f'[系统错误] 调度失败：{str(e)}',
            'intent': 'error',
            'session_id': session_id,
            'error': str(e),
        })

    # 添加积分
    try:
        reward_service.add_points(user.id, 'chat', description='对话互动')
    except Exception:
        pass  # 积分失败不影响主流程

    # 添加长期记忆信息到响应
    response['session_id'] = session_id
    response['health_summary'] = health_summary

    # 检测 AI 是否报错（带 [LLM错误] 前缀）
    content = response.get('content', '')
    if isinstance(content, str) and content.startswith('[LLM错误]'):
        response['error'] = content
        response['intent'] = response.get('intent', 'error')

    return jsonify(response)

@app.route('/api/chat/history', methods=['GET'])
def chat_history():
    """获取对话历史"""
    student_id = request.args.get('student_id')
    session_id = request.args.get('session_id')
    days = int(request.args.get('days', 30))
    
    user = User.query.filter_by(student_id=student_id).first()
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    history = memory_service.get_recent_messages(user.id, session_id, days=days)
    return jsonify({'history': history})

# ==================== 中医路由 ====================

@app.route('/api/tcm/food', methods=['POST'])
def tcm_food():
    data = request.json
    student_id = data.get('student_id')
    condition = data.get('condition')
    constitution = data.get('constitution')
    session_id = data.get('session_id', str(uuid.uuid4()))
    
    user = get_or_create_user(student_id)
    response = tcm_agent.recommend_food(user.id, session_id, condition, constitution)
    return jsonify(response)

@app.route('/api/tcm/constitution/quiz', methods=['GET'])
def constitution_quiz():
    """获取体质辨识问卷（从35题题库中随机抽取10题，每次出题不同）

    注意：选项顺序不打乱，以保留 weights 与选项位置的映射关系。
    """
    import random
    quiz_path = os.path.join(get_data_dir(), 'constitution_quiz.json')
    try:
        with open(quiz_path, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
        all_questions = data.get('questions', data) if isinstance(data, dict) else data
        # 随机抽取10题（题库共35题），保证每次测评题目组合不同
        quiz = random.sample(all_questions, 10) if len(all_questions) >= 10 else all_questions
        return jsonify({'quiz': quiz, 'total': len(all_questions), 'sampled': len(quiz)})
    except Exception as e:
        return jsonify({'error': f'加载问卷失败: {str(e)}'}), 500

@app.route('/api/tcm/constitution/assess', methods=['POST'])
def constitution_assess():
    """体质辨识评估"""
    data = request.json
    student_id = data.get('student_id')
    answers = data.get('answers', [])
    session_id = data.get('session_id', str(uuid.uuid4()))
    
    user = get_or_create_user(student_id)
    result = tcm_agent.assess_constitution(user.id, session_id, answers)
    
    # 添加积分和成就检查
    if result.get('success'):
        reward_service.add_points(user.id, 'constitution_test', description='完成体质辨识测试')
        reward_service.check_assessment_achievements(user.id, 'constitution')
    
    return jsonify(result)

@app.route('/api/tcm/constitution/history', methods=['GET'])
def constitution_history():
    """获取体质辨识历史"""
    student_id = request.args.get('student_id')
    user = User.query.filter_by(student_id=student_id).first()
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    records = ConstitutionAssessment.query.filter_by(user_id=user.id).order_by(
        ConstitutionAssessment.created_at.desc()
    ).limit(20).all()
    return jsonify({'history': [r.to_dict() for r in records]})

# ==================== 心理健康路由 ====================

@app.route('/api/mental/assessments', methods=['GET'])
def mental_assessments():
    student_id = request.args.get('student_id')
    user = User.query.filter_by(student_id=student_id).first()
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    history = mental_agent.get_assessment_history(user.id)
    return jsonify({'assessments': history})

@app.route('/api/mental/alerts', methods=['GET'])
def mental_alerts():
    """获取预警记录（辅导员用）"""
    student_id = request.args.get('student_id')
    user = User.query.filter_by(student_id=student_id).first()
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    alerts = AlertRecord.query.filter_by(user_id=user.id).order_by(AlertRecord.created_at.desc()).all()
    return jsonify({'alerts': [a.to_dict() for a in alerts]})

@app.route('/api/mental/score', methods=['GET'])
def get_mental_score():
    """获取用户心理状态评分"""
    student_id = request.args.get('student_id')
    user = User.query.filter_by(student_id=student_id).first()
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    return jsonify({
        'mental_score': user.mental_score,
        'mental_score_source': user.mental_score_source,
        'mental_score_updated_at': user.mental_score_updated_at.isoformat() if user.mental_score_updated_at else None,
        'alert_enabled': user.alert_enabled
    })

@app.route('/api/mental/score', methods=['POST'])
def update_mental_score():
    """更新用户心理状态评分"""
    data = request.json
    student_id = data.get('student_id')
    score = data.get('mental_score')
    source = data.get('source', 'ai_chat')
    
    user = User.query.filter_by(student_id=student_id).first()
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    if score is not None:
        user.mental_score = int(score)
        user.mental_score_source = source
        user.mental_score_updated_at = datetime.utcnow()
        db.session.commit()
    
    return jsonify({
        'success': True,
        'mental_score': user.mental_score,
        'mental_score_source': user.mental_score_source
    })

@app.route('/api/mental/quiz', methods=['GET'])
def mental_quiz():
    """获取心理状态测评问卷（从题库随机抽取20题，每次出题不同）

    题库共50题覆盖五个维度，每次随机抽20题以减轻答题负担同时保证评估准确性。
    """
    import random
    quiz_path = os.path.join(get_data_dir(), 'mental_quiz.json')
    try:
        with open(quiz_path, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
        all_questions = data.get('questions', data) if isinstance(data, dict) else data
        quiz = random.sample(all_questions, 20) if len(all_questions) >= 20 else all_questions
        return jsonify({'quiz': quiz, 'total': len(all_questions), 'sampled': len(quiz)})
    except Exception as e:
        return jsonify({'error': f'加载问卷失败: {str(e)}'}), 500

@app.route('/api/mental/quiz/assess', methods=['POST'])
def mental_quiz_assess():
    """心理状态问卷测评"""
    data = request.json
    student_id = data.get('student_id')
    answers = data.get('answers', [])
    session_id = data.get('session_id', str(uuid.uuid4()))
    
    user = get_or_create_user(student_id)
    result = mental_agent.assess_mental_quiz(user.id, session_id, answers)
    
    # 更新用户心理评分
    if result.get('success') and 'overall_score' in result:
        user.mental_score = result['overall_score']
        user.mental_score_source = 'quiz'
        user.mental_score_updated_at = datetime.utcnow()
        db.session.commit()
    
    # 添加积分和成就检查
    if result.get('success'):
        reward_service.add_points(user.id, 'mental_test', description='完成心理状态测试')
        reward_service.check_assessment_achievements(user.id, 'mental')
    
    return jsonify(result)

# ==================== 诊断路由 ====================

@app.route('/api/diagnosis/bmi', methods=['POST'])
def diagnosis_bmi():
    data = request.json
    student_id = data.get('student_id')
    try:
        height = float(data.get('height', 0))
        weight = float(data.get('weight', 0))
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': '身高体重必须为数字'}), 400
    if height <= 0 or weight <= 0:
        return jsonify({'success': False, 'message': '身高体重必须大于0'}), 400
    if height > 300 or weight > 500:
        return jsonify({'success': False, 'message': '请输入合理的身高体重值'}), 400
    gender = data.get('gender', 'male')
    session_id = data.get('session_id', str(uuid.uuid4()))
    
    user = get_or_create_user(student_id)
    response = diagnosis_agent.assess_bmi(user.id, session_id, height, weight, gender)
    
    # 添加积分和成就检查
    if response.get('success'):
        reward_service.add_points(user.id, 'bmi_analysis', description='BMI健康分析')
        reward_service.check_assessment_achievements(user.id, 'bmi')
    
    return jsonify(response)

@app.route('/api/diagnosis/bmi/history', methods=['GET'])
def bmi_history():
    """获取BMI评估历史"""
    student_id = request.args.get('student_id')
    user = User.query.filter_by(student_id=student_id).first()
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    records = BMIAssessment.query.filter_by(user_id=user.id).order_by(
        BMIAssessment.created_at.desc()
    ).limit(20).all()
    return jsonify({'history': [r.to_dict() for r in records]})

# ==================== 多模态路由 ====================

@app.route('/api/upload/image', methods=['POST'])
def upload_image():
    """上传图片进行分析"""
    if 'image' not in request.files:
        return jsonify({'error': '没有图片文件'}), 400
    
    file = request.files['image']
    image_type = request.form.get('image_type', 'tongue')  # tongue/meal
    student_id = request.form.get('student_id')
    session_id = request.form.get('session_id', str(uuid.uuid4()))
    
    if file.filename == '':
        return jsonify({'error': '未选择文件'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        user = get_or_create_user(student_id)
        
        # 分析图片
        if image_type == 'tongue':
            result = tcm_agent.analyze_tongue(user.id, session_id, filepath)
        else:
            result = tcm_agent.analyze_meal(user.id, session_id, filepath)
        
        result['image_path'] = f'/uploads/images/{filename}'
        
        # 上传图片积分
        reward_service.add_points(user.id, 'image_upload', description='上传舌象/餐食图片')
        
        return jsonify(result)
    
    return jsonify({'error': '不支持的文件类型'}), 400

# ==================== 激励路由 ====================

@app.route('/api/rewards/stats', methods=['GET'])
def rewards_stats():
    student_id = request.args.get('student_id')
    user = User.query.filter_by(student_id=student_id).first()
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    stats = reward_service.get_stats(user.id)
    return jsonify(stats)

@app.route('/api/rewards/history', methods=['GET'])
def rewards_history():
    student_id = request.args.get('student_id')
    user = User.query.filter_by(student_id=student_id).first()
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    history = reward_service.get_history(user.id)
    return jsonify({'history': history})

@app.route('/api/rewards/leaderboard', methods=['GET'])
def rewards_leaderboard():
    leaderboard = reward_service.get_leaderboard()
    return jsonify({'leaderboard': leaderboard})

@app.route('/api/rewards/overview', methods=['GET'])
def rewards_overview():
    """获取积分中心概览"""
    student_id = request.args.get('student_id')
    user = User.query.filter_by(student_id=student_id).first()
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    overview = reward_service.get_rewards_overview(user.id)
    return jsonify(overview)

@app.route('/api/rewards/achievements', methods=['GET'])
def rewards_achievements():
    """获取成就列表及解锁状态"""
    student_id = request.args.get('student_id')
    user = User.query.filter_by(student_id=student_id).first()
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    achievements = reward_service.get_achievement_status(user.id)
    return jsonify({'achievements': achievements})

# ==================== 积分商城路由 ====================

@app.route('/api/rewards/shop', methods=['GET'])
def rewards_shop():
    student_id = request.args.get('student_id')
    user = User.query.filter_by(student_id=student_id).first()
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    items = reward_service.get_shop_items(user.id)
    return jsonify({'items': items, 'user_points': user.total_points})

@app.route('/api/rewards/exchange', methods=['POST'])
def rewards_exchange():
    data = request.json
    student_id = data.get('student_id')
    item_id = data.get('item_id')
    
    user = User.query.filter_by(student_id=student_id).first()
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    result = reward_service.exchange(user.id, item_id)
    return jsonify(result)

@app.route('/api/rewards/exchange/history', methods=['GET'])
def rewards_exchange_history():
    student_id = request.args.get('student_id')
    user = User.query.filter_by(student_id=student_id).first()
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    history = reward_service.get_exchange_history(user.id)
    return jsonify({'history': history})

# ==================== 每日打卡路由 ====================

@app.route('/api/checkin', methods=['POST'])
def daily_checkin():
    """每日健康打卡（多任务版）"""
    data = request.json
    student_id = data.get('student_id')
    
    user = User.query.filter_by(student_id=student_id).first()
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    result = reward_service.perform_daily_checkin(
        user.id,
        breakfast_done=data.get('breakfast_done'),
        lunch_done=data.get('lunch_done'),
        dinner_done=data.get('dinner_done'),
        exercise_minutes=data.get('exercise_minutes'),
        water_cups=data.get('water_cups'),
        sleep_hours=data.get('sleep_hours'),
        mood_score=data.get('mood_score'),
        notes=data.get('notes')
    )
    return jsonify(result)

@app.route('/api/checkin/status', methods=['GET'])
def checkin_status():
    """获取打卡状态"""
    student_id = request.args.get('student_id')
    user = User.query.filter_by(student_id=student_id).first()
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    status = reward_service.get_checkin_status(user.id)
    return jsonify(status)

@app.route('/api/checkin/history', methods=['GET'])
def checkin_history():
    """获取打卡历史"""
    student_id = request.args.get('student_id')
    days = int(request.args.get('days', 30))
    user = User.query.filter_by(student_id=student_id).first()
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    from datetime import timedelta
    start_date = datetime.utcnow().date() - timedelta(days=days)
    records = DailyCheckIn.query.filter(
        DailyCheckIn.user_id == user.id,
        DailyCheckIn.checkin_date >= start_date
    ).order_by(DailyCheckIn.checkin_date.desc()).all()
    return jsonify({'success': True, 'history': [r.to_dict() for r in records]})

# ==================== 医案溯源路由 ====================

def load_cases():
    """加载医案数据"""
    case_path = os.path.join(get_data_dir(), 'cases.json')
    try:
        with open(case_path, 'r', encoding='utf-8-sig') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载医案失败: {e}")
        return {"cases": [], "categories": []}

@app.route('/api/tcm/case/<case_id>', methods=['GET'])
def get_medical_case(case_id):
    """获取医案详情"""
    data = load_cases()
    
    for case in data.get('cases', []):
        if case.get('case_id') == case_id:
            return jsonify({
                'success': True,
                'case': {
                    'case_id': case.get('case_id'),
                    'patient_info': case.get('patient_info', {}),
                    'chief_complaint': case.get('chief_complaint', ''),
                    'present_illness': case.get('present_illness', ''),
                    'physical_examination': case.get('physical_examination', {}),
                    'diagnosis': case.get('diagnosis', {}),
                    'treatment': case.get('treatment', {}),
                    'outcome': case.get('outcome', ''),
                    'follow_up': case.get('follow_up', ''),
                    'source': case.get('source', '中医病例数据库'),
                    'ai_learning_points': case.get('ai_learning_points', '')
                }
            })
    
    return jsonify({'success': False, 'message': '医案不存在'}), 404

@app.route('/api/tcm/cases', methods=['GET'])
def list_medical_cases():
    """获取医案列表（支持分页、分类筛选）"""
    data = load_cases()
    category = request.args.get('category', '')
    keyword = request.args.get('keyword', '').lower()
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 20))
    
    cases = data.get('cases', [])
    
    # 分类筛选
    if category:
        cases = [c for c in cases if c.get('diagnosis', {}).get('western_diagnosis', '') == category 
                 or category in c.get('diagnosis', {}).get('disease', '')]
    
    # 关键词搜索
    if keyword:
        filtered = []
        for case in cases:
            search_text = json.dumps(case, ensure_ascii=False).lower()
            if keyword in search_text:
                filtered.append(case)
        cases = filtered
    
    # 分页
    total = len(cases)
    start = (page - 1) * page_size
    end = start + page_size
    cases_page = cases[start:end]
    
    result = []
    for case in cases_page:
        result.append({
            'case_id': case.get('case_id'),
            'chief_complaint': case.get('chief_complaint', ''),
            'disease': case.get('diagnosis', {}).get('disease', ''),
            'syndrome': case.get('diagnosis', {}).get('syndrome', ''),
            'category': case.get('diagnosis', {}).get('western_diagnosis', ''),
            'patient_age': case.get('patient_info', {}).get('age', ''),
            'patient_gender': case.get('patient_info', {}).get('gender', '')
        })
    
    return jsonify({
        'success': True, 
        'cases': result,
        'total': total,
        'page': page,
        'page_size': page_size,
        'categories': data.get('categories', [])
    })

@app.route('/api/tcm/cases/search', methods=['GET'])
def search_medical_cases():
    """智能搜索医案 - 支持症状、病名、证型、方剂等多维度检索"""
    data = load_cases()
    query = request.args.get('q', '').lower()
    intent = request.args.get('intent', 'general')  # general, symptom, disease, syndrome, formula
    limit = int(request.args.get('limit', 5))
    
    if not query:
        return jsonify({'success': True, 'cases': [], 'message': '请输入搜索关键词'})
    
    cases = data.get('cases', [])
    scored_cases = []
    
    for case in cases:
        score = 0
        match_reasons = []
        
        # 构建可搜索文本
        searchable_fields = {
            'chief_complaint': case.get('chief_complaint', ''),
            'present_illness': case.get('present_illness', ''),
            'disease': case.get('diagnosis', {}).get('disease', ''),
            'syndrome': case.get('diagnosis', {}).get('syndrome', ''),
            'herbal_medicine': case.get('treatment', {}).get('herbal_medicine', ''),
            'dietary_advice': case.get('treatment', {}).get('dietary_advice', ''),
            'lifestyle_advice': case.get('treatment', {}).get('lifestyle_advice', ''),
        }
        
        # 症状匹配（主诉、现病史权重最高）
        if intent in ['general', 'symptom']:
            symptom_text = (searchable_fields['chief_complaint'] + ' ' + searchable_fields['present_illness']).lower()
            if query in symptom_text:
                score += 10
                match_reasons.append('症状匹配')
        
        # 病名匹配
        if intent in ['general', 'disease']:
            if query in searchable_fields['disease'].lower():
                score += 8
                match_reasons.append('病名匹配')
        
        # 证型匹配
        if intent in ['general', 'syndrome']:
            if query in searchable_fields['syndrome'].lower():
                score += 8
                match_reasons.append('证型匹配')
        
        # 方剂匹配
        if intent in ['general', 'formula']:
            if query in searchable_fields['herbal_medicine'].lower():
                score += 6
                match_reasons.append('方剂匹配')
        
        # 通用全文匹配
        if score == 0:
            full_text = ' '.join(searchable_fields.values()).lower()
            if query in full_text:
                score += 3
                match_reasons.append('全文匹配')
        
        if score > 0:
            scored_cases.append({
                'case': case,
                'score': score,
                'match_reasons': match_reasons
            })
    
    # 按分数排序
    scored_cases.sort(key=lambda x: x['score'], reverse=True)
    
    # 返回前 N 个结果
    results = []
    for item in scored_cases[:limit]:
        case = item['case']
        results.append({
            'case_id': case.get('case_id'),
            'chief_complaint': case.get('chief_complaint', ''),
            'disease': case.get('diagnosis', {}).get('disease', ''),
            'syndrome': case.get('diagnosis', {}).get('syndrome', ''),
            'herbal_medicine': case.get('treatment', {}).get('herbal_medicine', '')[:200],
            'score': item['score'],
            'match_reasons': item['match_reasons'],
            'patient_info': case.get('patient_info', {}),
        })
    
    return jsonify({
        'success': True,
        'cases': results,
        'query': query,
        'intent': intent,
        'total': len(scored_cases)
    })

@app.route('/api/tcm/cases/categories', methods=['GET'])
def get_case_categories():
    """获取医案分类"""
    data = load_cases()
    return jsonify({
        'success': True,
        'categories': data.get('categories', [])
    })

@app.route('/api/tcm/cases/related', methods=['POST'])
def get_related_cases():
    """根据症状描述获取相关医案（用于AI回答参考）"""
    data = load_cases()
    req = request.get_json(silent=True) or {}
    symptoms = req.get('symptoms', '')
    disease = req.get('disease', '')
    syndrome = req.get('syndrome', '')
    limit = req.get('limit', 3)
    
    cases = data.get('cases', [])
    scored = []
    
    for case in cases:
        score = 0
        reasons = []
        
        case_text = json.dumps(case, ensure_ascii=False).lower()
        
        # 症状匹配
        if symptoms:
            symptom_keywords = [kw.strip() for kw in symptoms.split('，') if kw.strip()]
            for kw in symptom_keywords:
                if kw.lower() in case_text:
                    score += 5
                    reasons.append(f'症状:{kw}')
        
        # 病名匹配
        if disease and disease.lower() in case.get('diagnosis', {}).get('disease', '').lower():
            score += 10
            reasons.append(f'病名:{disease}')
        
        # 证型匹配
        if syndrome and syndrome.lower() in case.get('diagnosis', {}).get('syndrome', '').lower():
            score += 10
            reasons.append(f'证型:{syndrome}')
        
        if score > 0:
            scored.append((score, case, reasons))
    
    scored.sort(key=lambda x: x[0], reverse=True)
    
    results = []
    for score, case, reasons in scored[:limit]:
        results.append({
            'case_id': case.get('case_id'),
            'chief_complaint': case.get('chief_complaint', ''),
            'disease': case.get('diagnosis', {}).get('disease', ''),
            'syndrome': case.get('diagnosis', {}).get('syndrome', ''),
            'herbal_medicine': case.get('treatment', {}).get('herbal_medicine', ''),
            'dietary_advice': case.get('treatment', {}).get('dietary_advice', ''),
            'outcome': case.get('outcome', ''),
            'score': score,
            'match_reasons': reasons
        })
    
    return jsonify({'success': True, 'cases': results})

# ==================== 膳食推荐路由 ====================

@app.route('/api/diet/categories', methods=['GET'])
def get_food_categories():
    """获取食物分类"""
    categories = FoodCategory.query.order_by(FoodCategory.sort_order).all()
    return jsonify({
        'success': True,
        'categories': [c.to_dict() for c in categories]
    })

@app.route('/api/diet/foods', methods=['GET'])
def list_foods():
    """获取食物列表（支持分类、标签、餐次筛选）"""
    category_id = request.args.get('category_id', type=int)
    meal_type = request.args.get('meal_type', '')  # breakfast/lunch/dinner/snack
    tags = request.args.get('tags', '')  # 逗号分隔
    constitution = request.args.get('constitution', '')
    keyword = request.args.get('keyword', '')
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 50))
    
    query = FoodItem.query.filter_by(is_active=True)
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    if meal_type:
        query = query.filter(FoodItem.meal_types.contains(meal_type))
    
    if tags:
        tag_list = [t.strip() for t in tags.split(',') if t.strip()]
        for tag in tag_list:
            query = query.filter(FoodItem.tags.contains(tag))
    
    if keyword:
        query = query.filter(FoodItem.name.contains(keyword))
    
    foods = query.order_by(FoodItem.name).all()
    
    # 按体质筛选
    if constitution:
        filtered = []
        for f in foods:
            avoid = f.avoid_constitutions.split(',') if f.avoid_constitutions else []
            suitable = f.suitable_constitutions.split(',') if f.suitable_constitutions else []
            if constitution in avoid:
                continue
            if not suitable or constitution in suitable:
                filtered.append(f)
        foods = filtered
    
    # 分页
    total = len(foods)
    start = (page - 1) * page_size
    end = start + page_size
    foods_page = foods[start:end]
    
    return jsonify({
        'success': True,
        'foods': [f.to_dict() for f in foods_page],
        'total': total,
        'page': page,
        'page_size': page_size
    })

@app.route('/api/diet/recommend', methods=['POST'])
def recommend_diet():
    """算法推荐膳食"""
    data = request.get_json(silent=True) or {}
    student_id = data.get('student_id')
    goal = data.get('goal', 'maintain')  # maintain/lose_weight/gain_muscle/heat_relief/warming/spleen_stomach
    user_tags = data.get('tags', [])  # 用户偏好标签
    constitution = data.get('constitution', '')
    notes = data.get('notes', '')
    use_bmi_data = data.get('use_bmi_data', True)  # 是否使用用户BMI数据
    
    if not student_id:
        return jsonify({'success': False, 'message': '缺少student_id'}), 400
    
    user = User.query.filter_by(student_id=student_id).first()
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'}), 404
    
    # 如果使用BMI数据，自动填充用户身高体重
    if use_bmi_data:
        latest_bmi = BMIAssessment.query.filter_by(user_id=user.id).order_by(BMIAssessment.created_at.desc()).first()
        if latest_bmi and not user.height:
            user.height = latest_bmi.height
        if latest_bmi and not user.weight:
            user.weight = latest_bmi.weight
        if latest_bmi and not user.gender:
            user.gender = latest_bmi.gender
    
    # 获取最新体质
    if not constitution:
        latest_constitution = ConstitutionAssessment.query.filter_by(user_id=user.id).order_by(ConstitutionAssessment.created_at.desc()).first()
        if latest_constitution:
            constitution = latest_constitution.primary_type_label
    
    try:
        plan = diet_service.generate_full_day_plan(user, goal, user_tags, constitution, notes)
        plan['constitution'] = constitution
        plan['goal'] = goal
        plan['notes'] = notes
        
        # 保存推荐记录
        rec = diet_service.save_recommendation(user.id, plan, goal, 'algorithm')
        plan['recommendation_id'] = rec.id
        
        return jsonify({'success': True, 'plan': plan})
    except Exception as e:
        return jsonify({'success': False, 'message': f'推荐失败: {str(e)}'}), 500

@app.route('/api/diet/recommend/ai', methods=['POST'])
def recommend_diet_ai():
    """AI精细化膳食推荐"""
    data = request.get_json(silent=True) or {}
    student_id = data.get('student_id')
    goal = data.get('goal', 'maintain')
    user_tags = data.get('tags', [])
    constitution = data.get('constitution', '')
    notes = data.get('notes', '')
    use_bmi_data = data.get('use_bmi_data', True)
    
    if not student_id:
        return jsonify({'success': False, 'message': '缺少student_id'}), 400
    
    user = User.query.filter_by(student_id=student_id).first()
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'}), 404
    
    if use_bmi_data:
        latest_bmi = BMIAssessment.query.filter_by(user_id=user.id).order_by(BMIAssessment.created_at.desc()).first()
        if latest_bmi and not user.height:
            user.height = latest_bmi.height
        if latest_bmi and not user.weight:
            user.weight = latest_bmi.weight
        if latest_bmi and not user.gender:
            user.gender = latest_bmi.gender
    
    if not constitution:
        latest_constitution = ConstitutionAssessment.query.filter_by(user_id=user.id).order_by(ConstitutionAssessment.created_at.desc()).first()
        if latest_constitution:
            constitution = latest_constitution.primary_type_label
    
    try:
        # 先生成算法推荐作为基础
        plan = diet_service.generate_full_day_plan(user, goal, user_tags, constitution, notes)
        plan['constitution'] = constitution
        plan['goal'] = goal
        plan['notes'] = notes
        
        # AI精细化调整
        ai_prompt = f"""你是营养师兼中医食疗专家，请根据以下基础推荐方案，结合用户需求进行精细化调整：

【用户画像】：
- 性别：{user.gender or '未知'}，身高：{user.height or '未知'}cm，体重：{user.weight or '未知'}kg
- BMI：{plan.get('bmi', '未知')}（{plan.get('bmi_category', '未知')}）
- 体质：{constitution or '未知'}
- 目标：{goal}
- 标签：{', '.join(user_tags) if user_tags else '无'}
- 备注：{notes or '无'}

【算法基础推荐】：
- 目标热量：{plan.get('target_calories')} kcal
- 早餐：{plan.get('breakfast_calories')} kcal
- 午餐：{plan.get('lunch_calories')} kcal
- 晚餐：{plan.get('dinner_calories')} kcal
- 加餐：{plan.get('snack_calories')} kcal

请输出JSON格式：
{{
  "adjustments": "调整说明",
  "breakfast": [{{"name": "菜名", "reason": "调整理由", "calories": 热量}}],
  "lunch": [...],
  "dinner": [...],
  "snack": [...],
  "tcm_advice": "中医食疗建议",
  "precautions": "注意事项"
}}"""
        
        ai_response = llm_service.chat([
            {"role": "system", "content": "你是专业营养师和中医食疗专家，擅长根据体质、目标制定个性化食谱。"},
            {"role": "user", "content": ai_prompt}
        ], temperature=0.7, max_tokens=2000)
        
        # 解析AI回复
        ai_data = None
        try:
            import re
            match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if match:
                ai_data = json.loads(match.group())
        except Exception:
            ai_data = {"raw_response": ai_response}
        
        plan['ai_recommendation'] = ai_data
        plan['constitution'] = constitution
        plan['goal'] = goal
        plan['notes'] = notes
        
        # 保存推荐记录
        rec = diet_service.save_recommendation(user.id, plan, goal, 'ai', ai_response)
        plan['recommendation_id'] = rec.id
        
        return jsonify({'success': True, 'plan': plan})
    except Exception as e:
        return jsonify({'success': False, 'message': f'AI推荐失败: {str(e)}'}), 500

@app.route('/api/diet/history', methods=['GET'])
def diet_history():
    """获取膳食推荐历史"""
    student_id = request.args.get('student_id')
    limit = int(request.args.get('limit', 20))
    
    user = User.query.filter_by(student_id=student_id).first()
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'}), 404
    
    recs = DietRecommendation.query.filter_by(user_id=user.id).order_by(
        DietRecommendation.created_at.desc()
    ).limit(limit).all()
    
    return jsonify({
        'success': True,
        'history': [r.to_dict() for r in recs]
    })

@app.route('/api/diet/recommendation/<int:rec_id>', methods=['GET'])
def get_diet_recommendation(rec_id):
    """获取单条推荐详情"""
    rec = DietRecommendation.query.get(rec_id)
    if not rec:
        return jsonify({'success': False, 'message': '推荐不存在'}), 404
    return jsonify({'success': True, 'recommendation': rec.to_dict()})

@app.route('/api/diet/bmi-sync', methods=['POST'])
def sync_bmi_to_diet():
    """BMI数据同步到膳食推荐"""
    data = request.get_json(silent=True) or {}
    student_id = data.get('student_id')
    
    user = User.query.filter_by(student_id=student_id).first()
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'}), 404
    
    latest_bmi = BMIAssessment.query.filter_by(user_id=user.id).order_by(BMIAssessment.created_at.desc()).first()
    
    if not latest_bmi:
        return jsonify({'success': False, 'message': '暂无BMI数据'}), 404
    
    # 更新用户基础数据
    user.height = latest_bmi.height
    user.weight = latest_bmi.weight
    user.gender = latest_bmi.gender
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'BMI数据已同步',
        'data': {
            'height': user.height,
            'weight': user.weight,
            'gender': user.gender,
            'bmi': latest_bmi.bmi_value,
            'bmi_category': latest_bmi.bmi_category_label
        }
    })

# ==================== 健康资讯路由 ====================

@app.route('/api/community/feed', methods=['GET'])
def community_feed():
    """获取健康资讯Feed"""
    category = request.args.get('category', '')
    
    feed = Config.HEALTH_NEWS_FEED
    
    if category:
        feed = [item for item in feed if item.get('category') == category]
    
    # 返回摘要列表（不含完整内容）
    summaries = [{
        'id': item['id'],
        'category': item['category'],
        'title': item['title'],
        'summary': item['summary'],
        'source': item['source'],
        'tags': item.get('tags', []),
        'image_icon': item.get('image_icon', 'fa-newspaper')
    } for item in feed]
    
    return jsonify({'feed': summaries, 'categories': list(set(item['category'] for item in Config.HEALTH_NEWS_FEED))})

@app.route('/api/community/feed/<feed_id>', methods=['GET'])
def community_feed_detail(feed_id):
    """获取健康资讯详情"""
    for item in Config.HEALTH_NEWS_FEED:
        if item['id'] == feed_id:
            # 阅读资讯积分
            student_id = request.args.get('student_id')
            if student_id:
                user = User.query.filter_by(student_id=student_id).first()
                if user:
                    reward_service.add_points(user.id, 'read_article', description='阅读健康资讯')
            return jsonify({'success': True, 'article': item})
    return jsonify({'success': False, 'message': '文章不存在'}), 404

@app.route('/api/community/links', methods=['GET'])
def community_links():
    """保留原有外链接口（兼容）"""
    return jsonify({'links': Config.COMMUNITY_LINKS})

# ==================== 健康档案路由 ====================

@app.route('/api/health/records', methods=['GET'])
def health_records():
    student_id = request.args.get('student_id')
    user = User.query.filter_by(student_id=student_id).first()
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    records = HealthRecord.query.filter_by(user_id=user.id).order_by(HealthRecord.record_date.desc()).all()
    decrypt_fn = privacy_service.decrypt if privacy_service else None
    return jsonify({'records': [r.to_dict(decrypt_fn=decrypt_fn) for r in records]})

# ==================== 静态文件服务 ====================

@app.route('/uploads/images/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/')
def index():
    return send_from_directory('../frontend', 'index.html')

@app.route('/css/<path:filename>')
def serve_css(filename):
    return send_from_directory('../frontend/css', filename)

@app.route('/js/<path:filename>')
def serve_js(filename):
    return send_from_directory('../frontend/js', filename)

@app.route('/img/<path:filename>')
def serve_img(filename):
    return send_from_directory('../frontend/img', filename)

# ==================== SSE流式聊天 endpoint ====================
@app.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    """SSE 流式聊天响应 - 简化版

    设计要点：
      1. 把整个回复作为一个 SSE 帧发送，不句分割
         → 前端处理逻辑简单（不需 buffer 复杂解析），避免 SyntaxError 之类 bug
      2. 后端先调 coordinator 拿到完整回复，再一次性 yield
         → AI 调用失败时直接在响应里返回 error 帧，前端能识别
      3. 前端拿到完整回复后用打字机效果逐字渲染（前端逻辑）
    """
    data = request.get_json(silent=True) or {}
    student_id = data.get('student_id')
    message = data.get('message')
    # 兜底 session_id：同 /api/chat 路由，避免 null 触发数据库约束
    session_id = data.get('session_id') or str(uuid.uuid4())

    def error_gen(msg):
        yield f"data: {json.dumps({'error': msg}, ensure_ascii=False)}\n\n"

    if not student_id or not message:
        return Response(error_gen('缺少参数 student_id 或 message'),
                        mimetype='text/event-stream')

    user = get_or_create_user(student_id)
    health_summary = memory_service.get_health_summary(user.id)
    force_intent = data.get('force_intent')

    # 关键：在请求上下文里同步调用 coordinator.process，避免在 generator
    # 异步执行时 Flask 上下文已销毁（"Working outside of application context"）
    try:
        response = coordinator.process(user.id, session_id, message,
                                       force_intent=force_intent)
    except Exception as e:
        print(f"[chat_stream] coordinator.process 异常: "
              f"{type(e).__name__}: {e}")
        import traceback; traceback.print_exc()
        err_payload = {
            'error': f'调度失败：{str(e)}',
            'chunk': f'[系统错误] 调度失败：{str(e)}',
            'done': True,
        }

        def err_gen():
            yield f"data: {json.dumps({'status': 'thinking'}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps(err_payload, ensure_ascii=False)}\n\n"
        return Response(err_gen(), mimetype='text/event-stream')

    content = response.get('content', '')
    is_error = isinstance(content, str) and content.startswith('[LLM错误]')

    # 把所有需要的字段预先计算好，generator 只负责 yield（不再访问任何 Flask 全局对象）
    final_payload = {
        'chunk': content,
        'done': True,
        'full_content': content,
        'session_id': response.get('session_id', session_id),
        'intent': response.get('intent', 'general'),
        'references': response.get('references', []),
        'mental_assessment': response.get('mental_assessment'),
        'alert_triggered': response.get('alert_triggered'),
        'health_summary': health_summary,
    }
    if is_error:
        final_payload['error'] = content
        final_payload['intent'] = 'error'

    # 预先生成所有 SSE 帧（确保上下文销毁后 generator 仍可正常 yield）
    thinking_frame = f"data: {json.dumps({'status': 'thinking'}, ensure_ascii=False)}\n\n"
    final_frame = f"data: {json.dumps(final_payload, ensure_ascii=False)}\n\n"

    def generate():
        yield thinking_frame
        # 模拟"思考"延迟（500ms），让前端有"AI 在思考"的视觉感受
        import time as _t; _t.sleep(0.5)
        yield final_frame

    return Response(generate(), mimetype='text/event-stream')


# ==================== 诊断报告导出路由 ====================
@app.route('/api/diagnosis/export', methods=['POST'])
def export_diagnosis():
    """导出诊断报告 - 生成可打印的HTML/PDF格式"""
    data = request.json
    student_id = data.get('student_id')
    session_id = data.get('session_id')
    content = data.get('content', '')
    answers = data.get('answers', {})
    
    user = User.query.filter_by(student_id=student_id).first()
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    # 生成导出报告
    from datetime import datetime
    report_html = generate_diagnosis_report(user, answers, content)
    
    return jsonify({
        'success': True,
        'report_html': report_html,
        'export_time': datetime.utcnow().isoformat()
    })


def generate_diagnosis_report(user, answers, content):
    """生成诊断报告HTML"""
    now = datetime.utcnow().strftime('%Y年%m月%d日 %H:%M')
    
    # 安全地格式化答案
    def fmt_answer(key, default='未填写'):
        return answers.get(key, default) if answers else default
    
    return f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>脉衡界诊断报告</title>
    <style>
        body {{ font-family: 'Noto Sans SC', sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; color: #334155; }}
        .header {{ text-align: center; border-bottom: 2px solid #2563eb; padding-bottom: 20px; margin-bottom: 30px; }}
        .header h1 {{ color: #2563eb; margin-bottom: 5px; }}
        .header .subtitle {{ color: #64748b; font-size: 14px; }}
        .section {{ margin-bottom: 25px; padding: 15px; background: #f8fafc; border-radius: 10px; }}
        .section-title {{ color: #2563eb; font-weight: 700; font-size: 16px; margin-bottom: 10px; }}
        .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
        .info-item {{ }}
        .info-label {{ font-weight: 600; color: #64748b; }}
        .info-value {{ margin-top: 2px; }}
        .content {{ white-space: pre-wrap; line-height: 1.8; }}
        .footer {{ text-align: center; margin-top: 30px; color: #94a3b8; font-size: 12px; border-top: 1px solid #e2e8f0; padding-top: 15px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📋 脉衡界健康问诊报告</h1>
        <p class="subtitle">校园健康智能体 · 结构化问诊结果</p>
    </div>
    
    <div class="section">
        <div class="section-title">👤 患者信息</div>
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">姓名</div>
                <div class="info-value">{user.username}</div>
            </div>
            <div class="info-item">
                <div class="info-label">学号</div>
                <div class="info-value">{user.student_id}</div>
            </div>
        </div>
    </div>
    
    <div class="section">
        <div class="section-title">📝 问诊记录</div>
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">主要症状</div>
                <div class="info-value">{fmt_answer('Q0')}</div>
            </div>
            <div class="info-item">
                <div class="info-label">症状持续</div>
                <div class="info-value">{fmt_answer('Q1')}</div>
            </div>
            <div class="info-item">
                <div class="info-label">部位位置</div>
                <div class="info-value">{fmt_answer('Q2')}</div>
            </div>
            <div class="info-item">
                <div class="info-label">症状程度</div>
                <div class="info-value">{fmt_answer('Q3')}</div>
            </div>
            <div class="info-item">
                <div class="info-label">伴随症状</div>
                <div class="info-value">{fmt_answer('Q4')}</div>
            </div>
            <div class="info-item">
                <div class="info-label">既往病史</div>
                <div class="info-value">{fmt_answer('Q5')}</div>
            </div>
        </div>
    </div>
    
    <div class="section">
        <div class="section-title">📋 AI诊断建议</div>
        <div class="content">{content.replace(chr(10), '<br>')}</div>
    </div>
    
    <div class="footer">
        <p>脉衡界校园健康智能体 © {now}</p>
        <p>⚠️ 说明：本报告为AI辅助诊断结果，仅供参考。正式诊断请务必前往医院就诊。</p>
    </div>
</body>
</html>
"""


# ==================== 饮食记录路由 ====================

@app.route('/api/diet/log', methods=['POST'])
def add_diet_log():
    """添加饮食记录"""
    data = request.json
    student_id = data.get('student_id')
    
    user = User.query.filter_by(student_id=student_id).first()
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    # 解析记录时间
    log_date_str = data.get('log_date')
    log_time_str = data.get('log_time')
    
    if log_date_str:
        log_date = datetime.strptime(log_date_str, '%Y-%m-%d').date()
    else:
        log_date = datetime.utcnow().date()
    
    if log_time_str:
        log_time = datetime.strptime(log_time_str, '%Y-%m-%d %H:%M:%S')
    else:
        log_time = datetime.utcnow()
    
    # 判断是否为夜宵（21:00-03:00）
    is_late_night = log_time.hour >= 21 or log_time.hour < 3
    
    # 创建饮食记录
    diet_log = DietLog(
        user_id=user.id,
        log_date=log_date,
        log_time=log_time,
        meal_type=data.get('meal_type', 'snack'),
        food_name=data.get('food_name', ''),
        food_item_id=data.get('food_item_id'),
        serving_size=data.get('serving_size', 100),
        serving_count=data.get('serving_count', 1),
        calories=data.get('calories', 0),
        protein=data.get('protein', 0),
        fat=data.get('fat', 0),
        carbs=data.get('carbs', 0),
        fiber=data.get('fiber', 0),
        is_late_night=is_late_night,
        notes=data.get('notes', ''),
        image_path=data.get('image_path')
    )
    
    db.session.add(diet_log)
    
    # 更新每日汇总
    _update_daily_summary(user.id, log_date)
    
    db.session.commit()
    
    # 添加积分奖励
    reward_service.add_points(user.id, 'diet_log', description='记录饮食')
    
    return jsonify({
        'success': True,
        'message': '饮食记录添加成功',
        'log': diet_log.to_dict()
    })


@app.route('/api/diet/logs', methods=['GET'])
def get_diet_logs():
    """获取饮食记录列表"""
    student_id = request.args.get('student_id')
    date_str = request.args.get('date')
    meal_type = request.args.get('meal_type')
    
    user = User.query.filter_by(student_id=student_id).first()
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    query = DietLog.query.filter_by(user_id=user.id)
    
    if date_str:
        log_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        query = query.filter_by(log_date=log_date)
    
    if meal_type:
        query = query.filter_by(meal_type=meal_type)
    
    logs = query.order_by(DietLog.log_time.desc()).limit(100).all()
    
    return jsonify({
        'success': True,
        'logs': [log.to_dict() for log in logs]
    })


@app.route('/api/diet/log/<int:log_id>', methods=['DELETE'])
def delete_diet_log(log_id):
    """删除饮食记录"""
    student_id = request.args.get('student_id')
    
    user = User.query.filter_by(student_id=student_id).first()
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    diet_log = DietLog.query.filter_by(id=log_id, user_id=user.id).first()
    if not diet_log:
        return jsonify({'error': '记录不存在'}), 404
    
    log_date = diet_log.log_date
    db.session.delete(diet_log)
    
    # 更新每日汇总
    _update_daily_summary(user.id, log_date)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': '记录已删除'
    })


@app.route('/api/diet/summary', methods=['GET'])
def get_diet_summary():
    """获取饮食汇总"""
    student_id = request.args.get('student_id')
    date_str = request.args.get('date')
    days = int(request.args.get('days', 7))
    
    user = User.query.filter_by(student_id=student_id).first()
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    if date_str:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        summary = DailyDietSummary.query.filter_by(
            user_id=user.id, summary_date=target_date
        ).first()
        
        if not summary:
            # 尝试创建汇总
            summary = _create_daily_summary(user.id, target_date)
        
        return jsonify({
            'success': True,
            'summary': summary.to_dict() if summary else None
        })
    else:
        # 获取多日汇总
        from datetime import timedelta
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days-1)
        
        summaries = DailyDietSummary.query.filter(
            DailyDietSummary.user_id == user.id,
            DailyDietSummary.summary_date >= start_date,
            DailyDietSummary.summary_date <= end_date
        ).order_by(DailyDietSummary.summary_date.asc()).all()
        
        # 补充没有记录的日期
        summary_dict = {s.summary_date: s for s in summaries}
        result = []
        current_date = start_date
        while current_date <= end_date:
            if current_date in summary_dict:
                result.append(summary_dict[current_date].to_dict())
            else:
                result.append({
                    'summary_date': current_date.isoformat(),
                    'total_calories': 0,
                    'total_protein': 0,
                    'total_fat': 0,
                    'total_carbs': 0,
                    'total_fiber': 0,
                    'breakfast_calories': 0,
                    'lunch_calories': 0,
                    'dinner_calories': 0,
                    'snack_calories': 0,
                    'late_night_count': 0,
                    'late_night_calories': 0,
                })
            current_date += timedelta(days=1)
        
        return jsonify({
            'success': True,
            'summaries': result
        })


@app.route('/api/diet/night-analysis', methods=['GET'])
def get_night_analysis():
    """获取夜宵习惯分析"""
    student_id = request.args.get('student_id')
    days = int(request.args.get('days', 30))
    
    user = User.query.filter_by(student_id=student_id).first()
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    from datetime import timedelta
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days-1)
    
    # 获取夜宵记录
    night_logs = DietLog.query.filter(
        DietLog.user_id == user.id,
        DietLog.is_late_night == True,
        DietLog.log_date >= start_date,
        DietLog.log_date <= end_date
    ).all()
    
    # 统计分析
    total_night_count = len(night_logs)
    total_night_calories = sum(log.calories for log in night_logs)
    avg_night_calories = total_night_calories / days if days > 0 else 0
    
    # 按时间段统计（21:00-23:00, 23:00-01:00, 01:00-03:00）
    time_periods = {
        '21-23': 0,
        '23-01': 0,
        '01-03': 0
    }
    for log in night_logs:
        hour = log.log_time.hour
        if 21 <= hour < 23:
            time_periods['21-23'] += 1
        elif hour >= 23 or hour < 1:
            time_periods['23-01'] += 1
        elif 1 <= hour < 3:
            time_periods['01-03'] += 1
    
    # 按食物类型统计
    food_types = {}
    for log in night_logs:
        food = log.food_name
        if food not in food_types:
            food_types[food] = {'count': 0, 'calories': 0}
        food_types[food]['count'] += 1
        food_types[food]['calories'] += log.calories
    
    # 排序取前5
    top_foods = sorted(food_types.items(), key=lambda x: x[1]['count'], reverse=True)[:5]
    
    # 频率分析（每周几次）
    weeks = days / 7
    weekly_frequency = total_night_count / weeks if weeks > 0 else 0
    
    # 健康评估
    health_level = '正常'
    health_suggestion = '保持良好的作息习惯'
    if weekly_frequency > 5:
        health_level = '严重'
        health_suggestion = '夜宵过于频繁，建议调整作息时间，避免深夜进食'
    elif weekly_frequency > 3:
        health_level = '偏高'
        health_suggestion = '夜宵频率偏高，建议减少深夜进食，选择清淡食物'
    elif weekly_frequency > 1:
        health_level = '一般'
        health_suggestion = '夜宵频率正常，注意选择健康食物'
    
    return jsonify({
        'success': True,
        'analysis': {
            'total_count': total_night_count,
            'total_calories': round(total_night_calories, 1),
            'avg_daily_calories': round(avg_night_calories, 1),
            'weekly_frequency': round(weekly_frequency, 1),
            'time_periods': time_periods,
            'top_foods': [{'name': name, **data} for name, data in top_foods],
            'health_level': health_level,
            'health_suggestion': health_suggestion,
            'days_analyzed': days
        }
    })


@app.route('/api/diet/calories-chart', methods=['GET'])
def get_calories_chart():
    """获取热量可视化数据"""
    student_id = request.args.get('student_id')
    days = int(request.args.get('days', 7))
    
    user = User.query.filter_by(student_id=student_id).first()
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    from datetime import timedelta
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days-1)
    
    # 获取用户的目标热量
    latest_recommendation = DietRecommendation.query.filter_by(
        user_id=user.id
    ).order_by(DietRecommendation.created_at.desc()).first()
    
    target_calories = latest_recommendation.target_calories if latest_recommendation else 2000
    
    # 获取每日汇总
    summaries = DailyDietSummary.query.filter(
        DailyDietSummary.user_id == user.id,
        DailyDietSummary.summary_date >= start_date,
        DailyDietSummary.summary_date <= end_date
    ).order_by(DailyDietSummary.summary_date.asc()).all()
    
    summary_dict = {s.summary_date: s for s in summaries}
    
    chart_data = {
        'labels': [],
        'actual': [],
        'target': [],
        'breakfast': [],
        'lunch': [],
        'dinner': [],
        'snack': [],
        'night': []
    }
    
    current_date = start_date
    while current_date <= end_date:
        chart_data['labels'].append(current_date.strftime('%m/%d'))
        
        if current_date in summary_dict:
            s = summary_dict[current_date]
            chart_data['actual'].append(round(s.total_calories, 0))
            chart_data['breakfast'].append(round(s.breakfast_calories, 0))
            chart_data['lunch'].append(round(s.lunch_calories, 0))
            chart_data['dinner'].append(round(s.dinner_calories, 0))
            chart_data['snack'].append(round(s.snack_calories, 0))
            chart_data['night'].append(round(s.late_night_calories, 0))
        else:
            chart_data['actual'].append(0)
            chart_data['breakfast'].append(0)
            chart_data['lunch'].append(0)
            chart_data['dinner'].append(0)
            chart_data['snack'].append(0)
            chart_data['night'].append(0)
        
        chart_data['target'].append(round(target_calories, 0))
        current_date += timedelta(days=1)
    
    # 计算统计信息
    actual_values = [v for v in chart_data['actual'] if v > 0]
    stats = {
        'avg_calories': round(sum(actual_values) / len(actual_values), 0) if actual_values else 0,
        'max_calories': max(actual_values) if actual_values else 0,
        'min_calories': min(actual_values) if actual_values else 0,
        'total_calories': sum(actual_values),
        'days_recorded': len(actual_values),
        'target_calories': target_calories
    }
    
    return jsonify({
        'success': True,
        'chart_data': chart_data,
        'stats': stats
    })


def _update_daily_summary(user_id, log_date):
    """更新每日饮食汇总"""
    summary = DailyDietSummary.query.filter_by(
        user_id=user_id, summary_date=log_date
    ).first()
    
    if not summary:
        summary = DailyDietSummary(
            user_id=user_id,
            summary_date=log_date
        )
        db.session.add(summary)
    
    # 获取当日所有饮食记录
    logs = DietLog.query.filter_by(
        user_id=user_id, log_date=log_date
    ).all()
    
    # 重置统计
    summary.total_calories = 0
    summary.total_protein = 0
    summary.total_fat = 0
    summary.total_carbs = 0
    summary.total_fiber = 0
    summary.breakfast_calories = 0
    summary.lunch_calories = 0
    summary.dinner_calories = 0
    summary.snack_calories = 0
    summary.late_night_count = 0
    summary.late_night_calories = 0
    summary.breakfast_count = 0
    summary.lunch_count = 0
    summary.dinner_count = 0
    summary.snack_count = 0
    
    # 重新计算
    for log in logs:
        summary.total_calories += log.calories
        summary.total_protein += log.protein
        summary.total_fat += log.fat
        summary.total_carbs += log.carbs
        summary.total_fiber += log.fiber
        
        if log.meal_type == 'breakfast':
            summary.breakfast_calories += log.calories
            summary.breakfast_count += 1
        elif log.meal_type == 'lunch':
            summary.lunch_calories += log.calories
            summary.lunch_count += 1
        elif log.meal_type == 'dinner':
            summary.dinner_calories += log.calories
            summary.dinner_count += 1
        elif log.meal_type == 'snack':
            summary.snack_calories += log.calories
            summary.snack_count += 1
        
        if log.is_late_night:
            summary.late_night_count += 1
            summary.late_night_calories += log.calories


def _create_daily_summary(user_id, log_date):
    """创建每日汇总"""
    _update_daily_summary(user_id, log_date)
    return DailyDietSummary.query.filter_by(
        user_id=user_id, summary_date=log_date
    ).first()


# ==================== 主入口 ====================
if __name__ == '__main__':
    print("=" * 50)
    print("脉衡界健康智能体系统启动中...")
    print("=" * 50)
    print(f"LLM 提供商: {Config.LLM_PROVIDER}")
    print(f"LLM 模型  : {Config.LLM_MODEL}")
    print(f"API 端点  : {Config.LLM_BASE_URL}")
    print(f"数据库    : {Config.SQLALCHEMY_DATABASE_URI}")
    print("=" * 50)
    print("[启动自检] AI 服务连通性验证已在后台异步执行...")
    print("          (不影响 Flask 启动，几秒后在此处显示结果)")
    print("=" * 50)
    sys.stdout.flush()

    # 异步执行 health_check，不阻塞 app.run()，避免网络慢时 Flask 启动卡死
    import threading
    def _async_health_check():
        try:
            health = llm_service.health_check()
            print()
            print("-" * 50)
            if health.get("ok"):
                print(f"  ✅ AI 服务可用: {health.get('message')}")
            else:
                print(f"  ❌ AI 服务不可用: {health.get('message')}")
                print(f"     错误类型: {health.get('kind')} | 可重试: {health.get('retryable')}")
                print(f"     提示: 请检查 backend/.env 中的 LLM_API_KEY / LLM_BASE_URL")
            print("-" * 50)
            sys.stdout.flush()
        except Exception as e:
            print(f"  ❌ 自检异常: {type(e).__name__}: {e}")
            sys.stdout.flush()

    threading.Thread(target=_async_health_check, daemon=True).start()

    # 立即启动 Flask，不等自检
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
