"""
Profile 模型：用户档案信息。

对应数据库表：profiles
职责：存储身体数据（年龄、体重、目标、伤病史等）

为什么和 User 拆开：
- 认证信息和档案信息变更频率不同
- 未来加微信登录、邮箱登录，只改 users 表
- profiles.user_id 加 UNIQUE，保证一个用户一份档案
"""

from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey

from app.models.base import Base


class Profile(Base):
    """用户档案表。只存身体数据，不存认证信息。"""

    __tablename__ = "profiles"

    # ── 主键 ──
    id = Column(Integer, primary_key=True, autoincrement=True)

    # ── 外键（唯一，一个用户一份档案）──
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        unique=True,
        nullable=False,
    )

    # ── 身体数据 ──
    gender = Column(String(10), nullable=False)       # male / female
    age = Column(Integer, nullable=False)
    weight_kg = Column(Float, nullable=False)
    height_cm = Column(Float, nullable=False)

    # ── 训练相关 ──
    activity = Column(String(20), nullable=False)     # sedentary/light/moderate/active/very_active
    goal = Column(String(20), nullable=False)         # cut/bulk/maintain
    experience = Column(String(20), nullable=False)   # beginner/intermediate/advanced
    days_per_week = Column(Integer, nullable=False)   # 每周训练天数

    # ── 伤病史（可空，用 TEXT 存长文本）──
    injuries = Column(Text, nullable=True)

    # ── 时间戳 ──
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),   # 每次 update 自动更新时间
    )

    def to_dict(self) -> dict:
        """转成 Agent 需要的 profile dict。"""
        return {
            "gender": self.gender,
            "age": self.age,
            "weight_kg": self.weight_kg,
            "height_cm": self.height_cm,
            "activity": self.activity,
            "goal": self.goal,
            "experience": self.experience,
            "injuries": self.injuries or "无",
            "days_per_week": self.days_per_week,
        }

    def __repr__(self):
        return f"<Profile user_id={self.user_id} goal={self.goal}>"