import asyncio
import time

from app.agents import graph as graph_module
from app.agents.graph import close_graph, init_graph
from app.core.logging import setup_logging
from app.models.base import SessionLocal
from app.repositories.profile_repo import ProfileRepository


async def main():
    setup_logging()

    await init_graph()

    user_id = 1
    db = SessionLocal()
    try:
        profile_repo = ProfileRepository(db)
        profile = profile_repo.get_by_user_id(user_id)
        if not profile:
            print(f"用户 {user_id} 没有档案")
            return

        print("=" * 60)
        print(f"测试用户: user_id={user_id}, goal={profile.goal}")
        print("=" * 60)

        total_start = time.time()

        config = {"configurable": {"thread_id": f"timing_test_{int(time.time())}"}}

        result = await graph_module.graph_app.ainvoke(
            {
                "user_profile": profile.to_dict(),
                "goal": profile.goal,
                "feedback": None,
                "retry_count": 0,
            },
            config=config,
        )

        total_cost = time.time() - total_start

        interrupts = result.get("__interrupt__", [])
        if interrupts:
            interrupt_value = interrupts[0].value
            print(f"    营养计划: {len(interrupt_value['nutrition_plan'])} 字")
            print(f"    训练计划: {len(interrupt_value['workout_plan'])} 字")

        print("=" * 60)
        print(f"总耗时: {total_cost:.2f} 秒")
        print("=" * 60)

    finally:
        db.close()
        await close_graph()   # ← 新增：关闭图，释放 aiosqlite 连接


if __name__ == "__main__":
    asyncio.run(main())