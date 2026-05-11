import asyncio
import time
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from .site_detector import SiteDetector, SiteProfile, SiteType, RenderStrategy, site_detector
from .firecrawl_client import firecrawl_client
from ..config import settings


@dataclass
class CrawlOptions:
    max_chars: int = 10000
    extract_images: bool = False
    extract_links: bool = True
    extract_tables: bool = True
    follow_pagination: bool = False
    max_pages: int = 1
    timeout: int = 30
    wait_for_selector: Optional[str] = None
    custom_headers: dict = field(default_factory=dict)
    force_firecrawl: bool = False


@dataclass
class CrawlResult:
    url: str
    title: str
    content: str
    content_hash: str
    site_type: SiteType
    render_strategy: RenderStrategy
    metadata: dict = field(default_factory=dict)
    links: list[str] = field(default_factory=list)
    images: list[dict] = field(default_factory=list)
    crawled_at: str = field(default_factory=lambda: datetime.now().isoformat())
    duration_ms: int = 0
    error: Optional[str] = None
    from_cache: bool = False

    @property
    def success(self) -> bool:
        return self.error is None and len(self.content) > 0


class CrawlerEngine:
    def __init__(self):
        self._detector = site_detector
        self._result_cache: dict[str, CrawlResult] = {}

    async def crawl(self, url: str, options: Optional[CrawlOptions] = None) -> CrawlResult:
        options = options or CrawlOptions()
        started = time.time()

        cache_key = self._cache_key(url, options)
        if cache_key in self._result_cache:
            cached = self._result_cache[cache_key]
            cached.from_cache = True
            return cached

        profile = self._detector.detect(url)

        use_firecrawl = (
            options.force_firecrawl
            or (settings.FIRECRAWL_ENABLED and firecrawl_client.available)
            or profile.render_strategy == RenderStrategy.FIRECRAWL
        )

        try:
            if use_firecrawl:
                result = await self._crawl_firecrawl(url, profile, options)
                if not result.success and settings.FIRECRAWL_FALLBACK and profile.render_strategy != RenderStrategy.FIRECRAWL:
                    logger.info("Firecrawl 抓取失败，回退到原始策略: %s", url)
                    if profile.render_strategy == RenderStrategy.STATIC:
                        result = await self._crawl_static(url, profile, options)
                    elif profile.render_strategy == RenderStrategy.JS_RENDER:
                        result = await self._crawl_js(url, profile, options)
                    else:
                        result = await self._crawl_hybrid(url, profile, options)
            elif profile.render_strategy == RenderStrategy.STATIC:
                result = await self._crawl_static(url, profile, options)
            elif profile.render_strategy == RenderStrategy.JS_RENDER:
                result = await self._crawl_js(url, profile, options)
            else:
                result = await self._crawl_hybrid(url, profile, options)

            result.duration_ms = int((time.time() - started) * 1000)
            self._result_cache[cache_key] = result
            return result

        except Exception as e:
            duration_ms = int((time.time() - started) * 1000)
            return CrawlResult(
                url=url,
                title="",
                content="",
                content_hash="",
                site_type=profile.site_type,
                render_strategy=profile.render_strategy,
                duration_ms=duration_ms,
                error=str(e),
            )

    async def _crawl_static(self, url: str, profile: SiteProfile, options: CrawlOptions) -> CrawlResult:
        from ..core.utils import _get_http_session, _load_zhihu_cookies

        session = _get_http_session()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        headers.update(options.custom_headers)

        if profile.site_type == SiteType.ZHIHU:
            cookies = _load_zhihu_cookies()
            if cookies:
                headers["Cookie"] = cookies

        response = session.get(url, headers=headers, timeout=options.timeout)
        response.encoding = response.apparent_encoding

        return self._parse_html(response.text, url, profile, options)

    async def _crawl_js(self, url: str, profile: SiteProfile, options: CrawlOptions) -> CrawlResult:
        from ..core.utils import _get_browser, BROWSER_CONTEXT_OPTIONS

        browser = await _get_browser()
        context = await browser.new_context(**BROWSER_CONTEXT_OPTIONS)

        try:
            page = await context.new_page()
            await page.goto(url, wait_until='domcontentloaded', timeout=options.timeout * 1000)

            if options.wait_for_selector:
                await page.wait_for_selector(options.wait_for_selector, timeout=10000)

            await page.wait_for_timeout(1500)
            html = await page.content()
        finally:
            await context.close()

        return self._parse_html(html, url, profile, options)

    async def _crawl_hybrid(self, url: str, profile: SiteProfile, options: CrawlOptions) -> CrawlResult:
        try:
            return await self._crawl_static(url, profile, options)
        except Exception:
            return await self._crawl_js(url, profile, options)

    async def _crawl_firecrawl(self, url: str, profile: SiteProfile, options: CrawlOptions) -> CrawlResult:
        logger.info("使用 Firecrawl 抓取: %s", url)
        fc_result = await firecrawl_client.scrape(
            url=url,
            max_chars=options.max_chars,
            extract_links=options.extract_links,
            extract_images=options.extract_images,
            wait_for_selector=options.wait_for_selector,
            custom_headers=options.custom_headers if options.custom_headers else None,
        )

        content_hash = hashlib.md5(fc_result.content.encode()).hexdigest()

        return CrawlResult(
            url=fc_result.url,
            title=fc_result.title,
            content=fc_result.content,
            content_hash=content_hash,
            site_type=profile.site_type,
            render_strategy=RenderStrategy.FIRECRAWL,
            metadata={**fc_result.metadata, "engine": "firecrawl"},
            links=fc_result.links,
            images=fc_result.images,
            duration_ms=fc_result.duration_ms,
            error=fc_result.error,
        )

    def _parse_html(self, html: str, url: str, profile: SiteProfile, options: CrawlOptions) -> CrawlResult:
        soup = BeautifulSoup(html, 'lxml')

        title = self._extract_title(soup, profile)
        content = self._extract_content(soup, profile, options)
        content_hash = hashlib.md5(content.encode()).hexdigest()

        links = []
        if options.extract_links:
            links = self._extract_links(soup, url)

        images = []
        if options.extract_images:
            images = self._extract_images(soup, url)

        metadata = self._extract_metadata(soup, url)

        return CrawlResult(
            url=url,
            title=title,
            content=content,
            content_hash=content_hash,
            site_type=profile.site_type,
            render_strategy=profile.render_strategy,
            metadata=metadata,
            links=links,
            images=images,
        )

    def _extract_title(self, soup: BeautifulSoup, profile: SiteProfile) -> str:
        for selector in profile.title_selectors:
            el = soup.select_one(selector)
            if el:
                return el.get_text(strip=True)

        h1 = soup.find('h1')
        if h1:
            return h1.get_text(strip=True)

        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text(strip=True)

        return ""

    def _extract_content(self, soup: BeautifulSoup, profile: SiteProfile, options: CrawlOptions) -> str:
        for tag in soup(profile.exclude_selectors):
            tag.decompose()

        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        content_text = ""

        for selector in profile.content_selectors:
            elements = soup.select(selector)
            if elements:
                parts = []
                for el in elements:
                    text = self._element_to_text(el, options)
                    if len(text) > 100:
                        parts.append(text)
                if parts:
                    content_text = "\n\n".join(parts)
                    break

        if not content_text or len(content_text) < 100:
            body = soup.find('body')
            if body:
                content_text = body.get_text(separator='\n', strip=True)

        lines = [line.strip() for line in content_text.splitlines() if line.strip()]
        content_text = '\n'.join(lines)

        if options.max_chars and len(content_text) > options.max_chars:
            content_text = content_text[:options.max_chars]

        return content_text

    def _element_to_text(self, element, options: CrawlOptions) -> str:
        if options.extract_tables:
            return element.get_text(separator='\n', strip=True)

        for table in element.find_all('table'):
            table.decompose()
        return element.get_text(separator='\n', strip=True)

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> list[str]:
        links = []
        parsed_base = urlparse(base_url)
        base_domain = parsed_base.netloc

        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith('#') or href.startswith('javascript:'):
                continue
            if href.startswith('/'):
                href = f"{parsed_base.scheme}://{base_domain}{href}"
            elif not href.startswith('http'):
                continue

            link_domain = urlparse(href).netloc
            if link_domain == base_domain or link_domain.endswith('.' + base_domain):
                if href not in links:
                    links.append(href)

        return links

    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> list[dict]:
        images = []
        parsed_base = urlparse(base_url)

        for img in soup.find_all('img', src=True):
            src = img['src']
            if src.startswith('data:'):
                continue
            if src.startswith('/'):
                src = f"{parsed_base.scheme}://{parsed_base.netloc}{src}"
            elif src.startswith('//'):
                src = f"{parsed_base.scheme}:{src}"

            images.append({
                'src': src,
                'alt': img.get('alt', ''),
                'title': img.get('title', ''),
            })

        return images

    def _extract_metadata(self, soup: BeautifulSoup, url: str) -> dict:
        metadata = {
            'source_url': url,
            'description': '',
            'keywords': '',
            'author': '',
            'published_at': '',
        }

        desc = soup.find('meta', attrs={'name': 'description'})
        if desc:
            metadata['description'] = desc.get('content', '')

        keywords = soup.find('meta', attrs={'name': 'keywords'})
        if keywords:
            metadata['keywords'] = keywords.get('content', '')

        author = soup.find('meta', attrs={'name': 'author'})
        if author:
            metadata['author'] = author.get('content', '')

        for prop in ['article:published_time', 'date']:
            pub = soup.find('meta', attrs={'property': prop}) or soup.find('meta', attrs={'name': prop})
            if pub:
                metadata['published_at'] = pub.get('content', '')
                break

        return metadata

    def _cache_key(self, url: str, options: CrawlOptions) -> str:
        raw = f"{url}|{options.max_chars}|{options.extract_images}|{options.extract_links}"
        return hashlib.md5(raw.encode()).hexdigest()

    def clear_cache(self):
        self._result_cache.clear()


crawler_engine = CrawlerEngine()
