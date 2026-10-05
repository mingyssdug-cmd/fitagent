"""
Profile Repository：封装 profiles 表的数据库操作。

职责：
- 按 user_id 查档案
- 创建档案
- 更新档案
"""

from sqlalchemy.orm import Session

from app.models.profile import Profile


class ProfileRepository:
    """Profile 表的数据访问对象。"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_user_id(self, user_id: int) -> Profile | None:
        """按 user_id 查档案。不存在返回 None。"""
        return self.db.query(Profile).filter(Profile.user_id == user_id).first()

    def create(self, user_id: int, **fields) -> Profile:
        """创建档案。

        参数：
            user_id: 用户 ID
            **fields: 档案字段（gender, age, weight_kg 等）
        """
        profile = Profile(user_id=user_id, **fields)
        self.db.add(profile)
        self.db.flush()
        return profile

    def update(self, profile: Profile, **fields) -> Profile:
        """更新档案字段。

        只更新传入的字段，未传入的保持不变。
        """
        for key, value in fields.items():
            setattr(profile, key, value)
        self.db.flush()
        return profile