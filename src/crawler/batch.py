import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Callable
from urllib.parse import urlparse

from .engine import CrawlerEngine, CrawlResult, CrawlOptions


@dataclass
class BatchResult:
    total_urls: int
    success_count: int
    failed_count: int
    results: list[CrawlResult]
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    finished_at: str = ""
    duration_ms: int = 0
    errors: list[dict] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        if self.total_urls == 0:
            return 0.0
        return self.success_count / self.total_urls


class BatchCrawler:
    def __init__(self, engine: Optional[CrawlerEngine] = None):
        self._engine = engine or CrawlerEngine()
        self._domain_timestamps: dict[str, float] = defaultdict(float)
        self._domain_lock = asyncio.Lock()

    async def crawl_batch(
        self,
        urls: list[str],
        options: Optional[CrawlOptions] = None,
        max_concurrent: int = 3,
        domain_delay: float = 2.0,
        progress_callback: Optional[Callable[[int, int, CrawlResult], None]] = None,
    ) -> BatchResult:
        options = options or CrawlOptions()
        started = time.time()
        semaphore = asyncio.Semaphore(max_concurrent)

        results: list[CrawlResult] = []
        errors: list[dict] = []

        async def crawl_one(url: str, index: int) -> CrawlResult:
            async with semaphore:
                domain = urlparse(url).netloc

                async with self._domain_lock:
                    now = time.time()
                    last = self._domain_timestamps.get(domain, 0)
                    wait = domain_delay - (now - last)
                    if wait > 0:
                        await asyncio.sleep(wait)
                    self._domain_timestamps[domain] = time.time()

                result = await self._engine.crawl(url, options)

                if progress_callback:
                    progress_callback(index + 1, len(urls), result)

                return result

        tasks = [crawl_one(url, i) for i, url in enumerate(urls)]
        gathered = await asyncio.gather(*tasks, return_exceptions=True)

        for i, item in enumerate(gathered):
            if isinstance(item, Exception):
                errors.append({'url': urls[i], 'error': str(item)})
            elif isinstance(item, CrawlResult):
                results.append(item)
                if not item.success:
                    errors.append({'url': item.url, 'error': item.error or 'unknown'})

        success_count = sum(1 for r in results if r.success)
        failed_count = len(results) - success_count + len([e for e in gathered if isinstance(e, Exception)])

        return BatchResult(
            total_urls=len(urls),
            success_count=success_count,
            failed_count=failed_count,
            results=results,
            finished_at=datetime.now().isoformat(),
            duration_ms=int((time.time() - started) * 1000),
            errors=errors,
        )

    async def crawl_with_incremental(
        self,
        urls: list[str],
        options: Optional[CrawlOptions] = None,
        max_concurrent: int = 3,
    ) -> BatchResult:
        from .incremental import incremental_tracker

        options = options or CrawlOptions()
        started = time.time()
        semaphore = asyncio.Semaphore(max_concurrent)

        results: list[CrawlResult] = []
        errors: list[dict] = []

        async def crawl_one(url: str, index: int) -> Optional[CrawlResult]:
            async with semaphore:
                result = await self._engine.crawl(url, options)

                if result.success:
                    changed, _ = incremental_tracker.check_changed(
                        url, result.content, result.title
                    )
                    if not changed:
                        result.from_cache = True

                return result

        tasks = [crawl_one(url, i) for i, url in enumerate(urls)]
        gathered = await asyncio.gather(*tasks, return_exceptions=True)

        for i, item in enumerate(gathered):
            if isinstance(item, Exception):
                errors.append({'url': urls[i], 'error': str(item)})
            elif item is not None:
                results.append(item)
                if not item.success:
                    errors.append({'url': item.url, 'error': item.error or 'unknown'})

        success_count = sum(1 for r in results if r.success)
        failed_count = len(urls) - success_count

        return BatchResult(
            total_urls=len(urls),
            success_count=success_count,
            failed_count=failed_count,
            results=results,
            finished_at=datetime.now().isoformat(),
            duration_ms=int((time.time() - started) * 1000),
            errors=errors,
        )


batch_crawler = BatchCrawler()
