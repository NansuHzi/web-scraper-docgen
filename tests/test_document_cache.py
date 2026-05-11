"""文档缓存单元测试"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.adapters.document_cache import DocumentCache


class TestDocumentCache:
    """文档缓存测试"""

    def test_cache_get_set(self):
        cache = DocumentCache(ttl_hours=1, max_entries=10)
        cache.set("https://example.com", "tech_doc", "test content")
        result = cache.get("https://example.com", "tech_doc")
        assert result == "test content"

    def test_cache_not_found(self):
        cache = DocumentCache()
        result = cache.get("https://nonexistent.com", "tech_doc")
        assert result is None

    def test_cache_eviction(self):
        cache = DocumentCache(max_entries=2)
        cache.set("https://a.com", "doc", "content A")
        cache.set("https://b.com", "doc", "content B")
        cache.set("https://c.com", "doc", "content C")

        assert cache.get("https://a.com", "doc") is None
        assert cache.get("https://b.com", "doc") == "content B"
        assert cache.get("https://c.com", "doc") == "content C"

    def test_cache_overwrite(self):
        cache = DocumentCache(max_entries=10)
        cache.set("https://example.com", "doc", "version 1")
        cache.set("https://example.com", "doc", "version 2")
        assert cache.get("https://example.com", "doc") == "version 2"

    def test_cache_different_doc_type(self):
        cache = DocumentCache(max_entries=10)
        cache.set("https://example.com", "tech_doc", "tech content")
        cache.set("https://example.com", "api_doc", "api content")
        assert cache.get("https://example.com", "tech_doc") == "tech content"
        assert cache.get("https://example.com", "api_doc") == "api content"

    def test_get_stats(self):
        cache = DocumentCache(max_entries=10)
        cache.set("https://a.com", "doc", "content A")
        stats = cache.get_stats()
        assert stats["total_entries"] == 1
        assert stats["max_entries"] == 10
