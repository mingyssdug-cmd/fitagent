"""
RAG 检索模块。

职责：
- 构建向量库（从 PDF 到 ChromaDB）
- 加载已有向量库
- 相似度检索

设计：
- 用 SegmentAPI 绕过 ChromaDB 的 Rust 绑定 Bug（你踩过的坑）
- 支持多 collection（营养库 + 动作库）
"""

from pathlib import Path

from chromadb.config import Settings as ChromaSettings
from langchain_chroma import Chroma

from app.core.config import settings
from app.rag.embedder import embeddings
from app.rag.loader import load_and_split

# ── 向量库持久化目录 ──
CHROMA_DIR = Path(__file__).resolve().parents[2] / settings.chroma_persist_dir

# ── 两个 collection 名称 ──
NUTRITION_COLLECTION = "nutrition_knowledge"
WORKOUT_COLLECTION = "workout_knowledge"


def _make_chroma(collection_name: str) -> Chroma:
    """创建 Chroma 实例。内部函数，统一配置。

    client_settings 里强制用 SegmentAPI（纯 Python 实现），
    绕开 ChromaDB 的 Rust 绑定 Bug。
    """
    return Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=str(CHROMA_DIR),
        client_settings=ChromaSettings(
            chroma_api_impl="chromadb.api.segment.SegmentAPI",
            anonymized_telemetry=False,
        ),
    )


def build_vectorstore(pdf_filename: str, collection_name: str) -> None:
    """从 PDF 构建向量库。重复运行会覆盖同名 collection。

    参数：
        pdf_filename: PDF 文件名
        collection_name: 向量库的 collection 名（用上面的常量）
    """
    chunks = load_and_split(pdf_filename)

    _make_chroma(collection_name).add_documents(chunks)

    print(f"[Retriever] {collection_name} 构建完成，共 {len(chunks)} 条")


def search(query: str, k: int = 3, collection_name: str = NUTRITION_COLLECTION):
    """检索。默认查营养库，可指定其他 collection。

    参数：
        query: 检索关键词
        k: 返回条数
        collection_name: 目标 collection

    返回：
        list[Document]
    """
    vectorstore = _make_chroma(collection_name)
    return vectorstore.similarity_search(query, k=k)