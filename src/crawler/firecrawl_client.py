import logging
import time
from dataclasses import dataclass, field
from typing import Optional

import requests

from ..config import settings

logger = logging.getLogger(__name__)


@dataclass
class FirecrawlScrapeResult:
    url: str
    title: str
    content: str
    markdown: str
    metadata: dict = field(default_factory=dict)
    links: list[str] = field(default_factory=list)
    images: list[dict] = field(default_factory=list)
    duration_ms: int = 0
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None and len(self.content) > 0


class FirecrawlClient:
    def __init__(self):
        self._base_url = settings.FIRECRAWL_BASE_URL.rstrip("/")
        self._api_key = settings.FIRECRAWL_API_KEY
        self._timeout = settings.FIRECRAWL_TIMEOUT
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        })

    @property
    def available(self) -> bool:
        if not settings.FIRECRAWL_ENABLED:
            return False
        try:
            resp = self._session.get(f"{self._base_url}/v1/health", timeout=5)
            return resp.status_code == 200
        except Exception as e:
            logger.warning("Firecrawl 健康检查失败: %s", e)
            return False

    async def scrape(
        self,
        url: str,
        max_chars: int = 10000,
        extract_links: bool = True,
        extract_images: bool = False,
        wait_for_selector: Optional[str] = None,
        custom_headers: Optional[dict] = None,
    ) -> FirecrawlScrapeResult:
        started = time.time()

        payload = {
            "url": url,
            "formats": ["markdown", "html"],
            "onlyMainContent": True,
            "waitFor": wait_for_selector or 2000,
            "includeTags": ["article", "main", "[role='main']"],
            "excludeTags": ["nav", "footer", "aside", ".sidebar", ".comments", ".ads", "#comments"],
        }

        if custom_headers:
            payload["headers"] = custom_headers

        try:
            resp = self._session.post(
                f"{self._base_url}/v1/scrape",
                json=payload,
                timeout=self._timeout,
            )
            resp.raise_for_status()
            data = resp.json()

            raw_content = ""
            markdown_text = ""

            if isinstance(data, dict) and "data" in data:
                inner = data["data"]
                if isinstance(inner, dict):
                    markdown_text = inner.get("markdown") or ""
                    html_content = inner.get("html") or ""
                    meta = inner.get("metadata", {})
                    title = meta.get("title") or inner.get("title") or ""
                    links_raw = inner.get("links", [])
                    images_raw = inner.get("images", [])

                    if not raw_content and markdown_text:
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(markdown_text, "html.parser")
                        raw_content = soup.get_text(separator="\n", strip=True)

                    if not raw_content and html_content:
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(html_content, "lxml")
                        for tag in soup(["script", "style", "noscript"]):
                            tag.decompose()
                        body = soup.find("body")
                        raw_content = body.get_text(separator="\n", strip=True) if body else ""

                    links = []
                    if extract_links and links_raw:
                        for link in links_raw:
                            href = link if isinstance(link, str) else link.get("href", "")
                            if href and href.startswith("http"):
                                links.append(href)

                    images = []
                    if extract_images and images_raw:
                        for img in images_raw[:20]:
                            if isinstance(img, dict):
                                images.append({
                                    "src": img.get("src", ""),
                                    "alt": img.get("alt", ""),
                                })
                            elif isinstance(img, str):
                                images.append({"src": img, "alt": ""})

                    duration_ms = int((time.time() - started) * 1000)

                    if max_chars and len(raw_content) > max_chars:
                        raw_content = raw_content[:max_chars]

                    return FirecrawlScrapeResult(
                        url=url,
                        title=title,
                        content=raw_content,
                        markdown=markdown_text,
                        metadata={
                            "source_url": url,
                            "description": meta.get("description", ""),
                            "author": meta.get("author", ""),
                            "og_title": meta.get("ogTitle", ""),
                            "og_description": meta.get("ogDescription", ""),
                        },
                        links=links,
                        images=images,
                        duration_ms=duration_ms,
                    )

            raise ValueError(f"Firecrawl 返回数据格式异常: {str(data)[:200]}")

        except requests.exceptions.ConnectionError as e:
            logger.error("Firecrawl 连接失败 (%s): %s", self._base_url, e)
            return FirecrawlScrapeResult(url=url, title="", content="", markdown="", error=f"连接失败: {e}")
        except requests.exceptions.Timeout as e:
            logger.error("Firecrawl 请求超时 (%ds): %s", self._timeout, e)
            return FirecrawlScrapeResult(url=url, title="", content="", markdown="", error=f"请求超时 ({self._timeout}s)")
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response is not None else 0
            body = (e.response.text[:300]) if e.response is not None else ""
            logger.error("Firecrawl HTTP 错误 %d: %s", status, body)
            return FirecrawlScrapeResult(url=url, title="", content="", markdown="", error=f"HTTP {status}: {body}")
        except Exception as e:
            duration_ms = int((time.time() - started) * 1000)
            logger.error("Firecrawl 抓取异常 [%s]: %s", url, e)
            return FirecrawlScrapeResult(url=url, title="", content="", markdown="", error=str(e), duration_ms=duration_ms)


firecrawl_client = FirecrawlClient()
