from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseAgent(ABC):
    """Agent基类"""
    
    def __init__(self, name: str, llm_service=None, memory_service=None, 
                 privacy_service=None, config=None):
        self.name = name
        self.llm = llm_service
        self.memory = memory_service
        self.privacy = privacy_service
        self.config = config
    
    @abstractmethod
    def process(self, user_id: int, session_id: str, message: str, **kwargs) -> Dict[str, Any]:
        """处理用户消息，子类必须实现"""
        pass
    
    def build_system_prompt(self) -> str:
        """构建系统提示词，子类可覆盖
        
        默认人设：温暖亲切、专业但不生硬、懂得主动关心、给出可执行建议
        """
        return """你是「小艺」，脉衡界校园健康智能体系统的AI助手。

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

注意：你是健康助手，不是医生。涉及具体诊断时请建议就医。"""
    
    def get_context(self, user_id: int, session_id: str, max_messages: int = 5) -> List[Dict[str, str]]:
        """获取对话上下文"""
        if self.memory:
            return self.memory.build_context_window(user_id, session_id, max_messages)
        return []
    
    def save_message(self, user_id: int, session_id: str, role: str, content: str, 
                     intent: str = None, case_reference: str = None):
        """保存消息到长期记忆"""
        if self.memory:
            self.memory.save_message(user_id, session_id, role, content, 
                                    intent=intent, case_reference=case_reference)
    
    def call_llm(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> str:
        """调用 LLM

        成功返回 AI 回复字符串；失败时返回带 "[LLM错误]" 前缀的友好中文提示，
        上游（coordinator/路由层）可据此识别错误并标记响应。
        """
        if not self.llm:
            return "[LLM错误] LLM 服务未初始化，请联系管理员检查配置"
        try:
            return self.llm.chat(messages, temperature=temperature)
        except Exception as e:
            # LLMError 优先用其 to_user_message；其他异常按 unknown 处理
            to_user = getattr(e, "to_user_message", None)
            if callable(to_user):
                return f"[LLM错误] {to_user()}"
            return f"[LLM错误] AI 调用失败：{str(e)}"
    
    def format_response(self, content: str, case_reference: str = None, 
                       attachments: Dict = None, references: list = None) -> Dict[str, Any]:
        """格式化响应"""
        resp = {
            "agent": self.name,
            "content": content,
            "case_reference": case_reference,
            "references": references or [],
            "timestamp": __import__('datetime').datetime.utcnow().isoformat()
        }
        if attachments:
            resp["attachments"] = attachments
        return resp
