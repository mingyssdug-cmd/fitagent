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

"""
API 层的依赖注入。
"""

import logging

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import UnauthorizedError
from app.core.security import decode_token
from app.models.base import SessionLocal
from app.models.user import User

logger = logging.getLogger(__name__)

# ── HTTPBearer 安全方案 ──
# 它会告诉 Swagger UI：这个接口需要 Bearer token
# Swagger 会自动在接口上显示锁图标，Authorize 填的 token 会自动注入
bearer_scheme = HTTPBearer(auto_error=False)


def get_db():
    """提供数据库 session。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """从 Authorization header 解析当前用户。

    用 HTTPBearer 替代手动解析 Header，好处：
    - Swagger UI 自动识别认证需求，显示锁图标
    - Authorize 填的 token 自动注入到请求头
    - 不用手动处理 "Bearer " 前缀

    异常：
        UnauthorizedError: 没带 token / token 无效 / 用户不存在
    """
    if credentials is None:
        raise UnauthorizedError("未登录")

    token = credentials.credentials   # HTTPBearer 已经帮你去掉了 "Bearer " 前缀
    user_id = decode_token(token)

    if user_id is None:
        raise UnauthorizedError("token 无效或已过期")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise UnauthorizedError("用户不存在")

    return user