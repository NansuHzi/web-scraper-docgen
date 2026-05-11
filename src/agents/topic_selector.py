from crewai import Agent
from ..core.llm import deepseek_llm


class TopicSelector:
    def __init__(self):
        self.agent = Agent(
            role='热点选题分析师',
            goal='分析微博和知乎热搜趋势，从海量信息中发现有价值的文档选题，为用户提供专业的选题建议',
            backstory=(
                '你拥有10年新媒体运营和内容策划经验，擅长从热搜数据中发现趋势、'
                '识别用户真正关心的话题，并判断哪些选题具有长期内容价值。'
                '你熟悉技术写作、知识科普和热点评论等多种文档类型。'
            ),
            llm=deepseek_llm,
            verbose=True,
        )
