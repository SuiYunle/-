"""LLM 服务层 - 统一的 AI 调用入口

设计原则：
1. 健壮性：自动重试可恢复的网络错误（指数退避 1s→2s→4s）
2. 错误分类：区分网络错/超时/鉴权/配额/模型不可用
3. 启动自检：首次创建客户端时发一个 1-token 测试请求验证 API key
4. 失败明确：返回特殊错误对象 LLMError，上游可识别（不再把"系统错误"字符串伪装成 AI 回复）
5. 降级：未配置 API key 时返回 _mock_response（演示模式）
"""
import os
import json
import base64
import time
import hashlib
import struct
from typing import List, Dict, Any, Optional, Union
from openai import OpenAI
import httpx


class LLMError(Exception):
    """LLM 调用失败的统一错误类型

    kind:
      - network       连接/读取超时、DNS 失败、TLS 错误等可重试错误
      - timeout       请求超时
      - auth          401/403 鉴权失败（API key 错）
      - quota         429 余额/配额不足
      - server        5xx 上游服务异常
      - client        4xx 客户端请求错误（如模型不存在）
      - unknown       其他
    """

    def __init__(self, message: str, kind: str = "unknown",
                 status_code: Optional[int] = None, retryable: bool = False):
        super().__init__(message)
        self.kind = kind
        self.status_code = status_code
        self.retryable = retryable

    def to_user_message(self) -> str:
        """面向最终用户的中文提示"""
        m = {
            "network": "网络连接失败，请检查网络后重试",
            "timeout": "AI 响应超时，请稍后重试",
            "auth": "AI 服务鉴权失败，请检查 API Key 配置",
            "quota": "AI 服务配额不足，请联系管理员",
            "server": "AI 服务暂不可用，请稍后重试",
            "client": "AI 请求参数有误，请联系管理员",
            "unknown": "AI 服务异常，请稍后重试",
        }
        return m.get(self.kind, m["unknown"]) + f"（详情：{self.args[0]}）"


def _classify_openai_error(e: Exception) -> LLMError:
    """把 OpenAI SDK 抛出的异常分类成 LLMError"""
    # 直接透传
    if isinstance(e, LLMError):
        return e

    # httpx 超时
    if isinstance(e, (httpx.TimeoutException, httpx.ReadTimeout,
                      httpx.ConnectTimeout)):
        return LLMError(str(e), kind="timeout", retryable=True)

    # httpx 网络层错误
    if isinstance(e, (httpx.ConnectError, httpx.ReadError,
                      httpx.NetworkError, httpx.RemoteProtocolError)):
        return LLMError(str(e), kind="network", retryable=True)

    # OpenAI APIStatusError（带 status_code）
    status_code = getattr(e, "status_code", None)
    if status_code is not None:
        body = ""
        try:
            body = str(getattr(e, "body", "") or "")
        except Exception:
            body = str(e)

        if status_code in (401, 403):
            return LLMError(f"HTTP {status_code}: {body}",
                            kind="auth", status_code=status_code,
                            retryable=False)
        if status_code == 429:
            return LLMError(f"HTTP 429: {body}",
                            kind="quota", status_code=status_code,
                            retryable=True)
        if 500 <= status_code < 600:
            return LLMError(f"HTTP {status_code}: {body}",
                            kind="server", status_code=status_code,
                            retryable=True)
        if 400 <= status_code < 500:
            return LLMError(f"HTTP {status_code}: {body}",
                            kind="client", status_code=status_code,
                            retryable=False)

    # APIConnectionError（OpenAI SDK 的网络层）
    name = type(e).__name__
    if "Connection" in name or "APITimeout" in name:
        return LLMError(str(e), kind="network", retryable=True)

    return LLMError(str(e), kind="unknown", retryable=False)


class LLMService:
    """LLM 服务层 - 支持文本、视觉、嵌入多客户端

    对外主要方法：
      chat(messages, ...)            文本对话，返回 str 或抛 LLMError
      chat_with_image(messages, ...) 视觉对话
      analyze_image_base64(...)
      analyze_image_file(...)
      get_embedding(text, ...)
      health_check()                启动/手动调用的连通性自检
    """

    # 重试参数
    MAX_RETRIES = 3
    BACKOFF_BASE = 1.0  # 秒，指数退避基数：1, 2, 4

    def __init__(self, config):
        self.config = config
        self.text_client: Optional[OpenAI] = None
        self.vision_client: Optional[OpenAI] = None
        self.embedding_client: Optional[OpenAI] = None
        self._init_clients()

    # ==================== 客户端创建 ====================
    def _create_client(self, api_key: str, base_url: str) -> Optional[OpenAI]:
        """创建 OpenAI 兼容客户端"""
        if not api_key:
            return None
        try:
            # 缩短超时，让前端能快速失败而不是一直 hang
            return OpenAI(
                api_key=api_key,
                base_url=base_url,
                timeout=httpx.Timeout(60.0, connect=15.0),
                max_retries=0,  # 由本层手动重试
            )
        except Exception as e:
            print(f"[LLM] 客户端初始化失败: {e}")
            return None

    def _init_clients(self):
        """初始化三类客户端"""
        # 1. 文本客户端 (主力: DeepSeek)
        self.text_client = self._create_client(
            self.config.LLM_API_KEY,
            self.config.LLM_BASE_URL
        )
        if self.text_client:
            print(f"[LLM] 文本客户端就绪: {self.config.LLM_PROVIDER} / {self.config.LLM_MODEL}")

        # 2. 视觉客户端 (需多模态)
        vision_key = getattr(self.config, "VISION_API_KEY", None)
        vision_url = getattr(self.config, "VISION_BASE_URL", None)
        if vision_key and vision_key != self.config.LLM_API_KEY:
            self.vision_client = self._create_client(vision_key, vision_url)
            if self.vision_client:
                print(f"[LLM] 视觉客户端就绪: "
                      f"{getattr(self.config, 'VISION_PROVIDER', 'same')} / "
                      f"{getattr(self.config, 'VISION_MODEL', 'same')}")
        else:
            self.vision_client = self.text_client

        # 3. 嵌入客户端
        emb_key = getattr(self.config, "EMBEDDING_API_KEY", None)
        emb_url = getattr(self.config, "EMBEDDING_BASE_URL", None)
        if emb_key and emb_key != self.config.LLM_API_KEY:
            self.embedding_client = self._create_client(emb_key, emb_url)
            if self.embedding_client:
                print(f"[LLM] 嵌入客户端就绪: "
                      f"{getattr(self.config, 'EMBEDDING_PROVIDER', 'same')} / "
                      f"{getattr(self.config, 'EMBEDDING_MODEL', 'same')}")
        else:
            self.embedding_client = self.text_client

    # ==================== 启动自检 ====================
    def health_check(self) -> Dict[str, Any]:
        """发一个最小请求验证 API key 可用。返回 {ok, message}"""
        if not self.text_client:
            return {"ok": False, "message": "未配置文本客户端（缺 API Key）",
                    "kind": "config"}
        try:
            resp = self.text_client.chat.completions.create(
                model=self.config.LLM_MODEL,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=1,
                temperature=0,
            )
            return {"ok": True,
                    "message": f"OK，模型回复: {resp.choices[0].message.content!r}",
                    "kind": "ok"}
        except Exception as e:
            err = _classify_openai_error(e)
            return {"ok": False, "message": str(err),
                    "kind": err.kind, "retryable": err.retryable}

    # ==================== 核心调用 ====================
    def _chat_with_retry(self, client: OpenAI, model: str,
                         messages: List[Dict[str, Any]],
                         temperature: float, max_tokens: int) -> str:
        """带重试的对话调用 - 失败抛 LLMError"""
        last_error: Optional[LLMError] = None
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                content = response.choices[0].message.content
                if not content:
                    # 极少情况下空回复，按错误处理
                    raise LLMError("AI 返回空回复",
                                   kind="server", retryable=True)
                return content
            except LLMError as e:
                last_error = e
            except Exception as e:
                last_error = _classify_openai_error(e)

            # 不可重试错误：直接抛
            if not last_error.retryable:
                break

            # 可重试错误：等待后重试（最后一次不用 sleep）
            if attempt < self.MAX_RETRIES:
                wait = self.BACKOFF_BASE * (2 ** (attempt - 1))
                print(f"[LLM] 第 {attempt} 次调用失败（{last_error.kind}），"
                      f"{wait:.1f}s 后重试: {last_error.args[0]}")
                time.sleep(wait)

        # 重试耗尽
        raise last_error if last_error else LLMError("未知错误", kind="unknown")

    # ==================== 文本对话 ====================
    def chat(self, messages: List[Dict[str, str]],
             model: str = None, temperature: float = 0.7,
             max_tokens: int = 2048) -> str:
        """通用文本对话 - 使用 text_client (DeepSeek)

        成功返回 AI 回复 str；失败抛 LLMError（上游 catch 后显示给用户）。
        """
        if not self.text_client:
            # 演示模式：未配置 API key 时返回模拟回复
            return self._mock_response(messages)

        model = model or self.config.LLM_MODEL
        try:
            return self._chat_with_retry(
                self.text_client, model, messages,
                temperature=temperature, max_tokens=max_tokens
            )
        except LLMError:
            raise
        except Exception as e:
            raise _classify_openai_error(e)

    # ==================== 多模态对话 (视觉) ====================
    def chat_with_image(self, messages: List[Dict[str, Any]],
                        model: str = None, temperature: float = 0.7,
                        max_tokens: int = 2048) -> str:
        """多模态对话 - 使用 vision_client"""
        client = self.vision_client or self.text_client
        if not client:
            return "[模拟模式] 图片已接收，但未配置视觉模型 API Key。"

        vision_model = model or getattr(self.config, "VISION_MODEL",
                                        self.config.LLM_MODEL)
        # DeepSeek 不支持视觉
        if "deepseek" in vision_model.lower() and not vision_model.startswith("gpt-"):
            return "[系统提示] 当前视觉模型不支持图片分析。请配置支持多模态的模型(如 GPT-4o、豆包、GLM-4V)。"

        try:
            return self._chat_with_retry(
                client, vision_model, messages,
                temperature=temperature, max_tokens=max_tokens
            )
        except LLMError as e:
            # 视觉失败不抛，返回提示文字（图片分析不是关键路径）
            return f"[系统错误] 视觉分析失败: {e.to_user_message()}"
        except Exception as e:
            err = _classify_openai_error(e)
            return f"[系统错误] 视觉分析失败: {err.to_user_message()}"

    def analyze_image_base64(self, image_base64: str, prompt: str,
                              model: str = None) -> str:
        """分析 Base64 编码的图片"""
        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url",
                 "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
            ]
        }]
        return self.chat_with_image(messages, model=model)

    def analyze_image_file(self, image_path: str, prompt: str,
                            model: str = None) -> str:
        """分析本地图片文件"""
        try:
            with open(image_path, "rb") as f:
                image_data = f.read()
            image_base64 = base64.b64encode(image_data).decode("utf-8")
            return self.analyze_image_base64(image_base64, prompt, model)
        except Exception as e:
            return f"[错误] 读取图片失败: {str(e)}"

    # ==================== 嵌入向量 ====================
    def get_embedding(self, text: str, model: str = None) -> List[float]:
        """获取文本嵌入向量"""
        client = self.embedding_client or self.text_client
        emb_model = model or getattr(self.config, "EMBEDDING_MODEL",
                                       "text-embedding-3-small")

        # DeepSeek 不支持 embeddings，降级到 hash
        if not client or "deepseek" in emb_model.lower():
            return self._hash_embedding(text)

        try:
            response = client.embeddings.create(
                model=emb_model,
                input=text
            )
            return response.data[0].embedding
        except Exception:
            return self._hash_embedding(text)

    def _hash_embedding(self, text: str, dim: int = 768) -> List[float]:
        """基于文本 hash 的确定性伪嵌入向量（降级方案）"""
        h = hashlib.sha256(text.encode("utf-8")).digest()
        vector = []
        for i in range(dim):
            byte_idx = (i * 4) % len(h)
            chunk = h[byte_idx:byte_idx + 4] if byte_idx + 4 <= len(h) else h[:4]
            val = struct.unpack("I", chunk)[0]
            vector.append((val / 0xFFFFFFFF) * 2 - 1)
        return vector

    # ==================== 模拟模式 ====================
    def _mock_response(self, messages: List[Dict[str, str]]) -> str:
        user_msg = ""
        for msg in messages:
            if msg.get("role") == "user":
                user_msg = msg.get("content", "")
                break

        if "舌" in user_msg or "苔" in user_msg:
            return "【模拟模式】舌象分析：舌淡红，苔薄白，属正常。建议规律作息，饮食清淡。"
        elif "心理" in user_msg or "压力" in user_msg or "焦虑" in user_msg:
            return ("【模拟模式】理解你的压力。建议：1.规律作息 2.适度运动 "
                    "3.倾诉交流 4.必要时寻求专业帮助。")
        elif "食谱" in user_msg or "饮食" in user_msg:
            return ("【模拟模式】推荐：早餐-小米粥蒸蛋；"
                    "午餐-清蒸鱼炒时蔬；晚餐-山药粥凉拌黄瓜。")
        else:
            return "【模拟模式】收到问题。未配置 API Key 时为模拟回复。"


# ==================== 单例 ====================
_llm_service = None


def get_llm_service(config=None):
    global _llm_service
    if _llm_service is None and config is not None:
        _llm_service = LLMService(config)
    return _llm_service
