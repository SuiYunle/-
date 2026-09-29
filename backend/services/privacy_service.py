from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import hashlib
import json

class PrivacyService:
    """隐私安全服务 - 数据加密、脱敏、完整性校验"""
    
    def __init__(self, key: bytes = None):
        if key is None:
            # 使用默认密钥（生产环境必须从环境变量读取）
            key = b'zhiyi-health-encryption-key-32bytes!'
        self.cipher = self._create_cipher(key)
    
    def _create_cipher(self, key: bytes):
        """创建加密器"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'zhiyi_fixed_salt_16b',
            iterations=100000,
        )
        key_derived = base64.urlsafe_b64encode(kdf.derive(key))
        return Fernet(key_derived)
    
    def encrypt(self, data: str) -> str:
        """加密字符串"""
        if not data:
            return None
        return self.cipher.encrypt(data.encode('utf-8')).decode('utf-8')
    
    def decrypt(self, encrypted_data: str) -> str:
        """解密字符串"""
        if not encrypted_data:
            return None
        try:
            return self.cipher.decrypt(encrypted_data.encode('utf-8')).decode('utf-8')
        except Exception as e:
            print(f"[解密错误] {e}")
            return None
    
    def encrypt_dict(self, data: dict) -> str:
        """加密字典"""
        return self.encrypt(json.dumps(data, ensure_ascii=False))
    
    def decrypt_dict(self, encrypted_data: str) -> dict:
        """解密为字典"""
        decrypted = self.decrypt(encrypted_data)
        if decrypted:
            return json.loads(decrypted)
        return {}
    
    def hash_data(self, data: str) -> str:
        """计算数据哈希（用于完整性校验）"""
        return hashlib.sha256(data.encode('utf-8')).hexdigest()
    
    def mask_phone(self, phone: str) -> str:
        """手机号脱敏"""
        if not phone or len(phone) < 7:
            return phone
        return phone[:3] + '****' + phone[-4:]
    
    def mask_name(self, name: str) -> str:
        """姓名脱敏"""
        if not name:
            return name
        if len(name) == 2:
            return name[0] + '*'
        return name[0] + '*' * (len(name) - 2) + name[-1]
    
    def mask_student_id(self, sid: str) -> str:
        """学号脱敏"""
        if not sid or len(sid) < 4:
            return sid
        return sid[:2] + '****' + sid[-2:]
    
    def desensitize_mental_summary(self, text: str) -> str:
        """心理健康摘要脱敏"""
        if not text:
            return text
        # 移除可能暴露身份的信息
        import re
        # 移除具体人名
        # 保留核心心理状态描述，模糊化具体事件细节
        lines = text.split('\n')
        filtered = []
        for line in lines:
            if any(kw in line for kw in ['姓名', '学号', '班级', '电话', '宿舍', '身份证号']):
                continue
            filtered.append(line)
        return '\n'.join(filtered[:5])  # 只保留前5行

# 单例
_privacy_service = None

def get_privacy_service(key=None):
    global _privacy_service
    if _privacy_service is None:
        _privacy_service = PrivacyService(key)
    return _privacy_service
