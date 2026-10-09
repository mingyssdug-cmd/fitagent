"""
LangGraph 编排层。

职责：
- 定义状态结构（PlanState）
- 定义节点函数（营养节点、训练节点、审核节点）
- 组装状态图（StateGraph）
- 提供编译后的 app 对象，供 Service 层调用

设计：
- 短期会话用 AsyncSqliteSaver 持久化（支持异步，中断后重启不丢）
- 用 interrupt() 实现 HITL
- 用 Command(resume=...) 从断点恢复
- 营养和训练节点并行执行（异步）
"""

import logging
import time
from pathlib import Path
from typing import Optional, TypedDict

import aiosqlite
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from app.agents.nutrition import nutrition_agent
from app.agents.workout import workout_agent

logger = logging.getLogger(__name__)

# ── SQLite 检查点文件路径 ──
CHECKPOINT_DB = "data/checkpoints.db"
Path(CHECKPOINT_DB).parent.mkdir(parents=True, exist_ok=True)


# ══════════════════════════════════════════════
# 状态定义
# ══════════════════════════════════════════════

class PlanState(TypedDict):
    """图的状态。"""
    user_profile: dict
    goal: str
    nutrition_plan: Optional[str]
    workout_plan: Optional[str]
    feedback: Optional[str]
    retry_count: int


# ══════════════════════════════════════════════
# 节点函数
# ══════════════════════════════════════════════

async def nutrition_node(state: PlanState) -> dict:
    """营养节点：调用营养 Agent 生成饮食计划。"""
    start = time.time()
    logger.info("[nutrition_node] 开始执行")

    prompt = (
        f"用户档案：{state['user_profile']}\n"
        f"目标：{state['goal']}\n"
    )
    if state.get("feedback"):
        prompt += f"\n用户反馈：{state['feedback']}\n请根据反馈调整计划。"

    prompt += "\n请生成饮食计划。"

    result = await nutrition_agent.ainvoke({
        "messages": [{"role": "user", "content": prompt}]
    })

    cost = time.time() - start
    logger.info("[nutrition_node] 耗时 %.2f 秒", cost)

    return {"nutrition_plan": result["messages"][-1].content}


async def workout_node(state: PlanState) -> dict:
    """训练节点：调用训练 Agent 生成训练计划。"""
    start = time.time()
    logger.info("[workout_node] 开始执行")

    prompt = (
        f"用户档案：{state['user_profile']}\n"
        f"目标：{state['goal']}\n"
    )
    if state.get("feedback"):
        prompt += f"\n用户反馈：{state['feedback']}\n请根据反馈调整计划。"

    prompt += "\n请生成训练计划。"

    result = await workout_agent.ainvoke({
        "messages": [{"role": "user", "content": prompt}]
    })

    cost = time.time() - start
    logger.info("[workout_node] 耗时 %.2f 秒", cost)

    return {"workout_plan": result["messages"][-1].content}


async def review_node(state: PlanState) -> dict:
    """审核节点：HITL 中断点。"""
    logger.info("[review_node] 进入审核节点")

    decision = interrupt({
        "nutrition_plan": state["nutrition_plan"],
        "workout_plan": state["workout_plan"],
        "question": "请确认计划。回复 'approve' 通过，或输入修改意见。",
    })

    if isinstance(decision, str) and decision.strip().lower() == "approve":
        return {"feedback": None}

    return {"feedback": decision}


def should_continue(state: PlanState) -> str:
    """条件边：判断审核后往哪走。"""
    if state.get("feedback"):
        state["retry_count"] = state.get("retry_count", 0) + 1
        if state["retry_count"] >= 3:
            return "end"
        return "regenerate"
    return "end"


# ══════════════════════════════════════════════
# 图组装
# ══════════════════════════════════════════════

def build_graph(checkpointer):
    """组装并编译 LangGraph 应用。

    参数：
        checkpointer: 由调用方传入的异步 checkpointer
    """
    graph = StateGraph(PlanState)

    graph.add_node("nutrition", nutrition_node)
    graph.add_node("workout", workout_node)
    graph.add_node("review", review_node)

    # START 分叉到两个节点，异步并行
    graph.add_edge(START, "nutrition")
    graph.add_edge(START, "workout")

    # 两个节点都完成后汇合到 review
    graph.add_edge("nutrition", "review")
    graph.add_edge("workout", "review")

    graph.add_conditional_edges(
        "review",
        should_continue,
        {
            "regenerate": "nutrition",
            "end": END,
        },
    )

    return graph.compile(checkpointer=checkpointer)


# ══════════════════════════════════════════════
# 全局初始化（FastAPI 启动时调用）
# ══════════════════════════════════════════════

# 模块级全局变量，由 init_graph() 赋值
graph_app = None

# 保存连接，防止被 GC
_db_conn = None


async def init_graph():
    """初始化图。在 FastAPI 启动时调用。"""
    global graph_app, _db_conn

    _db_conn = await aiosqlite.connect(CHECKPOINT_DB)
    checkpointer = AsyncSqliteSaver(_db_conn)
    graph_app = build_graph(checkpointer)

    logger.info("[Graph] 初始化完成")


async def close_graph():
    """关闭图。在 FastAPI 关闭时调用。"""
    global _db_conn
    if _db_conn:
        await _db_conn.close()
        _db_conn = None
        logger.info("[Graph] 已关闭")

async def stream_graph(user_profile: dict, goal: str, thread_id: str):
    """流式执行图，只输出 AI 生成的 token。"""
    from langchain_core.messages import AIMessageChunk

    config = {"configurable": {"thread_id": thread_id}}

    async for chunk in graph_app.astream(
        {
            "user_profile": user_profile,
            "goal": goal,
            "feedback": None,
            "retry_count": 0,
        },
        config=config,
        stream_mode="messages",
        subgraphs=True,
        version="v2",
    ):
        if chunk["type"] == "messages":
            msg, metadata = chunk["data"]
            if isinstance(msg, AIMessageChunk) and msg.content:
                yield msg.content