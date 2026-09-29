import json
import random
from datetime import datetime
from typing import Dict, List, Any, Optional
from models import db, FoodCategory, FoodItem, DietRecommendation, User

class DietService:
    """膳食推荐服务 - 算法推荐 + AI精细推荐"""
    
    # 活动系数
    ACTIVITY_FACTORS = {
        'sedentary': 1.2,      # 久坐不动
        'light': 1.375,        # 轻度活动
        'moderate': 1.55,      # 中度活动
        'active': 1.725,       # 高度活动
        'very_active': 1.9     # 极高活动
    }
    
    # 目标调整系数
    GOAL_FACTORS = {
        'maintain': 1.0,       # 维持
        'lose_weight': 0.85,   # 减肥 -15%
        'gain_muscle': 1.15,   # 增肌 +15%
        'heat_relief': 0.95,   # 消暑 -5%
        'warming': 1.05,       # 温养 +5%
        'spleen_stomach': 0.95, # 健脾养胃 -5%
        'blood_nourish': 1.0,  # 补血
        'qi_nourish': 1.0,     # 补气
    }
    
    # 三餐热量分配比例
    MEAL_RATIOS = {
        'standard': {'breakfast': 0.3, 'lunch': 0.4, 'dinner': 0.25, 'snack': 0.05},
        'weight_loss': {'breakfast': 0.35, 'lunch': 0.4, 'dinner': 0.2, 'snack': 0.05},
        'muscle_gain': {'breakfast': 0.3, 'lunch': 0.35, 'dinner': 0.3, 'snack': 0.05},
    }
    
    # 宏量营养素比例
    MACRO_RATIOS = {
        'standard': {'protein': 0.15, 'fat': 0.25, 'carbs': 0.60},
        'weight_loss': {'protein': 0.25, 'fat': 0.25, 'carbs': 0.50},
        'muscle_gain': {'protein': 0.25, 'fat': 0.25, 'carbs': 0.50},
        'low_carb': {'protein': 0.30, 'fat': 0.35, 'carbs': 0.35},
    }
    
    def __init__(self):
        self._food_cache = None
        self._categories_cache = None
    
    # ==================== 核心算法 ====================
    
    def calculate_bmr(self, gender: str, height: float, weight: float, age: int = 20) -> float:
        """计算基础代谢率 (Mifflin-St Jeor 公式)"""
        if gender == 'male':
            return 10 * weight + 6.25 * height - 5 * age + 5
        else:
            return 10 * weight + 6.25 * height - 5 * age - 161
    
    def calculate_tdee(self, bmr: float, activity_level: str = 'light') -> float:
        """计算每日总能量消耗"""
        factor = self.ACTIVITY_FACTORS.get(activity_level, 1.375)
        return bmr * factor
    
    def calculate_target_calories(self, tdee: float, goal: str) -> float:
        """根据目标调整目标热量"""
        factor = self.GOAL_FACTORS.get(goal, 1.0)
        return round(tdee * factor / 50) * 50  # 取整到50的倍数
    
    def get_meal_ratios(self, goal: str) -> Dict[str, float]:
        """获取餐次分配比例"""
        if goal == 'lose_weight':
            return self.MEAL_RATIOS['weight_loss']
        elif goal == 'gain_muscle':
            return self.MEAL_RATIOS['muscle_gain']
        return self.MEAL_RATIOS['standard']
    
    def get_macro_ratios(self, goal: str) -> Dict[str, float]:
        """获取宏量营养素比例"""
        return self.MACRO_RATIOS.get(goal, self.MACRO_RATIOS['standard'])
    
    # ==================== 食物数据管理 ====================
    
    def get_all_foods(self, active_only: bool = True) -> List[FoodItem]:
        """获取所有食物"""
        query = FoodItem.query
        if active_only:
            query = query.filter_by(is_active=True)
        return query.all()
    
    def get_foods_by_category(self, category_name: str) -> List[FoodItem]:
        """按分类获取食物"""
        cat = FoodCategory.query.filter_by(name=category_name).first()
        if not cat:
            return []
        return FoodItem.query.filter_by(category_id=cat.id, is_active=True).all()
    
    def get_foods_by_meal_type(self, meal_type: str) -> List[FoodItem]:
        """按餐次获取食物"""
        foods = self.get_all_foods()
        return [f for f in foods if meal_type in (f.meal_types or '')]
    
    def get_foods_by_tags(self, tags: List[str], exclude_tags: List[str] = None) -> List[FoodItem]:
        """按标签筛选食物"""
        foods = self.get_all_foods()
        result = []
        for f in foods:
            food_tags = f.tags.split(',') if f.tags else []
            # 包含任一目标标签
            if any(t in food_tags for t in tags):
                # 排除忌用标签
                if exclude_tags and any(t in food_tags for t in exclude_tags):
                    continue
                result.append(f)
        return result
    
    def filter_by_constitution(self, foods: List[FoodItem], constitution: str) -> List[FoodItem]:
        """按体质筛选食物"""
        if not constitution:
            return foods
        result = []
        for f in foods:
            suitable = f.suitable_constitutions.split(',') if f.suitable_constitutions else []
            avoid = f.avoid_constitutions.split(',') if f.avoid_constitutions else []
            if constitution in avoid:
                continue
            if not suitable or constitution in suitable:
                result.append(f)
        return result
    
    # ==================== 智能食谱生成算法 ====================
    
    def generate_meal_plan(self, 
                          target_calories: float,
                          meal_calories: float,
                          meal_type: str,
                          macro_targets: Dict[str, float],
                          user_tags: List[str] = None,
                          exclude_tags: List[str] = None,
                          constitution: str = None,
                          max_items: int = 4) -> List[Dict]:
        """为单餐生成食谱"""
        # 1. 获取候选食物
        candidates = self.get_foods_by_meal_type(meal_type)
        
        # 2. 按标签筛选
        if user_tags:
            candidates = self.get_foods_by_tags(user_tags, exclude_tags)
        else:
            candidates = [f for f in candidates if f.is_active]
        
        # 3. 按体质筛选
        if constitution:
            candidates = self.filter_by_constitution(candidates, constitution)
        
        if not candidates:
            return []
        
        # 4. 贪心算法选择食物组合
        selected = []
        remaining_calories = meal_calories
        remaining_protein = macro_targets.get('protein', 0)
        remaining_fat = macro_targets.get('fat', 0)
        remaining_carbs = macro_targets.get('carbs', 0)
        
        # 随机打乱增加多样性
        random.shuffle(candidates)
        
        for food in candidates:
            if len(selected) >= max_items:
                break
            
            # 计算份量
            serving_cal = food.calories * (food.serving_size / 100)
            if serving_cal > remaining_calories * 1.2:
                continue
            
            # 检查营养素是否超标
            serving_protein = food.protein * (food.serving_size / 100)
            serving_fat = food.fat * (food.serving_size / 100)
            serving_carbs = food.carbs * (food.serving_size / 100)
            
            selected.append({
                'food_id': food.id,
                'name': food.name,
                'category_id': food.category_id,
                'serving_size': food.serving_size,
                'serving_unit': food.serving_unit,
                'calories': round(serving_cal, 1),
                'protein': round(serving_protein, 1),
                'fat': round(serving_fat, 1),
                'carbs': round(serving_carbs, 1),
                'tcm_function': food.tcm_function,
                'tags': food.tags.split(',') if food.tags else [],
            })
            
            remaining_calories -= serving_cal
            remaining_protein -= serving_protein
            remaining_fat -= serving_fat
            remaining_carbs -= serving_carbs
            
            if remaining_calories <= meal_calories * 0.15:
                break
        
        return selected
    
    def generate_full_day_plan(self, user: User, goal: str = 'maintain', 
                              user_tags: List[str] = None, 
                              constitution: str = None,
                              notes: str = '') -> Dict:
        """生成全天食谱"""
        # 1. 计算热量需求
        age = 20
        if user.birth_date:
            age = (datetime.now().date() - user.birth_date).days // 365
        
        gender = user.gender or 'male'
        height = user.height or 170
        weight = user.weight or 60
        
        bmr = self.calculate_bmr(gender, height, weight, age)
        tdee = self.calculate_tdee(bmr, 'light')
        target_calories = self.calculate_target_calories(tdee, goal)
        
        # 2. 宏量营养素目标
        macro_ratios = self.get_macro_ratios(goal)
        target_protein = round(target_calories * macro_ratios['protein'] / 4, 1)
        target_fat = round(target_calories * macro_ratios['fat'] / 9, 1)
        target_carbs = round(target_calories * macro_ratios['carbs'] / 4, 1)
        
        # 3. 餐次分配
        meal_ratios = self.get_meal_ratios(goal)
        breakfast_cal = round(target_calories * meal_ratios['breakfast'])
        lunch_cal = round(target_calories * meal_ratios['lunch'])
        dinner_cal = round(target_calories * meal_ratios['dinner'])
        snack_cal = round(target_calories * meal_ratios['snack'])
        
        # 4. 生成各餐食谱
        macro_per_meal = {
            'protein': target_protein * meal_ratios.get('breakfast', 0.3),
            'fat': target_fat * meal_ratios.get('breakfast', 0.3),
            'carbs': target_carbs * meal_ratios.get('breakfast', 0.3),
        }
        
        breakfast = self.generate_meal_plan(
            target_calories, breakfast_cal, 'breakfast',
            {'protein': target_protein * meal_ratios['breakfast'],
             'fat': target_fat * meal_ratios['breakfast'],
             'carbs': target_carbs * meal_ratios['breakfast']},
            user_tags, constitution=constitution, max_items=4
        )
        
        lunch = self.generate_meal_plan(
            target_calories, lunch_cal, 'lunch',
            {'protein': target_protein * meal_ratios['lunch'],
             'fat': target_fat * meal_ratios['lunch'],
             'carbs': target_carbs * meal_ratios['lunch']},
            user_tags, constitution=constitution, max_items=5
        )
        
        dinner = self.generate_meal_plan(
            target_calories, dinner_cal, 'dinner',
            {'protein': target_protein * meal_ratios['dinner'],
             'fat': target_fat * meal_ratios['dinner'],
             'carbs': target_carbs * meal_ratios['dinner']},
            user_tags, constitution=constitution, max_items=4
        )
        
        snack = self.generate_meal_plan(
            target_calories, snack_cal, 'snack',
            {'protein': target_protein * meal_ratios['snack'],
             'fat': target_fat * meal_ratios['snack'],
             'carbs': target_carbs * meal_ratios['snack']},
            user_tags, constitution=constitution, max_items=2
        )
        
        # 5. 计算实际营养
        actual_cal = sum(m['calories'] for meal in [breakfast, lunch, dinner, snack] for m in meal)
        actual_protein = sum(m['protein'] for meal in [breakfast, lunch, dinner, snack] for m in meal)
        actual_fat = sum(m['fat'] for meal in [breakfast, lunch, dinner, snack] for m in meal)
        actual_carbs = sum(m['carbs'] for meal in [breakfast, lunch, dinner, snack] for m in meal)
        
        return {
            'daily_calories': round(tdee, 1),
            'target_calories': target_calories,
            'bmi': round(weight / (height/100)**2, 1),
            'bmr': round(bmr, 1),
            'target_protein': target_protein,
            'target_fat': target_fat,
            'target_carbs': target_carbs,
            'breakfast_calories': breakfast_cal,
            'lunch_calories': lunch_cal,
            'dinner_calories': dinner_cal,
            'snack_calories': snack_cal,
            'breakfast': breakfast,
            'lunch': lunch,
            'dinner': dinner,
            'snack': snack,
            'actual_calories': round(actual_cal, 1),
            'actual_protein': round(actual_protein, 1),
            'actual_fat': round(actual_fat, 1),
            'actual_carbs': round(actual_carbs, 1),
        }
    
    # ==================== 保存推荐记录 ====================
    
    def save_recommendation(self, user_id: int, plan: Dict, goal: str, 
                           recommendation_type: str = 'algorithm',
                           ai_recommendation: str = None) -> DietRecommendation:
        """保存推荐记录"""
        user = User.query.get(user_id)
        
        rec = DietRecommendation(
            user_id=user_id,
            gender=user.gender,
            height=user.height,
            weight=user.weight,
            bmi=plan.get('bmi'),
            bmi_category=plan.get('bmi_category'),
            constitution=plan.get('constitution'),
            daily_calories=plan.get('daily_calories'),
            target_calories=plan.get('target_calories'),
            breakfast_calories=plan.get('breakfast_calories'),
            lunch_calories=plan.get('lunch_calories'),
            dinner_calories=plan.get('dinner_calories'),
            snack_calories=plan.get('snack_calories'),
            target_protein=plan.get('target_protein'),
            target_fat=plan.get('target_fat'),
            target_carbs=plan.get('target_carbs'),
            breakfast_items=json.dumps(plan.get('breakfast', []), ensure_ascii=False),
            lunch_items=json.dumps(plan.get('lunch', []), ensure_ascii=False),
            dinner_items=json.dumps(plan.get('dinner', []), ensure_ascii=False),
            snack_items=json.dumps(plan.get('snack', []), ensure_ascii=False),
            user_goal=goal,
            recommendation_type=recommendation_type,
            ai_recommendation=ai_recommendation,
        )
        db.session.add(rec)
        db.session.commit()
        return rec


# 单例
_diet_service = None

def get_diet_service():
    global _diet_service
    if _diet_service is None:
        _diet_service = DietService()
    return _diet_service