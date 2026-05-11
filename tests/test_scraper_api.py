"""API 工具函数单元测试"""
import sys
import os
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.api.scraper import validate_url_format, generate_filename


class TestValidateUrlFormat:
    """URL 格式验证"""

    def test_valid_http(self):
        assert validate_url_format("http://example.com") is True

    def test_valid_https(self):
        assert validate_url_format("https://example.com/path?query=1") is True

    def test_valid_with_port(self):
        assert validate_url_format("https://example.com:8080/path") is True

    def test_missing_scheme(self):
        assert validate_url_format("example.com/path") is False

    def test_empty_string(self):
        assert validate_url_format("") is False

    def test_just_scheme(self):
        assert validate_url_format("https://") is False

    def test_invalid_scheme(self):
        # ftp 也是有效 scheme，urlparse 接受各种 scheme
        assert validate_url_format("ftp://files.example.com") is True

    def test_ip_address(self):
        assert validate_url_format("https://192.168.1.1/path") is True


class TestGenerateFilename:
    """文件名生成"""

    def test_from_markdown_title(self):
        doc = "# Python异步编程指南\n\n正文内容..."
        filename = generate_filename(doc, "https://example.com")
        assert filename.startswith("Python异步编程指南_")
        assert filename.endswith(".md")

    def test_special_chars_in_title(self):
        doc = "# C++: 模板<typename T> 使用指南\n\n正文"
        filename = generate_filename(doc, "https://example.com")
        assert ":" not in filename
        assert "<" not in filename
        assert ">" not in filename

    def test_long_title_truncated(self):
        doc = "# " + "A" * 80 + "\n\nContent"
        filename = generate_filename(doc, "https://example.com")
        # 标题截断为 50 字符
        title_part = filename.split("_")[0]
        assert len(title_part) <= 50

    def test_fallback_to_domain(self):
        doc = "No title here\nJust content"
        filename = generate_filename(doc, "https://docs.python.org/3/library/asyncio.html")
        assert "docs_python_org" in filename
        assert filename.endswith(".md")

    def test_timestamp_format(self):
        doc = "# Test Title\n\nContent"
        filename = generate_filename(doc, "https://example.com")
        # 格式: Title_YYYYMMDD_HHMMSS.md
        pattern = r'^Test Title_\d{8}_\d{6}\.md$'
        assert re.match(pattern, filename) is not None

    def test_empty_doc(self):
        filename = generate_filename("", "https://example.com/page")
        assert "example_com" in filename
        assert ".md" in filename
