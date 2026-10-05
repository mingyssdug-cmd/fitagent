"""
动作库检索工具。

职责：
- 把 retriever.search() 包装成 Agent 可调用的 @tool
- 格式化输出，带来源标注

设计和 nutrition_search.py 一致，只是查的 collection 不同。
"""

from langchain.tools import tool

from app.rag.retriever import WORKOUT_COLLECTION, search


@tool
def search_workout(query: str) -> str:
    """检索健身动作规范知识库。

    当用户询问某个动作怎么做、目标肌群、常见错误、禁忌人群时，
    调用此工具检索动作库。

    Args:
        query: 检索关键词，如"卧推动作要领"、"深蹲禁忌"

    Returns:
        格式化后的检索结果，带来源标注
    """
    docs = search(query, k=3, collection_name=WORKOUT_COLLECTION)

    if not docs:
        return "动作库中未找到相关内容。"

    results = []
    for i, doc in enumerate(docs, 1):
        page = doc.metadata.get("page", "?")
        results.append(f"[来源 {i} | 第 {page} 页]\n{doc.page_content}")

    return "\n\n".join(results)