import json
import re
import os
import random
from datetime import datetime
from typing import Dict, Any
from agents.base_agent import BaseAgent
from models import db, MentalAssessment, AlertRecord, User

class MentalHealthAgent(BaseAgent):
    """心理健康智能体 - 心理疏导、心理评分、预警机制"""
    
    def __init__(self, llm_service=None, memory_service=None, privacy_service=None, config=None):
        super().__init__("心理健康Agent", llm_service, memory_service, privacy_service, config)
    
    def build_system_prompt(self) -> str:
        return """你是一位温暖、专业的心理健康咨询师，拥有丰富的校园心理咨询经验。

你的沟通风格：
🌿 温暖接纳 - 先倾听，后回应，让用户感受到被理解和接纳
💡 专业引导 - 用心理学知识帮助用户理解自己的情绪
🤝 平等陪伴 - 不是居高临下的说教，而是像朋友一样陪伴
🎯 具体可行 - 给出的建议都是用户可以立即尝试的小行动

回答结构：
1. 先共情回应用户的感受（"我能理解你现在的感受..."）
2. 帮助用户理解和命名自己的情绪
3. 提供1-2个具体的情绪调节方法（如呼吸练习、书写表达等）
4. 温暖的收尾，鼓励继续倾诉

特别注意：
- 不要诊断疾病，只提供情绪支持和建议
- 如果用户有自伤/自杀倾向，立即建议拨打24小时心理援助热线：400-161-9995
- 鼓励用户寻求学校心理咨询中心的专业帮助
- 保护用户隐私，建立安全信任的对话空间"""
    
    def process(self, user_id: int, session_id: str, message: str, **kwargs) -> Dict[str, Any]:
        """处理心理健康相关请求"""
        context = self.get_context(user_id, session_id, max_messages=8)
        
        messages = [
            {"role": "system", "content": self.build_system_prompt()}
        ]
        messages.extend(context)
        messages.append({"role": "user", "content": message})
        
        content = self.call_llm(messages, temperature=0.8)
        
        # 保存对话
        self.save_message(user_id, session_id, "assistant", content, intent="mental")
        
        # 评估心理状态
        assessment = self._assess_mental_state(user_id, session_id, message, content)
        
        # 检查是否需要预警
        alert_info = None
        if assessment and assessment.get('overall_score', 100) < (self.config.MENTAL_ALERT_THRESHOLD if self.config else 60):
            alert_info = self._trigger_alert(user_id, assessment)
        
        response = self.format_response(content)
        response['mental_assessment'] = assessment
        if alert_info:
            response['alert_triggered'] = alert_info
        
        return response
    
    def _assess_mental_state(self, user_id: int, session_id: str, user_msg: str, assistant_msg: str) -> Dict:
        """评估用户心理状态（AI自动评分）"""
        prompt = f"""基于以下对话，请评估用户当前的心理状态。

用户消息：{user_msg[:300]}
助手回复：{assistant_msg[:200]}

请从以下维度给出0-100的评分（100为最佳）：
- overall_score: 综合心理状态总分
- anxiety_score: 焦虑程度（0=极度焦虑，100=无焦虑）
- depression_score: 抑郁倾向（0=严重抑郁倾向，100=无抑郁倾向）
- stress_score: 压力水平（0=极度压力，100=无压力）
- sleep_score: 睡眠状况（0=严重失眠，100=睡眠良好）
- social_score: 社交状态（0=严重社交回避，100=社交良好）

请以JSON格式输出，不要包含其他解释：
{{"overall_score": 75, "anxiety_score": 70, "depression_score": 80, "stress_score": 65, "sleep_score": 75, "social_score": 80, "summary": "简短分析摘要"}}"""
        
        try:
            result = self.call_llm([
                {"role": "system", "content": "你是一个心理状态评估助手，请严格按JSON格式输出评分。"},
                {"role": "user", "content": prompt}
            ], temperature=0.3)
            
            # 提取JSON
            match = re.search(r'\{.*\}', result, re.DOTALL)
            if match:
                assessment = json.loads(match.group(0))
                
                # 保存评估记录
                self._save_assessment(user_id, assessment, user_msg)
                return assessment
        except Exception as e:
            print(f"[心理评估] 失败: {e}")
        
        return None
    
    def _save_assessment(self, user_id: int, assessment: Dict, raw_summary: str):
        """保存心理评估"""
        # 加密存储摘要
        encrypted_summary = None
        if self.privacy:
            encrypted_summary = self.privacy.encrypt(raw_summary[:500])
        
        overall = assessment.get('overall_score', 100)
        
        ma = MentalAssessment(
            user_id=user_id,
            overall_score=overall,
            anxiety_score=assessment.get('anxiety_score'),
            depression_score=assessment.get('depression_score'),
            stress_score=assessment.get('stress_score'),
            sleep_score=assessment.get('sleep_score'),
            social_score=assessment.get('social_score'),
            source='ai_chat',
            encrypted_summary=encrypted_summary,
            alert_triggered=overall < (self.config.MENTAL_ALERT_THRESHOLD if self.config else 60)
        )
        
        db.session.add(ma)
        db.session.commit()
        
        return ma
    
    def _trigger_alert(self, user_id: int, assessment: Dict) -> Dict:
        """触发心理预警"""
        user = User.query.get(user_id)
        if not user or not user.alert_enabled:
            return None  # 用户未开启预警功能
        
        # 脱敏处理
        summary = assessment.get('summary', '用户心理状态需要关注')
        if self.privacy:
            summary = self.privacy.desensitize_mental_summary(summary)
        
        # 创建预警记录
        alert = AlertRecord(
            user_id=user_id,
            alert_type='mental',
            severity='high' if assessment.get('overall_score', 100) < 40 else 'medium',
            summary=f"心理评分{assessment.get('overall_score')}分 - {summary[:100]}",
            status='pending'
        )
        
        db.session.add(alert)
        
        # 更新评估记录
        ma = MentalAssessment.query.filter_by(user_id=user_id).order_by(MentalAssessment.id.desc()).first()
        if ma:
            ma.alert_sent = True
            ma.alert_time = datetime.utcnow()
        
        db.session.commit()
        
        return {
            'alert_id': alert.id,
            'severity': alert.severity,
            'counselor_notified': True if user.counselor_id else False,
            'message': '你的心理状态评分较低，系统已通知辅导员关注（你可以在隐私设置中关闭此功能）'
        }
    
    def get_assessment_history(self, user_id: int, limit: int = 30) -> list:
        """获取心理评估历史"""
        from models import MentalAssessment
        records = MentalAssessment.query.filter_by(user_id=user_id).order_by(
            MentalAssessment.assessment_date.desc()
        ).limit(limit).all()
        
        decrypt_fn = self.privacy.decrypt if self.privacy else None
        return [r.to_dict(decrypt_fn=decrypt_fn) for r in records]

    # ==================== 心理问卷测评（纯数值计算，零AI调用）====================

    def _load_mental_quiz(self) -> Dict:
        """加载心理测评问卷数据"""
        import json, os
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'data')
        quiz_path = os.path.join(data_dir, 'mental_quiz.json')
        with open(quiz_path, 'r', encoding='utf-8-sig') as f:
            return json.load(f)

    def _load_mental_profiles(self) -> Dict:
        """加载心理测评结果语料"""
        import json, os
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'data')
        profile_path = os.path.join(data_dir, 'mental_profiles.json')
        with open(profile_path, 'r', encoding='utf-8-sig') as f:
            return json.load(f)

    def assess_mental_quiz(self, user_id: int, session_id: str, answers: list) -> Dict[str, Any]:
        """心理状态问卷测评 - 纯数值计算，零AI调用

        answers 格式: [{"question_id": "q1", "option_index": 0}, ...]
        每个选项含 weights 字段（中文键：焦虑/抑郁/压力/睡眠/社交）。
        归一化：维度得分 = (该维度累加权重 / 实际回答的相关问题最大可能权重) * 100
        说明：
          - 睡眠/社交 为正向维度（权重越高=状态越好），直接归一化。
          - 焦虑/抑郁/压力 为负向维度（权重越高=症状越重），做反转：健康分 = 100 - 归一化值。
          - 这样所有维度均为健康分（100=最佳），与等级映射 excellent(85-100) 保持一致。
        """
        # 1. 加载问卷与语料数据
        try:
            quiz_data = self._load_mental_quiz()
            profiles_data = self._load_mental_profiles()
        except Exception as e:
            return {'success': False, 'message': f'加载问卷/语料数据失败: {e}'}

        # 维度中英文映射
        dim_map = {
            '焦虑': 'anxiety',
            '抑郁': 'depression',
            '压力': 'stress',
            '睡眠': 'sleep',
            '社交': 'social',
        }
        # 负向维度：权重越高表示症状越严重，需反转得到健康分（100=最佳）
        negative_dims = {'anxiety', 'depression', 'stress'}

        questions = quiz_data.get('questions', [])
        # 建立 question_id -> question 的索引
        q_index = {q.get('id'): q for q in questions}

        # 各维度累加权重 / 实际回答的相关问题最大可能权重
        dim_accumulated = {en: 0.0 for en in dim_map.values()}
        dim_max_possible = {en: 0.0 for en in dim_map.values()}

        answered_count = 0
        for ans in (answers or []):
            qid = ans.get('question_id')
            opt_idx = ans.get('option_index')
            q = q_index.get(qid)
            if not q or opt_idx is None:
                continue
            options = q.get('options', [])
            if opt_idx < 0 or opt_idx >= len(options):
                continue

            chosen_weights = options[opt_idx].get('weights', {})
            # 累加用户选择项的权重
            for cn, en in dim_map.items():
                dim_accumulated[en] += chosen_weights.get(cn, 0)
            # 累加该问题在各维度的最大可能权重（仅相关问题计入基数）
            for cn, en in dim_map.items():
                max_w = max(
                    (opt.get('weights', {}).get(cn, 0) for opt in options),
                    default=0
                )
                dim_max_possible[en] += max_w
            answered_count += 1

        if answered_count == 0:
            return {'success': False, 'message': '未提供有效回答，无法完成测评'}

        # 2. 计算各维度健康分（0-100，100=最佳）
        scores = {}
        for en in dim_map.values():
            if dim_max_possible[en] > 0:
                raw = (dim_accumulated[en] / dim_max_possible[en]) * 100
                if en in negative_dims:
                    # 负向维度：反转，使高分=健康
                    score = 100.0 - raw
                else:
                    # 正向维度（睡眠/社交）：高分=状态好
                    score = raw
            else:
                # 该维度无相关已回答问题：默认满分（无证据表明存在问题）
                score = 100.0
            scores[en] = round(score, 1)

        # 3. 总分 = 五个维度的平均值
        overall_score = round(sum(scores.values()) / len(scores), 1)

        # 4. 根据总分匹配等级
        if overall_score >= 85:
            level = 'excellent'
        elif overall_score >= 70:
            level = 'good'
        elif overall_score >= 55:
            level = 'moderate'
        elif overall_score >= 40:
            level = 'low'
        else:
            level = 'warning'

        # 5. 从语料中随机选取描述与建议（每个类别1条）
        profile = profiles_data.get(level, {}) if isinstance(profiles_data, dict) else {}
        label = profile.get('label', level)
        color = profile.get('color', '#888888')
        range_text = profile.get('range', '')

        description_list = profile.get('description', [])
        if isinstance(description_list, list) and description_list:
            description = random.choice(description_list)
        else:
            description = description_list if isinstance(description_list, str) else ''

        advice = {}
        for cat in ['self_regulation', 'lifestyle', 'social', 'professional']:
            cat_list = profile.get(cat, [])
            if isinstance(cat_list, list) and cat_list:
                advice[cat] = random.choice(cat_list)
            else:
                advice[cat] = ''

        # 6. 保存 MentalAssessment 记录到数据库（source='quiz'）
        assessment_saved = False
        try:
            threshold = self.config.MENTAL_ALERT_THRESHOLD if self.config else 60
            ma = MentalAssessment(
                user_id=user_id,
                overall_score=overall_score,
                anxiety_score=scores['anxiety'],
                depression_score=scores['depression'],
                stress_score=scores['stress'],
                sleep_score=scores['sleep'],
                social_score=scores['social'],
                source='quiz',
                encrypted_summary=None,
                alert_triggered=overall_score < threshold
            )
            db.session.add(ma)
            db.session.commit()
            assessment_saved = True
        except Exception as e:
            db.session.rollback()
            print(f"[心理问卷测评] 保存评估记录失败: {e}")

        # 7. 返回完整结果
        return {
            'success': True,
            'overall_score': overall_score,
            'scores': scores,
            'level': level,
            'label': label,
            'color': color,
            'range': range_text,
            'description': description,
            'advice': advice,
            'assessment_saved': assessment_saved
        }
