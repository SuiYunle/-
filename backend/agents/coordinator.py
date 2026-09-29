from typing import Dict, Any
from agents.base_agent import BaseAgent

class CoordinatorAgent(BaseAgent):
    """协调Agent - 意图识别和路由分发"""
    
    def __init__(self, llm_service=None, memory_service=None, privacy_service=None, config=None):
        super().__init__("协调Agent", llm_service, memory_service, privacy_service, config)
        self.agents = {}
    
    def register_agent(self, intent: str, agent: BaseAgent):
        """注册子Agent"""
        self.agents[intent] = agent
    
    def detect_intent(self, message: str) -> str:
        """意图识别 - 优先匹配中医关键词，避免中医症状被误判为心理问题"""
        message = message.lower()

        # 中医问诊相关（含医案库覆盖的所有核心症状词）—— 优先检查
        tcm_keywords = [
            # 中医理论词
            '舌', '苔', '体质', '调理', '中药', '针灸', '经络', '养生', '食疗', '气虚', '阳虚', '阴虚',
            '痰湿', '湿热', '气郁', '肝气', '脾虚', '气血', '阴阳', '方剂', '当归', '枸杞',
            # 医案库症状词（C001-C005覆盖）
            '咳嗽', '痰', '咽痛', '口渴', '多饮', '多食', '消渴',
            '胃痛', '胃脘', '胁', '嗳气', '月经不调', '月经',
            '眩晕', '头晕', '头痛', '头疼', '腰膝', '酸软', '乏力', '疲劳',
            # 阴虚/阳虚相关症状（常见但容易被误判为心理问题）
            '失眠', '多梦', '口干', '咽燥', '咽干', '手脚心热', '五心烦热',
            '潮热', '盗汗', '手脚发凉', '怕冷', '便秘', '腹泻', '腹胀',
            '食欲', '胃口', '消化', '脾', '胃', '肝', '肾', '脉',
            # 体质类型词
            '气虚质', '阳虚质', '阴虚质', '痰湿质', '湿热质', '血瘀质', '气郁质', '特禀质', '平和质',
            '医案',
        ]
        tcm_score = sum(1 for kw in tcm_keywords if kw in message)

        # 心理健康相关
        mental_keywords = ['心理', '压力', '焦虑', '抑郁', '情绪', '紧张', '考试', '学业', '心情不好', '难过', '想哭', '崩溃', '自闭']
        mental_score = sum(1 for kw in mental_keywords if kw in message)

        # 优先路由到中医（中医症状更具体，如"失眠多梦+手脚心热"明显是阴虚而非心理问题）
        if tcm_score > 0 and tcm_score >= mental_score:
            return 'tcm'
        if mental_score > 0:
            return 'mental'
        
        # 诊断相关（一般症状描述，不涉及医案库的）
        diagnosis_keywords = ['痛', '不舒服', '症状', '感冒', '发烧', '头疼', '肚子疼', '恶心']
        if any(kw in message for kw in diagnosis_keywords):
            return 'diagnosis'
        
        # 三下乡/运动会
        if any(kw in message for kw in ['三下乡', '下乡', '帮扶', '运动会', '比赛', '赛前', '运动']):
            return 'diagnosis'
        
        # 默认通用对话
        return 'general'
    
    def process(self, user_id: int, session_id: str, message: str, **kwargs) -> Dict[str, Any]:
        """协调处理 - 识别意图并路由到对应Agent"""
        force_intent = kwargs.get('force_intent')
        intent = force_intent if force_intent and force_intent in self.agents else self.detect_intent(message)
        
        # 保存用户消息（带意图标签）
        self.save_message(user_id, session_id, "user", message, intent=intent)
        
        # 路由到对应Agent
        agent = self.agents.get(intent)
        if agent:
            response = agent.process(user_id, session_id, message, **kwargs)
            response['intent'] = intent
            return response
        
        # 没有匹配的Agent，使用通用回复
        return self._general_response(user_id, session_id, message)
    
    def _general_response(self, user_id: int, session_id: str, message: str) -> Dict[str, Any]:
        """通用回复"""
        context = self.get_context(user_id, session_id)
        messages = [
            {"role": "system", "content": """你是「小艺」，脉衡界校园健康智能体系统的AI助手。

你的性格特点：
- 温暖亲切，像一位关心你的学长学姐
- 专业但不生硬，善于用通俗的语言解释医学知识
- 会主动关心用户，适时追问细节
- 回答有结构感，用分段和emoji让内容更易读
- 会给出具体的、可执行的建议，而不是空泛的道理

回答格式要求：
1. 先共情/理解用户的问题
2. 给出结构化的专业回答（可用分段、编号）
3. 补充实用建议或注意事项
4. 以一个温暖的跟进问题结尾（如"你最近还有其他不舒服吗？"）

注意：你是健康助手，不是医生。涉及具体诊断时请建议就医。"""}
        ]
        messages.extend(context)
        messages.append({"role": "user", "content": message})
        
        content = self.call_llm(messages, temperature=0.8)
        
        # 保存助手回复
        self.save_message(user_id, session_id, "assistant", content, intent="general")
        
        return self.format_response(content)
