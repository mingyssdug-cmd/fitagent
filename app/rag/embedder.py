"""
RAG 嵌入模块。

职责：
- 封装 OpenAIEmbeddings（走 DashScope 兼容接口）
- 提供全局单例，避免重复创建

设计：
- check_embedding_ctx_length=False：DashScope 要原始字符串，不要 token ID
- chunk_size=10：DashScope 单次请求最多 10 条
"""

from langchain_openai import OpenAIEmbeddings

from app.core.config import settings

# ── 全局单例 ──
# 嵌入模型初始化成本高（要建立连接），只创建一次
embeddings = OpenAIEmbeddings(
    model="text-embedding-v4",
    api_key=settings.dashscope_api_key,
    base_url=settings.dashscope_base_url,
    # DashScope 的兼容接口要求原始字符串，不要 LangChain 预处理的 token ID
    check_embedding_ctx_length=False,
    # DashScope 单次请求最多 10 条文本
    chunk_size=10,
)