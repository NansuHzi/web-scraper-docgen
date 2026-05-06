from crewai import Crew, Process, Task
from ..agents.researcher import Researcher
from ..agents.writer import Writer
from ..agents.reviewer import Reviewer


def create_research_crew(url: str):
    """创建仅包含 Researcher 的 Crew（第一阶段）"""
    researcher = Researcher().agent
    
    research_task = Task(
        description=f"使用你的网页抓取工具，抓取并分析以下网页的关键信息：{url}",
        expected_output="结构化网页内容摘要，包括网页标题、关键段落和重要数据点",
        agent=researcher
    )
    
    crew = Crew(
        agents=[researcher],
        tasks=[research_task],
        process=Process.sequential,
        verbose=True
    )
    
    return crew, research_task


def create_document_crew(url: str, doc_type: str, research_task):
    """创建 Writer + Reviewer 的 Crew（第二阶段）"""
    writer = Writer().agent
    reviewer = Reviewer().agent
    
    # 撰写任务
    write_task = Task(
        description=f"基于研究员提供的网页信息，创建一个【{doc_type}】类型的文档。"
                    f"要求：使用标准Markdown语法，层级清晰，重点突出，适合存入RAG知识库。",
        expected_output="格式良好的Markdown文档，包含标题、章节和关键内容",
        agent=writer,
        context=[research_task]
    )
    
    # 审查任务
    review_task = Task(
        description="请审查生成的文档。检查是否有明显的语句不通、格式错误（如缺少#号、列表不规范等）。"
                    "直接输出修改完善后的最终版Markdown文档，不要附带任何多余的评论。",
        expected_output="经过验证的最终版Markdown文档",
        agent=reviewer,
        context=[write_task]
    )
    
    crew = Crew(
        agents=[writer, reviewer],
        tasks=[write_task, review_task],
        process=Process.sequential,
        verbose=True
    )

    return crew


def create_rag_document_crew(topic: str, doc_type: str, context_text: str):
    """基于 RAG 检索上下文创建文档（无需 Researcher 抓取）"""
    writer = Writer().agent
    reviewer = Reviewer().agent

    write_task = Task(
        description=f"基于以下参考资料，创建一个【{doc_type}】类型的文档。\n"
                    f"主题：{topic}\n\n"
                    f"参考资料：\n{context_text}\n\n"
                    f"要求：使用标准Markdown语法，层级清晰，重点突出，综合所有参考资料的内容。",
        expected_output="格式良好的Markdown文档，包含标题、章节和关键内容",
        agent=writer,
    )

    review_task = Task(
        description="审查并优化生成的文档。检查语句流畅性、格式规范、内容完整性。"
                    "直接输出修改完善后的最终版Markdown文档，不要附带多余评论。",
        expected_output="经过验证的最终版Markdown文档",
        agent=reviewer,
        context=[write_task],
    )

    crew = Crew(
        agents=[writer, reviewer],
        tasks=[write_task, review_task],
        process=Process.sequential,
        verbose=True
    )

    return crew
