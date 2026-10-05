"""
计划相关的 Pydantic 模型。

职责：
- 生成计划响应
- 确认计划响应
- 修改计划请求/响应
- 历史计划列表
- 计划详情
"""

from datetime import datetime

from pydantic import BaseModel, Field


class GeneratePlanData(BaseModel):
    """POST /plans/generate 的响应数据。"""

    plan_id: str               # 临时 ID（如 tmp_001）
    status: str                # pending_review
    nutrition_plan: str        # 营养计划全文
    workout_plan: str          # 训练计划全文
    question: str              # 给用户的提示语


class ConfirmPlanData(BaseModel):
    """POST /plans/{plan_id}/confirm 的响应数据。"""

    plan_id: int               # 真实数据库 ID
    status: str                # completed
    nutrition_plan: str
    workout_plan: str
    created_at: datetime


class RevisePlanRequest(BaseModel):
    """POST /plans/{plan_id}/revise 的请求体。"""

    feedback: str = Field(..., min_length=1, max_length=500, description="修改意见")


class RevisePlanData(BaseModel):
    """POST /plans/{plan_id}/revise 的响应数据。"""

    plan_id: str
    status: str                # pending_review
    nutrition_plan: str
    workout_plan: str
    question: str
    retry_count: int           # 当前重试次数


class PlanListItem(BaseModel):
    """历史计划列表中的单条数据。"""

    plan_id: int
    nutrition_plan: str
    workout_plan: str
    created_at: datetime


class PlanDetailData(BaseModel):
    """GET /plans/{plan_id} 的响应数据。"""

    plan_id: int
    nutrition_plan: str
    workout_plan: str
    feedback: str | None
    status: str
    created_at: datetime