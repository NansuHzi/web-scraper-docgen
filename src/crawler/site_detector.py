from dataclasses import dataclass, field
from enum import Enum
from urllib.parse import urlparse
from typing import Optional
import re


class SiteType(Enum):
    WORDPRESS = "wordpress"
    HEXO = "hexo"
    VUEPRESS = "vuepress"
    DOCUSAURUS = "docusaurus"
    GITBOOK = "gitbook"
    CONFLUENCE = "confluence"
    MEDIUM = "medium"
    CSDN = "csdn"
    JUEJIN = "juejin"
    JIANSHU = "jianshu"
    CNBLOGS = "cnblogs"
    ZHIHU = "zhihu"
    WECHAT = "wechat"
    GITHUB = "github"
    GENERIC_BLOG = "generic_blog"
    GENERIC_DOCS = "generic_docs"
    UNKNOWN = "unknown"


class RenderStrategy(Enum):
    STATIC = "static"
    JS_RENDER = "js_render"
    HYBRID = "hybrid"
    FIRECRAWL = "firecrawl"


@dataclass
class SiteProfile:
    site_type: SiteType
    render_strategy: RenderStrategy
    content_selectors: list[str] = field(default_factory=list)
    title_selectors: list[str] = field(default_factory=list)
    nav_selectors: list[str] = field(default_factory=list)
    pagination_selectors: list[str] = field(default_factory=list)
    exclude_selectors: list[str] = field(default_factory=list)
    needs_login: bool = False
    rate_limit_delay: float = 1.0


SITE_SIGNATURES = {
    SiteType.WORDPRESS: {
        "meta_generator": "WordPress",
        "paths": ["/wp-content/", "/wp-admin/", "/wp-json/"],
        "classes": ["wp-block-", "entry-content", "post-content"],
        "selectors": [".entry-content", ".post-content", "article .content"],
    },
    SiteType.HEXO: {
        "meta_generator": "Hexo",
        "classes": ["post-content", "article-content", "markdown-body"],
        "selectors": [".post-content", ".article-content", ".markdown-body"],
    },
    SiteType.VUEPRESS: {
        "meta_generator": "VuePress",
        "classes": ["theme-default-content", "content__default"],
        "selectors": [".theme-default-content", ".content__default"],
    },
    SiteType.DOCUSAURUS: {
        "meta_generator": "Docusaurus",
        "classes": ["markdown", "theme-doc-markdown"],
        "selectors": ["article .markdown", ".theme-doc-markdown"],
    },
    SiteType.GITBOOK: {
        "meta_generator": "GitBook",
        "classes": ["page-wrapper", "markdown-section"],
        "selectors": [".page-wrapper", ".markdown-section"],
    },
    SiteType.CONFLUENCE: {
        "paths": ["/wiki/", "/confluence/"],
        "classes": ["wiki-content", "confluence-content"],
        "selectors": [".wiki-content", "#main-content"],
    },
    SiteType.MEDIUM: {
        "domains": ["medium.com"],
        "classes": ["article-content", "postArticle-content"],
        "selectors": ["article", ".postArticle-content"],
    },
    SiteType.GITHUB: {
        "domains": ["github.com", "raw.githubusercontent.com"],
        "classes": ["markdown-body", "repository-content"],
        "selectors": [".markdown-body", "article.markdown-body"],
    },
}

DOMAIN_SITE_MAP = {
    "blog.csdn.net": SiteType.CSDN,
    "juejin.cn": SiteType.JUEJIN,
    "www.jianshu.com": SiteType.JIANSHU,
    "www.cnblogs.com": SiteType.CNBLOGS,
    "zhuanlan.zhihu.com": SiteType.ZHIHU,
    "www.zhihu.com": SiteType.ZHIHU,
    "mp.weixin.qq.com": SiteType.WECHAT,
    "medium.com": SiteType.MEDIUM,
    "github.com": SiteType.GITHUB,
}

SITE_PROFILES = {
    SiteType.WORDPRESS: SiteProfile(
        site_type=SiteType.WORDPRESS,
        render_strategy=RenderStrategy.STATIC,
        content_selectors=[".entry-content", ".post-content", "article", ".content-area"],
        title_selectors=[".entry-title", "h1"],
        nav_selectors=[".nav-menu", ".menu"],
        pagination_selectors=[".nav-links", ".pagination"],
        exclude_selectors=[".sidebar", ".comments", ".related-posts", ".advertisement"],
    ),
    SiteType.VUEPRESS: SiteProfile(
        site_type=SiteType.VUEPRESS,
        render_strategy=RenderStrategy.JS_RENDER,
        content_selectors=[".theme-default-content", ".content__default"],
        title_selectors=["h1"],
        nav_selectors=[".sidebar", ".navbar"],
        pagination_selectors=[".page-nav"],
        exclude_selectors=[".sidebar", ".navbar", ".page-edit", ".page-nav"],
    ),
    SiteType.DOCUSAURUS: SiteProfile(
        site_type=SiteType.DOCUSAURUS,
        render_strategy=RenderStrategy.JS_RENDER,
        content_selectors=["article .markdown", ".theme-doc-markdown"],
        title_selectors=["h1"],
        nav_selectors=[".menu", ".navbar"],
        pagination_selectors=[".pagination-nav"],
        exclude_selectors=[".table-of-contents", ".navbar", ".footer"],
    ),
    SiteType.GITBOOK: SiteProfile(
        site_type=SiteType.GITBOOK,
        render_strategy=RenderStrategy.JS_RENDER,
        content_selectors=[".page-wrapper", ".markdown-section"],
        title_selectors=["h1"],
        nav_selectors=[".book-summary", ".header"],
        pagination_selectors=[".page-toc"],
        exclude_selectors=[".book-summary", ".page-toc"],
    ),
    SiteType.CSDN: SiteProfile(
        site_type=SiteType.CSDN,
        render_strategy=RenderStrategy.HYBRID,
        content_selectors=["#article_content", "#content_views", "article"],
        title_selectors=[".title-article", "h1"],
        exclude_selectors=[".recommend-box", ".comment-box", ".toolbar", "aside"],
        needs_login=False,
    ),
    SiteType.JUEJIN: SiteProfile(
        site_type=SiteType.JUEJIN,
        render_strategy=RenderStrategy.JS_RENDER,
        content_selectors=[".article-content", ".markdown-body", "article"],
        title_selectors=[".article-title", "h1"],
        exclude_selectors=[".sidebar", ".comment-box", ".author-info-block"],
        needs_login=False,
    ),
    SiteType.ZHIHU: SiteProfile(
        site_type=SiteType.ZHIHU,
        render_strategy=RenderStrategy.JS_RENDER,
        content_selectors=[".Post-RichTextContainer", ".RichText", ".Post-Main", "article"],
        title_selectors=[".QuestionHeader-title", "h1"],
        exclude_selectors=[".ContentItem-actions", ".Comments-container", ".CornerButtons"],
        needs_login=False,
    ),
    SiteType.WECHAT: SiteProfile(
        site_type=SiteType.WECHAT,
        render_strategy=RenderStrategy.STATIC,
        content_selectors=["#js_content", ".rich_media_content", "article"],
        title_selectors=[".rich_media_title", "h1"],
        exclude_selectors=[".rich_media_tool", ".reward_area", ".like_comment_wrp"],
    ),
    SiteType.GITHUB: SiteProfile(
        site_type=SiteType.GITHUB,
        render_strategy=RenderStrategy.HYBRID,
        content_selectors=[".markdown-body", "article.markdown-body"],
        title_selectors=["h1"],
        exclude_selectors=[".file-navigation", ".gh-header-actions", ".footer"],
    ),
    SiteType.GENERIC_BLOG: SiteProfile(
        site_type=SiteType.GENERIC_BLOG,
        render_strategy=RenderStrategy.HYBRID,
        content_selectors=["article", "main", ".content", ".post", ".article"],
        title_selectors=["h1", ".title"],
        exclude_selectors=["nav", "footer", ".sidebar", ".comments", ".advertisement"],
    ),
    SiteType.GENERIC_DOCS: SiteProfile(
        site_type=SiteType.GENERIC_DOCS,
        render_strategy=RenderStrategy.HYBRID,
        content_selectors=["article", "main", ".markdown-body", ".doc-content"],
        title_selectors=["h1"],
        exclude_selectors=["nav", "footer", ".sidebar", ".toc"],
    ),
    SiteType.UNKNOWN: SiteProfile(
        site_type=SiteType.UNKNOWN,
        render_strategy=RenderStrategy.JS_RENDER,
        content_selectors=["article", "main", "body"],
        title_selectors=["h1", "title"],
        exclude_selectors=["nav", "footer", "script", "style"],
    ),
}


class SiteDetector:
    def __init__(self):
        self._cache: dict[str, SiteProfile] = {}

    def detect(self, url: str, html_content: Optional[str] = None) -> SiteProfile:
        parsed = urlparse(url)
        hostname = parsed.hostname or ""

        if hostname in self._cache:
            return self._cache[hostname]

        profile = self._detect_by_domain(hostname)

        if profile.site_type == SiteType.UNKNOWN and html_content:
            profile = self._detect_by_content(html_content, hostname)

        self._cache[hostname] = profile
        return profile

    def _detect_by_domain(self, hostname: str) -> SiteProfile:
        if hostname in DOMAIN_SITE_MAP:
            site_type = DOMAIN_SITE_MAP[hostname]
            return SITE_PROFILES.get(site_type, SITE_PROFILES[SiteType.UNKNOWN])

        for domain, site_type in DOMAIN_SITE_MAP.items():
            if hostname.endswith("." + domain) or hostname == domain:
                return SITE_PROFILES.get(site_type, SITE_PROFILES[SiteType.UNKNOWN])

        return SITE_PROFILES[SiteType.UNKNOWN]

    def _detect_by_content(self, html: str, hostname: str) -> SiteProfile:
        for site_type, signature in SITE_SIGNATURES.items():
            if "meta_generator" in signature:
                pattern = rf'<meta\s+name=["\']generator["\']\s+content=["\']{signature["meta_generator"]}'
                if re.search(pattern, html, re.IGNORECASE):
                    return SITE_PROFILES.get(site_type, SITE_PROFILES[SiteType.UNKNOWN])

            if "classes" in signature:
                for cls in signature["classes"]:
                    if cls in html:
                        return SITE_PROFILES.get(site_type, SITE_PROFILES[SiteType.UNKNOWN])

            if "paths" in signature:
                for path in signature["paths"]:
                    if path in html:
                        return SITE_PROFILES.get(site_type, SITE_PROFILES[SiteType.UNKNOWN])

        if any(kw in html for kw in ["wp-content", "wp-includes", "wp-json"]):
            return SITE_PROFILES[SiteType.WORDPRESS]

        if "hexo" in html.lower() or "hexo-theme" in html:
            return SITE_PROFILES[SiteType.HEXO]

        return SITE_PROFILES[SiteType.UNKNOWN]

    def get_profile(self, url: str) -> SiteProfile:
        return self.detect(url)

    def clear_cache(self):
        self._cache.clear()


site_detector = SiteDetector()
