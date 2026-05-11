from pydantic_settings import BaseSettings
from pydantic import Field


class AppSettings(BaseSettings):
    LOG_LEVEL: str = "INFO"

    CORS_ORIGINS: str = ""

    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
    INTENT_LLM_MODEL: str = "deepseek-chat"
    REPLY_LLM_MODEL: str = "deepseek-chat"

    QWEN_API_KEY: str = ""
    QWEN_BASE_URL: str = ""

    USE_LLM: bool = True

    SERVER_PUBLIC_URL: str = "http://127.0.0.1:8000"

    FIRECRAWL_ENABLED: bool = False
    FIRECRAWL_BASE_URL: str = "http://localhost:3002"
    FIRECRAWL_API_KEY: str = "fc-local"
    FIRECRAWL_TIMEOUT: int = 60
    FIRECRAWL_FALLBACK: bool = True

    XIANYU_GATEWAY: str = "mock"
    XIANYU_COOKIE_DIR: str = "data"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = AppSettings()
