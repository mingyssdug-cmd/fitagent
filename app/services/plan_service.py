"""
计划服务。

职责：
- 生成计划（调 LangGraph，跑到 HITL 中断）
- 确认计划（恢复图执行，落库）
- 提交修改意见（带反馈重新生成）
- 查询历史计划

设计：
- 临时 plan_id 用 thread_id（格式：user_{id}_plan_{时间戳}）
- 生成阶段计划不落库，存在 checkpointer
- 确认后才写入 plans 表
- 通过 graph_module.graph_app 访问图对象（因为 init_graph() 后才赋值）
"""

import logging
import time

from langgraph.types import Command
from sqlalchemy.orm import Session

from app.agents import graph as graph_module
from app.core.exceptions import (
    NotFoundError,
    ProfileIncompleteError,
    ValidationError,
)
from app.repositories.plan_repo import PlanRepository
from app.repositories.profile_repo import ProfileRepository

logger = logging.getLogger(__name__)

MAX_RETRY = 3


class PlanService:
    """计划相关的业务逻辑。"""

    def __init__(self, db: Session):
        self.db = db
        self.plan_repo = PlanRepository(db)
        self.profile_repo = ProfileRepository(db)

    def _make_thread_id(self, user_id: int) -> str:
        """生成临时 thread_id。格式：user_{id}_plan_{时间戳}。"""
        return f"user_{user_id}_plan_{int(time.time())}"

    def _make_config(self, thread_id: str) -> dict:
        """构造 LangGraph 的 config。"""
        return {"configurable": {"thread_id": thread_id}}

    async def generate(self, user_id: int) -> dict:
        """生成计划。"""
        logger.info("[PlanService] 收到生成请求: user_id=%s", user_id)

        profile = self.profile_repo.get_by_user_id(user_id)
        if not profile:
            raise ProfileIncompleteError("请先完善个人档案")

        thread_id = self._make_thread_id(user_id)
        config = self._make_config(thread_id)

        logger.info("[PlanService] 开始调用 LangGraph...")
        result = await graph_module.graph_app.ainvoke(
            {
                "user_profile": profile.to_dict(),
                "goal": profile.goal,
                "feedback": None,
                "retry_count": 0,
            },
            config=config,
        )

        interrupts = result.get("__interrupt__", [])
        if not interrupts:
            raise ValidationError("未命中中断点")

        interrupt_value = interrupts[0].value

        return {
            "plan_id": thread_id,
            "status": "pending_review",
            "nutrition_plan": interrupt_value["nutrition_plan"],
            "workout_plan": interrupt_value["workout_plan"],
            "question": interrupt_value["question"],
        }

    async def generate_stream(self, user_id: int):
        """流式生成计划。逐 token yield LLM 输出。

        注意：这是异步生成器，不能直接 return，要用 yield。
        """
        from app.agents.graph import stream_graph

        profile = self.profile_repo.get_by_user_id(user_id)
        if not profile:
            raise ProfileIncompleteError("请先完善个人档案")

        thread_id = self._make_thread_id(user_id)

        async for token in stream_graph(
                profile.to_dict(),
                profile.goal,
                thread_id,
        ):
            yield token
    async def confirm(self, user_id: int, plan_id: str) -> dict:
        """确认计划。恢复图执行，落库。"""
        # 1. 校验 thread_id 属于这个用户
        if not plan_id.startswith(f"user_{user_id}_plan_"):
            raise ValidationError("无效的 plan_id")

        config = self._make_config(plan_id)

        # 2. 恢复图执行
        result = await graph_module.graph_app.ainvoke(
            Command(resume="approve"),
            config=config,
        )

        # 3. 检查是否又中断了
        if result.get("__interrupt__"):
            raise ValidationError("计划确认异常")

        # 4. 从 profile 拿 goal（快照）
        profile = self.profile_repo.get_by_user_id(user_id)
        goal = profile.goal if profile else "maintain"

        # 5. 落库
        plan = self.plan_repo.create(
            user_id=user_id,
            goal=goal,
            nutrition_plan=result["nutrition_plan"],
            workout_plan=result["workout_plan"],
            feedback=None,
        )
        self.db.commit()
        self.db.refresh(plan)

        logger.info("计划已保存: user_id=%s plan_db_id=%s", user_id, plan.id)

        return {
            "plan_id": plan.id,
            "status": "completed",
            "nutrition_plan": plan.nutrition_plan,
            "workout_plan": plan.workout_plan,
            "created_at": plan.created_at,
        }

    async def revise(self, user_id: int, plan_id: str, feedback: str) -> dict:
        """提交修改意见，触发重生成。"""
        if not feedback or not feedback.strip():
            raise ValidationError("反馈不能为空")

        if not plan_id.startswith(f"user_{user_id}_plan_"):
            raise ValidationError("无效的 plan_id")

        config = self._make_config(plan_id)

        # 恢复图，传反馈
        result = await graph_module.graph_app.ainvoke(
            Command(resume=feedback),
            config=config,
        )

        # 检查是否又中断
        interrupts = result.get("__interrupt__", [])
        if not interrupts:
            raise ValidationError("重生成未命中中断点")

        interrupt_value = interrupts[0].value
        retry_count = result.get("retry_count", 0)

        if retry_count >= MAX_RETRY:
            raise ValidationError(f"已达到最大修改次数 {MAX_RETRY}")

        logger.info("计划修改: user_id=%s retry=%s", user_id, retry_count)

        return {
            "plan_id": plan_id,
            "status": "pending_review",
            "nutrition_plan": interrupt_value["nutrition_plan"],
            "workout_plan": interrupt_value["workout_plan"],
            "question": interrupt_value["question"],
            "retry_count": retry_count,
        }

    def list_plans(self, user_id: int, page: int = 1, page_size: int = 10) -> dict:
        """查询历史计划列表。"""
        items, total = self.plan_repo.list_by_user(user_id, page, page_size)

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [
                {
                    "plan_id": p.id,
                    "nutrition_plan": p.nutrition_plan,
                    "workout_plan": p.workout_plan,
                    "created_at": p.created_at,
                }
                for p in items
            ],
        }

    def get_plan(self, user_id: int, plan_id: int) -> dict:
        """查询单个计划详情。"""
        plan = self.plan_repo.get_by_id(plan_id)

        if not plan:
            raise NotFoundError("计划不存在")

        if plan.user_id != user_id:
            raise NotFoundError("计划不存在")

        return {
            "plan_id": plan.id,
            "nutrition_plan": plan.nutrition_plan,
            "workout_plan": plan.workout_plan,
            "feedback": plan.feedback,
            "status": plan.status,
            "created_at": plan.created_at,
        }

