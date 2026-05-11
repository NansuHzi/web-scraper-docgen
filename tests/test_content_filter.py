"""内容安全过滤器单元测试"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.adapters.content_filter import ContentFilter


class TestContentFilter:
    """URL 安全检查"""

    def test_check_url_safety_valid(self):
        safe, error = ContentFilter.check_url_safety("https://www.example.com")
        assert safe is True
        assert error is None

    def test_check_url_safety_contains_blocked_word(self):
        safe, error = ContentFilter.check_url_safety("https://www.example.com/porn/video")
        assert safe is False
        assert "porn" in error

    def test_check_url_safety_gambling(self):
        safe, error = ContentFilter.check_url_safety("https://gambling.example.com")
        assert safe is False
        assert "gambling" in error

    def test_check_url_safety_case_insensitive(self):
        safe, error = ContentFilter.check_url_safety("https://PORN.example.com")
        assert safe is False

    def test_check_url_safety_clean_url(self):
        safe, error = ContentFilter.check_url_safety("https://docs.python.org/3/library/unittest.html")
        assert safe is True

    def test_detect_sensitive_content_normal(self):
        safe, error = ContentFilter.detect_sensitive_content("这是正常的技术文档内容")
        assert safe is True
        assert error is None

    def test_detect_sensitive_content_found(self):
        safe, error = ContentFilter.detect_sensitive_content("这里有色情内容")
        assert safe is False
        assert error is not None

    def test_detect_sensitive_content_english(self):
        safe, error = ContentFilter.detect_sensitive_content("暴力内容 violence")
        assert safe is False

    def test_detect_sensitive_content_empty(self):
        safe, error = ContentFilter.detect_sensitive_content("")
        assert safe is True
        assert error is None

    def test_detect_sensitive_content_none(self):
        safe, error = ContentFilter.detect_sensitive_content(None)
        assert safe is True
        assert error is None

    def test_filter_content_replaces_all_patterns(self):
        result = ContentFilter.filter_content("这里有色情和赌博内容")
        assert "色情" not in result
        assert "赌博" not in result
        assert "[内容已过滤]" in result

    def test_filter_content_custom_replace(self):
        result = ContentFilter.filter_content("色情内容", replace_char="***")
        assert result == "***内容"

    def test_filter_content_empty(self):
        result = ContentFilter.filter_content("")
        assert result == ""

    def test_filter_content_no_sensitive(self):
        result = ContentFilter.filter_content("正常内容")
        assert result == "正常内容"

    def test_validate_request_url_only_pass(self):
        ok, error = ContentFilter.validate_request("https://example.com", None)
        assert ok is True

    def test_validate_request_url_only_blocked(self):
        ok, error = ContentFilter.validate_request("https://xxx.com", None)
        assert ok is False

    def test_validate_request_content_blocked(self):
        ok, error = ContentFilter.validate_request("https://safe.com", "含有色情的内容")
        assert ok is False

    def test_validate_request_all_pass(self):
        ok, error = ContentFilter.validate_request("https://safe.com", "正常内容")
        assert ok is True
