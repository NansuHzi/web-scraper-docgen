"""格式适配器单元测试"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.adapters.format_adapter import FormatAdapter, TxtExporter, MarkdownExporter


class TestMarkdownExporter:
    def test_export_md(self):
        exporter = MarkdownExporter()
        content = "# Title\n\nBody content"
        filepath = exporter.export(content, "test_md_basic")
        assert filepath.endswith(".md")
        assert os.path.exists(filepath)
        with open(filepath, "r", encoding="utf-8") as f:
            assert f.read() == content
        os.remove(filepath)

    def test_get_extension(self):
        assert MarkdownExporter().get_extension() == ".md"


class TestTxtExporter:
    def test_export_txt_strips_markdown(self):
        exporter = TxtExporter()
        content = "# Title\n\n**bold** and *italic*"
        filepath = exporter.export(content, "test_txt_strip")
        assert filepath.endswith(".txt")
        assert os.path.exists(filepath)
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()
            assert "#" not in text
            assert "**" not in text
            assert "*" not in text
        os.remove(filepath)

    def test_export_txt_strips_all_syntax(self):
        exporter = TxtExporter()
        content = "## Header\n\n- list item\n\n> blockquote\n\n`code`\n\n[link](url)"
        filepath = exporter.export(content, "test_txt_all")
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()
            assert "#" not in text
            assert ">" not in text
            assert "[" not in text
            assert "]" not in text
            assert "`" not in text
            assert "- " not in text
        os.remove(filepath)

    def test_export_txt_collapses_newlines(self):
        exporter = TxtExporter()
        content = "Paragraph one\n\n\n\n\n\n\nParagraph two"
        filepath = exporter.export(content, "test_txt_newlines")
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()
            # 多个空行应该被折叠为最多一个空行
            assert "\n\n\n" not in text
        os.remove(filepath)

    def test_get_extension(self):
        assert TxtExporter().get_extension() == ".txt"


class TestFormatAdapter:
    def test_export_md(self):
        adapter = FormatAdapter()
        content = "# Title\n\nContent"
        filepath = adapter.export(content, "test_fa_md", "md")
        assert os.path.exists(filepath)
        os.remove(filepath)

    def test_export_txt(self):
        adapter = FormatAdapter()
        content = "# Title\n\nContent"
        filepath = adapter.export(content, "test_fa_txt", "txt")
        assert os.path.exists(filepath)
        os.remove(filepath)

    def test_export_invalid_format(self):
        import pytest
        adapter = FormatAdapter()
        with pytest.raises(ValueError, match="不支持的格式"):
            adapter.export("content", "test", "pdf")

    def test_get_supported_formats(self):
        adapter = FormatAdapter()
        formats = adapter.get_supported_formats()
        assert "md" in formats
        assert "txt" in formats
        assert "ppt" in formats
