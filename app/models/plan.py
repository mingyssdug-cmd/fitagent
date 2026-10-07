"""
Plan 模型：历史计划。

对应数据库表：plans
职责：存储用户确认后的营养计划和训练计划

设计决策：
- 只存"已确认"的计划。生成中的计划在 LangGraph checkpointer 里，不落库
- goal 字段是"生成时的目标快照"。用户改了目标后，历史计划的语义不变
"""

from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index

from app.models.base import Base


class Plan(Base):
    """历史计划表。每次用户确认计划，写入一条记录。"""

    __tablename__ = "plans"

    # ── 主键 ──
    id = Column(Integer, primary_key=True, autoincrement=True)

    # ── 外键（一个用户多个计划）──
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,   # 按用户查历史时加速
    )

    # ── 目标快照（记录生成时的目标，不受用户后续改目标影响）──
    goal = Column(String(20), nullable=False)

    # ── 计划内容（TEXT 支持长文本 + Markdown）──
    nutrition_plan = Column(Text, nullable=False)
    workout_plan = Column(Text, nullable=False)

    # ── 用户反馈（最后一次修改意见）──
    feedback = Column(Text, nullable=True)

    # ── 状态（v1.0 只有 completed，保留字段供未来扩展）──
    status = Column(String(20), nullable=False, default="completed")

    # ── 时间戳 ──
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # ── 复合索引：按用户查历史并按时间倒序 ──
    __table_args__ = (
        Index("idx_plans_user_created", "user_id", created_at.desc()),
    )

    def __repr__(self):
        return f"<Plan id={self.id} user_id={self.user_id} goal={self.goal}>"