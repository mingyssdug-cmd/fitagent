"""
API 层的依赖注入。

职责：
- 提供数据库 session 的依赖
- 提供当前用户的依赖（从 token 解析）
- 提供配置的依赖

设计：
- FastAPI 的 Depends 机制会自动调用这些函数，把结果注入路由参数
- get_current_user 解析 token 后查数据库，返回 User 对象
"""

import logging

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.core.exceptions import UnauthorizedError
from app.core.security import decode_token
from app.models.base import SessionLocal
from app.models.user import User

logger = logging.getLogger(__name__)


def get_db():
    """提供数据库 session。

    每个请求创建一个 session，请求结束后自动关闭。
    用 yield 让 FastAPI 在请求结束时执行 finally 块。
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db),
) -> User:
    """从 Authorization header 解析当前用户。

    header 格式：Authorization: Bearer <token>

    异常：
        UnauthorizedError: 没带 token / token 无效 / 用户不存在
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedError("未登录")

    token = authorization.split(" ", 1)[1]
    user_id = decode_token(token)

    if user_id is None:
        raise UnauthorizedError("token 无效或已过期")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise UnauthorizedError("用户不存在")

    return user