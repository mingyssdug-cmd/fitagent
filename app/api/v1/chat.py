"""
聊天路由。

职责：
- POST /chat/simple：简单对话（非流式，调试用）
- POST /chat/stream：通用流式对话（聊天页用）
"""

import logging
import time

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.agents import model
from app.core.exceptions import ValidationError
from app.schemas.common import ApiResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["聊天"])


class SimpleChatRequest(BaseModel):
    message: str


@router.post("/simple", response_model=ApiResponse[dict])
def simple_chat(req: SimpleChatRequest):
    """简单对话（非流式）。"""
    from app.services.chat_service import ChatService

    service = ChatService()
    reply = service.simple_chat(req.message)

    return ApiResponse(data={"reply": reply})


@router.post("/stream")
async def chat_stream(req: dict):
    """通用流式对话。聊天页调这个接口。"""
    message = req.get("message", "").strip()
    if not message:
        raise ValidationError("message 不能为空")

    logger.info("[chat_stream] 收到消息: %s", message[:50])

    # 系统提示词：定义 AI 的人设
    SYSTEM_PROMPT = """你是 FitAgent，一个专业的健身助理。

    你的身份：
    - 名字：FitAgent
    - 角色：健身助理
    - 专长：健身训练、营养饮食、体态改善

    你的职责：
    1. 回答用户的健身、营养、训练相关问题
    2. 如果用户问"你是谁"，回答"我是你的健身助理 FitAgent"
    3. 如果用户想生成完整的训练/饮食计划，提示他点"⚡ 一键生成"

    回答风格：
    - 专业但不死板
    - 简洁，控制在 100-200 字
    - 用纯文本，不要用 Markdown 语法
    - 用 · 开头表示列表项
    - 主动询问用户的目标，帮助他制定方案
    """

    async def event_stream():
        try:
            # 构造消息列表（带系统提示词）
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message},
            ]

            async for chunk in model.astream(messages):
                if chunk.content:
                    yield f"data: {chunk.content}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.exception("[chat_stream] 出错")
            yield f"data: [ERROR] {str(e)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )