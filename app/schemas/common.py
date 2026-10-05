"""
通用 Pydantic 模型。

职责：
- 定义统一响应格式（所有接口返回这个结构）
- 定义分页响应格式

设计：
- 所有接口返回 {"code": 0, "message": "success", "data": ...}
- 前端只需要判断 code 是否为 0
"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

# 泛型类型变量：让 ApiResponse[T] 支持任意 data 类型
T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """统一响应格式。

    用法：
        return ApiResponse(data=user_dict)
        return ApiResponse(code=1002, message="未登录", data=None)
    """
    code: int = 0
    message: str = "success"
    data: T | None = None


class PaginationData(BaseModel, Generic[T]):
    """分页数据格式。用于 GET /plans 这类返回列表的接口。"""
    total: int           # 总条数
    page: int            # 当前页码
    page_size: int       # 每页条数
    items: list[T]       # 当前页的数据列表