from bs4 import BeautifulSoup
from urllib.parse import urlparse
import logging
import re
import os
import json
import atexit
import asyncio
import threading
import requests

logger = logging.getLogger(__name__)

_BROWSER_STATE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.browser_state')
ZHIHU_STATE_FILE = os.path.join(_BROWSER_STATE_DIR, 'zhihu_state.json')

# Shared HTTP session with connection pooling
_http_session = None


def _get_http_session() -> requests.Session:
    global _http_session
    if _http_session is None:
        _http_session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(pool_connections=20, pool_maxsize=50, max_retries=1)
        _http_session.mount('https://', adapter)
        _http_session.mount('http://', adapter)
    return _http_session


# Persistent browser pool to avoid ~3s browser launch per request
_browser_instance = None
_browser_lock = threading.Lock()
_browser_usage_count = 0
_browser_max_uses = 50  # Recycle browser after N uses to prevent memory leaks


async def _get_browser():
    """Get or create a persistent browser instance (lazy init, thread-safe)"""
    global _browser_instance, _browser_usage_count
    with _browser_lock:
        _browser_usage_count += 1
        if _browser_instance is None or _browser_usage_count > _browser_max_uses:
            if _browser_instance is not None:
                try:
                    await _browser_instance.close()
                except Exception:
                    pass
            from playwright.async_api import async_playwright
            _pw = await async_playwright().start()
            _browser_instance = await _pw.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-infobars',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-gpu',
                    '--single-process',
                ],
            )
            _browser_usage_count = 0
        return _browser_instance


def _cleanup_browser():
    """Cleanup browser on shutdown"""
    global _browser_instance
    if _browser_instance is not None:
        try:
            asyncio.get_event_loop().run_until_complete(_browser_instance.close())
        except Exception:
            pass
        _browser_instance = None


atexit.register(_cleanup_browser)

ANTI_SCRAPING_SITES = {
    "zhihu.com": {
        "selectors": [".Post-RichTextContainer", ".RichText", ".Post-Main", "article"],
        "login_detect": "登录/注册",
        "cookie_consent": True,
    },
    "zhuanlan.zhihu.com": {
        "selectors": [".Post-RichTextContainer", ".RichText", ".Post-Main", "article"],
        "login_detect": "登录/注册",
        "cookie_consent": True,
    },
    "www.zhihu.com": {
        "selectors": [".Post-RichTextContainer", ".RichText", ".Post-Main", "article"],
        "login_detect": "登录/注册",
        "cookie_consent": True,
    },
    "mp.weixin.qq.com": {
        "selectors": ["#js_content", ".rich_media_content", "article"],
        "login_detect": None,
        "cookie_consent": False,
    },
    "www.jianshu.com": {
        "selectors": ["article", ".show-content", ".article"],
        "login_detect": None,
        "cookie_consent": False,
    },
    "www.cnblogs.com": {
        "selectors": ["#cnblogs_post_body", ".postBody", "article"],
        "login_detect": None,
        "cookie_consent": False,
    },
    "blog.csdn.net": {
        "selectors": ["#article_content", ".article_content", "article"],
        "login_detect": "登录",
        "cookie_consent": False,
    },
    "juejin.cn": {
        "selectors": [".article-content", "article", ".markdown-body"],
        "login_detect": "登录",
        "cookie_consent": False,
    },
}

BROWSER_CONTEXT_OPTIONS = {
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "viewport": {"width": 1920, "height": 1080},
    "locale": "zh-CN",
    "timezone_id": "Asia/Shanghai",
    "java_script_enabled": True,
    "color_scheme": "light",
    "extra_http_headers": {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.baidu.com/",
        "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
    },
}

_ZHIHU_CLEAN_PATTERNS = [
    r"关注\s*\d+",
    r"赞同\s*\d+",
    r"评论\s*\d+",
    r"收藏\s*\d+",
    r"喜欢\s*\d+",
    r"分享",
    r"举报",
    r"写下你的评论...",
    r"登录/注册",
    r"下载知乎 App",
    r"关注问题",
    r"\d+ 人赞同了该回答",
    r"发布于\s*\d{4}",
    r"编辑于\s*\d{4}",
    r"著作权归作者所有",
]


def _get_site_config(url: str) -> dict | None:
    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    for domain, config in ANTI_SCRAPING_SITES.items():
        if hostname == domain or hostname.endswith("." + domain):
            return config
    return None


def _extract_with_selectors(soup, selectors: list[str]) -> str | None:
    for selector in selectors:
        if selector.startswith("#"):
            element = soup.find(id=selector[1:])
        elif selector.startswith("."):
            element = soup.find(class_=selector[1:].replace("-", "_"))
            if not element:
                for tag in soup.find_all(True):
                    classes = tag.get("class", [])
                    if selector[1:] in classes:
                        element = tag
                        break
        else:
            element = soup.find(selector)

        if element:
            text = element.get_text(separator='\n', strip=True)
            if len(text) > 100:
                return text
    return None


def _clean_zhihu_content(text: str) -> str:
    for pattern in _ZHIHU_CLEAN_PATTERNS:
        text = re.sub(pattern, '', text)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return '\n'.join(lines)


def _is_zhihu_url(url: str) -> bool:
    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    return "zhihu.com" in hostname


def _load_zhihu_cookies() -> str:
    """从状态文件加载知乎Cookie"""
    if os.path.exists(ZHIHU_STATE_FILE):
        try:
            with open(ZHIHU_STATE_FILE, 'r', encoding='utf-8') as f:
                state = json.load(f)
            cookies = state.get('cookies', [])
            cookie_string = '; '.join([f"{c['name']}={c['value']}" for c in cookies])
            return cookie_string
        except Exception as e:
            logger.warning(f"加载知乎Cookie失败: {e}")
    return ""


async def _run_playwright_async(params: dict) -> str:
    """使用Playwright异步API抓取网页（复用浏览器实例）"""
    url = params["url"]
    max_chars = params.get("max_chars", 3000)
    lang = params.get("lang", "en")
    zhihu_state_file = params.get("zhihu_state_file", "")

    site_config = _get_site_config(url)
    is_zhihu = _is_zhihu_url(url)

    browser = await _get_browser()

    if is_zhihu and zhihu_state_file and os.path.exists(zhihu_state_file):
        context = await browser.new_context(
            storage_state=zhihu_state_file,
            **BROWSER_CONTEXT_OPTIONS,
        )
    else:
        context = await browser.new_context(**BROWSER_CONTEXT_OPTIONS)

    try:
        page = await context.new_page()
        await page.set_viewport_size({"width": 1920, "height": 1080})

        if site_config and site_config.get("cookie_consent"):
            try:
                await page.goto(url, wait_until='domcontentloaded', timeout=15000)
                await page.wait_for_timeout(1000)

                try:
                    cookie_btn = await page.query_selector('button:has-text("同意")')
                    if cookie_btn:
                        await cookie_btn.click()
                        await page.wait_for_timeout(500)
                except Exception:
                    pass

                current_url = page.url
                if "signin" in current_url or "login" in current_url:
                    if is_zhihu:
                        logger.warning(f"Zhihu redirected to login page. URL: {current_url}")
                    await page.go_back()
                    await page.wait_for_timeout(1000)

                await page.wait_for_load_state('domcontentloaded', timeout=8000)
                await page.wait_for_timeout(500)

            except Exception as e:
                logger.warning(f"Cookie consent failed: {e}")
                await page.goto(url, wait_until='domcontentloaded', timeout=15000)
                await page.wait_for_timeout(1000)
        else:
            await page.goto(url, wait_until='domcontentloaded', timeout=15000)
            await page.wait_for_timeout(1000)

        html_content = await page.content()
        title = await page.title()

    finally:
        await context.close()

    soup = BeautifulSoup(html_content, 'html.parser')

    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    extracted_text = None

    if site_config:
        selectors = site_config.get("selectors", [])
        if selectors:
            extracted_text = _extract_with_selectors(soup, selectors)

        if not extracted_text:
            main_content = soup.find('main') or soup.find('article') or soup.find('body')
            if main_content:
                extracted_text = main_content.get_text(separator='\n', strip=True)

        if site_config.get("login_detect") and extracted_text:
            if site_config["login_detect"] in extracted_text[:500]:
                logger.warning(f"Detected login wall for {url}, attempting deeper extraction")
                for selector in selectors:
                    if selector.startswith("#"):
                        element = soup.find(id=selector[1:])
                    elif selector.startswith("."):
                        element = None
                        for tag in soup.find_all(True):
                            classes = tag.get("class", [])
                            if selector[1:] in classes:
                                element = tag
                                break
                    else:
                        element = soup.find(selector)

                    if element:
                        text = element.get_text(separator='\n', strip=True)
                        if len(text) > 200 and site_config["login_detect"] not in text[:200]:
                            extracted_text = text
                            break

        if "zhihu.com" in url and extracted_text:
            extracted_text = _clean_zhihu_content(extracted_text)

    if not extracted_text:
        main_content = soup.find('main') or soup.find('article') or soup.find('body')
        extracted_text = main_content.get_text(separator='\n', strip=True) if main_content else soup.get_text(separator='\n', strip=True)

    lines = [line.strip() for line in extracted_text.splitlines() if line.strip()]
    cleaned_text = '\n'.join(lines)

    if not cleaned_text or len(cleaned_text.strip()) < 50:
        raise Exception(f"网页内容为空或过少（{len(cleaned_text)}字符），无法继续处理")

    if max_chars and len(cleaned_text) > max_chars:
        cleaned_text = cleaned_text[:max_chars] + "..."

    if lang == "zh":
        return f"网页标题: {title}\n\n网页内容摘要:\n{cleaned_text}"
    return f"# {title}\n\n{cleaned_text}"


def _scrape_with_requests(url: str, max_chars: int = 3000, lang: str = "en") -> str:
    """使用纯HTTP请求抓取网页（备选方案，复用连接池）"""
    zhihu_cookies = _load_zhihu_cookies()

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.zhihu.com/",
        "Connection": "keep-alive",
        "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
    }

    if zhihu_cookies:
        headers["Cookie"] = zhihu_cookies

    try:
        session = _get_http_session()
        session.headers.update(headers)

        response = session.get(url, timeout=15)
        response.encoding = response.apparent_encoding
        html_content = response.text

        if len(html_content) < 500:
            raise Exception(f"响应内容过短（{len(html_content)}字符），可能被反爬虫拦截")
        
        soup = BeautifulSoup(html_content, 'html.parser')
        title = soup.title.string if soup.title else "未知标题"
        
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        
        site_config = _get_site_config(url)
        extracted_text = None
        
        if site_config:
            selectors = site_config.get("selectors", [])
            if selectors:
                extracted_text = _extract_with_selectors(soup, selectors)
        
        if not extracted_text:
            main_content = soup.find('main') or soup.find('article') or soup.find('body')
            extracted_text = main_content.get_text(separator='\n', strip=True) if main_content else soup.get_text(separator='\n', strip=True)
        
        if "zhihu.com" in url and extracted_text:
            extracted_text = _clean_zhihu_content(extracted_text)
        
        lines = [line.strip() for line in extracted_text.splitlines() if line.strip()]
        cleaned_text = '\n'.join(lines)
        
        if not cleaned_text or len(cleaned_text.strip()) < 50:
            raise Exception(f"网页内容为空或过少（{len(cleaned_text)}字符）")
        
        if len(cleaned_text) > max_chars:
            cleaned_text = cleaned_text[:max_chars] + "..."
        
        if lang == "zh":
            return f"网页标题: {title}\n\n网页内容摘要:\n{cleaned_text}"
        return f"# {title}\n\n{cleaned_text}"
    
    except Exception as e:
        raise Exception(f"HTTP请求抓取失败: {str(e)}")


async def scrape_url_content(url: str, max_chars: int | None = 3000, lang: str = "en") -> str:
    """异步抓取网页内容（复用浏览器，支持JS渲染）"""
    params = {
        "url": url,
        "max_chars": max_chars,
        "lang": lang,
        "zhihu_state_file": ZHIHU_STATE_FILE if os.path.exists(ZHIHU_STATE_FILE) else "",
    }

    try:
        return await _run_playwright_async(params)
    except Exception as e:
        logger.warning(f"Playwright抓取失败: {e}，尝试使用HTTP请求备选方案")
        return _scrape_with_requests(url, max_chars or 3000, lang)
