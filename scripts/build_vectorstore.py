"""
构建向量库脚本。

作用：
- 从 PDF 构建营养库和动作库
- 只需跑一次，之后直接检索

用法：
python -m scripts.build_vectorstore
"""

from app.rag.retriever import (
    NUTRITION_COLLECTION,
    WORKOUT_COLLECTION,
    build_vectorstore,
)


def main():
    print("开始构建营养库...")
    build_vectorstore("nutrition_guide.pdf", NUTRITION_COLLECTION)

    print("\n开始构建动作库...")
    build_vectorstore("workout_guide.pdf", WORKOUT_COLLECTION)

    print("\n完成。向量库已持久化到 chroma_db/")


if __name__ == "__main__":
    main()