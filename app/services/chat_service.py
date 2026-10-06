"""
聊天服务。

职责：
- 简单对话（不走 Agent、不走 RAG）
- 用于验证模型连通性

设计：
- 直接调 LLM，不涉及业务逻辑
"""

import logging

from app.agents import model
from app.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


class ChatService:
    """简单对话服务。"""

    def simple_chat(self, message: str) -> str:
        """直接调模型，返回回复。

        参数：
            message: 用户输入

        返回：
            模型回复文本

        异常：
            ValidationError: message 为空
        """
        if not message or not message.strip():
            raise ValidationError("message 不能为空")

        response = model.invoke(message)

        logger.info("简单对话完成，输入长度=%s", len(message))

        return response.content