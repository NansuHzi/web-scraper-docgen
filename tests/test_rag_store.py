"""RAG 文本分块单元测试"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.adapters.rag_store import _split_text


class TestSplitText:
    """文本分块逻辑测试"""

    def test_short_text_no_split(self):
        result = _split_text("Hello world", chunk_size=100, chunk_overlap=20)
        assert result == ["Hello world"]

    def test_empty_string(self):
        result = _split_text("", chunk_size=100)
        assert result == []

    def test_whitespace_only(self):
        result = _split_text("   \n  \t  ", chunk_size=100)
        assert result == []

    def test_split_on_double_newline(self):
        text = "A" * 800 + "\n\n" + "B" * 800
        result = _split_text(text, chunk_size=1000, chunk_overlap=0)
        assert len(result) >= 2

    def test_split_on_period_chinese(self):
        text = "第一句话。" + "内容" * 200 + "。" + "第二句话。" + "更多" * 200
        result = _split_text(text, chunk_size=300, chunk_overlap=50)
        assert len(result) > 1

    def test_chunks_have_overlap(self):
        text = "ABCDEFGHIJ" * 200
        result = _split_text(text, chunk_size=200, chunk_overlap=50)
        assert len(result) > 1

    def test_no_overlap(self):
        text = "ABCDEFGHIJ" * 200
        result = _split_text(text, chunk_size=200, chunk_overlap=0)
        assert len(result) > 1

    def test_single_char(self):
        result = _split_text("X", chunk_size=1000)
        assert result == ["X"]

    def test_exact_chunk_size_boundary(self):
        text = "A" * 500 + "\n\n" + "B" * 500
        result = _split_text(text, chunk_size=1000, chunk_overlap=0)
        assert len(result) >= 2

    def test_chinese_text_splitting(self):
        text = "这是第一段内容。包含了中文的句子。" + "数据" * 300 + "这是第二段。更多内容在这里。"
        result = _split_text(text, chunk_size=300, chunk_overlap=50)
        assert len(result) > 1
        # 所有 chunk 都应该是非空的
        for chunk in result:
            assert len(chunk.strip()) > 0
