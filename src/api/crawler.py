from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from ..crawler.engine import crawler_engine, CrawlOptions
from ..crawler.batch import batch_crawler
from ..crawler.incremental import incremental_tracker
from ..crawler.site_detector import site_detector

router = APIRouter()


class CrawlRequest(BaseModel):
    url: str
    max_chars: int = 10000
    extract_links: bool = True
    extract_images: bool = False
    extract_tables: bool = True
    wait_for_selector: Optional[str] = None
    timeout: int = 30


class BatchCrawlRequest(BaseModel):
    urls: list[str]
    max_chars: int = 10000
    max_concurrent: int = 3
    domain_delay: float = 2.0
    incremental: bool = False


@router.post("/crawler/crawl")
async def crawl_single(request: CrawlRequest):
    try:
        options = CrawlOptions(
            max_chars=request.max_chars,
            extract_links=request.extract_links,
            extract_images=request.extract_images,
            extract_tables=request.extract_tables,
            wait_for_selector=request.wait_for_selector,
            timeout=request.timeout,
        )

        result = await crawler_engine.crawl(request.url, options)

        return {
            "success": result.success,
            "url": result.url,
            "title": result.title,
            "content": result.content,
            "content_hash": result.content_hash,
            "site_type": result.site_type.value,
            "render_strategy": result.render_strategy.value,
            "metadata": result.metadata,
            "links": result.links[:50],
            "images": result.images[:20],
            "crawled_at": result.crawled_at,
            "duration_ms": result.duration_ms,
            "from_cache": result.from_cache,
            "error": result.error,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"爬取失败: {str(e)}")


@router.post("/crawler/batch")
async def crawl_batch(request: BatchCrawlRequest):
    try:
        if not request.urls:
            raise HTTPException(status_code=400, detail="URL列表不能为空")

        if len(request.urls) > 50:
            raise HTTPException(status_code=400, detail="单次批量最多50个URL")

        options = CrawlOptions(
            max_chars=request.max_chars,
            extract_links=True,
            extract_images=False,
            extract_tables=True,
        )

        if request.incremental:
            result = await batch_crawler.crawl_with_incremental(
                request.urls, options, max_concurrent=request.max_concurrent
            )
        else:
            result = await batch_crawler.crawl_batch(
                request.urls, options,
                max_concurrent=request.max_concurrent,
                domain_delay=request.domain_delay,
            )

        return {
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
                    "site_type": r.site_type.value,
                    "success": r.success,
                    "error": r.error,
                    "duration_ms": r.duration_ms,
                }
                for r in result.results
            ],
            "errors": result.errors,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量爬取失败: {str(e)}")


@router.get("/crawler/analyze")
async def analyze_site(url: str = Query(..., description="目标网站URL")):
    try:
        profile = site_detector.detect(url)

        return {
            "url": url,
            "site_type": profile.site_type.value,
            "render_strategy": profile.render_strategy.value,
            "content_selectors": profile.content_selectors,
            "title_selectors": profile.title_selectors,
            "exclude_selectors": profile.exclude_selectors,
            "needs_login": profile.needs_login,
            "rate_limit_delay": profile.rate_limit_delay,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"站点分析失败: {str(e)}")


@router.get("/crawler/incremental/status")
async def get_incremental_status(url: Optional[str] = Query(None)):
    try:
        if url:
            entry = incremental_tracker.get_hash(url)
            if entry is None:
                return {"url": url, "tracked": False}
            return {
                "url": entry.url,
                "tracked": True,
                "hash_value": entry.hash_value,
                "title": entry.title,
                "content_length": entry.content_length,
                "last_checked": entry.last_checked,
                "last_changed": entry.last_changed,
                "change_count": entry.change_count,
            }

        all_tracked = incremental_tracker.get_all_tracked()
        stats = incremental_tracker.get_stats()

        return {
            "stats": stats,
            "tracked_urls": [
                {
                    "url": t.url,
                    "title": t.title,
                    "last_checked": t.last_checked,
                    "change_count": t.change_count,
                }
                for t in all_tracked[:100]
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取增量状态失败: {str(e)}")


@router.get("/crawler/incremental/history")
async def get_change_history(url: str = Query(...), limit: int = Query(20)):
    try:
        history = incremental_tracker.get_change_history(url, limit)
        return {"url": url, "history": history, "total_changes": len(history)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取变更历史失败: {str(e)}")


@router.delete("/crawler/incremental/{url:path}")
async def remove_incremental_tracking(url: str):
    try:
        incremental_tracker.remove(url)
        return {"success": True, "message": f"已移除 {url} 的增量追踪"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"移除失败: {str(e)}")
