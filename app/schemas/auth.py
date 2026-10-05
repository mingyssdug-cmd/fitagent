"""
认证相关的 Pydantic 模型。

职责：
- 注册请求体
- 登录请求体
- 认证响应数据
"""

from pydantic import BaseModel, Field, field_validator


class RegisterRequest(BaseModel):
    """注册请求体。"""

    phone: str = Field(
        ...,
        min_length=11,
        max_length=11,
        description="手机号，11 位数字",
    )
    password: str = Field(
        ...,
        min_length=6,
        max_length=64,
        description="密码，至少 6 位",
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="姓名",
    )

    @field_validator("phone")
    @classmethod
    def phone_must_be_digits(cls, v: str) -> str:
        """手机号必须是纯数字。"""
        if not v.isdigit():
            raise ValueError("手机号必须是纯数字")
        return v


class LoginRequest(BaseModel):
    """登录请求体。"""

    phone: str = Field(..., description="手机号")
    password: str = Field(..., description="密码")


class AuthData(BaseModel):
    """认证成功后返回的数据。注册和登录共用。"""

    user_id: int
    token: str
    name: str