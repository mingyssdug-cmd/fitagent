import asyncio

from app.agents.graph import close_graph, init_graph, stream_graph
from app.core.logging import setup_logging
from app.models.base import SessionLocal
from app.repositories.profile_repo import ProfileRepository


async def main():
    setup_logging()
    await init_graph()

    db = SessionLocal()
    try:
        profile_repo = ProfileRepository(db)
        profile = profile_repo.get_by_user_id(1)
        if not profile:
            print("用户 1 没有档案")
            return

        thread_id = "test_stream_001"
        print("开始流式输出：")
        print("-" * 60)

        async for token in stream_graph(
            profile.to_dict(),
            profile.goal,
            thread_id,
        ):
            print(token, end="", flush=True)

        print()
        print("-" * 60)
        print("流式输出完成")

    finally:
        db.close()
        await close_graph()


if __name__ == "__main__":
    asyncio.run(main())