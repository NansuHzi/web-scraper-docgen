from crewai import Crew, Process, Task
from ..agents.researcher import Researcher
from ..agents.writer import Writer
from ..agents.reviewer import Reviewer
from ..core.llm import deepseek_llm, qwen_llm


def create_research_crew(url: str, llm=None):
    researcher_agent = Researcher().agent
    if llm:
        researcher_agent.llm = llm

    research_task = Task(
        description=f"使用你的网页抓取工具，抓取并分析以下网页的关键信息：{url}",
        expected_output="结构化网页内容摘要，包括网页标题、关键段落和重要数据点",
        agent=researcher_agent
    )

    crew = Crew(
        agents=[researcher_agent],
        tasks=[research_task],
        process=Process.sequential,
        verbose=True
    )

    return crew, research_task


def create_document_crew(url: str, doc_type: str, research_task, llm=None):
    writer_agent = Writer().agent
    reviewer_agent = Reviewer().agent

    if llm:
        writer_agent.llm = llm

    write_task = Task(
        description=f"基于研究员提供的网页信息，创建一个【{doc_type}】类型的文档。"
                    f"要求：使用标准Markdown语法，层级清晰，重点突出，适合存入RAG知识库。",
        expected_output="格式良好的Markdown文档，包含标题、章节和关键内容",
        agent=writer_agent,
        context=[research_task]
    )

    review_task = Task(
        description="请审查生成的文档。检查是否有明显的语句不通、格式错误（如缺少#号、列表不规范等）。"
                    "直接输出修改完善后的最终版Markdown文档，不要附带任何多余的评论。",
        expected_output="经过验证的最终版Markdown文档",
        agent=reviewer_agent,
        context=[write_task]
    )

    crew = Crew(
        agents=[writer_agent, reviewer_agent],
        tasks=[write_task, review_task],
        process=Process.sequential,
        verbose=True
    )

    return crew


def create_rag_document_crew(topic: str, doc_type: str, context_text: str, llm=None):
    writer_agent = Writer().agent
    reviewer_agent = Reviewer().agent

    if llm:
        writer_agent.llm = llm

    write_task = Task(
        description=f"基于以下参考资料，创建一个【{doc_type}】类型的文档。\n"
                    f"主题：{topic}\n\n"
                    f"参考资料：\n{context_text}\n\n"
                    f"要求：使用标准Markdown语法，层级清晰，重点突出，综合所有参考资料的内容。",
        expected_output="格式良好的Markdown文档，包含标题、章节和关键内容",
        agent=writer_agent,
    )

    review_task = Task(
        description="审查并优化生成的文档。检查语句流畅性、格式规范、内容完整性。"
                    "直接输出修改完善后的最终版Markdown文档，不要附带多余评论。",
        expected_output="经过验证的最终版Markdown文档",
        agent=reviewer_agent,
        context=[write_task],
    )

    crew = Crew(
        agents=[writer_agent, reviewer_agent],
        tasks=[write_task, review_task],
        process=Process.sequential,
        verbose=True
    )

    return crew


def create_topic_analysis_crew(topic_data: str):
    from ..agents.topic_selector import TopicSelector

    analyst = TopicSelector().agent

    analyze_task = Task(
        description=f"基于以下热搜数据进行趋势分析和选题推荐：\n\n{topic_data}\n\n"
                    "任务：1. 识别热点主题和趋势集群 2. 按内容价值排序 3. 为每个推荐选题提供理由和切入角度",
        expected_output="JSON格式的推荐选题列表，包含排名、选题名称、推荐理由、切入角度、热度评估",
        agent=analyst,
    )

    crew = Crew(
        agents=[analyst],
        tasks=[analyze_task],
        process=Process.sequential,
        verbose=True,
    )

    return crew, analyze_task
