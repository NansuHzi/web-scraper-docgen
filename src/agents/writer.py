from crewai import Agent
from src.core.llm import deepseek_llm


class Writer:
    def __init__(self):
        self.agent = Agent(
            role='文档撰写员',
            goal='将分析结果转化为专业、结构化的Markdown文档',
            backstory='你是一位技术文档专家，擅长将碎片化的信息转化为清晰易读、结构严谨的Markdown文档，特别适合用于知识库构建。',
            llm=deepseek_llm,
            verbose=True
        )
