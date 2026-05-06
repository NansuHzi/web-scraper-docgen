from crewai import Agent
from crewai.tools import tool
from src.core.llm import deepseek_llm
from src.core.utils import scrape_url_content
import asyncio


@tool
def scrape_webpage(url: str) -> str:
    """抓取指定URL的网页内容，提取纯文本和标题（支持JavaScript动态渲染）"""
    return asyncio.run(scrape_url_content(url, max_chars=5000, lang="zh"))


class Researcher:
    def __init__(self):
        self.agent = Agent(
            role='网页内容研究员',
            goal='准确抓取并且提取网页中的关键信息',
            backstory='你拥有10年经验的网页内容分析专家，擅长从复杂的网页中提取结构化数据，为后续文档撰写提供原材料。',
            tools=[scrape_webpage],
            llm=deepseek_llm,
            verbose=True
        )
