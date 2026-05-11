from crewai import LLM
from ..config import settings

deepseek_llm = LLM(
    model="deepseek-v4-pro",
    api_key=settings.DEEPSEEK_API_KEY,
    base_url=settings.DEEPSEEK_BASE_URL,
    provider="openai",
)

qwen_llm = LLM(
    model="qwen3.5-35b-a3b",
    api_key=settings.QWEN_API_KEY,
    base_url=settings.QWEN_BASE_URL,
    provider="openai",
)
