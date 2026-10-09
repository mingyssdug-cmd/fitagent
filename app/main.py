"""
FastAPI 入口。

职责：
- 创建 FastAPI 应用
- 注册路由
- 注册全局异常处理器
- 初始化日志
- 配置 CORS
- 启动时初始化 LangGraph 图

设计：
- main.py 只做"组装"，不写任何业务逻辑
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import auth, chat, plans, users
from app.agents.graph import close_graph, init_graph
from app.core.exceptions import AppException
from app.core.logging import setup_logging

# 初始化日志（必须在其他模块之前）
setup_logging()
logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════
# 生命周期：启动时初始化图，关闭时清理
# ══════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI 生命周期管理。

    启动时调用 init_graph() 初始化 LangGraph 的异步 checkpointer。
    关闭时调用 close_graph() 释放连接。
    """
    logger.info("应用启动，初始化 LangGraph...")
    await init_graph()
    logger.info("LangGraph 初始化完成")
    yield
    logger.info("应用关闭，清理 LangGraph...")
    await close_graph()


# ── 创建 FastAPI 应用 ──
app = FastAPI(
    title="FitAgent API",
    description="个人健身助手 Agent",
    version="1.0.0",
    lifespan=lifespan,
)


# ══════════════════════════════════════════════
# 中间件
# ══════════════════════════════════════════════

# CORS：允许跨域（小程序开发时需要用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # 生产环境要改成具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ══════════════════════════════════════════════
# 全局异常处理器
# ══════════════════════════════════════════════

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """处理所有自定义业务异常。

    Service 层抛 AppException，这里统一转成 {"code": ..., "message": ...}
    """
    logger.warning("业务异常: code=%s message=%s path=%s", exc.code, exc.message, request.url.path)
    return JSONResponse(
        status_code=200,       # HTTP 状态码统一用 200，业务状态码放在 body 里
        content={
            "code": exc.code,
            "message": exc.message,
            "data": None,
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """处理未预期的异常。"""
    logger.exception("未处理的异常: path=%s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "code": 5000,
            "message": "服务器内部错误",
            "data": None,
        },
    )


# ══════════════════════════════════════════════
# 注册路由
# ══════════════════════════════════════════════

API_PREFIX = "/api/v1"

app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(users.router, prefix=API_PREFIX)
app.include_router(plans.router, prefix=API_PREFIX)
app.include_router(chat.router, prefix=API_PREFIX)


# ══════════════════════════════════════════════
# 健康检查
# ══════════════════════════════════════════════

@app.get("/health")
def health():
    """健康检查接口。"""
    return {"status": "ok"}