from crewai import Agent
from ..core.llm import deepseek_llm


class Scheduler:
    def __init__(self):
        self.agent = Agent(
            role='任务调度员',
            goal='管理定时任务，确保文档抓取和生成任务按计划执行',
            backstory=(
                '你是一位经验丰富的任务调度专家，负责管理定时抓取和文档生成任务。'
                '你确保每个任务按时执行，监控执行状态，并在出现问题时及时处理。'
            ),
            llm=deepseek_llm,
            verbose=True,
        )
