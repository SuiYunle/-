from models import db, Conversation
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json
import pickle

class MemoryService:
    """长期记忆服务 - 管理用户4年健康档案和对话历史"""
    
    def __init__(self, llm_service=None):
        self.llm = llm_service
    
    def save_message(self, user_id: int, session_id: str, role: str, content: str, 
                     msg_type: str = 'text', image_path: str = None, 
                     intent: str = None, case_reference: str = None) -> Conversation:
        """保存单条消息"""
        conv = Conversation(
            user_id=user_id,
            session_id=session_id,
            role=role,
            content=content,
            msg_type=msg_type,
            image_path=image_path,
            intent=intent,
            case_reference=case_reference
        )
        
        # 计算并保存嵌入向量（用于语义检索，失败时静默跳过）
        if self.llm and content:
            try:
                embedding = self.llm.get_embedding(content[:500])
                conv.embedding = pickle.dumps(embedding)
            except Exception:
                pass  # 嵌入计算失败不影响主流程
        
        db.session.add(conv)
        db.session.commit()
        return conv
    
    def get_recent_messages(self, user_id: int, session_id: str = None, 
                           limit: int = 20, days: int = 30) -> List[Dict]:
        """获取近期消息"""
        query = Conversation.query.filter(
            Conversation.user_id == user_id,
            Conversation.created_at >= datetime.utcnow() - timedelta(days=days)
        )
        if session_id:
            query = query.filter(Conversation.session_id == session_id)
        
        msgs = query.order_by(Conversation.created_at.desc()).limit(limit).all()
        return [m.to_dict() for m in reversed(msgs)]
    
    def get_all_history(self, user_id: int, record_type: str = None, 
                       start_date: datetime = None, end_date: datetime = None) -> List[Dict]:
        """获取完整历史档案（支持4年累积）"""
        query = Conversation.query.filter(Conversation.user_id == user_id)
        
        if record_type:
            query = query.filter(Conversation.intent == record_type)
        if start_date:
            query = query.filter(Conversation.created_at >= start_date)
        if end_date:
            query = query.filter(Conversation.created_at <= end_date)
        
        msgs = query.order_by(Conversation.created_at.asc()).all()
        return [m.to_dict() for m in msgs]
    
    def search_memory(self, user_id: int, keyword: str, limit: int = 10) -> List[Dict]:
        """关键词搜索历史记忆"""
        query = Conversation.query.filter(
            Conversation.user_id == user_id,
            Conversation.content.contains(keyword)
        ).order_by(Conversation.created_at.desc()).limit(limit)
        
        return [m.to_dict() for m in query.all()]
    
    def build_context_window(self, user_id: int, session_id: str, 
                            max_messages: int = 10) -> List[Dict[str, str]]:
        """构建LLM上下文窗口"""
        messages = self.get_recent_messages(user_id, session_id, limit=max_messages)
        context = []
        for msg in messages:
            context.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        return context
    
    def get_health_summary(self, user_id: int) -> Dict[str, Any]:
        """生成用户健康摘要（用于快速了解用户历史）"""
        # 获取最近6个月的对话
        six_months_ago = datetime.utcnow() - timedelta(days=180)
        recent = Conversation.query.filter(
            Conversation.user_id == user_id,
            Conversation.created_at >= six_months_ago
        ).all()
        
        # 统计
        intents = {}
        for conv in recent:
            intent = conv.intent or 'general'
            intents[intent] = intents.get(intent, 0) + 1
        
        # 获取最新消息
        latest = Conversation.query.filter_by(user_id=user_id).order_by(
            Conversation.created_at.desc()
        ).first()
        
        return {
            'total_conversations': len(recent),
            'intent_distribution': intents,
            'last_active': latest.created_at.isoformat() if latest else None,
            'coverage_months': 6
        }
    
    def clear_session(self, user_id: int, session_id: str):
        """清空指定会话"""
        Conversation.query.filter_by(user_id=user_id, session_id=session_id).delete()
        db.session.commit()
    
    def delete_all_user_data(self, user_id: int):
        """删除用户所有数据（隐私合规 - 用户有权删除）"""
        Conversation.query.filter_by(user_id=user_id).delete()
        db.session.commit()

# 单例
_memory_service = None

def get_memory_service(llm_service=None):
    global _memory_service
    if _memory_service is None:
        _memory_service = MemoryService(llm_service)
    return _memory_service
