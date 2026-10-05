"""
RAG 加载模块。

职责：
- 从 data/knowledge/ 目录加载 PDF
- 切分成 chunk（小块）
- 返回 Document 列表

设计：
- 切分参数用默认值（chunk_size=500, chunk_overlap=50）
- 后续优化时再调参（已在 S2 的"后续优化方向"里记录）
"""

from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 知识库目录：项目根/data/knowledge/
# __file__ 是当前文件路径，parents[2] 向上两级到项目根
KNOWLEDGE_DIR = Path(__file__).resolve().parents[2] / "data" / "knowledge"


def load_and_split(pdf_filename: str):
    """加载单个 PDF 并切分成 chunk。

    参数：
        pdf_filename: PDF 文件名（不含路径），如 "nutrition_guide.pdf"

    返回：
        list[Document]，每个 Document 是一个 chunk
    """
    pdf_path = KNOWLEDGE_DIR / pdf_filename

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF 不存在: {pdf_path}")

    # 1. 加载 PDF
    # PyPDFLoader 会为每一页生成一个 Document
    docs = PyPDFLoader(str(pdf_path)).load()

    # 2. 切分
    # RecursiveCharacterTextSplitter 按段落、句子、字符逐级尝试切分
    # 优先在段落边界切，保证语义完整
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,       # 每个 chunk 最多 500 字符
        chunk_overlap=50,     # 相邻 chunk 重叠 50 字符，防止语义断裂
    )
    chunks = splitter.split_documents(docs)

    return chunks