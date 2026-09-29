import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # 基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'zhiyi-health-ai-dev-key-2024'
    
    # 数据库（使用相对路径，避免改文件夹名后出错）
    _BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(_BASE_DIR, 'data', 'zhiyi.db').replace('\\', '/')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 上传配置
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'uploads', 'images')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # ==================== LLM 文本模型 (DeepSeek为主力) ====================
    LLM_PROVIDER = os.environ.get('LLM_PROVIDER') or 'deepseek'  # deepseek/openai/volcano/aliyun/zhipu
    LLM_API_KEY = os.environ.get('LLM_API_KEY') or 'sk-8bc733dbfe9244f8b0782cea823bc94d'
    LLM_BASE_URL = os.environ.get('LLM_BASE_URL') or 'https://api.deepseek.com/v1'
    LLM_MODEL = os.environ.get('LLM_MODEL') or 'deepseek-chat'
    
    # ==================== 视觉模型 (舌象/餐食分析) - 独立配置 ====================
    # DeepSeek暂不支持视觉，需单独配置支持多模态的模型
    VISION_PROVIDER = os.environ.get('VISION_PROVIDER') or LLM_PROVIDER
    VISION_API_KEY = os.environ.get('VISION_API_KEY') or LLM_API_KEY
    VISION_BASE_URL = os.environ.get('VISION_BASE_URL') or LLM_BASE_URL
    VISION_MODEL = os.environ.get('VISION_MODEL') or LLM_MODEL
    
    # ==================== 嵌入模型 (向量检索/RAG) - 独立配置 ====================
    # DeepSeek暂无嵌入API，需单独配置
    EMBEDDING_PROVIDER = os.environ.get('EMBEDDING_PROVIDER') or LLM_PROVIDER
    EMBEDDING_API_KEY = os.environ.get('EMBEDDING_API_KEY') or LLM_API_KEY
    EMBEDDING_BASE_URL = os.environ.get('EMBEDDING_BASE_URL') or LLM_BASE_URL
    EMBEDDING_MODEL = os.environ.get('EMBEDDING_MODEL') or 'text-embedding-3-small'
    
    # 隐私加密密钥（必须妥善保管）
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY') or b'zhiyi-health-encryption-key-32bytes!'
    
    # 心理预警阈值
    MENTAL_ALERT_THRESHOLD = 60  # 低于60分触发预警
    
    # 激励积分配置
    REWARD_CHAT_PER_MESSAGE = 3
    REWARD_DAILY_DIARY = 5
    REWARD_DAILY_LOGIN = 5
    REWARD_MAX_DAILY = 100
    REWARD_WELCOME_BONUS = 30  # 新用户注册欢迎积分
    
    # 健康微社区外链配置
    COMMUNITY_LINKS = [
        {"name": "国家医保服务平台", "url": "https://fuwu.nhsa.gov.cn", "icon": "shield"},
        {"name": "国家卫生健康委员会", "url": "http://www.nhc.gov.cn", "icon": "hospital"},
        {"name": "中国居民膳食指南", "url": "http://dg.cnsoc.org", "icon": "book"},
        {"name": "国家统计局健康数据", "url": "https://data.stats.gov.cn", "icon": "chart"},
        {"name": "中国疾病预防控制中心", "url": "https://www.chinacdc.cn", "icon": "bug"},
        {"name": "心理健康教育与咨询", "url": "https://www.mohurd.gov.cn", "icon": "heart"},
    ]
    
    # 健康资讯推送内容
    HEALTH_NEWS_FEED = [
        {
            "id": "n001",
            "category": "中医养生",
            "title": "立秋养生：润肺防燥正当时",
            "summary": "立秋后气候逐渐干燥，中医认为秋季对应肺脏，应注意润肺养阴。推荐食用银耳、百合、梨等润肺食材，避免辛辣刺激。",
            "content": "立秋是秋季的第一个节气，标志着孟秋时节的正式开始。中医认为，秋季对应肺脏，燥为秋季主气。立秋后气候逐渐干燥，容易出现口干、鼻干、咽干、皮肤干燥等症状。\n\n养生要点：\n1. 饮食调养：多食银耳、百合、莲藕、梨、蜂蜜等润肺生津之品；少食葱、姜、蒜、辣椒等辛辣刺激食物。\n2. 起居调摄：早卧早起，与鸡俱兴，使志安宁，以缓秋刑。\n3. 运动养生：可选择太极拳、八段锦等柔和运动，避免大汗淋漓。\n4. 精神调养：秋内应于肺，肺在志为忧，应保持心情舒畅，避免悲忧情绪。",
            "source": "中华中医药学会",
            "tags": ["秋季养生", "润肺", "食疗"],
            "image_icon": "fa-leaf"
        },
        {
            "id": "n002",
            "category": "心理健康",
            "title": "开学季心理调适指南：如何应对开学焦虑",
            "summary": "新学期开始，不少同学会出现焦虑、失眠等情绪。本文提供5个实用的心理调适方法，帮助你快速适应新学期。",
            "content": "开学季是心理问题的高发期。面对新学期的学业压力、人际关系变化，很多同学会出现不同程度的焦虑情绪。\n\n5个调适方法：\n1. 接纳情绪：允许自己有不安和焦虑，这是正常的反应。\n2. 重建规律：提前调整作息，恢复规律的睡眠和饮食。\n3. 社交连接：主动联系同学，重建社交支持网络。\n4. 目标分解：将大目标分解为小任务，逐步完成。\n5. 正念练习：每天5分钟深呼吸或冥想，缓解紧张情绪。\n\n如果持续两周以上情绪低落、失眠，建议寻求学校心理咨询中心帮助。",
            "source": "教育部高校心理健康教育专家委员会",
            "tags": ["开学焦虑", "心理调适", "睡眠"],
            "image_icon": "fa-brain"
        },
        {
            "id": "n003",
            "category": "营养膳食",
            "title": "大学生均衡膳食指南：一日三餐怎么吃",
            "summary": "中国营养学会发布最新膳食指南，建议大学生每天摄入12种以上食物，每周25种以上。一文读懂怎么吃才健康。",
            "content": "《中国居民膳食指南（2022）》核心建议：\n\n1. 食物多样，合理搭配\n   - 每天摄入12种以上食物，每周25种以上\n   - 谷薯类为主食，每天200-300g\n\n2. 多吃蔬果、奶类、全谷、大豆\n   - 餐餐有蔬菜，每天不少于300g\n   - 天天吃水果，每天200-350g\n   - 每天一杯奶（300ml以上）\n\n3. 适量吃鱼、禽、蛋、瘦肉\n   - 每周吃鱼2次或300-500g\n   - 每天一个鸡蛋\n\n4. 少盐少油，控糖限酒\n   - 每天食盐不超过5g\n   - 每天烹调油25-30g\n   - 每天糖摄入不超过50g\n\n5. 规律进餐，足量饮水\n   - 三餐定时定量\n   - 每天饮水1500-1700ml",
            "source": "中国营养学会",
            "tags": ["膳食指南", "营养", "大学生健康"],
            "image_icon": "fa-utensils"
        },
        {
            "id": "n004",
            "category": "疾病预防",
            "title": "秋冬季节流感预防全攻略",
            "summary": "秋冬是流感高发季，接种疫苗、勤洗手、戴口罩是三大防线。中医也有预防妙招，一起来看看。",
            "content": "秋冬流感预防攻略：\n\n【现代医学预防】\n1. 接种流感疫苗（每年9-10月最佳）\n2. 勤洗手，使用七步洗手法\n3. 室内通风，每天2-3次，每次30分钟\n4. 在人群密集场所佩戴口罩\n5. 出现症状及时就医，避免带病上课\n\n【中医预防】\n1. 艾灸足三里、大椎穴，增强免疫力\n2. 佩戴中药香囊（藿香、佩兰、苍术等）\n3. 金银花、菊花泡水代茶饮\n4. 起居有常，避免熬夜耗伤正气\n5. 食疗：葱白生姜汤、萝卜排骨汤\n\n【运动增强】\n每天30分钟中等强度运动，如快走、慢跑、八段锦等。",
            "source": "中国疾病预防控制中心",
            "tags": ["流感预防", "秋冬养生", "疫苗接种"],
            "image_icon": "fa-shield-virus"
        },
        {
            "id": "n005",
            "category": "运动健康",
            "title": "科学运动不受伤：大学生运动指南",
            "summary": "运动前热身5-10分钟，运动后拉伸放松，每周150分钟中等强度运动。掌握科学运动方法，远离运动损伤。",
            "content": "科学运动指南：\n\n1. 运动前准备\n   - 热身5-10分钟（慢跑、动态拉伸）\n   - 检查运动装备和场地安全\n   - 运动前1小时适量进食\n\n2. 运动强度\n   - 每周至少150分钟中等强度有氧运动\n   - 或75分钟高强度有氧运动\n   - 每周2-3次力量训练\n\n3. 运动后恢复\n   - 静态拉伸每个动作保持15-30秒\n   - 补充水分和电解质\n   - 运动后30分钟内补充蛋白质\n\n4. 常见损伤预防\n   - 踝关节扭伤：选择合适运动鞋\n   - 膝关节损伤：避免过度跑步\n   - 肌肉拉伤：充分热身，循序渐进\n\n5. 运动禁忌\n   - 发热、感冒时避免剧烈运动\n   - 饭后1小时内不剧烈运动\n   - 空腹不宜长时间运动",
            "source": "国家体育总局",
            "tags": ["科学运动", "运动损伤", "体育健身"],
            "image_icon": "fa-person-running"
        },
        {
            "id": "n006",
            "category": "中医养生",
            "title": "九种体质自查：你是哪种体质？",
            "summary": "中华中医药学会将人体体质分为九种类型。了解自己的体质，才能有针对性地养生调理。",
            "content": "中医九种体质分类：\n\n1. 平和质（最健康）\n   体形匀称，精力充沛，睡眠良好\n\n2. 气虚质\n   容易疲乏，气短懒言，易出虚汗\n   调理：黄芪、党参、山药\n\n3. 阳虚质\n   手脚发凉，怕冷，喜热饮\n   调理：羊肉、生姜、桂圆\n\n4. 阴虚质\n   手脚心热，口干咽燥，便秘\n   调理：银耳、百合、枸杞\n\n5. 痰湿质\n   体形肥胖，腹部肥满，身体沉重\n   调理：薏米、冬瓜、陈皮\n\n6. 湿热质\n   面部油腻，易生痤疮，口苦口臭\n   调理：绿豆、苦瓜、薏米\n\n7. 血瘀质\n   皮肤瘀斑，肤色晦暗，黑眼圈\n   调理：山楂、桃仁、红花\n\n8. 气郁质\n   情绪低落，多愁善感，容易紧张\n   调理：玫瑰花、佛手、柑橘\n\n9. 特禀质\n   过敏体质，容易打喷嚏，起荨麻疹\n   调理：灵芝、红枣、蜂蜜\n\n推荐使用平台的「中医体质辨识」功能进行专业测评。",
            "source": "中华中医药学会",
            "tags": ["体质辨识", "九种体质", "中医养生"],
            "image_icon": "fa-hand-holding-medical"
        }
    ]
    
    # 三下乡/运动会扩展配置
    EXTENSION_MODULES = {
        "rural_medical": {"name": "三下乡医疗帮扶", "enabled": True},
        "sports_assessment": {"name": "运动会赛前评估", "enabled": True},
    }
