from crewai import Agent
from src.core.llm import qwen_llm


class Reviewer:
    def __init__(self):
        self.agent = Agent(
            role='内容审查员',
            goal='审查并优化文档，确保内容准确、格式标准',
            backstory='你是一位严谨的出版审核编辑，擅长发现文本中的逻辑漏洞、格式错误，并能给出最终的完美版本。',
            llm=qwen_llm,  # ← 指定使用千问
            verbose=True
        )
