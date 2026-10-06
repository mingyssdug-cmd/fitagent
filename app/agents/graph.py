"""
LangGraph 编排层。

职责：
- 定义状态结构（PlanState）
- 定义节点函数（营养节点、训练节点、审核节点）
- 组装状态图（StateGraph）
- 提供编译后的 app 对象，供 Service 层调用

设计：
- 短期会话用 SqliteSaver 持久化（中断后重启不丢）
- 用 interrupt() 实现 HITL
- 用 Command(resume=...) 从断点恢复
"""

import sqlite3
from pathlib import Path
from typing import Optional, TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from app.agents.nutrition import nutrition_agent
from app.agents.workout import workout_agent

# ── SQLite 检查点文件路径 ──
# 存 LangGraph 的中断状态。放在项目根目录的 data/ 下
CHECKPOINT_DB = "data/checkpoints.db"

# 确保 data/ 目录存在，否则 SQLite 会报 "unable to open database file"
Path(CHECKPOINT_DB).parent.mkdir(parents=True, exist_ok=True)


# ══════════════════════════════════════════════
# 状态定义
# ══════════════════════════════════════════════

class PlanState(TypedDict):
    """图的状态。

    字段说明：
    - user_profile: 用户档案（从 profiles 表读出来的 dict）
    - goal: 目标（cut/bulk/maintain）
    - nutrition_plan: 营养计划全文（营养节点写入）
    - workout_plan: 训练计划全文（训练节点写入）
    - feedback: 用户反馈（revise 时写入，用于触发重生成）
    - retry_count: 重试次数（防止无限循环）
    """
    user_profile: dict
    goal: str
    nutrition_plan: Optional[str]
    workout_plan: Optional[str]
    feedback: Optional[str]
    retry_count: int


# ══════════════════════════════════════════════
# 节点函数
# ══════════════════════════════════════════════

def nutrition_node(state: PlanState) -> dict:
    """营养节点：调用营养 Agent 生成饮食计划。

    输入：state 里的 user_profile、goal、feedback
    输出：state 里的 nutrition_plan
    """
    # 构造给 Agent 的提示词
    prompt = (
        f"用户档案：{state['user_profile']}\n"
        f"目标：{state['goal']}\n"
    )
    # 如果有反馈（重生成场景），带上反馈
    if state.get("feedback"):
        prompt += f"\n用户反馈：{state['feedback']}\n请根据反馈调整计划。"

    prompt += "\n请生成饮食计划。"

    # 调用营养 Agent
    result = nutrition_agent.invoke({
        "messages": [{"role": "user", "content": prompt}]
    })

    # 返回状态更新（LangGraph 会自动合并到 state）
    return {"nutrition_plan": result["messages"][-1].content}


def workout_node(state: PlanState) -> dict:
    """训练节点：调用训练 Agent 生成训练计划。"""
    prompt = (
        f"用户档案：{state['user_profile']}\n"
        f"目标：{state['goal']}\n"
    )
    if state.get("feedback"):
        prompt += f"\n用户反馈：{state['feedback']}\n请根据反馈调整计划。"

    prompt += "\n请生成训练计划。"

    result = workout_agent.invoke({
        "messages": [{"role": "user", "content": prompt}]
    })

    return {"workout_plan": result["messages"][-1].content}


def review_node(state: PlanState) -> dict:
    """审核节点：HITL 中断点。

    调用 interrupt() 暂停图执行，返回两份计划给调用方。
    调用方（Service 层）通过 Command(resume=...) 传入用户的决定。

    返回：
    - 若用户 approve，返回 {"feedback": None}
    - 若用户提了意见，返回 {"feedback": 意见}
    """
    # 暂停，把当前状态暴露给调用方
    decision = interrupt({
        "nutrition_plan": state["nutrition_plan"],
        "workout_plan": state["workout_plan"],
        "question": "请确认计划。回复 'approve' 通过，或输入修改意见。",
    })

    # 恢复后，decision 是调用方传来的值
    if isinstance(decision, str) and decision.strip().lower() == "approve":
        return {"feedback": None}

    # 不是 approve，视为修改意见
    return {"feedback": decision}


def should_continue(state: PlanState) -> str:
    """条件边：判断审核后往哪走。

    返回值必须是 add_conditional_edges 映射表里的 key。
    """
    # 有反馈 → 重生成
    if state.get("feedback"):
        # 重试次数 +1
        state["retry_count"] = state.get("retry_count", 0) + 1
        # 超过 3 次强制结束（防止无限循环）
        if state["retry_count"] >= 3:
            return "end"
        return "regenerate"
    # 无反馈 → 结束
    return "end"


# ══════════════════════════════════════════════
# 图组装
# ══════════════════════════════════════════════

def build_graph():
    """组装并编译 LangGraph 应用。

    返回：编译后的图对象，可以 .invoke() 调用
    """
    # 1. 创建图
    graph = StateGraph(PlanState)

    # 2. 添加节点
    graph.add_node("nutrition", nutrition_node)
    graph.add_node("workout", workout_node)
    graph.add_node("review", review_node)

    # 3. 添加边
    graph.add_edge(START, "nutrition")
    graph.add_edge("nutrition", "workout")
    graph.add_edge("workout", "review")

    # 4. 条件边：审核后的分支
    graph.add_conditional_edges(
        "review",
        should_continue,
        {
            "regenerate": "nutrition",  # 有反馈 → 回到营养节点重生成
            "end": END,                 # 无反馈 → 结束
        },
    )

    # 5. 创建 SQLite checkpointer
    # 注意：不用 SqliteSaver.from_conn_string()
    # 它返回的是上下文管理器，不是 BaseCheckpointSaver 实例
    # 直接 sqlite3.connect() 构造连接，再传给 SqliteSaver
    # check_same_thread=False：允许跨线程使用（uvicorn 多线程场景需要）
    conn = sqlite3.connect(CHECKPOINT_DB, check_same_thread=False)
    checkpointer = SqliteSaver(conn)

    # 6. 编译
    return graph.compile(checkpointer=checkpointer)


# ── 全局单例：编译后的图对象 ──
graph_app = build_graph()