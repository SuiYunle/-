import json
import os
import re
import random
from typing import Dict, Any, List, Optional
from agents.base_agent import BaseAgent

class DiagnosisAgent(BaseAgent):
    """综合诊断Agent - AI问诊、BMI评估、结构化问诊流程"""
    
    # 问诊问题序列
    CONSULTATION_QUESTIONS = [
        "请描述你的主要症状（比如：哪里不适、是什么感觉）",  # Q1: 主要症状
        "症状持续了多久了？（比如：今天刚开始、已经一周了、反复发作）",  # Q2: 持续时间
        "不适或疼痛主要位置在哪里？",  # Q3: 部位位置
        "你觉得症状程度如何？(轻微/中度/严重)",  # Q4: 程度
        "还有没有其他伴随症状？比如发热、恶心、乏力等",  # Q5: 伴随症状
        "你有没有相关的既往病史？比如慢性病、以前的手术、过敏史等",  # Q6: 既往史
    ]
    
    def __init__(self, llm_service=None, memory_service=None, privacy_service=None, config=None):
        super().__init__("诊断Agent", llm_service, memory_service, privacy_service, config)
        self.medical_cases = self._load_medical_cases()
        self.bmi_profiles = self._load_bmi_profiles()
        # 初始化会话中的问诊状态（使用memory_service跨会话持久化）
        self.consultation_steps = {}  # session_id -> {"step": int, "answers": dict}
    
    def _load_medical_cases(self) -> Dict:
        """加载医案库"""
        try:
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'data')
            case_path = os.path.join(data_dir, 'cases.json')
            if os.path.exists(case_path):
                with open(case_path, 'r', encoding='utf-8-sig') as f:
                    return json.load(f)
        except Exception as e:
            print(f"[诊断Agent] 加载医案失败: {e}")
        return {"cases": []}
    
    def _load_bmi_profiles(self) -> Dict:
        """加载BMI预计算配置"""
        try:
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'data')
            bmi_path = os.path.join(data_dir, 'bmi_profiles.json')
            if os.path.exists(bmi_path):
                with open(bmi_path, 'r', encoding='utf-8-sig') as f:
                    return json.load(f)
        except Exception as e:
            print(f"[诊断Agent] 加载BMI配置失败: {e}")
        return {}
    
    def _find_related_cases(self, message: str) -> list:
        """根据用户消息关键词匹配相关医案"""
        cases = self.medical_cases.get("cases", [])
        if not cases:
            return []
        
        scored = []
        # 扩展关键词库，覆盖20个病例的所有核心症状
        keywords = [
            '咳嗽', '痰', '咽痛', '发热', '恶寒', '头痛', '头身疼痛', '鼻塞', '流清涕', '喷嚏',
            '胃痛', '胃脘', '胁痛', '嗳气', '泛酸', '纳呆', '大便不畅',
            '月经不调', '月经', '经量', '经色', '血块', '乳房胀痛', '情绪',
            '眩晕', '头晕', '头疼', '面红目赤', '急躁易怒', '口苦咽干', '失眠',
            '口渴', '多饮', '多食', '消渴', '多尿', '乏力', '疲劳', '手足心热', '腰膝酸软', '体重下降',
            '大便干结', '便秘', '羊屎', '口干咽燥', '皮肤干燥', '头晕耳鸣', '心烦少寐',
            '身目发黄', '尿黄', '胁胀痛', '脘腹痞闷', '恶心欲呕', '口苦口干', '大便秘结',
            '尿频', '尿急', '尿痛', '尿道灼热', '小腹坠胀', '腰酸', '小便黄赤',
            '情绪低落', '郁郁寡欢', '善太息', '胸胁胀闷', '脘腹胀满', '不思饮食', '夜寐不安', '多梦易醒',
            '关节疼痛', '游走性', '屈伸不利', '怕冷', '得热则舒', '阴雨天加重',
            '月经量多', '淋漓不尽', '色淡质稀', '神疲乏力', '气短懒言', '面色萎黄', '头晕心悸', '大便溏薄',
            '厌食', '不思饮食', '面色少华', '形体偏瘦', '大便干结', '夜间磨牙', '腹痛', '口气臭',
            '耳鸣', '耳聋', '听力下降', '头晕目眩', '腰膝酸软', '神疲健忘', '失眠多梦', '头发早白脱落',
            '喘息', '哮鸣', '胸闷', '不能平卧', '咳痰色白清稀', '背冷', '恶寒无汗', '口不渴',
            '气虚', '阳虚', '阴虚', '痰湿', '湿热', '气郁', '肝气', '脾虚', '血瘀', '气血', '阴阳',
            '风寒', '风热', '痰热', '寒饮', '肝阳上亢', '心脾两虚', '脾肾阳虚', '肝胆湿热', '膀胱湿热',
            '肝气郁结', '脾不统血', '脾虚食积', '肾精亏虚', '外寒内饮'
        ]
        
        msg_lower = message.lower()
        for case in cases:
            case_text = json.dumps(case, ensure_ascii=False).lower()
            
            matched = [kw for kw in keywords if kw in msg_lower and kw in case_text]
            
            disease = case.get('diagnosis', {}).get('disease', '')
            if disease and disease in msg_lower:
                matched.append(disease)
            
            syndrome = case.get('diagnosis', {}).get('syndrome', '')
            if syndrome and syndrome.replace('证', '') in msg_lower:
                matched.append(syndrome)
            
            score = len(matched)
            if score > 0:
                case_info = (
                    f"[医案 {case.get('case_id')}] "
                    f"主诉：{case.get('chief_complaint', '')}；"
                    f"诊断：{disease}（{syndrome}）；"
                    f"方剂：{case.get('treatment', {}).get('herbal_medicine', '')}"
                )
                scored.append((score, case_info, case.get('case_id')))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [(info, cid) for _, info, cid in scored[:3]]
    
    def build_system_prompt(self) -> str:
        return """你是一位全科医生，拥有中西医结合的诊疗经验，同时也是校园健康顾问。

你的诊疗风格：
🏥 严谨专业 - 基于症状给出合理分析，不过度解读
🌿 中西结合 - 同时从中医和西医角度分析问题
📋 结构清晰 - 回答有明确的结构，便于理解
⚠️ 安全第一 - 明确区分可以自我处理和需要就医的情况

回答结构（结构化问诊完成后）：
1. 🔍 症状分析：分析可能的原因
2. 💊 处理建议：给出具体的自我护理建议
3. 🏥 就医提示：什么情况下需要就医
4. 📚 参考资料：如有相关医案，引用编号[医案 C001]
5. 📝 就诊摘要：关键信息概览（主症、风险级别、推荐科室、下一步行动）

原则：
- 明确说明这是初步建议，不能替代专业医生诊断
- 紧急情况（如胸痛、呼吸困难、剧烈腹痛等）必须建议立即就医
- 结合中医和西医视角给出全面建议"""
    
    def _get_consultation_state(self, user_id: int, session_id: str) -> Dict[str, Any]:
        """获取问诊状态 - 从内存或持久化存储"""
        context = self.get_context(user_id, session_id, max_messages=20)
        consultation_answers = {}
        for msg in context:
            if msg.get('content', '').startswith('[咨询答案]'):
                pass
        return {"step": 0, "answers": {}, "session_id": session_id}
    
    def _save_consultation_answer(self, user_id: int, session_id: str, question_num: int, answer: str):
        """保存问诊答案到会话记录"""
        self.save_message(user_id, session_id, "assistant", 
                         f"[咨询答案 Q{question_num + 1}]: {answer}", 
                         intent="diagnosis_consultation")
    
    def _get_next_question_step(self, user_id: int, session_id: str) -> int:
        """获取下一个问题的步骤号"""
        state = self._get_consultation_state(user_id, session_id)
        return state.get("step", 0)
    
    def _is_consultation_complete(self, state: Dict[str, Any]) -> bool:
        """检查问诊是否完成"""
        return state.get("step", 0) >= len(self.CONSULTATION_QUESTIONS)
    
    def _start_consultation(self, user_id: int, session_id: str, message: str) -> Dict[str, Any]:
        """启动结构化问诊流程"""
        state = self._get_consultation_state(user_id, session_id)
        state["step"] = 1
        state["answers"] = {"Q0": message}
        self._save_consultation_answer(user_id, session_id, 0, message)
        return self._start_next_question(user_id, session_id, 0)
    
    def _handle_consultation_step(self, user_id: int, session_id: str, message: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """处理问诊流程中的当前步骤"""
        current_step = state["step"]
        self._save_consultation_answer(user_id, session_id, current_step - 1, message)
        state["answers"][f"Q{current_step}"] = message
        state["step"] = current_step + 1
        
        self.save_message(user_id, session_id, "assistant",
                         f"[咨询状态] 已收集 {current_step} / {len(self.CONSULTATION_QUESTIONS)} 个问题的答案",
                         intent="diagnosis_consultation")
        
        if state["step"] < len(self.CONSULTATION_QUESTIONS):
            return self._start_next_question(user_id, session_id, state["step"])
        
        return self._generate_structured_diagnosis(user_id, session_id, state["answers"])
    
    def process(self, user_id: int, session_id: str, message: str, **kwargs) -> Dict[str, Any]:
        """处理诊断相关请求"""
        state = self._get_consultation_state(user_id, session_id)
        force_intent = kwargs.get('force_intent')
        
        if state.get("step", 0) > 0 and state.get("step", 0) <= len(self.CONSULTATION_QUESTIONS):
            return self._handle_consultation_step(user_id, session_id, message, state)
        
        if force_intent == 'diagnosis' or self._should_start_consultation(message):
            return self._start_consultation(user_id, session_id, message)
        
        return self._handle_general_diagnosis(user_id, session_id, message)
    
    def _should_start_consultation(self, message: str) -> bool:
        """判断是否应该启动结构化问诊流程"""
        # 关键词触发：疼痛、不适、症状描述
        trigger_kw = ['痛', '不舒服', '症状', '感冒', '发烧', '头疼', '肚子疼', '恶心',
                      '头痛', '咳嗽', '胃痛', '腹痛', '咽痛']
        return any(kw in message.lower() for kw in trigger_kw)
    
    def _start_next_question(self, user_id: int, session_id: str, step: int) -> Dict[str, Any]:
        """开始询问下一个问题"""
        if step < len(self.CONSULTATION_QUESTIONS):
            question = self.CONSULTATION_QUESTIONS[step]
            # 保存问题状态
            self._save_consultation_answer(user_id, session_id, step, "")  # 占位，实际答案由用户提供
            
            # 返回问题给用户
            return {
                "intent": "diagnosis_consultation",
                "content": f"小艺：{question}\n\n请直接回答即可，我会记录下来。",
                "question": question,
                "step": step + 1,  # 下一步的步号
                "consultation": True
            }
        else:
            # 应该已经完成了，这不应该发生
            return self._generate_structured_diagnosis(user_id, session_id, {})
    
    def _generate_structured_diagnosis(self, user_id: int, session_id: str, answers: Dict[str, str]) -> Dict[str, Any]:
        """生成结构化诊断输出"""
        # 提取答案
        main_symptom = answers.get("Q0", "")  # Q0是主要症状
        duration = answers.get("Q1", "")
        location = answers.get("Q2", "")
        severity = answers.get("Q3", "")
        accompaniments = answers.get("Q4", "")
        history = answers.get("Q5", "")
        
        # 构建系统提示词，引导LLM给出结构化回复
        system_prompt = self.build_system_prompt() + """
        
        根据以下用户提供的问诊信息，给出结构化的诊断报告：
        
        【用户问诊信息】：
        - 主要症状: {main_symptom}
        - 症状持续: {duration}
        - 部位位置: {location}
        - 程度: {severity}
        - 伴随症状: {accompaniments}
        - 既往病史: {history}
        
        请按照以下格式输出（必须包含所有项目，即使某项为“无”}：
        
        症状分析: [在这里分析可能的原因]
        处理建议: [在这里给出自我护理建议]
        就医提示: [在这里说明什么情况下需要就医]
        风险等级: [轻度/中度/高度]
        推荐科室: [建议就诊科室]
        下一步行动: [给用户的具体行动建议]
        就诊摘要: [为医生准备的简短摘要，包含关键信息]
        """.format(
            main_symptom=main_symptom or "未描述",
            duration=duration or "未说明",
            location=location or "未说明",
            severity=severity or "未说明",
            accompaniments=accompaniments or "未描述",
            history=history or "未描述"
        )
        
        # 获取上下文
        context = self.get_context(user_id, session_id)
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(context)
        messages.append({"role": "user", "content": str(answers)})
        
        content = self.call_llm(messages)
        
        # 保存助手回复
        self.save_message(user_id, session_id, "assistant", content, 
                         intent="diagnosis", case_reference=None)
        
        # 保存结构化数据到会话以备后用
        self._save_consultation_answer(user_id, session_id, -1, json.dumps(answers, ensure_ascii=False))
        
        return self.format_response(content, case_reference=None)
    
    def _handle_general_diagnosis(self, user_id: int, session_id: str, message: str) -> Dict[str, Any]:
        """常规AI问诊（回退方案）"""
        context = self.get_context(user_id, session_id)
        
        system_prompt = self.build_system_prompt()
        
        # 检索相关医案
        related_cases = self._find_related_cases(message)
        matched_case_ids = []
        if related_cases:
            system_prompt += "\n\n以下是与用户症状相关的中医医案，请在回答中结合中医视角引用对应医案编号（格式：[医案 C001]）：\n"
            for case_info, case_id in related_cases:
                system_prompt += case_info + "\n"
                matched_case_ids.append(case_id)
        
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        messages.extend(context)
        messages.append({"role": "user", "content": message})
        
        content = self.call_llm(messages)
        
        # 自动补充医案引用
        case_ref = None
        if matched_case_ids:
            import re
            case_refs = re.findall(r'C\d{3}', content)
            if not case_refs:
                case_ref = matched_case_ids[0]
                content += f"\n\n参考资料：[医案 {case_ref}]"
            else:
                case_ref = case_refs[0]
        
        self.save_message(user_id, session_id, "assistant", content, 
                         intent="diagnosis", case_reference=case_ref)
        
        return self.format_response(content, case_reference=case_ref)
    
    def assess_bmi(self, user_id: int, session_id: str, height: float, weight: float, gender: str = 'male') -> Dict[str, Any]:
        """BMI评估 - 零AI调用，使用预计算数据和算法"""
        # 1. 计算BMI: BMI = weight(kg) / (height(m))²
        height_m = height / 100.0
        if height_m <= 0:
            return {'success': False, 'message': '身高必须大于0'}
        bmi = weight / (height_m ** 2)
        
        # 2. BMI分类（男女通用区间键名）
        if bmi < 18.5:
            category = 'underweight'
        elif bmi < 24:
            category = 'normal'
        elif bmi < 28:
            category = 'overweight'
        else:
            category = 'obese'
        
        # 3. 从bmi_profiles.json读取对应性别和区间的预计算建议
        gender_key = gender if gender in self.bmi_profiles else 'male'
        profile = self.bmi_profiles.get(gender_key, {}).get(category, {})
        
        if not profile:
            return {
                "success": False,
                "error": f"未找到性别{gender_key}、区间{category}的BMI配置数据",
                "bmi_value": round(bmi, 2),
                "bmi_category": category,
            }
        
        # 4. 随机选择1条饮食建议、1条运动建议、1条生活建议
        descriptions = profile.get('description', [])
        diet_tips = profile.get('diet', [])
        exercise_tips = profile.get('exercise', [])
        lifestyle_tips = profile.get('lifestyle', [])
        
        description = random.choice(descriptions) if descriptions else ''
        diet_tip = random.choice(diet_tips) if diet_tips else ''
        exercise_tip = random.choice(exercise_tips) if exercise_tips else ''
        lifestyle_tip = random.choice(lifestyle_tips) if lifestyle_tips else ''
        
        bmi_category_label = profile.get('label', '')
        color = profile.get('color', '')
        
        # 5. 保存BMIAssessment记录到数据库
        try:
            from models import db, BMIAssessment
            assessment = BMIAssessment(
                user_id=user_id,
                gender=gender_key,
                height=height,
                weight=weight,
                bmi_value=round(bmi, 2),
                bmi_category=category,
                bmi_category_label=bmi_category_label,
                color=color,
                diet_tip=diet_tip,
                exercise_tip=exercise_tip,
                lifestyle_tip=lifestyle_tip,
            )
            db.session.add(assessment)
            db.session.commit()
        except Exception as e:
            print(f"[诊断Agent] 保存BMI评估记录失败: {e}")
            try:
                db.session.rollback()
            except Exception:
                pass
        
        # 6. 返回结果（不调用任何LLM）
        return {
            "success": True,
            "bmi_value": round(bmi, 2),
            "bmi_category": category,
            "bmi_category_label": bmi_category_label,
            "color": color,
            "gender": gender_key,
            "height": height,
            "weight": weight,
            "diet_tip": diet_tip,
            "exercise_tip": exercise_tip,
            "lifestyle_tip": lifestyle_tip,
            "description": description,
        }