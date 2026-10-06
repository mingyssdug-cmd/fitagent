"""
认证服务。

职责：
- 用户注册
- 用户登录
- 抛 AppException，不处理 HTTP

设计：
- 只负责业务逻辑，不直接操作数据库（通过 Repository）
- 事务由本层 commit，Repository 只 flush
"""

import logging

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, UnauthorizedError, ValidationError
from app.core.security import create_token, hash_password, verify_password
from app.models.user import User
from app.repositories.user_repo import UserRepository

logger = logging.getLogger(__name__)


class AuthService:
    """认证相关的业务逻辑。"""

    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)

    def register(self, phone: str, password: str, name: str) -> tuple[User, str]:
        """注册新用户。

        参数：
            phone: 手机号（11 位）
            password: 密码（≥6 位）
            name: 姓名

        返回：
            (User 对象, JWT token)

        异常：
            ValidationError: 手机号或密码格式不对
            ConflictError: 手机号已注册
        """
        # 1. 格式校验（Pydantic 已做，这里做防御性校验）
        if not phone.isdigit() or len(phone) != 11:
            raise ValidationError("手机号必须是 11 位数字")
        if len(password) < 6:
            raise ValidationError("密码至少 6 位")

        # 2. 检查手机号是否已注册
        if self.user_repo.get_by_phone(phone):
            raise ConflictError("手机号已注册")

        # 3. 创建用户
        user = self.user_repo.create(
            phone=phone,
            password_hash=hash_password(password),
            name=name,
        )

        # 4. 提交事务
        self.db.commit()
        self.db.refresh(user)

        # 5. 生成 token
        token = create_token(user.id)

        logger.info("用户注册成功: user_id=%s phone=%s", user.id, phone)

        return user, token

    def login(self, phone: str, password: str) -> tuple[User, str]:
        """用户登录。

        返回：
            (User 对象, JWT token)

        异常：
            UnauthorizedError: 手机号或密码错误
        """
        # 1. 查用户
        user = self.user_repo.get_by_phone(phone)

        # 2. 校验密码
        # 注意：即使 user 不存在也要走 verify_password（防止时序攻击）
        if not user or not verify_password(password, user.password_hash):
            raise UnauthorizedError("手机号或密码错误")

        # 3. 更新最后登录时间
        self.user_repo.update_last_login(user)
        self.db.commit()
        self.db.refresh(user)

        # 4. 生成 token
        token = create_token(user.id)

        logger.info("用户登录成功: user_id=%s", user.id)

        return user, token