"""
用户路由。

职责：
- GET /users/me：获取当前用户档案
- PUT /users/me：更新当前用户档案
"""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.user import ProfileData, UpdateUserRequest, UserDetailData
from app.services.user_service import UserService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["用户"])


@router.get("/me", response_model=ApiResponse[UserDetailData])
def get_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的档案。"""
    service = UserService(db)
    user, profile = service.get_me(current_user.id)

    return ApiResponse(data=UserDetailData(
        user_id=user.id,
        phone=user.phone,
        name=user.name,
        profile=ProfileData(**profile.to_dict()) if profile else None,
    ))


@router.put("/me", response_model=ApiResponse[UserDetailData])
def update_me(
    req: UpdateUserRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新当前用户档案。"""
    service = UserService(db)
    user, profile = service.update_me(
        user_id=current_user.id,
        name=req.name,
        profile_data=req.profile.model_dump(),
    )

    return ApiResponse(data=UserDetailData(
        user_id=user.id,
        phone=user.phone,
        name=user.name,
        profile=ProfileData(**profile.to_dict()),
    ))