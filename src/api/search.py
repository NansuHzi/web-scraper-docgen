import os
import re
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from urllib.parse import urlparse
import asyncio
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

SEARXNG_LOCAL = os.environ.get("SEARXNG_URL", "")


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=200, description="搜索关键词")
    max_results: int = Field(default=10, ge=1, le=20, description="最大结果数")


@router.post("/search")
async def search_web(request: SearchRequest):
    """搜索相关网站（多搜索引擎融合，保证结果多样性）"""
    try:
        def _sync_search():
            all_results = []
            seen_urls = set()
            domain_counts = {}

            search_methods = [
                _bing_search,
                _sogou_search,
                _so360_search,
                _baidu_search,
            ]

            max_per_engine = max(2, request.max_results // len(search_methods))

            for method in search_methods:
                try:
                    results = method(request.query, max_per_engine * 2)
                    
                    for result in results:
                        url = result.get("url", "")
                        if not url or url in seen_urls:
                            continue

                        parsed_url = urlparse(url)
                        domain = parsed_url.netloc.lower()

                        max_for_domain = 2
                        if "zhihu.com" in domain:
                            max_for_domain = 2
                        
                        if domain_counts.get(domain, 0) >= max_for_domain:
                            continue

                        seen_urls.add(url)
                        domain_counts[domain] = domain_counts.get(domain, 0) + 1
                        all_results.append(result)

                        if len(all_results) >= request.max_results:
                            return all_results[:request.max_results]
                except Exception as e:
                    logger.debug(f"搜索方法 {method.__name__} 失败: {e}")

            if not all_results:
                logger.info("所有外部搜索均失败，使用内置搜索结果")
                all_results = _built_in_search(request.query, request.max_results)

            logger.info(f"搜索完成: 关键词={request.query}, 结果数={len(all_results)}")
            return all_results[:request.max_results]

        results = await asyncio.to_thread(_sync_search)

        return {
            "success": True,
            "results": results,
            "total": len(results),
            "query": request.query,
        }

    except Exception as e:
        error_str = str(e)
        logger.error(f"搜索错误: {error_str}")
        if "ConnectError" in error_str or "connect" in error_str.lower():
            raise HTTPException(
                status_code=502,
                detail="搜索服务暂时不可用，请稍后重试"
            )
        raise HTTPException(status_code=500, detail=f"搜索失败: {error_str}")


def _searxng_search(query: str, max_results: int) -> list:
    """使用 SearXNG 搜索（本地实例）"""
    import requests

    try:
        search_url = f"{SEARXNG_LOCAL.rstrip('/')}/search"
        params = {
            "q": query,
            "format": "json",
            "categories": "general",
            "language": "zh-CN",
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
        }

        response = requests.get(search_url, params=params, headers=headers, timeout=10)
        if response.status_code != 200:
            return []

        data = response.json()
        raw_results = data.get("results", [])
        if not raw_results:
            return []

        results = []
        seen_urls = set()
        for item in raw_results:
            if len(results) >= max_results:
                break
            url = item.get("url", "")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            title = item.get("title", "") or "未命名"
            snippet = (item.get("content", "") or "")[:200]
            results.append({
                "title": _clean_text(title),
                "url": url,
                "snippet": _clean_text(snippet),
            })

        if results:
            logger.info(f"SearXNG 搜索成功: 结果数={len(results)}")
        return results

    except Exception as e:
        logger.debug(f"SearXNG 搜索失败: {e}")
        return []


def _bing_search(query: str, max_results: int) -> list:
    """Bing 搜索（国内可用）"""
    import requests
    from bs4 import BeautifulSoup
    from urllib.parse import quote_plus

    try:
        search_url = f"https://cn.bing.com/search?q={quote_plus(query)}&count={max_results * 2}&setlang=zh-CN"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }

        response = requests.get(search_url, headers=headers, timeout=15)
        if response.status_code != 200:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        seen_urls = set()

        for item in soup.find_all('li', class_='b_algo'):
            if len(results) >= max_results:
                break

            title_tag = item.find('h2')
            if not title_tag:
                continue

            url_tag = title_tag.find('a')
            if not url_tag:
                continue

            url = url_tag.get('href', '')
            if not url or not url.startswith('http') or url in seen_urls:
                continue
            seen_urls.add(url)

            title = title_tag.get_text(strip=True)

            snippet = ''
            snippet_tag = item.find('p') or item.find('div', class_='b_caption')
            if snippet_tag:
                snippet = snippet_tag.get_text(strip=True)[:200]

            results.append({
                "title": _clean_text(title),
                "url": url,
                "snippet": _clean_text(snippet),
            })

        if results:
            logger.info(f"Bing 搜索成功: 结果数={len(results)}")
        return results

    except Exception as e:
        logger.debug(f"Bing 搜索失败: {e}")
        return []


def _sogou_search(query: str, max_results: int) -> list:
    """搜狗搜索（国内可用）"""
    import requests
    from bs4 import BeautifulSoup
    from urllib.parse import quote_plus

    try:
        search_url = f"https://www.sogou.com/web?query={quote_plus(query)}&num={max_results * 2}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }

        response = requests.get(search_url, headers=headers, timeout=15)
        if response.status_code != 200:
            return []

        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        seen_urls = set()

        for item in soup.find_all('div', class_='vrwrap') or soup.find_all('div', class_='rb'):
            if len(results) >= max_results:
                break

            title_tag = item.find('h3')
            if not title_tag:
                continue

            url_tag = title_tag.find('a')
            if not url_tag:
                continue

            url = url_tag.get('href', '')
            if not url:
                continue

            if url.startswith('/'):
                url = f"https://www.sogou.com{url}"

            if not url.startswith('http') or url in seen_urls:
                continue
            seen_urls.add(url)

            title = title_tag.get_text(strip=True)

            snippet = ''
            snippet_tag = item.find('p', class_='str-text-info') or item.find('div', class_='str_info')
            if snippet_tag:
                snippet = snippet_tag.get_text(strip=True)[:200]

            results.append({
                "title": _clean_text(title),
                "url": url,
                "snippet": _clean_text(snippet),
            })

        if results:
            logger.info(f"搜狗搜索成功: 结果数={len(results)}")
        return results

    except Exception as e:
        logger.debug(f"搜狗搜索失败: {e}")
        return []


def _so360_search(query: str, max_results: int) -> list:
    """360搜索（国内可用）"""
    import requests
    from bs4 import BeautifulSoup
    from urllib.parse import quote_plus

    try:
        search_url = f"https://www.so.com/s?q={quote_plus(query)}&pn=1&ps={max_results * 2}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }

        response = requests.get(search_url, headers=headers, timeout=15)
        if response.status_code != 200:
            return []

        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        seen_urls = set()

        for item in soup.find_all('li', class_='res-list'):
            if len(results) >= max_results:
                break

            title_tag = item.find('h3')
            if not title_tag:
                continue

            url_tag = title_tag.find('a')
            if not url_tag:
                continue

            url = url_tag.get('href', '') or url_tag.get('data-url', '')
            if not url or not url.startswith('http') or url in seen_urls:
                continue
            seen_urls.add(url)

            title = title_tag.get_text(strip=True)

            snippet = ''
            snippet_tag = item.find('p', class_='res-desc') or item.find('div', class_='res-rich')
            if snippet_tag:
                snippet = snippet_tag.get_text(strip=True)[:200]

            results.append({
                "title": _clean_text(title),
                "url": url,
                "snippet": _clean_text(snippet),
            })

        if results:
            logger.info(f"360搜索成功: 结果数={len(results)}")
        return results

    except Exception as e:
        logger.debug(f"360搜索失败: {e}")
        return []


def _baidu_search(query: str, max_results: int) -> list:
    """百度搜索（备用方案）"""
    import requests
    from bs4 import BeautifulSoup

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
    })

    try:
        session.get("https://www.baidu.com", timeout=10)
    except Exception:
        pass

    search_url = f"https://www.baidu.com/s?wd={requests.utils.quote(query)}&pn=0&rn={max_results * 3}"

    try:
        response = session.get(search_url, timeout=15)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"百度搜索请求失败: {e}")
        return []

    html_content = _decode_response(response)

    if "百度安全验证" in html_content or "安全验证" in html_content:
        logger.warning("百度搜索触发安全验证")
        return []

    soup = BeautifulSoup(html_content, 'html.parser')
    results = []
    seen_urls = set()

    all_items = []
    all_items.extend(soup.find_all('div', class_='result-op'))
    all_items.extend(soup.find_all('div', class_='result'))
    all_items.extend(soup.find_all('div', class_='c-container'))
    all_items.extend(soup.find_all('div', attrs={'tpl': 'se_com_default'}))

    for item in all_items:
        if len(results) >= max_results:
            break

        url_tag = item.find('a')
        if not url_tag:
            continue

        url = url_tag.get('href', '')
        if not url or not url.startswith('http'):
            continue

        if url in seen_urls:
            continue
        seen_urls.add(url)

        title_tag = item.find('h3')
        if not title_tag:
            title_tag = item.find('h2')

        if title_tag:
            title = title_tag.get_text(strip=True)
        else:
            title = url_tag.get_text(strip=True) or '未命名'

        title = _clean_text(title)

        snippet = ''
        snippet_tag = item.find('p', class_='news-summary_1E9I7')
        if not snippet_tag:
            snippet_tag = item.find('span', class_='content-right_8Zs40')
        if not snippet_tag:
            snippet_tag = item.find('div', class_='c-abstract')
        if not snippet_tag:
            snippet_tag = item.find('p', class_='c-summary')
        if snippet_tag:
            snippet = snippet_tag.get_text(strip=True)[:200]
            snippet = _clean_text(snippet)

        if title and len(title) < 3:
            continue

        results.append({
            "title": title,
            "url": url,
            "snippet": snippet,
        })

    if results:
        logger.info(f"百度搜索成功: 结果数={len(results)}")
    return results


def _decode_response(response):
    """正确解码响应内容"""
    encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030']
    for encoding in encodings:
        try:
            return response.content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return response.text


def _clean_text(text: str) -> str:
    """清理文本中的乱码和特殊字符"""
    if not text:
        return ''
    cleaned = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', text)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


def _built_in_search(query: str, max_results: int) -> list:
    """内置搜索结果，当所有外部搜索不可用时使用"""
    search_index = {
        "python": [
            {"title": "Python 官方网站", "url": "https://www.python.org/", "snippet": "Python 是一种高级通用编程语言，以简洁、易读的语法著称。"},
            {"title": "Python 中文教程", "url": "https://docs.python.org/zh-cn/3/", "snippet": "Python 官方中文文档，包含完整的语言参考和教程。"},
            {"title": "菜鸟教程 Python", "url": "https://www.runoob.com/python/python-tutorial.html", "snippet": "Python 基础教程，适合初学者入门学习。"},
            {"title": "Python 教程 | 廖雪峰", "url": "https://www.liaoxuefeng.com/wiki/1016959663602400", "snippet": "廖雪峰的 Python 教程，深入浅出讲解 Python 编程。"},
            {"title": "Python 标准库", "url": "https://docs.python.org/zh-cn/3/library/", "snippet": "Python 标准库文档，包含各种内置模块的使用说明。"},
        ],
        "javascript": [
            {"title": "JavaScript MDN", "url": "https://developer.mozilla.org/zh-CN/docs/Web/JavaScript", "snippet": "MDN Web Docs 提供的 JavaScript 完整参考文档。"},
            {"title": "JavaScript 教程 | 菜鸟教程", "url": "https://www.runoob.com/js/js-tutorial.html", "snippet": "JavaScript 基础入门教程，从基础语法到高级特性。"},
            {"title": "ES6 入门教程", "url": "https://es6.ruanyifeng.com/", "snippet": "阮一峰的 ES6 入门教程，讲解 ECMAScript 6 新特性。"},
            {"title": "JavaScript.info", "url": "https://zh.javascript.info/", "snippet": "现代 JavaScript 教程，涵盖从基础到高级的所有内容。"},
        ],
        "java": [
            {"title": "Java 官方网站", "url": "https://www.java.com/zh-CN/", "snippet": "Java 编程语言官方网站，包含下载和文档。"},
            {"title": "Java 教程 | 菜鸟教程", "url": "https://www.runoob.com/java/java-tutorial.html", "snippet": "Java 基础教程，适合初学者学习。"},
            {"title": "Spring Framework", "url": "https://spring.io/", "snippet": "Spring 框架官方网站，企业级 Java 开发框架。"},
            {"title": "Java 文档", "url": "https://docs.oracle.com/en/java/", "snippet": "Oracle 官方 Java 文档和 API 参考。"},
        ],
        "前端": [
            {"title": "前端开发入门", "url": "https://developer.mozilla.org/zh-CN/docs/Learn", "snippet": "MDN 前端学习路径，从 HTML/CSS/JS 开始学习。"},
            {"title": "Vue.js 官方文档", "url": "https://cn.vuejs.org/", "snippet": "Vue.js 渐进式 JavaScript 框架官方文档。"},
            {"title": "React 中文文档", "url": "https://zh-hans.react.dev/", "snippet": "React 官方中文文档，学习现代前端开发。"},
            {"title": "CSS-Tricks", "url": "https://css-tricks.com/", "snippet": "CSS 技巧和前端开发资源网站。"},
        ],
        "后端": [
            {"title": "Node.js 官方网站", "url": "https://nodejs.org/zh-cn/", "snippet": "Node.js 基于 Chrome V8 引擎的 JavaScript 运行时。"},
            {"title": "Django 官方网站", "url": "https://www.djangoproject.com/", "snippet": "Django 高级 Python Web 框架。"},
            {"title": "FastAPI 文档", "url": "https://fastapi.tiangolo.com/zh/", "snippet": "FastAPI 现代、快速的 Python Web 框架。"},
            {"title": "Redis 官方网站", "url": "https://redis.io/", "snippet": "Redis 开源内存数据库。"},
        ],
        "数据库": [
            {"title": "MySQL 官方网站", "url": "https://www.mysql.com/", "snippet": "MySQL 世界最流行的开源关系型数据库。"},
            {"title": "PostgreSQL 官方网站", "url": "https://www.postgresql.org/", "snippet": "PostgreSQL 功能强大的开源关系型数据库。"},
            {"title": "MongoDB 官方网站", "url": "https://www.mongodb.com/", "snippet": "MongoDB NoSQL 文档数据库。"},
            {"title": "SQLite 官方网站", "url": "https://www.sqlite.org/", "snippet": "SQLite 轻量级嵌入式数据库。"},
        ],
        "运维": [
            {"title": "Docker 官方网站", "url": "https://www.docker.com/", "snippet": "Docker 容器化平台，简化应用部署。"},
            {"title": "Kubernetes 官方网站", "url": "https://kubernetes.io/zh-cn/", "snippet": "Kubernetes 容器编排平台。"},
            {"title": "Linux 教程", "url": "https://www.runoob.com/linux/linux-tutorial.html", "snippet": "Linux 系统入门教程。"},
            {"title": "Nginx 官方网站", "url": "https://nginx.org/", "snippet": "Nginx 高性能 Web 服务器。"},
        ],
        "算法": [
            {"title": "LeetCode", "url": "https://leetcode.cn/", "snippet": "LeetCode 在线编程平台，包含大量算法题目。"},
            {"title": "算法导论", "url": "https://mitpress.mit.edu/books/introduction-algorithms", "snippet": "经典算法教材，深入讲解各种算法。"},
            {"title": "数据结构与算法", "url": "https://www.geeksforgeeks.org/", "snippet": "GeeksforGeeks 数据结构和算法教程。"},
        ],
    }

    query_lower = query.lower()
    matched_results = []

    for keyword, results in search_index.items():
        if keyword in query_lower or query_lower in keyword:
            matched_results.extend(results)

    if not matched_results:
        matched_results = [
            {"title": "GitHub", "url": "https://github.com", "snippet": "GitHub 开源代码托管平台。"},
            {"title": "Stack Overflow", "url": "https://stackoverflow.com", "snippet": "Stack Overflow 技术问答社区。"},
            {"title": "MDN Web Docs", "url": "https://developer.mozilla.org/zh-CN/", "snippet": "Mozilla 开发者网络文档。"},
            {"title": "CSDN", "url": "https://www.csdn.net/", "snippet": "CSDN 中文开发者社区。"},
            {"title": "掘金", "url": "https://juejin.cn/", "snippet": "掘金技术社区，分享开发经验。"},
        ]

    return matched_results[:max_results]