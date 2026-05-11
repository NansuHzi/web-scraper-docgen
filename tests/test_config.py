import pytest
import os
from src.config import AppSettings


class TestAppSettings:
    def test_default_values(self):
        s = AppSettings(_env_file=None)
        assert s.LOG_LEVEL == "INFO"
        assert s.USE_LLM is True
        assert s.XIANYU_COOKIE_DIR == "data"
        assert s.SERVER_PUBLIC_URL == "http://127.0.0.1:8000"
        assert s.DEEPSEEK_BASE_URL == "https://api.deepseek.com/v1"
        assert s.INTENT_LLM_MODEL == "deepseek-chat"
        assert s.REPLY_LLM_MODEL == "deepseek-chat"

    def test_cors_origins_default(self):
        s = AppSettings(_env_file=None)
        assert isinstance(s.CORS_ORIGINS, str)

    def test_api_keys_are_strings(self):
        s = AppSettings(_env_file=None)
        assert isinstance(s.DEEPSEEK_API_KEY, str)
        assert isinstance(s.QWEN_API_KEY, str)

    def test_env_override(self):
        os.environ["LOG_LEVEL"] = "DEBUG"
        try:
            s = AppSettings(_env_file=None)
            assert s.LOG_LEVEL == "DEBUG"
        finally:
            del os.environ["LOG_LEVEL"]
