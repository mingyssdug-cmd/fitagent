"""
用户档案相关的 Pydantic 模型。

职责：
- 档案数据的请求/响应
- 用户信息的响应
"""

from pydantic import BaseModel, Field


class ProfileData(BaseModel):
    """档案数据。用于 PUT /users/me 的请求体，也用于 GET /users/me 的响应。"""

    gender: str = Field(..., description="male / female")
    age: int = Field(..., ge=1, le=120, description="年龄")
    weight_kg: float = Field(..., gt=0, le=500, description="体重（公斤）")
    height_cm: float = Field(..., gt=0, le=300, description="身高（厘米）")
    activity: str = Field(..., description="sedentary/light/moderate/active/very_active")
    goal: str = Field(..., description="cut/bulk/maintain")
    experience: str = Field(..., description="beginner/intermediate/advanced")
    injuries: str | None = Field(None, description="伤病史，可为空")
    days_per_week: int = Field(..., ge=1, le=7, description="每周训练天数")


class UpdateUserRequest(BaseModel):
    """PUT /users/me 的请求体。"""

    name: str = Field(..., min_length=1, max_length=50)
    profile: ProfileData


class UserDetailData(BaseModel):
    """GET /users/me 的响应数据。"""

    user_id: int
    phone: str
    name: str
    profile: ProfileData | None  # 可能为 null（用户还没填档案）