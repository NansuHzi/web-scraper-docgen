from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel
import asyncio
import logging
import re
import os
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from ..core.crew import create_research_crew, create_document_crew
from ..adapters.document_cache import document_cache
from ..adapters.session_manager import session_manager
from ..core.llm import qwen_llm
from typing import Optional

logger = logging.getLogger(__name__)

router = APIRouter()

document_store = {}

_scheduler_semaphore = asyncio.Semaphore(2)
_topic_semaphore = asyncio.Semaphore(1)


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
    except Exception:
        return False


def validate_research_output(research_task) -> str:
    """验证 Researcher 任务的输出，失败则抛出异常"""
    if hasattr(research_task, 'output') and hasattr(research_task.output, 'raw'):
        output = str(research_task.output.raw)
    elif hasattr(research_task, 'output'):
        output = str(research_task.output)
    else:
        output = str(research_task)
    
    if not output or len(output.strip()) < 50:
        raise Exception(f"网页抓取失败：输出内容为空或过短（{len(output)}字符）")
    
    error_keywords = ["抓取失败", "403", "404", "访问被拒绝", "无法访问", 
                     "任务已终止", "网页内容为空", "无法继续处理",
                     "访问异常", "被限制", "权限", "安全验证", "反爬虫"]
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


async def process_document_generation(document_id: str, url: str, doc_type: str, format_type: str = "md", use_qwen: bool = False):
    async with _scheduler_semaphore:
        try:
            from ..adapters.format_adapter import FormatAdapter

            if document_id in document_store:
                document_store[document_id]["status"] = "processing"

            doc_type_mapping = {
                "tech_doc": "技术文档",
                "api_doc": "API文档",
                "readme": "README",
                "summary": "摘要总结"
            }
            document_type_cn = doc_type_mapping.get(doc_type, "技术文档")

            llm = qwen_llm if use_qwen else None

            llm_label = "[千问]" if use_qwen else "[DeepSeek]"
            logger.info("[%s] 阶段1: 正在抓取网页... %s", document_id, llm_label)
            research_crew, research_task = create_research_crew(url, llm=llm)
            await asyncio.to_thread(research_crew.kickoff)

            try:
                validate_research_output(research_task)
            except Exception as validation_error:
                error_msg = str(validation_error)
                logger.error("[%s] 网页抓取失败: %s", document_id, error_msg)
                if document_id in document_store:
                    document_store[document_id].update({
                        "status": "failed",
                        "error": error_msg
                    })
                return

            logger.info("[%s] 阶段1完成: 网页抓取成功", document_id)

            logger.info("[%s] 阶段2: 正在生成文档... %s", document_id, llm_label)
            document_crew = create_document_crew(url, document_type_cn, research_task, llm=llm)
            final_result = await asyncio.to_thread(document_crew.kickoff)
            logger.info("[%s] 阶段2完成: 文档生成成功", document_id)

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
            logger.info("[%s] 文档已缓存 | URL: %s | 类型: %s", document_id, url, doc_type)

            adapter = FormatAdapter()
            filename_without_ext = generate_filename(final_doc, url).replace(".md", "")
            saved_file = adapter.export(final_doc, filename_without_ext, format_type)

            if document_id in document_store:
                document_store[document_id].update({
                    "status": "completed",
                    "content": final_doc,
                    "filename": os.path.basename(saved_file),
                    "saved_file": saved_file
                })

        except Exception as e:
            error_msg = str(e)
            logger.error("[%s] 任务执行失败: %s", document_id, error_msg)

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

        if session_id and doc_data.get("session_id") not in (session_id, "rag"):
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
                "url": doc_data.get("url", ""),
                "urls": doc_data.get("urls", []),
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
        logger.error("Failed to read from filesystem: %s", e)
    
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
            if data.get("session_id") in (session_id, "rag"):
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
        logger.info("阶段1: 正在抓取网页...")
        research_crew, research_task = create_research_crew(request.url)
        await asyncio.to_thread(research_crew.kickoff)
        
        validate_research_output(research_task)
        logger.info("阶段1完成: 网页抓取成功")
        
        logger.info("阶段2: 正在生成文档...")
        document_crew = create_document_crew(request.url, request.document_type, research_task)
        final_result = await asyncio.to_thread(document_crew.kickoff)
        logger.info("阶段2完成: 文档生成成功")
        
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
        logger.error("任务执行失败: %s", error_msg)
        raise HTTPException(status_code=500, detail=f"处理失败: {error_msg}")


@router.get("/document/{document_id}/download")
async def download_document(document_id: str):
    doc_data = document_store.get(document_id, {})

    if doc_data.get("status") == "completed":
        saved_file = doc_data.get("saved_file", "")
        if saved_file and Path(saved_file).exists():
            return FileResponse(
                path=saved_file,
                filename=Path(saved_file).name,
                media_type="text/markdown",
            )

        content = doc_data.get("content", "")
        filename = doc_data.get("filename", f"{document_id}.md")
        if content:
            import tempfile
            tmp = tempfile.NamedTemporaryFile(
                mode="w", suffix=".md", delete=False, encoding="utf-8"
            )
            tmp.write(content)
            tmp.close()
            return FileResponse(
                path=tmp.name,
                filename=filename,
                media_type="text/markdown",
            )

    output_dir = Path(__file__).parent.parent.parent / "output"

    timestamp = document_id.replace("doc_", "").replace("task_", "")
    try:
        ts_int = int(timestamp)
        files = list(output_dir.glob("*.md"))
        for f in files:
            if str(ts_int) in f.name:
                return FileResponse(
                    path=str(f),
                    filename=f.name,
                    media_type="text/markdown",
                )
    except (ValueError, Exception):
        pass

    if document_id.startswith("task_"):
        files = sorted(output_dir.glob("*.md"), key=lambda f: f.stat().st_mtime, reverse=True)
        if files:
            return FileResponse(
                path=str(files[0]),
                filename=files[0].name,
                media_type="text/markdown",
            )

    raise HTTPException(status_code=404, detail="文档文件未找到")


@router.get("/payment/pending")
async def get_pending_payments():
    """获取待验证付款的订单列表"""
    from ..bot.database import bot_db
    
    pending_orders = bot_db.get_orders_by_payment("unpaid")
    return {"orders": pending_orders}


@router.post("/payment/verify")
async def verify_payment(order_id: str):
    """管理员手动验证付款并开始处理任务"""
    from ..bot.database import bot_db
    from ..bot.session_manager import session_manager
    
    order = bot_db.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    
    if order["payment_status"] != "unpaid":
        raise HTTPException(status_code=400, detail="订单状态不是待付款")
    
    # 更新付款状态
    bot_db.update_order_payment(order_id, "paid")
    
    # 尝试获取会话并继续处理
    user_id = order["user_id"]
    session = session_manager.get(user_id)
    
    if session and session.pending_order:
        # 创建任务
        from ..worker.dispatcher import task_dispatcher
        from ..worker.models import TaskType, TaskPriority
        
        urls = session.pending_order.urls
        task_ids = []
        for url in urls:
            task = await task_dispatcher.submit(
                task_type=TaskType.GENERATE_DOCUMENT,
                payload={
                    "url": url,
                    "tier": session.pending_order.tier,
                    "format": session.pending_order.format,
                    "use_qwen": session.pending_order.use_qwen,
                },
                priority=TaskPriority.NORMAL,
                user_id=user_id,
                session_id=user_id,
            )
            task_ids.append(task.id)
        
        bot_db.update_order_task_ids(order_id, task_ids)
        session_manager.add_task(user_id, task_ids)
        session.pending_order = None
        session_manager.update_state(user_id, session_manager.SessionState.PROCESSING)
        
        return {
            "success": True,
            "order_id": order_id,
            "task_ids": task_ids,
            "message": "付款已验证，任务已创建"
        }
    
    return {
        "success": True,
        "order_id": order_id,
        "message": "付款已验证，但未找到待处理会话"
    }
