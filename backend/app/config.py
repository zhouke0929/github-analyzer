"""应用配置管理"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""
    # 应用配置
    app_name: str = "GitHub项目智能分析"
    app_version: str = "1.0.0"
    debug: bool = True

    # GitHub配置
    github_token: str = ""

    # AI模型配置
    default_ai_provider: str = "openai"
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"
    claude_api_key: str = ""

    # 数据库配置
    database_url: str = "sqlite:///./data/analyzer.db"

    # CORS配置
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
