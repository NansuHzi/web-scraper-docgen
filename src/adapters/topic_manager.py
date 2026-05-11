import json
import logging
import re
from datetime import datetime
from typing import Optional

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

WEIBO_HOT_URL = "https://weibo.com/ajax/side/hotSearch"
ZHIHU_HOT_URL = "https://www.zhihu.com/hot"


class TopicManager:
    """热点话题管理器 — 抓取微博/知乎热搜 + LLM分析"""

    @staticmethod
    def scrape_weibo_hot(max_items: int = 20) -> list[dict]:
        """从微博 API 获取热搜榜"""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Referer": "https://weibo.com/",
            }
            resp = requests.get(WEIBO_HOT_URL, headers=headers, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            topics = []
            realtime = data.get("data", {}).get("realtime", [])
            for item in realtime[:max_items]:
                label_map = {1: "热", 2: "沸", 3: "新", 4: "爆"}
                topics.append({
                    "title": item.get("word", "").strip(),
                    "source": "weibo",
                    "url": f"https://s.weibo.com/weibo?q={item.get('word', '')}",
                    "rank": item.get("realpos", 0),
                    "heat": label_map.get(item.get("label"), ""),
                    "hot_value": str(item.get("raw_hot", "")),
                })
            return topics
        except Exception as e:
            logger.error(f"Weibo hot search scrape failed: {e}")
            return []

    @staticmethod
    async def scrape_zhihu_hot(max_items: int = 20) -> list[dict]:
        """使用 Playwright 抓取知乎热榜"""
        try:
            from ..core.utils import scrape_url_content
            content = await scrape_url_content(ZHIHU_HOT_URL, max_chars=15000, lang="zh")

            topics = TopicManager._parse_zhihu_hot_html(content, max_items)
            if not topics:
                topics = TopicManager._parse_zhihu_hot_text(content, max_items)
            return topics
        except Exception as e:
            logger.error(f"Zhihu hot list scrape failed: {e}")
            return []

    @staticmethod
    def _parse_zhihu_hot_html(content: str, max_items: int) -> list[dict]:
        """兼容性更强的解析 — 从 HTML/文本中提取"""
        topics = []
        try:
            soup = BeautifulSoup(content, 'html.parser')
            items = soup.select('.HotList-item') or soup.select('[class*="HotItem"]') or soup.select('h2')
            for i, item in enumerate(items[:max_items]):
                link = item.find('a') if item.name != 'a' else item
                if not link:
                    link = item
                title_el = item.find(class_=re.compile(r'HotItem.*Title|title', re.I)) or item
                title = title_el.get_text(strip=True) if title_el else item.get_text(strip=True)
                if title and len(title) > 1:
                    url = ""
                    if hasattr(link, 'get'):
                        url = link.get('href', '')
                        if url and url.startswith('/'):
                            url = f"https://www.zhihu.com{url}"
                    metrics_el = item.find(class_=re.compile(r'HotItem.*Metrics|metrics', re.I))
                    hot_value = metrics_el.get_text(strip=True) if metrics_el else ""
                    topics.append({
                        "title": title[:80],
                        "source": "zhihu",
                        "url": url or f"https://www.zhihu.com/hot",
                        "rank": i + 1,
                        "heat": "",
                        "hot_value": hot_value,
                    })
        except Exception as e:
            logger.warning(f"Zhihu HTML parse failed: {e}")
        return topics

    @staticmethod
    def _parse_zhihu_hot_text(content: str, max_items: int) -> list[dict]:
        """从纯文本中提取知乎热榜（备选）"""
        topics = []
        lines = content.splitlines()
        count = 0
        for line in lines:
            line = line.strip()
            if not line or len(line) < 2:
                continue
            # 跳过明显的非标题行
            skip_prefixes = ("网页标题:", "知乎", "登录", "注册", "首页", "发现", "等你来答",
                           "推荐", "关注", "热榜", "搜索", "为你推荐", "圆桌", "盐选")
            if any(line.startswith(p) for p in skip_prefixes):
                continue
            # 跳过包含 URL 的行
            if "http" in line or "www." in line:
                continue
            topics.append({
                "title": line[:80],
                "source": "zhihu",
                "url": "https://www.zhihu.com/hot",
                "rank": count + 1,
                "heat": "",
                "hot_value": "",
            })
            count += 1
            if count >= max_items:
                break
        return topics

    def build_llm_prompt(self, weibo_topics: list[dict], zhihu_topics: list[dict]) -> str:
        """构建 LLM 分析提示词"""
        prompt_parts = ["请分析以下热搜数据，识别当前最热门的趋势主题，并推荐值得撰写文档的选题。\n"]
        prompt_parts.append("## 输出格式要求\n")
        prompt_parts.append("请按照以下 JSON 格式输出推荐结果：\n")
        prompt_parts.append('{"recommendations": [{"rank": 1, "title": "选题标题", "reason": "推荐理由", "angle": "切入角度", "estimated_interest": "high|medium|low", "related_topics": ["相关话题"]}]}\n\n')

        if weibo_topics:
            prompt_parts.append("## 微博热搜\n")
            for t in weibo_topics[:15]:
                heat_tag = f"[{t.get('heat', '')}]" if t.get('heat') else ""
                hot_val = f"({t.get('hot_value', '')})" if t.get('hot_value') else ""
                prompt_parts.append(f"{t['rank']}. {t['title']} {heat_tag} {hot_val}".strip())

        if zhihu_topics:
            prompt_parts.append("\n## 知乎热榜\n")
            for t in zhihu_topics[:15]:
                hot_val = f"({t.get('hot_value', '')})" if t.get('hot_value') else ""
                prompt_parts.append(f"{t['rank']}. {t['title']} {hot_val}".strip())

        prompt_parts.append("\n请分析以上数据，给出 5-8 个推荐选题。只输出 JSON，不要其他文字。")
        return "\n".join(prompt_parts)


topic_manager = TopicManager()
