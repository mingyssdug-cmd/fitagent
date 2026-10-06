"""
计划路由。

职责：
- POST /plans/generate：生成计划
- POST /plans/{plan_id}/confirm：确认计划
- POST /plans/{plan_id}/revise：提交修改意见
- GET /plans：查询历史列表
- GET /plans/{plan_id}：查询详情
"""

import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.common import ApiResponse, PaginationData
from app.schemas.plan import (
    ConfirmPlanData,
    GeneratePlanData,
    PlanDetailData,
    PlanListItem,
    RevisePlanData,
    RevisePlanRequest,
)
from app.services.plan_service import PlanService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/plans", tags=["计划"])


@router.post("/generate", response_model=ApiResponse[GeneratePlanData])
def generate_plan(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """生成计划。跑到 HITL 中断点，返回两份计划。"""
    service = PlanService(db)
    result = service.generate(current_user.id)

    return ApiResponse(data=GeneratePlanData(**result))


@router.post("/{plan_id}/confirm", response_model=ApiResponse[ConfirmPlanData])
def confirm_plan(
    plan_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """确认计划。恢复图执行，落库。"""
    service = PlanService(db)
    result = service.confirm(current_user.id, plan_id)

    return ApiResponse(data=ConfirmPlanData(**result))


@router.post("/{plan_id}/revise", response_model=ApiResponse[RevisePlanData])
def revise_plan(
    plan_id: str,
    req: RevisePlanRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """提交修改意见，触发重生成。"""
    service = PlanService(db)
    result = service.revise(current_user.id, plan_id, req.feedback)

    return ApiResponse(data=RevisePlanData(**result))


@router.get("", response_model=ApiResponse[PaginationData[PlanListItem]])
def list_plans(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """查询历史计划列表。"""
    service = PlanService(db)
    result = service.list_plans(current_user.id, page, page_size)

    return ApiResponse(data=PaginationData(
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
        items=[PlanListItem(**item) for item in result["items"]],
    ))


@router.get("/{plan_id}", response_model=ApiResponse[PlanDetailData])
def get_plan(
    plan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """查询单个计划详情。"""
    service = PlanService(db)
    result = service.get_plan(current_user.id, plan_id)

    return ApiResponse(data=PlanDetailData(**result))