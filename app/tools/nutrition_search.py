"""
营养库检索工具。

职责：
- 把 retriever.search() 包装成 Agent 可调用的 @tool
- 格式化输出，带来源标注

设计：
- 检索结果带 [来源 X | 第 Y 页]，方便用户追溯
- 空结果返回友好提示，不让 Agent 拿到空字符串
"""

from langchain.tools import tool

from app.rag.retriever import NUTRITION_COLLECTION, search


@tool
def search_nutrition(query: str) -> str:
    """检索健身营养知识库。

    当用户询问营养原则、餐次分配、食物选择、特殊人群注意事项时，
    调用此工具检索知识库，不要凭记忆回答。

    Args:
        query: 检索关键词，如"减脂期蛋白质摄入"、"5餐制分配"

    Returns:
        格式化后的检索结果，带来源标注
    """
    docs = search(query, k=3, collection_name=NUTRITION_COLLECTION)

    if not docs:
        return "营养库中未找到相关内容。"

    results = []
    for i, doc in enumerate(docs, 1):
        page = doc.metadata.get("page", "?")
        results.append(f"[来源 {i} | 第 {page} 页]\n{doc.page_content}")

    return "\n\n".join(results)