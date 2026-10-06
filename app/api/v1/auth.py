"""
认证路由。

职责：
- POST /auth/register：注册
- POST /auth/login：登录
"""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.auth import AuthData, LoginRequest, RegisterRequest
from app.schemas.common import ApiResponse
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=ApiResponse[AuthData])
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """注册新用户。"""
    service = AuthService(db)
    user, token = service.register(
        phone=req.phone,
        password=req.password,
        name=req.name,
    )

    return ApiResponse(data=AuthData(
        user_id=user.id,
        token=token,
        name=user.name,
    ))


@router.post("/login", response_model=ApiResponse[AuthData])
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """用户登录。"""
    service = AuthService(db)
    user, token = service.login(phone=req.phone, password=req.password)

    return ApiResponse(data=AuthData(
        user_id=user.id,
        token=token,
        name=user.name,
    ))