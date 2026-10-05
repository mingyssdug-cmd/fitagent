"""
Plan Repository：封装 plans 表的数据库操作。

职责：
- 创建计划
- 按 ID 查计划
- 按 user_id 分页查历史
- 统计用户计划总数
"""

from sqlalchemy.orm import Session

from app.models.plan import Plan


class PlanRepository:
    """Plan 表的数据访问对象。"""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        user_id: int,
        goal: str,
        nutrition_plan: str,
        workout_plan: str,
        feedback: str | None = None,
    ) -> Plan:
        """创建计划记录。"""
        plan = Plan(
            user_id=user_id,
            goal=goal,
            nutrition_plan=nutrition_plan,
            workout_plan=workout_plan,
            feedback=feedback,
            status="completed",
        )
        self.db.add(plan)
        self.db.flush()
        return plan

    def get_by_id(self, plan_id: int) -> Plan | None:
        """按 ID 查计划。"""
        return self.db.query(Plan).filter(Plan.id == plan_id).first()

    def list_by_user(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[Plan], int]:
        """按用户分页查询历史计划。

        返回：
            (计划列表, 总数)
        """
        query = self.db.query(Plan).filter(Plan.user_id == user_id)

        total = query.count()

        items = (
            query.order_by(Plan.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return items, total