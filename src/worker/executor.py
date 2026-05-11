import asyncio
from .models import Task, TaskType
from .dispatcher import task_dispatcher


async def handle_crawl_single(task: Task):
    from ..crawler.engine import crawler_engine, CrawlOptions

    url = task.payload.get("url", "")
    max_chars = task.payload.get("max_chars", 10000)

    options = CrawlOptions(
        max_chars=max_chars,
        extract_links=task.payload.get("extract_links", True),
        extract_images=task.payload.get("extract_images", False),
        extract_tables=task.payload.get("extract_tables", True),
    )

    task.progress = 0.1
    task.progress_message = "正在爬取网页..."

    result = await crawler_engine.crawl(url, options)

    task.progress = 0.9
    task.progress_message = "爬取完成"

    task.result = {
        "url": result.url,
        "title": result.title,
        "content": result.content,
        "content_hash": result.content_hash,
        "site_type": result.site_type.value,
        "metadata": result.metadata,
        "links": result.links[:50],
        "crawled_at": result.crawled_at,
        "duration_ms": result.duration_ms,
    }

    if not result.success:
        raise Exception(result.error or "爬取失败")


async def handle_crawl_batch(task: Task):
    from ..crawler.batch import batch_crawler
    from ..crawler.engine import CrawlOptions

    urls = task.payload.get("urls", [])
    max_chars = task.payload.get("max_chars", 10000)
    max_concurrent = task.payload.get("max_concurrent", 3)

    options = CrawlOptions(
        max_chars=max_chars,
        extract_links=True,
        extract_images=False,
        extract_tables=True,
    )

    task.progress = 0.05
    task.progress_message = f"开始批量爬取 {len(urls)} 个URL..."

    result = await batch_crawler.crawl_batch(
        urls, options, max_concurrent=max_concurrent,
    )

    task.progress = 0.95
    task.progress_message = f"批量爬取完成: {result.success_count}/{result.total_urls}"

    task.result = {
        "total_urls": result.total_urls,
        "success_count": result.success_count,
        "failed_count": result.failed_count,
        "success_rate": round(result.success_rate, 2),
        "duration_ms": result.duration_ms,
        "results": [
            {
                "url": r.url,
                "title": r.title,
                "content": r.content,
                "success": r.success,
                "error": r.error,
            }
            for r in result.results
        ],
    }


async def handle_generate_document(task: Task):
    from ..api.scraper import process_document_generation

    url = task.payload.get("url", "")
    tier = task.payload.get("tier", "basic")
    format_type = task.payload.get("format", "md")
    use_qwen = task.payload.get("use_qwen", False)

    tier_to_doc_type = {
        "basic": "tech_doc",
        "advanced": "tech_doc",
        "multi": "tech_doc",
    }
    doc_type = task.payload.get("doc_type") or tier_to_doc_type.get(tier, "tech_doc")

    document_id = task.id
    task.progress = 0.1
    task.progress_message = "开始生成文档..."

    await process_document_generation(document_id, url, doc_type, format_type, use_qwen=use_qwen)

    from ..api.scraper import document_store
    doc_data = document_store.get(document_id, {})

    if doc_data.get("status") == "failed":
        raise Exception(doc_data.get("error", "文档生成失败"))

    task.progress = 0.95
    task.progress_message = "文档生成完成"

    task.result = {
        "document_id": document_id,
        "content": doc_data.get("content", ""),
        "filename": doc_data.get("filename", ""),
        "url": url,
        "doc_type": doc_type,
        "tier": tier,
    }


async def handle_build_rag(task: Task):
    from ..api.rag import build_rag_knowledge_base

    urls = task.payload.get("urls", [])
    rag_name = task.payload.get("rag_name", "knowledge_base")

    task.progress = 0.1
    task.progress_message = f"开始构建RAG知识库: {rag_name}"

    result = await build_rag_knowledge_base(urls, rag_name)

    task.progress = 0.95
    task.progress_message = "RAG知识库构建完成"

    task.result = result


def register_default_handlers():
    task_dispatcher.register_handler(TaskType.CRAWL_SINGLE, handle_crawl_single)
    task_dispatcher.register_handler(TaskType.CRAWL_BATCH, handle_crawl_batch)
    task_dispatcher.register_handler(TaskType.GENERATE_DOCUMENT, handle_generate_document)
    task_dispatcher.register_handler(TaskType.BUILD_RAG, handle_build_rag)
