"""
初始化数据库脚本。

作用：
- 导入所有模型，让 Base.metadata 知道有哪些表
- 调用 create_all() 建表

用法：
python -m scripts.init_db
"""

from app.models.base import Base, engine

# 必须导入所有模型，否则 create_all 不知道它们的存在
from app.models.user import User        # noqa: F401
from app.models.profile import Profile  # noqa: F401
from app.models.plan import Plan        # noqa: F401


def init_db():
    """创建所有表。已存在的表不会重复创建。"""
    Base.metadata.create_all(engine)
    print("[DB] 表已创建:", list(Base.metadata.tables.keys()))


if __name__ == "__main__":
    init_db()