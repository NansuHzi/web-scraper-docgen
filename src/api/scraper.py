from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, HttpUrl
import asyncio
import re
import os
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from ..core.crew import create_research_crew, create_document_crew
from ..adapters.document_cache import document_cache
from ..adapters.session_manager import session_manager
from typing import Optional

router = APIRouter()

document_store = {}


class ValidateRequest(BaseModel):
    url: str
    doc_type: str


class GenerateRequest(BaseModel):
    url: str
    doc_type: str
    format: Optional[str] = "md"


class ScrapingRequest(BaseModel):
    url: str
    document_type: str = "技术报告"


def validate_url_format(url: str) -> bool:
    """Validate URL format"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


def validate_research_output(research_task) -> str:
    """验证 Researcher 任务的输出，失败则抛出异常"""
    if hasattr(research_task, 'output') and hasattr(research_task.output, 'raw'):
        output = str(research_task.output.raw)
    else:
        output = str(research_task.output)
    
    if not output or len(output.strip()) < 50:
        raise Exception(f"网页抓取失败：输出内容为空或过短（{len(output)}字符）")
    
    error_keywords = ["抓取失败", "403", "404", "访问被拒绝", "无法访问", 
                     "任务已终止", "网页内容为空", "无法继续处理"]
    if any(keyword in output for keyword in error_keywords):
        raise Exception(f"网页抓取失败：{output[:200]}")
    
    return output


def generate_filename(final_doc: str, url: str) -> str:
    """从文档标题生成文件名"""
    title_match = re.search(r'^#\s+(.+)$', final_doc, re.MULTILINE)
    
    if title_match:
        title = title_match.group(1).strip()
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)[:50]
    else:
        parsed_url = urlparse(url)
        safe_title = parsed_url.netloc.replace(":", "_").replace(".", "_")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{safe_title}_{timestamp}.md"


def save_document(filepath: Path, content: str) -> None:
    """保存 Markdown 文档到本地"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)


@router.post("/validate")
async def validate_request(request: ValidateRequest):
    """验证 URL 和文档类型"""
    try:
        from ..adapters.content_filter import ContentFilter

        url_safe, url_error = ContentFilter.check_url_safety(request.url)
        if not url_safe:
            return {
                "valid": False,
                "message": f"URL安全检查失败: {url_error}"
            }

        valid_url = validate_url_format(request.url)
        if not valid_url:
            return {
                "valid": False,
                "message": "Invalid URL format"
            }

        valid_doc_types = ["tech_doc", "api_doc", "readme", "summary"]
        if request.doc_type not in valid_doc_types:
            return {
                "valid": False,
                "message": f"Invalid document type. Must be one of: {', '.join(valid_doc_types)}"
            }

        return {
            "valid": True,
            "message": "URL and document type are valid"
        }

    except Exception as e:
        return {
            "valid": False,
            "message": f"Validation failed: {str(e)}"
        }


@router.post("/generate")
async def generate_document(request: GenerateRequest, http_request: Request):
    """生成文档（异步处理）"""
    try:
        client_ip = http_request.client.host if http_request.client else "unknown"
        session_id = session_manager.get_or_create_session(client_ip)

        from ..adapters.content_filter import ContentFilter

        url_safe, url_error = ContentFilter.check_url_safety(request.url)
        if not url_safe:
            raise HTTPException(status_code=400, detail=f"URL安全检查失败: {url_error}")

        if not validate_url_format(request.url):
            raise HTTPException(status_code=400, detail="Invalid URL format")

        valid_doc_types = ["tech_doc", "api_doc", "readme", "summary"]
        if request.doc_type not in valid_doc_types:
            raise HTTPException(status_code=400, detail=f"Invalid document type. Must be one of: {', '.join(valid_doc_types)}")

        valid_formats = ["md", "txt", "ppt"]
        if request.format not in valid_formats:
            raise HTTPException(status_code=400, detail=f"Invalid format. Must be one of: {', '.join(valid_formats)}")

        cached_content = document_cache.get(request.url, request.doc_type)
        if cached_content:
            document_id = f"doc_{int(datetime.now().timestamp())}_cached"
            document_store[document_id] = {
                "session_id": session_id,
                "client_ip": client_ip,
                "url": request.url,
                "doc_type": request.doc_type,
                "format": request.format,
                "status": "completed",
                "content": cached_content,
                "from_cache": True,
                "created_at": datetime.now().isoformat()
            }
            return {
                "success": True,
                "document_id": document_id,
                "session_id": session_id,
                "message": "Document found in cache",
                "cached": True
            }

        document_id = f"doc_{int(datetime.now().timestamp())}"

        document_store[document_id] = {
            "session_id": session_id,
            "client_ip": client_ip,
            "url": request.url,
            "doc_type": request.doc_type,
            "format": request.format,
            "status": "processing",
            "content": None,
            "error": None,
            "created_at": datetime.now().isoformat()
        }

        asyncio.create_task(process_document_generation(document_id, request.url, request.doc_type, request.format))

        return {
            "success": True,
            "document_id": document_id,
            "session_id": session_id,
            "message": "Document generation started successfully",
            "estimated_time": 30
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start document generation: {str(e)}")


async def process_document_generation(document_id: str, url: str, doc_type: str, format_type: str = "md"):
    """异步处理文档生成"""
    try:
        from ..adapters.format_adapter import FormatAdapter
        
        # 更新状态
        if document_id in document_store:
            document_store[document_id]["status"] = "processing"
        
        # 映射文档类型到中文
        doc_type_mapping = {
            "tech_doc": "技术文档",
            "api_doc": "API文档",
            "readme": "README",
            "summary": "摘要总结"
        }
        document_type_cn = doc_type_mapping.get(doc_type, "技术文档")
        
        # 阶段1：执行 Researcher
        print(f"\n🔍 [{document_id}] 阶段1: 正在抓取网页...")
        research_crew, research_task = create_research_crew(url)
        await asyncio.to_thread(research_crew.kickoff)
        
        validate_research_output(research_task)
        print(f"✅ [{document_id}] 阶段1完成: 网页抓取成功\n")
        
        # 阶段2：执行 Writer + Reviewer
        print(f"📝 [{document_id}] 阶段2: 正在生成文档...")
        document_crew = create_document_crew(url, document_type_cn, research_task)
        final_result = await asyncio.to_thread(document_crew.kickoff)
        print(f"✅ [{document_id}] 阶段2完成: 文档生成成功\n")
        
        # 提取最终文档内容
        if hasattr(final_result, 'raw'):
            final_doc = final_result.raw
        elif hasattr(final_result, 'tasks_output') and len(final_result.tasks_output) > 0:
            last_task = final_result.tasks_output[-1]
            final_doc = last_task.raw if hasattr(last_task, 'raw') else str(last_task)
        else:
            final_doc = str(final_result)
        
        if not final_doc or len(final_doc.strip()) == 0:
            raise Exception("生成的文档为空，请检查 Agent 配置和 API Key")

        document_cache.set(url, doc_type, final_doc)
        print(f"💾 [{document_id}] 文档已缓存 | URL: {url} | 类型: {doc_type}")

        adapter = FormatAdapter()
        filename_without_ext = generate_filename(final_doc, url).replace(".md", "")
        saved_file = adapter.export(final_doc, filename_without_ext, format_type)

        # 更新存储
        if document_id in document_store:
            document_store[document_id].update({
                "status": "completed",
                "content": final_doc,
                "filename": os.path.basename(saved_file),
                "saved_file": saved_file
            })
        
    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ [{document_id}] 任务执行失败: {error_msg}\n")
        
        if document_id in document_store:
            document_store[document_id].update({
                "status": "failed",
                "error": error_msg
            })


@router.get("/document/{document_id}")
async def get_document(document_id: str, http_request: Request = None):
    """获取生成的文档"""
    client_ip = http_request.client.host if http_request.client else "unknown" if http_request else "unknown"
    session_id = session_manager.get_or_create_session(client_ip) if http_request else None

    if document_id in document_store:
        doc_data = document_store[document_id]

        if session_id and doc_data.get("session_id") != session_id:
            raise HTTPException(status_code=403, detail="Access denied: document belongs to another user")

        if doc_data["status"] == "processing":
            return {
                "document_id": document_id,
                "status": "processing",
                "message": "Document is still being generated"
            }

        if doc_data["status"] == "failed":
            return {
                "document_id": document_id,
                "status": "failed",
                "error": doc_data.get("error", "Unknown error")
            }

        if doc_data.get("content"):
            return {
                "document_id": document_id,
                "content": doc_data["content"],
                "url": doc_data["url"],
                "doc_type": doc_data["doc_type"],
                "created_at": doc_data["created_at"],
                "filename": doc_data.get("filename", "")
            }
    
    # 如果内存中没有数据或内容为空，尝试从文件系统读取
    output_dir = Path(__file__).parent.parent.parent / "output"
    
    # 查找匹配的文件（document_id 格式为 doc_timestamp）
    timestamp = document_id.replace("doc_", "")
    try:
        # 尝试查找匹配时间戳的文件
        files = list(output_dir.glob(f"*_{timestamp}.md"))
        
        if files:
            filepath = files[0]
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            
            return {
                "document_id": document_id,
                "content": content,
                "url": "unknown",
                "doc_type": "tech_doc",
                "created_at": datetime.fromtimestamp(int(timestamp)).isoformat(),
                "filename": filepath.name,
                "status": "completed"
            }
    except Exception as e:
        print(f"Failed to read from filesystem: {e}")
    
    # 如果都找不到，返回错误
    raise HTTPException(status_code=404, detail="Document not found")


@router.get("/history")
async def get_history(limit: int = 20, http_request: Request = None):
    """获取文档生成历史记录"""
    try:
        client_ip = http_request.client.host if http_request.client else "unknown"
        session_id = session_manager.get_or_create_session(client_ip)

        history = []
        for doc_id, data in sorted(document_store.items(), key=lambda x: x[1].get('created_at', ''), reverse=True):
            if data.get("session_id") == session_id:
                history.append({
                    "document_id": doc_id,
                    "url": data.get("url", ""),
                    "doc_type": data.get("doc_type", ""),
                    "format": data.get("format", "md"),
                    "status": data.get("status", ""),
                    "created_at": data.get("created_at", ""),
                    "from_cache": data.get("from_cache", False)
                })
            if len(history) >= limit:
                break
        return {"history": history, "total": len(history)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")


@router.post("/scrape")
async def scrape_webpage(request: ScrapingRequest):
    """处理网页抓取和文档生成请求（Legacy endpoint）"""
    try:
        print("\n🔍 阶段1: 正在抓取网页...")
        research_crew, research_task = create_research_crew(request.url)
        await asyncio.to_thread(research_crew.kickoff)
        
        validate_research_output(research_task)
        print("✅ 阶段1完成: 网页抓取成功\n")
        
        print("📝 阶段2: 正在生成文档...")
        document_crew = create_document_crew(request.url, request.document_type, research_task)
        final_result = await asyncio.to_thread(document_crew.kickoff)
        print("✅ 阶段2完成: 文档生成成功\n")
        
        if hasattr(final_result, 'raw'):
            final_doc = final_result.raw
        elif hasattr(final_result, 'tasks_output') and len(final_result.tasks_output) > 0:
            last_task = final_result.tasks_output[-1]
            final_doc = last_task.raw if hasattr(last_task, 'raw') else str(last_task)
        else:
            final_doc = str(final_result)
        
        if not final_doc or len(final_doc.strip()) == 0:
            raise Exception("生成的文档为空，请检查 Agent 配置和 API Key")
        
        output_dir = Path(__file__).parent.parent.parent / "output"
        output_dir.mkdir(exist_ok=True)
        
        filename = generate_filename(final_doc, request.url)
        filepath = output_dir / filename
        save_document(filepath, final_doc)
        
        return {
            "status": "success",
            "document": final_doc,
            "url": request.url,
            "document_type": request.document_type,
            "saved_file": str(filepath),
            "filename": filename
        }
        
    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ 任务执行失败: {error_msg}\n")
        raise HTTPException(status_code=500, detail=f"处理失败: {error_msg}")
