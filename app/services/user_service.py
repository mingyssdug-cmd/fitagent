"""
用户服务。

职责：
- 获取用户档案
- 更新用户档案

设计：
- 档案不存在时自动创建（用户首次填档案）
"""

import logging

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.profile import Profile
from app.models.user import User
from app.repositories.profile_repo import ProfileRepository
from app.repositories.user_repo import UserRepository

logger = logging.getLogger(__name__)


class UserService:
    """用户档案相关的业务逻辑。"""

    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.profile_repo = ProfileRepository(db)

    def get_me(self, user_id: int) -> tuple[User, Profile | None]:
        """获取当前用户的档案。

        返回：
            (User 对象, Profile 对象或 None)
        """
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("用户不存在")

        profile = self.profile_repo.get_by_user_id(user_id)

        return user, profile

    def update_me(self, user_id: int, name: str, profile_data: dict) -> tuple[User, Profile]:
        """更新用户档案。

        参数：
            user_id: 用户 ID
            name: 姓名
            profile_data: 档案字段 dict

        返回：
            (User 对象, Profile 对象)
        """
        # 1. 查用户
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("用户不存在")

        # 2. 更新 name
        user.name = name

        # 3. 档案存在则更新，不存在则创建
        profile = self.profile_repo.get_by_user_id(user_id)
        if profile:
            self.profile_repo.update(profile, **profile_data)
        else:
            profile = self.profile_repo.create(user_id=user_id, **profile_data)

        # 4. 提交
        self.db.commit()
        self.db.refresh(user)
        self.db.refresh(profile)

        logger.info("用户档案更新: user_id=%s", user_id)

        return user, profile