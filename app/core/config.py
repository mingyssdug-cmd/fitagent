from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置。所有值从 .env 读取。"""

    # ── 模型 ──
    dashscope_api_key: str
    dashscope_base_url: str

    # ── 数据库 ──
    database_url: str

    # ── JWT ──
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24

    # ── 向量库 ──
    chroma_persist_dir: str = "./chroma_db"

    # ── 应用 ──
    app_env: str = "development"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()