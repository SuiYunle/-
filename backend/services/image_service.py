import os
import json
from models import db, ImageAnalysis
from typing import Dict, Any

class ImageService:
    """多模态图像分析服务"""
    
    def __init__(self, llm_service=None):
        self.llm = llm_service
    
    def analyze_tongue(self, image_path: str, user_id: int = None) -> Dict[str, Any]:
        """舌苔分析"""
        prompt = """你是一位中医专家，请仔细分析这张舌象照片，并给出以下信息：
1. 舌色（淡红/红/绛/紫/淡白等）
2. 舌苔（薄白/厚腻/黄腻/少苔/剥苔等）
3. 舌形（胖大/瘦薄/齿痕/裂纹等）
4. 综合分析的体质倾向
5. 初步的中医辨证
6. 调理建议

请以JSON格式输出，包含以下字段：
{
  "tongue_color": "舌色",
  "coating": "舌苔",
  "tongue_shape": "舌形",
  "constitution": "体质倾向",
  "syndrome": "辨证",
  "suggestions": "调理建议",
  "confidence": "高/中/低"
}"""
        
        result_text = self.llm.analyze_image_file(image_path, prompt) if self.llm else "模拟分析结果"
        
        # 尝试解析JSON
        result = self._extract_json(result_text)
        if not result:
            result = {
                "tongue_color": "分析中",
                "coating": "分析中",
                "tongue_shape": "分析中",
                "constitution": "分析中",
                "syndrome": "分析中",
                "suggestions": result_text,
                "confidence": "低",
                "raw_response": result_text
            }
        
        # 保存记录
        if user_id:
            self._save_analysis(user_id, 'tongue', image_path, result)
        
        return result
    
    def analyze_meal(self, image_path: str, user_id: int = None, constitution: str = None) -> Dict[str, Any]:
        """餐食分析"""
        prompt = f"""你是一位营养师和中医食疗专家，请分析这张餐食照片：
1. 识别食物种类和大概分量
2. 估算总热量和营养成分
3. 从中医角度分析是否适合{constitution or '当前'}体质
4. 给出改进建议

请以JSON格式输出：
{{
  "foods": ["食物1", "食物2"],
  "estimated_calories": "估算热量",
  "nutrition_analysis": "营养分析",
  "tcm_suitability": "中医适宜性评价",
  "suggestions": "改进建议"
}}"""
        
        result_text = self.llm.analyze_image_file(image_path, prompt) if self.llm else "模拟分析结果"
        result = self._extract_json(result_text)
        if not result:
            result = {
                "foods": [],
                "estimated_calories": "分析中",
                "nutrition_analysis": "分析中",
                "tcm_suitability": "分析中",
                "suggestions": result_text,
                "raw_response": result_text
            }
        
        if user_id:
            self._save_analysis(user_id, 'meal', image_path, result)
        
        return result
    
    def _extract_json(self, text: str) -> Dict:
        """从文本中提取JSON"""
        import re
        try:
            # 尝试找到JSON代码块
            match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
            if match:
                return json.loads(match.group(1))
            
            # 尝试找到花括号包裹的内容
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                return json.loads(match.group(0))
        except Exception:
            pass
        return None
    
    def _save_analysis(self, user_id: int, image_type: str, image_path: str, result: Dict):
        """保存分析记录"""
        analysis = ImageAnalysis(
            user_id=user_id,
            image_type=image_type,
            image_path=image_path,
            analysis_result=json.dumps(result, ensure_ascii=False)
        )
        db.session.add(analysis)
        db.session.commit()

# 单例
_image_service = None

def get_image_service(llm_service=None):
    global _image_service
    if _image_service is None:
        _image_service = ImageService(llm_service)
    return _image_service
