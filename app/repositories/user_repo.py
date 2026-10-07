"""
User Repository：封装 users 表的数据库操作。

职责：
- 按手机号查用户
- 按 ID 查用户
- 创建用户
- 更新最后登录时间

设计：
- 不 commit，由 Service 层控制事务
- 只做数据访问，不做业务判断（如"手机号是否已注册"由 Service 判断）
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    """User 表的数据访问对象。"""

    def __init__(self, db: Session):
        """构造时传入 session。由 Service 层创建并传入。"""
        self.db = db

    def get_by_id(self, user_id: int) -> User | None:
        """按 ID 查用户。不存在返回 None。"""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_phone(self, phone: str) -> User | None:
        """按手机号查用户。不存在返回 None。"""
        return self.db.query(User).filter(User.phone == phone).first()

    def create(self, phone: str, password_hash: str, name: str) -> User:
        """创建用户。

        注意：
        - 只 add，不 commit。commit 由 Service 层负责
        - 返回的 User 对象还没有 id，需要 flush 或 refresh 后才拿到
        """
        user = User(
            phone=phone,
            password_hash=password_hash,
            name=name,
            status=1,
        )
        self.db.add(user)
        self.db.flush()   # flush 让 user 拿到 id，但不 commit
        return user

    def update_last_login(self, user: User) -> None:
        """更新最后登录时间。"""
        user.last_login_at = datetime.now(timezone.utc)
        self.db.flush()