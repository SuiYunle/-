import json
import os
from typing import Dict, Any
from agents.base_agent import BaseAgent

class TCMAgent(BaseAgent):
    """中医智能体 - 体质辨识、食疗推荐、多模态舌诊/餐食分析"""

    def __init__(self, llm_service=None, memory_service=None, privacy_service=None, config=None, image_service=None):
        super().__init__("中医Agent", llm_service, memory_service, privacy_service, config)
        self.image_service = image_service
        self.medical_cases = self._load_medical_cases()
        # 预计算数据缓存（体质问卷/语料库），按需懒加载
        self._constitution_quiz_cache = None
        self._constitution_profiles_cache = None

    def _load_medical_cases(self) -> Dict:
        """加载医案库"""
        try:
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'data')
            case_path = os.path.join(data_dir, 'cases.json')
            if os.path.exists(case_path):
                with open(case_path, 'r', encoding='utf-8-sig') as f:
                    return json.load(f)
        except Exception as e:
            print(f"[中医Agent] 加载医案失败: {e}")
        return {"cases": []}

    def build_system_prompt(self) -> str:
        return """你是一位有30年临床经验的中医专家，同时也是一位善于沟通的健康顾问。

回答风格：
- 专业权威，但语言通俗易懂
- 善用类比和比喻解释中医概念
- 回答结构清晰，使用分段和编号
- 给出具体的、可操作的调理建议
- 适当引用经典中医理论增加可信度

回答结构：
1. 🔍 辨证分析：分析用户的问题属于什么证型
2. 💡 调理建议：给出食疗、起居、运动等具体建议
3. ⚠️ 注意事项：提醒禁忌和需要就医的情况
4. 📚 参考资料：引用相关医案编号，格式为[医案 C001]

重要：必须在回答中引用至少一个相关医案，标注医案编号。如果问题涉及具体疾病，建议用户到正规中医院就诊。"""

    def process(self, user_id: int, session_id: str, message: str, **kwargs) -> Dict[str, Any]:
        """处理中医相关请求"""
        # 获取上下文
        context = self.get_context(user_id, session_id)

        # 构建系统提示
        system_prompt = self.build_system_prompt()

        # 检索相关医案（关键词匹配）
        related_cases = self._find_related_cases(message)
        matched_case_ids = []
        if related_cases:
            case_text = "\n\n以下是与用户问题相关的医案，请在回答中引用对应的医案编号：\n"
            for case_info, case_id in related_cases:
                case_text += case_info + "\n"
                matched_case_ids.append(case_id)
            system_prompt += case_text
        else:
            # 没有匹配到医案时，提示LLM可以引用通用医案
            system_prompt += "\n\n（当前问题未匹配到具体医案，如回答中涉及相关中医理论，可引用医案库中的通用案例，编号格式：[医案 C001]）"

        # 构建消息
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        messages.extend(context)
        messages.append({"role": "user", "content": message})

        # 调用LLM
        content = self.call_llm(messages, temperature=0.7)

        # 提取医案引用
        case_refs = self._extract_case_references(content)

        # 如果LLM没有引用但我们有匹配的医案，自动补充引用
        if not case_refs and matched_case_ids:
            case_refs = matched_case_ids[:1]
            content += f"\n\n参考资料：[医案 {case_refs[0]}]"

        # 保存到记忆
        self.save_message(user_id, session_id, "assistant", content,
                         intent="tcm", case_reference=",".join(case_refs) if case_refs else None)

        # 构建参考资料列表
        references = []
        if related_cases:
            for case_info, case_id in related_cases:
                case_data = None
                for c in self.medical_cases.get("cases", []):
                    if c.get("case_id") == case_id:
                        case_data = c
                        break
                if case_data:
                    references.append({
                        "case_id": case_id,
                        "title": f"医案 {case_id}：{case_data.get('chief_complaint', '')}",
                        "disease": case_data.get('diagnosis', {}).get('disease', ''),
                        "syndrome": case_data.get('diagnosis', {}).get('syndrome', ''),
                        "prescription": case_data.get('treatment', {}).get('herbal_medicine', ''),
                        "dietary_advice": case_data.get('treatment', {}).get('dietary_advice', ''),
                        "outcome": case_data.get('outcome', ''),
                        "source": case_data.get('source', '中医病例数据库')
                    })

        return self.format_response(content, case_reference=case_refs[0] if case_refs else None, references=references)

    def analyze_tongue(self, user_id: int, session_id: str, image_path: str) -> Dict[str, Any]:
        """舌苔分析（多模态）"""
        if not self.image_service:
            return self.format_response("[错误] 图像服务未初始化")

        result = self.image_service.analyze_tongue(image_path, user_id)

        # 生成中医解读
        analysis_text = f"""【舌象分析报告】
舌色：{result.get('tongue_color', '未知')}
舌苔：{result.get('coating', '未知')}
舌形：{result.get('tongue_shape', '未知')}
体质倾向：{result.get('constitution', '未知')}
辨证：{result.get('syndrome', '未知')}

调理建议：
{result.get('suggestions', '暂无')}
"""

        self.save_message(user_id, session_id, "assistant", analysis_text,
                         intent="tcm", case_reference=result.get('case_reference'))

        return self.format_response(analysis_text, attachments={"image_analysis": result})

    def analyze_meal(self, user_id: int, session_id: str, image_path: str, constitution: str = None) -> Dict[str, Any]:
        """餐食分析（多模态）"""
        if not self.image_service:
            return self.format_response("[错误] 图像服务未初始化")

        result = self.image_service.analyze_meal(image_path, user_id, constitution)

        analysis_text = f"""【餐食分析报告】
食物：{', '.join(result.get('foods', []))}
估算热量：{result.get('estimated_calories', '未知')}
营养分析：{result.get('nutrition_analysis', '未知')}
中医适宜性：{result.get('tcm_suitability', '未知')}

改进建议：
{result.get('suggestions', '暂无')}
"""

        self.save_message(user_id, session_id, "assistant", analysis_text, intent="tcm")

        return self.format_response(analysis_text, attachments={"image_analysis": result})

    def recommend_food(self, user_id: int, session_id: str, condition: str, constitution: str = None) -> Dict[str, Any]:
        """食谱推荐"""
        system_prompt = self.build_system_prompt()

        # 检索相关医案
        search_text = f"{condition} {constitution or ''}"
        related_cases = self._find_related_cases(search_text)
        matched_case_ids = []
        if related_cases:
            case_text = "\n\n以下是与用户问题相关的医案，请在回答中引用对应的医案编号：\n"
            for case_info, case_id in related_cases:
                case_text += case_info + "\n"
                matched_case_ids.append(case_id)
            system_prompt += case_text

        prompt = f"""请根据以下条件推荐中医食疗方案：
身体状况/需求：{condition}
体质类型：{constitution or '未明确'}

请给出：
1. 推荐食谱（早中晚三餐）
2. 每道菜的中医功效
3. 注意事项和禁忌
4. 参考资料（引用相关医案编号）"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]

        content = self.call_llm(messages)

        # 提取医案引用
        case_refs = self._extract_case_references(content)
        if not case_refs and matched_case_ids:
            case_refs = matched_case_ids[:1]
            content += f"\n\n参考资料：[医案 {case_refs[0]}]"

        self.save_message(user_id, session_id, "assistant", content,
                         intent="tcm", case_reference=",".join(case_refs) if case_refs else None)

        # 构建参考资料列表
        references = []
        if related_cases:
            for case_info, case_id in related_cases:
                case_data = None
                for c in self.medical_cases.get("cases", []):
                    if c.get("case_id") == case_id:
                        case_data = c
                        break
                if case_data:
                    references.append({
                        "case_id": case_id,
                        "title": f"医案 {case_id}：{case_data.get('chief_complaint', '')}",
                        "disease": case_data.get('diagnosis', {}).get('disease', ''),
                        "syndrome": case_data.get('diagnosis', {}).get('syndrome', ''),
                        "prescription": case_data.get('treatment', {}).get('herbal_medicine', ''),
                        "dietary_advice": case_data.get('treatment', {}).get('dietary_advice', ''),
                        "outcome": case_data.get('outcome', ''),
                        "source": case_data.get('source', '中医病例数据库')
                    })

        return self.format_response(content, case_reference=case_refs[0] if case_refs else None, references=references)

    def assess_constitution(self, user_id: int, session_id: str, answers: list) -> Dict[str, Any]:
        """基于问卷答案推断中医体质类型（预计算 + 加权算法，零AI调用）

        流程：
        1. 从 constitution_quiz.json 加载带权重的题目（注意：app.py 路由返回的题目
           不含权重，本方法直接从 JSON 文件读取带 weights 字段的原始题目）
        2. 按 answer 中的 question_id + option_index 取出该选项的 weights
        3. 按九种体质类型累加权重，计算各体质百分比
        4. 主体质类型 = 权重最高的类型
        5. 从 constitution_profiles.json 随机选取建议语料
           （description 选 1 条，diet/exercise/lifestyle 各选 1 条）
        6. 保存 ConstitutionAssessment 记录到数据库（而非仅 HealthRecord）

        answers 格式: [{"question_id": "q1", "option_index": 0}, ...]
        """
        import random

        # 九种体质类型：拼音(key) <-> 中文(label)
        constitution_map = {
            'pinghe': '平和质',
            'qixu': '气虚质',
            'yangxu': '阳虚质',
            'yinxu': '阴虚质',
            'tanshi': '痰湿质',
            'shire': '湿热质',
            'xueyu': '血瘀质',
            'qiyu': '气郁质',
            'tebin': '特禀质',
        }
        label_to_key = {v: k for k, v in constitution_map.items()}

        # 1. 加载问卷数据（每个选项含 weights 字段）
        quiz_data = self._load_constitution_quiz()
        if not quiz_data or not quiz_data.get('questions'):
            return {'success': False, 'message': '体质问卷数据加载失败'}

        question_lookup = {q.get('id'): q for q in quiz_data.get('questions', [])}

        # 2 & 3. 按体质类型累加权重
        scores = {key: 0 for key in constitution_map.keys()}
        for ans in answers:
            qid = ans.get('question_id')
            opt_idx = ans.get('option_index')
            question = question_lookup.get(qid)
            if not question:
                continue
            options = question.get('options', []) or []
            if opt_idx is None or not isinstance(opt_idx, int) or opt_idx < 0 or opt_idx >= len(options):
                continue
            weights = options[opt_idx].get('weights', {}) or {}
            for cn_label, w in weights.items():
                key = label_to_key.get(cn_label)
                if key:
                    scores[key] += w

        total_weight = sum(scores.values())
        if total_weight <= 0:
            return {'success': False, 'message': '无法计算体质得分，请检查问卷答案'}

        # 计算各体质百分比
        percentages = {k: round(v / total_weight * 100, 1) for k, v in scores.items()}

        # 4. 主体质类型 = 权重最高的类型
        primary_key = max(scores, key=scores.get)
        primary_label = constitution_map[primary_key]

        # 5. 从语料库随机选择建议（在符合本体质条件的建议池中随机抽取）
        profiles = self._load_constitution_profiles()
        profile = profiles.get(primary_label, {}) if profiles else {}

        descriptions = profile.get('descriptions', []) or []
        description = random.choice(descriptions) if descriptions else ''

        # 四类生活建议：分别从该体质的 4 组建议池中随机选 1 条
        # （emotion 此前遗漏，补上以驱动前端"情志调摄"卡片）
        suggestions = profile.get('suggestions', []) or []
        diet_tips = [s.get('diet', '') for s in suggestions if s.get('diet')]
        exercise_tips = [s.get('exercise', '') for s in suggestions if s.get('exercise')]
        lifestyle_tips = [s.get('lifestyle', '') for s in suggestions if s.get('lifestyle')]
        emotion_tips = [s.get('emotion', '') for s in suggestions if s.get('emotion')]
        diet_tip = random.choice(diet_tips) if diet_tips else ''
        exercise_tip = random.choice(exercise_tips) if exercise_tips else ''
        lifestyle_tip = random.choice(lifestyle_tips) if lifestyle_tips else ''
        emotion_tip = random.choice(emotion_tips) if emotion_tips else ''

        # 易患风险 / 推荐食材 / 少食食材：每组各从 4 个子池中随机选一组
        risks_pool = profile.get('risks', []) or []
        risks_selected = random.choice(risks_pool) if risks_pool else []

        rec_foods_pool = profile.get('recommended_foods', []) or []
        recommended_foods = random.choice(rec_foods_pool) if rec_foods_pool else []

        avoid_foods_pool = profile.get('avoid_foods', []) or []
        avoid_foods = random.choice(avoid_foods_pool) if avoid_foods_pool else []

        # 次体质：第二高占比>=15% 才标注，避免噪声
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        secondary_label = None
        if len(sorted_scores) > 1:
            secondary_key = sorted_scores[1][0]
            if secondary_key != primary_key and percentages.get(secondary_key, 0) >= 15:
                secondary_label = constitution_map[secondary_key]

        # 6. 保存 ConstitutionAssessment 记录到数据库（而非仅 HealthRecord）
        try:
            from models import db, ConstitutionAssessment
            assessment = ConstitutionAssessment(
                user_id=user_id,
                primary_type=primary_key,
                primary_type_label=primary_label,
                percentages=json.dumps(percentages, ensure_ascii=False),
                description=description,
                diet_tip=diet_tip,
                exercise_tip=exercise_tip,
                lifestyle_tip=lifestyle_tip,
            )
            db.session.add(assessment)
            db.session.commit()
        except Exception as e:
            print(f"[中医Agent] 保存体质辨识记录失败: {e}")
            try:
                db.session.rollback()
            except Exception:
                pass

        # 保存对话消息
        summary = f"体质辨识结果：{primary_label}（{percentages[primary_key]}%）\n\n{description}"
        self.save_message(user_id, session_id, "assistant", summary, intent="tcm_constitution")

        # 7. 返回完整结果（字段对齐前端 renderConstitutionResult 期望）
        return {
            'success': True,
            'primary_type': primary_label,          # 中文标签，前端直接作为徽章显示
            'primary_type_key': primary_key,         # 拼音key，保留给需要英文标识的调用方
            'primary_type_label': primary_label,
            'secondary_type': secondary_label,       # 次体质中文标签，可能为 None
            'score': percentages[primary_key],       # 主体质匹配度（百分比数字）
            'percentages': percentages,
            'description': description,
            'suggestions': {
                'diet': diet_tip,
                'exercise': exercise_tip,
                'lifestyle': lifestyle_tip,
                'emotion': emotion_tip,
            },
            'risks': risks_selected,                 # list[str]，前端渲染为风险标签
            'recommended_foods': recommended_foods,  # list[str]
            'avoid_foods': avoid_foods,              # list[str]
        }

    def _load_constitution_quiz(self) -> Dict:
        """加载体质问卷数据（带权重），带实例缓存"""
        if self._constitution_quiz_cache is not None:
            return self._constitution_quiz_cache
        try:
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'data')
            quiz_path = os.path.join(data_dir, 'constitution_quiz.json')
            with open(quiz_path, 'r', encoding='utf-8-sig') as f:
                self._constitution_quiz_cache = json.load(f)
        except Exception as e:
            print(f"[中医Agent] 加载体质问卷失败: {e}")
            self._constitution_quiz_cache = {}
        return self._constitution_quiz_cache

    def _load_constitution_profiles(self) -> Dict:
        """加载体质结果语料库，带实例缓存"""
        if self._constitution_profiles_cache is not None:
            return self._constitution_profiles_cache
        try:
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'data')
            profile_path = os.path.join(data_dir, 'constitution_profiles.json')
            with open(profile_path, 'r', encoding='utf-8-sig') as f:
                self._constitution_profiles_cache = json.load(f)
        except Exception as e:
            print(f"[中医Agent] 加载体质语料库失败: {e}")
            self._constitution_profiles_cache = {}
        return self._constitution_profiles_cache

    def _find_related_cases(self, message: str) -> list:
        """根据用户消息关键词匹配相关医案"""
        import re
        cases = self.medical_cases.get("cases", [])
        if not cases:
            return []

        scored = []
        for case in cases:
            # 构建医案全文用于关键词匹配
            case_text = json.dumps(case, ensure_ascii=False).lower()
            msg_lower = message.lower()

            # 提取用户消息中的关键词 - 扩展覆盖所有20个病例
            keywords = []
            # 症状关键词
            symptom_kws = ['咳嗽', '痰', '胃痛', '胃脘', '胁', '嗳气', '月经', '头晕', '头痛',
                          '眩晕', '口渴', '多饮', '多食', '消渴', '失眠', '疲劳', '乏力',
                          '气虚', '阳虚', '阴虚', '痰湿', '湿热', '气郁', '肝气', '脾虚',
                          '咳嗽', '咽痛', '发热', '感冒', '腰膝', '酸软', '恶寒', '头身疼痛',
                          '鼻塞', '流清涕', '喷嚏', '泛酸', '纳呆', '大便不畅', '经量', '经色',
                          '血块', '乳房胀痛', '情绪', '面红目赤', '急躁易怒', '口苦咽干',
                          '手足心热', '体重下降', '大便干结', '便秘', '羊屎', '口干咽燥',
                          '皮肤干燥', '头晕耳鸣', '心烦少寐', '身目发黄', '尿黄', '胁胀痛',
                          '脘腹痞闷', '恶心欲呕', '大便秘结', '尿频', '尿急', '尿痛', '尿道灼热',
                          '小腹坠胀', '腰酸', '小便黄赤', '情绪低落', '郁郁寡欢', '善太息',
                          '胸胁胀闷', '脘腹胀满', '不思饮食', '夜寐不安', '多梦易醒',
                          '关节疼痛', '游走性', '屈伸不利', '怕冷', '得热则舒', '阴雨天加重',
                          '月经量多', '淋漓不尽', '色淡质稀', '神疲乏力', '气短懒言', '面色萎黄',
                          '头晕心悸', '大便溏薄', '厌食', '不思饮食', '面色少华', '形体偏瘦',
                          '夜间磨牙', '腹痛', '口气臭', '耳鸣', '耳聋', '听力下降', '头发早白脱落',
                          '喘息', '哮鸣', '胸闷', '不能平卧', '咳痰色白清稀', '背冷', '恶寒无汗', '口不渴']
            for kw in symptom_kws:
                if kw in msg_lower:
                    keywords.append(kw)

            # 体质关键词
            constitution_kws = ['气虚质', '阳虚质', '阴虚质', '痰湿质', '湿热质', '血瘀质', '气郁质', '特禀质', '平和质']
            for kw in constitution_kws:
                if kw in msg_lower:
                    keywords.append(kw)

            # 证型关键词
            syndrome_kws = ['风寒束表', '痰热壅肺', '肝气犯胃', '心脾两虚', '寒凝血瘀', '脾虚', '肝阳上亢', '阴虚肠燥',
                          '痰浊中阻', '心血瘀阻', '脾肾阳虚', '气阴两虚', '肝胆湿热', '膀胱湿热', '肝气郁结',
                          '风寒湿痹', '脾不统血', '脾虚食积', '肾精亏虚', '外寒内饮']
            for kw in syndrome_kws:
                if kw in msg_lower:
                    keywords.append(kw)

            # 计算匹配分数
            score = 0
            for kw in keywords:
                if kw in case_text:
                    score += 1

            # 疾病名直接匹配
            disease = case.get('diagnosis', {}).get('disease', '')
            syndrome = case.get('diagnosis', {}).get('syndrome', '')
            if disease and disease in msg_lower:
                score += 3
            if syndrome and any(w in msg_lower for w in syndrome.split('证')[0] if len(w) > 1):
                score += 2

            if score > 0:
                # 提供详细医案信息供LLM引用
                case_info = (
                    f"[医案 {case.get('case_id')}] "
                    f"主诉：{case.get('chief_complaint', '')}；"
                    f"诊断：{disease}（{syndrome}）；"
                    f"方剂：{case.get('treatment', {}).get('herbal_medicine', '')}；"
                    f"饮食建议：{case.get('treatment', {}).get('dietary_advice', '')}"
                )
                scored.append((score, case_info, case.get('case_id')))

        # 按匹配分数排序，取前3个
        scored.sort(key=lambda x: x[0], reverse=True)
        return [(info, cid) for _, info, cid in scored[:3]]

    def _extract_case_references(self, text: str) -> list:
        """从文本中提取医案引用编号"""
        import re
        refs = set()
        # 匹配多种格式：[医案 C001]、医案C001、医案 C001、C001
        patterns = [
            r'医案\s*[A-Z]?\d+',
            r'\[医案\s*([A-Z]?\d+)\]',
            r'(?<![A-Z])C\d{3}',
        ]
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for m in matches:
                # 提取编号
                nums = re.findall(r'C?\d+', m if isinstance(m, str) else '')
                for n in nums:
                    if n.isdigit():
                        refs.add(f'C{n.zfill(3)}' if not n.startswith('C') else n)
        return list(refs)
