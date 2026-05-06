import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()

rag_store_status: dict[str, dict] = {}


class BuildRagRequest(BaseModel):
    urls: list[str] = Field(..., min_length=1, max_length=20, description="要整理的URL列表")
    doc_type: str = Field(default="tech_doc", description="文档类型")


class GenerateFromRagRequest(BaseModel):
    rag_id: Optional[str] = Field(default=None, description="RAG知识库ID")
    urls: Optional[list[str]] = Field(default=None, min_length=1, max_length=20, description="要整理的URL列表")
    doc_type: str = Field(default="tech_doc", description="文档类型")
    mode: str = Field(default="merge", description="生成模式: merge | separate")
    format: Optional[str] = Field(default="md", description="输出格式: md | txt | ppt")
    topic: Optional[str] = Field(default="", description="文档主题（合并模式使用）")


@router.post("/build-rag")
async def build_rag(request: BuildRagRequest):
    """构建文档（异步）- 兼容旧的RAG流程"""
    from ..adapters.content_filter import ContentFilter

    safe_urls = []
    for url in request.urls:
        url_safe, url_error = ContentFilter.check_url_safety(url)
        if not url_safe:
            continue
        safe_urls.append(url)

    if not safe_urls:
        raise HTTPException(status_code=400, detail="所有 URL 均未通过安全检查")

    rag_id = f"rag_{int(datetime.now().timestamp())}"

    rag_store_status[rag_id] = {
        "status": "ready",
        "urls": safe_urls,
        "doc_type": request.doc_type,
        "chunk_count": len(safe_urls),
        "created_at": datetime.now().isoformat(),
        "error": None,
    }

    return {
        "success": True,
        "rag_id": rag_id,
        "sources_count": len(safe_urls),
        "message": f"知识库构建完成，{len(safe_urls)} 个来源",
    }


@router.get("/rag/{rag_id}")
async def get_rag_status(rag_id: str):
    """获取RAG状态（兼容旧流程）"""
    if rag_id in rag_store_status:
        return rag_store_status[rag_id]
    raise HTTPException(status_code=404, detail="知识库不存在")


@router.post("/generate-from-rag")
async def generate_from_rag(request: GenerateFromRagRequest):
    """基于多个URL生成文档"""
    from ..adapters.content_filter import ContentFilter
    from .scraper import document_store

    urls = []
    
    if request.rag_id:
        rag = rag_store_status.get(request.rag_id)
        if rag:
            urls = rag.get("urls", [])
    elif request.urls:
        urls = request.urls
    else:
        raise HTTPException(status_code=400, detail="必须提供 rag_id 或 urls")

    safe_urls = []
    for url in urls:
        url_safe, url_error = ContentFilter.check_url_safety(url)
        if not url_safe:
            continue
        safe_urls.append(url)

    if not safe_urls:
        raise HTTPException(status_code=400, detail="所有 URL 均未通过安全检查")

    doc_type_mapping = {
        "tech_doc": "技术文档", "api_doc": "API文档",
        "readme": "README", "summary": "摘要总结",
    }
    doc_type_cn = doc_type_mapping.get(request.doc_type, "技术文档")

    if request.mode == "merge":
        document_id = f"doc_{int(datetime.now().timestamp())}"

        document_store[document_id] = {
            "status": "processing",
            "urls": safe_urls,
            "doc_type": request.doc_type,
            "mode": "merge",
            "format": request.format or "md",
            "topic": request.topic or "",
            "created_at": datetime.now().isoformat(),
            "error": None,
            "session_id": "rag",
        }

        asyncio.create_task(_process_document_merge(
            document_id, safe_urls, doc_type_cn, request.format or "md", request.topic or "",
        ))

        return {
            "success": True,
            "document_id": document_id,
            "mode": "merge",
            "message": "合并文档生成已启动",
        }

    else:  # separate mode
        documents = []

        for url in safe_urls:
            document_id = f"doc_{int(datetime.now().timestamp())}"
            document_store[document_id] = {
                "status": "processing",
                "url": url,
                "doc_type": request.doc_type,
                "mode": "separate",
                "format": request.format or "md",
                "created_at": datetime.now().isoformat(),
                "error": None,
                "session_id": "rag",
            }
            documents.append({"document_id": document_id, "url": url})

        asyncio.create_task(_process_document_separate(
            documents, request.doc_type, request.format or "md",
        ))

        return {
            "success": True,
            "documents": documents,
            "mode": "separate",
            "message": f"已启动 {len(documents)} 个独立文档生成",
        }


async def _process_document_merge(document_id: str, urls: list[str], doc_type: str, format_type: str, topic: str = ""):
    """异步处理合并模式文档生成"""
    from .scraper import document_store
    from ..core.utils import scrape_url_content
    from ..core.crew import create_rag_document_crew
    from ..adapters.format_adapter import FormatAdapter

    try:
        all_contents = []
        for url in urls:
            content = await scrape_url_content(url, max_chars=5000)
            if content:
                all_contents.append(f"【来源：{url}】\n{content}")

        if not all_contents:
            raise Exception("无法从任何URL抓取到内容")

        context_text = "\n\n---\n\n".join(all_contents)
        context_text = context_text[:12000]

        crew = create_rag_document_crew(topic or "综合文档", doc_type, context_text)
        final_result = await asyncio.to_thread(crew.kickoff)

        if hasattr(final_result, 'raw'):
            final_doc = final_result.raw
        elif hasattr(final_result, 'tasks_output') and len(final_result.tasks_output) > 0:
            final_doc = final_result.tasks_output[-1].raw if hasattr(final_result.tasks_output[-1], 'raw') else str(final_result.tasks_output[-1])
        else:
            final_doc = str(final_result)

        if not final_doc or len(final_doc.strip()) == 0:
            raise Exception("生成的文档为空")

        adapter = FormatAdapter()
        filename_without_ext = f"rag_merged_{document_id}"
        saved_file = adapter.export(final_doc, filename_without_ext, format_type)

        if document_id in document_store:
            document_store[document_id].update({
                "status": "completed",
                "content": final_doc,
                "filename": saved_file,
            })

    except Exception as e:
        if document_id in document_store:
            document_store[document_id].update({
                "status": "failed",
                "error": str(e),
            })


async def _process_document_separate(documents: list[dict], doc_type: str, format_type: str):
    """异步处理独立模式文档生成"""
    from .scraper import process_document_generation

    async def _generate_one(doc):
        try:
            await process_document_generation(
                doc["document_id"], doc["url"], doc_type, format_type,
            )
        except Exception as e:
            from .scraper import document_store
            if doc["document_id"] in document_store:
                document_store[doc["document_id"]].update({
                    "status": "failed",
                    "error": str(e),
                })

    await asyncio.gather(*[_generate_one(d) for d in documents])