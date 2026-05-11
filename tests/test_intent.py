import pytest
from src.bot.intent import (
    Intent, IntentParser, URL_PATTERN, TASK_ID_PATTERN,
    clean_url, is_valid_url, parse_options, TIER_MAP, FORMAT_MAP,
)


class TestCleanUrl:
    def test_removes_trailing_chinese_punctuation(self):
        assert clean_url("https://example.com/page。") == "https://example.com/page"

    def test_removes_trailing_chinese_chars(self):
        assert clean_url("https://example.com/page的") == "https://example.com/page"

    def test_removes_trailing_brackets(self):
        assert clean_url("https://example.com/page)") == "https://example.com/page"

    def test_clean_url_no_change(self):
        assert clean_url("https://example.com/page") == "https://example.com/page"


class TestIsValidUrl:
    def test_valid_http(self):
        assert is_valid_url("http://example.com") is True

    def test_valid_https(self):
        assert is_valid_url("https://example.com/path?q=1") is True

    def test_invalid_no_scheme(self):
        assert is_valid_url("example.com") is False

    def test_invalid_ftp(self):
        assert is_valid_url("ftp://example.com") is False

    def test_invalid_empty(self):
        assert is_valid_url("") is False


class TestParseOptions:
    def test_tier_basic(self):
        result = parse_options("我要基础版")
        assert result["tier"] == "basic"

    def test_tier_advanced(self):
        result = parse_options("进阶版")
        assert result["tier"] == "advanced"

    def test_tier_multi(self):
        result = parse_options("多页整合")
        assert result["tier"] == "multi"

    def test_format_md(self):
        result = parse_options("markdown格式")
        assert result["format"] == "md"

    def test_format_txt(self):
        result = parse_options("纯文本")
        assert result["format"] == "txt"

    def test_use_qwen(self):
        result = parse_options("用千问模型")
        assert result["use_qwen"] is True

    def test_use_deepseek(self):
        result = parse_options("用deepseek")
        assert result["use_qwen"] is False

    def test_empty_text(self):
        result = parse_options("")
        assert result == {}


class TestIntentParser:
    def setup_method(self):
        self.parser = IntentParser()

    def test_submit_url_single(self):
        intent, data = self.parser.parse("帮我处理 https://example.com/page")
        assert intent == Intent.SUBMIT_URL
        assert "https://example.com/page" in data["urls"]

    def test_submit_url_multiple(self):
        intent, data = self.parser.parse(
            "处理这些 https://a.com 和 https://b.com"
        )
        assert intent == Intent.SUBMIT_URL
        assert len(data["urls"]) == 2

    def test_help(self):
        intent, data = self.parser.parse("帮助")
        assert intent == Intent.HELP

    def test_pricing(self):
        intent, data = self.parser.parse("多少钱")
        assert intent == Intent.PRICING

    def test_greeting(self):
        intent, data = self.parser.parse("你好")
        assert intent == Intent.GREETING

    def test_cancel(self):
        intent, data = self.parser.parse("取消")
        assert intent == Intent.CANCEL

    def test_query_status_with_task_id(self):
        intent, data = self.parser.parse("task-abc123456789 查询进度")
        assert intent == Intent.QUERY_STATUS
        assert len(data["task_ids"]) > 0

    def test_unknown(self):
        intent, data = self.parser.parse("这是一段无法识别的较长文本内容")
        assert intent == Intent.UNKNOWN

    def test_awaiting_confirmation_confirm(self):
        intent, data = self.parser.parse("确认", session_state="awaiting_confirmation")
        assert intent == Intent.CONFIRM_ORDER

    def test_awaiting_confirmation_payment(self):
        intent, data = self.parser.parse("已付款", session_state="awaiting_confirmation")
        assert intent == Intent.PAYMENT_DONE

    def test_awaiting_confirmation_cancel(self):
        intent, data = self.parser.parse("不要了", session_state="awaiting_confirmation")
        assert intent == Intent.CANCEL

    def test_awaiting_options_select_tier(self):
        intent, data = self.parser.parse("进阶版", session_state="awaiting_options")
        assert intent == Intent.SELECT_OPTION
        assert data["tier"] == "advanced"

    def test_vectorize(self):
        intent, data = self.parser.parse("向量化")
        assert intent == Intent.VECTORIZE

    def test_url_with_chinese_trailing(self):
        intent, data = self.parser.parse("https://example.com/page的")
        assert intent == Intent.SUBMIT_URL
