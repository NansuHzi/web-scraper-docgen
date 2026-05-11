import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()

rag_store_status: dict[str, dict] = {}


class BuildRagRequest(BaseModel):
    urls: list[str] = Field(..., min_length=1, max_length=20, description="要抓取的URL列表")
    doc_type: str = Field(default="tech_doc", description="文档类型")


class RagSearchRequest(BaseModel):
    rag_id: str = Field(..., description="知识库ID")
    query: str = Field(..., min_length=1, max_length=500, description="搜索查询")
    top_k: int = Field(default=5, ge=1, le=20, description="返回结果数")


class GenerateFromRagRequest(BaseModel):
    rag_id: Optional[str] = Field(default=None, description="RAG知识库ID")
    urls: Optional[list[str]] = Field(default=None, min_length=1, max_length=20)
    doc_type: str = Field(default="tech_doc", description="文档类型")
    mode: str = Field(default="merge", description="生成模式: merge | separate")
    format: Optional[str] = Field(default="md", description="输出格式: md | txt | ppt")
    topic: Optional[str] = Field(default="", description="文档主题（合并模式使用）")


@router.post("/build-rag")
async def build_rag(request: BuildRagRequest):
    """构建 RAG 知识库 — 抓取URL、向量化并存入ChromaDB"""
    from ..adapters.content_filter import ContentFilter
    from ..adapters.rag_store import rag_store

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
        "status": "building",
        "urls": safe_urls,
        "doc_type": request.doc_type,
        "chunk_count": 0,
        "created_at": datetime.now().isoformat(),
        "error": None,
    }

    rag_store.start_build(rag_id, safe_urls)

    return {
        "success": True,
        "rag_id": rag_id,
        "sources_count": len(safe_urls),
        "message": f"知识库构建已启动，共 {len(safe_urls)} 个来源",
    }


@router.get("/rag/list")
async def list_rag_stores():
    """列出所有知识库"""
    from ..adapters.rag_store import rag_store
    stores = rag_store.list_stores()
    return {"stores": stores, "total": len(stores)}


@router.get("/rag/{rag_id}")
async def get_rag_status(rag_id: str):
    """获取知识库状态"""
    from ..adapters.rag_store import rag_store

    store_stats = rag_store.get_stats(rag_id)
    if store_stats:
        return store_stats

    if rag_id in rag_store_status:
        return rag_store_status[rag_id]

    raise HTTPException(status_code=404, detail="知识库不存在")


@router.delete("/rag/{rag_id}")
async def delete_rag(rag_id: str):
    """删除知识库"""
    from ..adapters.rag_store import rag_store

    if rag_id in rag_store_status:
        del rag_store_status[rag_id]

    deleted = rag_store.delete_store(rag_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="知识库不存在")
    return {"success": True, "message": f"知识库 {rag_id} 已删除"}


@router.post("/rag/search")
async def search_rag(request: RagSearchRequest):
    """语义搜索知识库"""
    from ..adapters.rag_store import rag_store

    store = rag_store.get_stats(request.rag_id)
    if not store:
        raise HTTPException(status_code=404, detail="知识库不存在")
    if store["status"] == "building":
        raise HTTPException(status_code=400, detail="知识库正在构建中，请稍后再试")
    if store["status"] == "failed":
        raise HTTPException(status_code=400, detail=f"知识库构建失败: {store.get('error', '未知错误')}")

    results = rag_store.query(request.rag_id, request.query, request.top_k)

    return {
        "rag_id": request.rag_id,
        "query": request.query,
        "results": results,
        "count": len(results),
    }


@router.post("/generate-from-rag")
async def generate_from_rag(request: GenerateFromRagRequest):
    """基于 RAG 知识库生成文档"""
    from ..adapters.content_filter import ContentFilter
    from ..adapters.rag_store import rag_store
    from .scraper import document_store

    if request.rag_id:
        store = rag_store.get_stats(request.rag_id)
        if not store:
            raise HTTPException(status_code=404, detail="知识库不存在")
        if store["status"] != "ready":
            raise HTTPException(status_code=400, detail=f"知识库状态异常: {store['status']}")

    doc_type_mapping = {
        "tech_doc": "技术文档", "api_doc": "API文档",
        "readme": "README", "summary": "摘要总结",
    }
    doc_type_cn = doc_type_mapping.get(request.doc_type, "技术文档")

    if request.mode == "merge":
        document_id = f"doc_{int(datetime.now().timestamp())}"

        document_store[document_id] = {
            "status": "processing",
            "urls": [],
            "doc_type": request.doc_type,
            "mode": "merge",
            "format": request.format or "md",
            "topic": request.topic or "",
            "created_at": datetime.now().isoformat(),
            "error": None,
            "session_id": "rag",
        }

        asyncio.create_task(_process_rag_document(
            document_id, request.rag_id, request.topic or "综合文档",
            doc_type_cn, request.format or "md",
        ))

        return {
            "success": True,
            "document_id": document_id,
            "mode": "merge",
            "message": "RAG 文档生成已启动",
        }

    else:  # separate mode — 对每个 URL 独立生成
        urls = []
        if request.rag_id:
            store = rag_store.get_stats(request.rag_id)
            if store:
                urls = store.get("urls", [])
        elif request.urls:
            for url in request.urls:
                url_safe, _ = ContentFilter.check_url_safety(url)
                if url_safe:
                    urls.append(url)

        if not urls:
            raise HTTPException(status_code=400, detail="没有可用的 URL")

        documents = []
        for url in urls:
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


async def _process_rag_document(document_id: str, rag_id: str, topic: str, doc_type: str, format_type: str):
    """基于 RAG 存储生成文档 — 先语义搜索再生成"""
    from .scraper import document_store
    from ..adapters.rag_store import rag_store
    from ..core.crew import create_rag_document_crew
    from ..adapters.format_adapter import FormatAdapter

    try:
        results = rag_store.query(rag_id, topic, top_k=15)
        if not results:
            raise Exception("从知识库中未检索到相关内容")

        context_parts = []
        for item in results:
            source_tag = f"【来源：{item.get('source', '知识库')}】"
            context_parts.append(f"{source_tag}\n{item['content']}")

        context_text = "\n\n---\n\n".join(context_parts)
        context_text = context_text[:12000]

        crew = create_rag_document_crew(topic, doc_type, context_text)
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
        filename_without_ext = f"rag_doc_{document_id}"
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
