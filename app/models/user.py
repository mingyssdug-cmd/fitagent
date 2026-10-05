"""
User 模型：用户认证信息。

对应数据库表：users
职责：存储手机号、密码哈希、姓名、状态、最后登录时间

为什么 name 放在这里而不是 Profile：
- 注册时必须填 name，放 users 表方便
- name 变更频率低，和认证信息一起管理更简单
"""

from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, SmallInteger

from app.models.base import Base


class User(Base):
    """用户表。只存认证相关信息，不存身体数据。"""

    __tablename__ = "users"

    # ── 主键 ──
    id = Column(Integer, primary_key=True, autoincrement=True)

    # ── 认证信息 ──
    phone = Column(
        String(11),
        unique=True,      # 手机号唯一，防止重复注册
        nullable=False,
        index=True,       # 登录时按手机号查，加索引加速
    )
    password_hash = Column(
        String(255),
        nullable=False,   # 密码哈希，不存明文
    )

    # ── 基本信息 ──
    name = Column(String(50), nullable=False)

    # ── 状态 ──
    status = Column(
        SmallInteger,
        nullable=False,
        default=1,        # 1=正常，0=禁用（不是物理删除）
    )

    # ── 时间戳 ──
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<User id={self.id} phone={self.phone} name={self.name}>"