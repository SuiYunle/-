from config import Config
from services.llm_service import get_llm_service

print('Provider:', Config.LLM_PROVIDER)
print('Base URL:', Config.LLM_BASE_URL)
print('Model:', Config.LLM_MODEL)
print('Vision Model:', Config.VISION_MODEL)
print('Embedding Model:', Config.EMBEDDING_MODEL)
print('API Key prefix:', Config.LLM_API_KEY[:20] + '...' if Config.LLM_API_KEY else 'NOT SET')

service = get_llm_service(Config)
print('Client initialized:', service.client is not None)