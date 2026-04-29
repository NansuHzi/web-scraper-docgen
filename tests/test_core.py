"""DocGen 单元测试"""
import pytest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.adapters.content_filter import ContentFilter
from src.adapters.document_cache import DocumentCache
from src.adapters.session_manager import session_manager


class TestContentFilter:
    """内容过滤器测试"""

    def test_check_url_safety_valid(self):
        """测试合法URL"""
        safe, error = ContentFilter.check_url_safety("https://www.example.com")
        assert safe is True
        assert error is None

    def test_check_url_safety_contains_blocked_word(self):
        """测试包含黑名单关键词的URL"""
        safe, error = ContentFilter.check_url_safety("https://www.example.com/porn/video")
        assert safe is False
        assert "porn" in error

    def test_check_url_safety_gambling(self):
        """测试赌博相关URL"""
        safe, error = ContentFilter.check_url_safety("https://gambling.example.com")
        assert safe is False
        assert "gambling" in error

    def test_detect_sensitive_content(self):
        """测试敏感内容检测"""
        safe, error = ContentFilter.detect_sensitive_content("这是正常内容")
        assert safe is True
        
        safe, error = ContentFilter.detect_sensitive_content("色情内容测试")
        assert safe is False
        assert "色情" in error


class TestDocumentCache:
    """文档缓存测试"""

    def test_cache_get_set(self):
        """测试缓存读写"""
        cache = DocumentCache(ttl_hours=1, max_entries=10)
        cache.set("https://example.com", "tech_doc", "test content")
        result = cache.get("https://example.com", "tech_doc")
        assert result == "test content"

    def test_cache_not_found(self):
        """测试缓存未命中"""
        cache = DocumentCache()
        result = cache.get("https://nonexistent.com", "tech_doc")
        assert result is None

    def test_cache_eviction(self):
        """测试LRU淘汰"""
        cache = DocumentCache(max_entries=2)
        cache.set("https://a.com", "doc", "content A")
        cache.set("https://b.com", "doc", "content B")
        cache.set("https://c.com", "doc", "content C")
        
        # 第一个应该被淘汰
        assert cache.get("https://a.com", "doc") is None
        assert cache.get("https://b.com", "doc") == "content B"
        assert cache.get("https://c.com", "doc") == "content C"


class TestSessionManager:
    """会话管理器测试"""

    def test_get_or_create_session(self):
        """测试会话创建"""
        session_id1 = session_manager.get_or_create_session("192.168.1.1")
        session_id2 = session_manager.get_or_create_session("192.168.1.1")
        session_id3 = session_manager.get_or_create_session("192.168.1.2")
        
        # 同一IP应该返回相同会话
        assert session_id1 == session_id2
        # 不同IP应该返回不同会话
        assert session_id1 != session_id3

    def test_validate_session(self):
        """测试会话验证"""
        session_id = session_manager.get_or_create_session("192.168.1.100")
        valid = session_manager.validate_session(session_id, "192.168.1.100")
        assert valid is True
        
        invalid = session_manager.validate_session(session_id, "192.168.1.200")
        assert invalid is False


class TestFormatAdapter:
    """格式适配器测试"""

    def test_export_md(self):
        """测试Markdown导出"""
        from src.adapters.format_adapter import FormatAdapter
        
        adapter = FormatAdapter()
        content = "# 标题\n\n正文内容"
        filepath = adapter.export(content, "test_md", "md")
        
        assert filepath.endswith(".md")
        assert os.path.exists(filepath)
        os.remove(filepath)

    def test_export_txt(self):
        """测试纯文本导出"""
        from src.adapters.format_adapter import FormatAdapter
        
        adapter = FormatAdapter()
        content = "# 标题\n\n正文内容"
        filepath = adapter.export(content, "test_txt", "txt")
        
        assert filepath.endswith(".txt")
        assert os.path.exists(filepath)
        os.remove(filepath)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
