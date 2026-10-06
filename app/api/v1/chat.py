"""
聊天路由。

职责：
- POST /chat/simple：简单对话（调试用，不走 Agent）
"""

import logging

from fastapi import APIRouter, Depends

from app.schemas.common import ApiResponse
from app.services.chat_service import ChatService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["聊天"])


@router.post("/simple", response_model=ApiResponse[dict])
def simple_chat(req: dict):
    """简单对话。直接调模型，不走 Agent。

    请求体：{"message": "..."}
    """
    service = ChatService()
    reply = service.simple_chat(req.get("message", ""))

    return ApiResponse(data={"reply": reply})