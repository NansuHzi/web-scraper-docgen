# src/core/llm.py
import os
from crewai import LLM  # 改用 CrewAI 的 LLM 类

# 定义三个不同模型
deepseek_llm = LLM(
    model="deepseek-chat",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL"),
    provider="openai",  # DeepSeek 兼容 OpenAI 接口
)

qwen_llm = LLM(
    model="qwen3.5-35b-a3b",
    api_key=os.getenv("QWEN_API_KEY"),
    base_url=os.getenv("QWEN_BASE_URL"),
    provider="openai",  # 通义千问兼容 OpenAI 接口
)
