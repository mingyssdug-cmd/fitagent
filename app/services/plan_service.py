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
"""

import logging
import time

from langgraph.types import Command
from sqlalchemy.orm import Session

from app.agents.graph import graph_app
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

    def generate(self, user_id: int) -> dict:
        """生成计划。

        流程：
        1. 检查用户档案完整
        2. 生成 thread_id
        3. 调用图，跑到 review 中断
        4. 返回两份计划 + 中断信息

        返回：
            {
                "plan_id": thread_id,
                "status": "pending_review",
                "nutrition_plan": ...,
                "workout_plan": ...,
                "question": ...,
            }
        """
        # 1. 检查用户档案
        profile = self.profile_repo.get_by_user_id(user_id)
        if not profile:
            raise ProfileIncompleteError("请先完善个人档案")

        # 2. 生成 thread_id
        thread_id = self._make_thread_id(user_id)
        config = self._make_config(thread_id)

        # 3. 调用图
        result = graph_app.invoke(
            {
                "user_profile": profile.to_dict(),
                "goal": profile.goal,
                "feedback": None,
                "retry_count": 0,
            },
            config=config,
        )

        # 4. 提取中断信息
        interrupts = result.get("__interrupt__", [])
        if not interrupts:
            raise ValidationError("未命中中断点，请检查图配置")

        interrupt_value = interrupts[0].value

        logger.info("计划生成完成: user_id=%s thread_id=%s", user_id, thread_id)

        return {
            "plan_id": thread_id,
            "status": "pending_review",
            "nutrition_plan": interrupt_value["nutrition_plan"],
            "workout_plan": interrupt_value["workout_plan"],
            "question": interrupt_value["question"],
        }

    def confirm(self, user_id: int, plan_id: str) -> dict:
        """确认计划。恢复图执行，落库。

        参数：
            user_id: 用户 ID（用于校验权限）
            plan_id: 临时 ID（即 thread_id）

        返回：
            最终计划的 dict
        """
        # 1. 校验 thread_id 属于这个用户
        if not plan_id.startswith(f"user_{user_id}_plan_"):
            raise ValidationError("无效的 plan_id")

        config = self._make_config(plan_id)

        # 2. 恢复图执行
        result = graph_app.invoke(Command(resume="approve"), config=config)

        # 3. 检查是否又中断了（不应该，approve 应该结束）
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

    def revise(self, user_id: int, plan_id: str, feedback: str) -> dict:
        """提交修改意见，触发重生成。

        参数：
            user_id: 用户 ID
            plan_id: 临时 ID
            feedback: 修改意见

        返回：
            新的中断信息
        """
        if not feedback or not feedback.strip():
            raise ValidationError("反馈不能为空")

        if not plan_id.startswith(f"user_{user_id}_plan_"):
            raise ValidationError("无效的 plan_id")

        config = self._make_config(plan_id)

        # 恢复图，传反馈
        result = graph_app.invoke(Command(resume=feedback), config=config)

        # 检查是否又中断
        interrupts = result.get("__interrupt__", [])
        if not interrupts:
            raise ValidationError("重生成未命中中断点")

        interrupt_value = interrupts[0].value
        retry_count = result.get("retry_count", 0)

        # 检查重试次数
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
            raise NotFoundError("计划不存在")  # 不暴露"无权访问"信息，防止枚举

        return {
            "plan_id": plan.id,
            "nutrition_plan": plan.nutrition_plan,
            "workout_plan": plan.workout_plan,
            "feedback": plan.feedback,
            "status": plan.status,
            "created_at": plan.created_at,
        }