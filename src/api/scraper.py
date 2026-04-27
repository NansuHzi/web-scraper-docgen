from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import asyncio
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from ..core.crew import create_research_crew, create_document_crew

router = APIRouter()


class ScrapingRequest(BaseModel):
    url: str
    document_type: str = "技术报告"  # 默认文档类型


def validate_research_output(research_task) -> str:
    """验证 Researcher 任务的输出，失败则抛出异常"""
    # 提取任务输出内容
    if hasattr(research_task, 'output') and hasattr(research_task.output, 'raw'):
        output = str(research_task.output.raw)
    else:
        output = str(research_task.output)
    
    # 检查是否为空或过短
    if not output or len(output.strip()) < 50:
        raise Exception(f"网页抓取失败：输出内容为空或过短（{len(output)}字符）")
    
    # 检查是否包含错误关键词
    error_keywords = ["抓取失败", "403", "404", "访问被拒绝", "无法访问", 
                     "任务已终止", "网页内容为空", "无法继续处理"]
    if any(keyword in output for keyword in error_keywords):
        raise Exception(f"网页抓取失败：{output[:200]}")
    
    return output


def generate_filename(final_doc: str, url: str) -> str:
    """从文档标题生成文件名"""
    # 尝试从 Markdown 第一行提取标题
    title_match = re.search(r'^#\s+(.+)$', final_doc, re.MULTILINE)
    
    if title_match:
        # 使用文档标题
        title = title_match.group(1).strip()
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)[:50]
    else:
        # 回退到 URL 域名
        parsed_url = urlparse(url)
        safe_title = parsed_url.netloc.replace(":", "_").replace(".", "_")
    
    # 添加时间戳
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{safe_title}_{timestamp}.md"


def save_document(filepath: Path, content: str) -> None:
    """保存 Markdown 文档到本地"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)


@router.post("/scrape")
async def scrape_webpage(request: ScrapingRequest):
    """处理网页抓取和文档生成请求"""
    try:
        # ===== 阶段1：执行 Researcher =====
        print("\n🔍 阶段1: 正在抓取网页...")
        research_crew, research_task = create_research_crew(request.url)
        await asyncio.to_thread(research_crew.kickoff)
        
        # 验证抓取结果
        validate_research_output(research_task)
        print("✅ 阶段1完成: 网页抓取成功\n")
        
        # ===== 阶段2：执行 Writer + Reviewer =====
        print("📝 阶段2: 正在生成文档...")
        document_crew = create_document_crew(request.url, request.document_type, research_task)
        final_result = await asyncio.to_thread(document_crew.kickoff)
        print("✅ 阶段2完成: 文档生成成功\n")
        
        # ===== 提取最终文档内容 =====
        if hasattr(final_result, 'raw'):
            final_doc = final_result.raw
        elif hasattr(final_result, 'tasks_output') and len(final_result.tasks_output) > 0:
            last_task = final_result.tasks_output[-1]
            final_doc = last_task.raw if hasattr(last_task, 'raw') else str(last_task)
        else:
            final_doc = str(final_result)
        
        # 验证文档不为空
        if not final_doc or len(final_doc.strip()) == 0:
            raise Exception("生成的文档为空，请检查 Agent 配置和 API Key")
        
        # ===== 保存文档到本地 =====
        output_dir = Path(__file__).parent.parent.parent / "output"
        output_dir.mkdir(exist_ok=True)
        
        filename = generate_filename(final_doc, request.url)
        filepath = output_dir / filename
        save_document(filepath, final_doc)
        
        # ===== 返回结果 =====
        return {
            "status": "success",
            "document": final_doc,
            "url": request.url,
            "document_type": request.document_type,
            "saved_file": str(filepath),
            "filename": filename
        }
        
    except Exception as e:
        # 捕获所有异常并返回错误信息
        error_msg = str(e)
        print(f"\n❌ 任务执行失败: {error_msg}\n")
        raise HTTPException(status_code=500, detail=f"处理失败: {error_msg}")
