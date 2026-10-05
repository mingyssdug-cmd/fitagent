"""
数据库基础模块。

职责：
- 创建 SQLAlchemy 引擎（连接 MySQL）
- 创建 Session 工厂（每个请求一个 session）
- 定义 Base 类（所有 ORM 模型的基类）

注意：
- 这个模块是全项目唯一创建 engine 的地方
- 其他模块用 `from app.models.base import SessionLocal, Base`
- 不要在其他地方重复创建 engine
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

# ── 数据库引擎 ──
# pool_pre_ping=True：每次取连接前 ping 一下，防止 MySQL 长时间无操作后断连
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    echo=False,  # 设 True 会打印所有 SQL，调试时打开
)

# ── Session 工厂 ──
# autoflush=False：查询前不自动 flush，避免意外写库
# autocommit=False：不自动提交，必须手动 commit（保证事务边界清晰）
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

# ── ORM 基类 ──
# 所有模型都继承它。Base.metadata.create_all() 会遍历它建表
Base = declarative_base()