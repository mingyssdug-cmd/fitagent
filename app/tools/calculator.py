"""
计算工具集。

职责：
- BMR（基础代谢率）
- TDEE（每日总消耗）
- 宏量营养素分配

设计：
- 所有数学计算都在这里，LLM 永远不自己算
- 用 @tool 装饰器，让 Agent 能调用
"""

from langchain.tools import tool

# 活动系数表：不同活动水平的 TDEE 乘数
ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,      # 久坐
    "light": 1.375,        # 轻度活动
    "moderate": 1.55,      # 中度活动
    "active": 1.725,       # 高度活动
    "very_active": 1.9,    # 极高强度
}

# 蛋白质摄入系数（克/公斤体重）
PROTEIN_PER_KG = {
    "cut": 2.2,       # 减脂期：高蛋白保肌肉
    "bulk": 1.8,      # 增肌期：适度蛋白
    "maintain": 1.6,  # 维持期：基础蛋白
}


@tool
def calculate_bmr(
    gender: str,
    age: int,
    weight_kg: float,
    height_cm: float,
) -> int:
    """计算基础代谢率 BMR（Mifflin-St Jeor 公式）。

    Args:
        gender: 性别，male 或 female
        age: 年龄（岁）
        weight_kg: 体重（公斤）
        height_cm: 身高（厘米）

    Returns:
        BMR（整数 kcal）
    """
    if gender == "male":
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
    return int(bmr)


@tool
def calculate_tdee(bmr: int, activity: str) -> int:
    """根据 BMR 和活动水平计算每日总消耗 TDEE。

    Args:
        bmr: 基础代谢率
        activity: 活动水平，可选 sedentary/light/moderate/active/very_active

    Returns:
        TDEE（整数 kcal）
    """
    multiplier = ACTIVITY_MULTIPLIERS.get(activity, 1.55)
    return int(bmr * multiplier)


@tool
def calculate_macros(
    target_calories: int,
    weight_kg: float,
    goal: str,
) -> dict:
    """根据目标热量、体重和目标类型计算三大营养素分配。

    Args:
        target_calories: 每日目标热量（kcal）
        weight_kg: 体重（公斤）
        goal: 目标，cut（减脂）/ bulk（增肌）/ maintain（维持）

    Returns:
        dict: 包含 protein_g, fat_g, carb_g 及各自的热量
    """
    # 蛋白质：按体重算
    protein_g = int(weight_kg * PROTEIN_PER_KG.get(goal, 1.6))

    # 脂肪：占总热量 25%
    fat_g = int(target_calories * 0.25 / 9)   # 每克脂肪 9 kcal

    # 碳水：剩余热量
    remaining = target_calories - (protein_g * 4 + fat_g * 9)
    carb_g = int(remaining / 4)                # 每克碳水 4 kcal

    return {
        "protein_g": protein_g,
        "fat_g": fat_g,
        "carb_g": carb_g,
        "protein_kcal": protein_g * 4,
        "fat_kcal": fat_g * 9,
        "carb_kcal": carb_g * 4,
    }