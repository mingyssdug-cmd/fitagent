"""
Agent 包初始化。

职责：
- 在这里初始化 LLM 模型（全项目共用一份）
- 其他 Agent 文件通过 `from app.agents import model` 使用

为什么放在 __init__.py：
- 避免在每个 Agent 文件里重复初始化模型
- 模型初始化成本高（要建立连接），只做一次
"""

from langchain.chat_models import init_chat_model

from app.core.config import settings

# ── LLM 模型（全局单例）──
# 用 DashScope 的 OpenAI 兼容接口
model = init_chat_model(
    model="qwen3.7-plus",
    model_provider="openai",
    base_url=settings.dashscope_base_url,
    api_key=settings.dashscope_api_key,
)