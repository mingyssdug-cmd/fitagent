"""
营养 Agent。

职责：
- 组装营养规划智能体
- 工具集：BMR/TDEE/宏量计算 + 营养库检索
- 系统提示词约束：所有数字必须来自工具，所有建议必须来自知识库

设计：
- 用 create_agent 组装（LangChain 1.x 的标准入口）
- 变量名带 nutrition_ 前缀，避免和其他 Agent 混淆
"""

from langchain.agents import create_agent

from app.agents import model
from app.tools.calculator import calculate_bmr, calculate_tdee, calculate_macros
from app.tools.nutrition_search import search_nutrition

# ── 系统提示词 ──
# 这段提示词告诉 Agent：
#   1. 什么时候调哪个工具
#   2. 不能自己心算
#   3. 不能凭记忆回答营养问题
NUTRITION_SYSTEM_PROMPT = """你是一个专业的健身营养规划助手。

你的职责：根据用户的身体数据和目标，生成个性化的饮食计划。

工作流程：
1. 用户提供性别、年龄、体重、身高后，必须先调用 calculate_bmr 计算基础代谢率
2. 根据活动水平调用 calculate_tdee 计算每日总消耗
3. 根据目标和 TDEE 计算目标热量（减脂 -500，增肌 +300，维持不变）
4. 调用 calculate_macros 计算蛋白质、脂肪、碳水化合物的克数
5. 调用 search_nutrition 检索知识库，获取餐次分配、食物选择的建议
6. 生成最终的饮食计划

重要约束：
- 所有数字必须来自工具返回结果，不要自己心算
- 所有营养建议必须来自知识库检索，不要凭记忆回答
- 如果检索结果带 [来源 X | 第 Y 页]，在输出中保留这个标注
"""

# ── 组装 Agent ──
nutrition_agent = create_agent(
    model=model,
    tools=[
        calculate_bmr,
        calculate_tdee,
        calculate_macros,
        search_nutrition,
    ],
    system_prompt=NUTRITION_SYSTEM_PROMPT,
)