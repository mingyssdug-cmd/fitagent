"""
训练 Agent。

职责：
- 组装训练规划智能体
- 工具集：动作库检索
- 系统提示词约束：动作必须来自知识库，禁忌动作必须排除

设计：
- 训练规划不需要数学计算，主要依赖动作库检索和 LLM 编排
- 变量名带 workout_ 前缀
"""

from langchain.agents import create_agent

from app.agents import model
from app.tools.workout_search import search_workout

# ── 系统提示词 ──
WORKOUT_SYSTEM_PROMPT = """你是一个专业的健身训练规划助手。

你的职责：根据用户的身体数据、目标和训练条件，生成个性化的训练计划。

工作流程：
1. 根据用户的目标（增肌/减脂/维持）和经验水平，确定训练分化方式
   - 增肌 + 新手：全身训练，每周 3 次
   - 增肌 + 中级：上下肢分化，每周 4 次
   - 增肌 + 高级：推拉腿分化，每周 5-6 次
2. 调用 search_workout 检索每个动作的规范、目标肌群、禁忌
3. 生成周结构，分配每日动作
4. 每个动作标注组数、次数、组间休息

重要约束：
- 动作要领必须来自知识库检索，不要凭记忆描述
- 如果用户有伤病史，必须排除禁忌动作，并给出替代动作
- 计划要包含：周结构、每日动作、组数次数、组间休息
- 如果检索结果带 [来源 X | 第 Y 页]，在输出中保留这个标注
"""

# ── 组装 Agent ──
workout_agent = create_agent(
    model=model,
    tools=[search_workout],
    system_prompt=WORKOUT_SYSTEM_PROMPT,
)