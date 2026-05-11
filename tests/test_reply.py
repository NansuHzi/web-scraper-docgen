import pytest
from src.bot.reply import ReplyEngine, FORMAT_NAMES
from src.bot.intent import Intent
from src.bot.models import Reply, Message, Session, SessionState, PendingOrder


class TestCalcPrice:
    def setup_method(self):
        self.engine = ReplyEngine()

    def test_basic_tier(self):
        price, name, desc = self.engine._calc_price("basic", 1)
        assert price == 9.9
        assert name == "基础版"

    def test_advanced_tier(self):
        price, name, desc = self.engine._calc_price("advanced", 1)
        assert price == 19.9
        assert name == "进阶版"

    def test_multi_tier_within_limit(self):
        price, name, desc = self.engine._calc_price("multi", 5)
        assert price == 39.9
        assert name == "多页整合"

    def test_multi_tier_over_limit(self):
        price, name, desc = self.engine._calc_price("multi", 7)
        assert price == 49.9
        assert "7个URL" in desc

    def test_unknown_tier_defaults_basic(self):
        price, name, desc = self.engine._calc_price("unknown", 1)
        assert price == 9.9
        assert name == "基础版"


class TestFormatNames:
    def test_md(self):
        assert FORMAT_NAMES["md"] == "Markdown"

    def test_txt(self):
        assert FORMAT_NAMES["txt"] == "纯文本TXT"


class TestReplyEngine:
    def setup_method(self):
        self.engine = ReplyEngine()

    def _make_message(self, text="test", user_id="user1"):
        return Message(id="msg1", user_id=user_id, content=text)

    def _make_session(self, user_id="user1"):
        return Session(user_id=user_id, state=SessionState.IDLE)

    def test_greeting_reply(self):
        msg = self._make_message("你好")
        session = self._make_session()
        reply = self.engine.generate(Intent.GREETING, msg, session, {})
        assert reply.user_id == "user1"
        assert "助手" in reply.content

    def test_help_reply(self):
        msg = self._make_message("帮助")
        session = self._make_session()
        reply = self.engine.generate(Intent.HELP, msg, session, {})
        assert "帮助" in reply.content or "功能" in reply.content

    def test_pricing_reply(self):
        msg = self._make_message("价格")
        session = self._make_session()
        reply = self.engine.generate(Intent.PRICING, msg, session, {})
        assert "9.9" in reply.content
        assert "19.9" in reply.content
        assert "39.9" in reply.content

    def test_cancel_reply(self):
        msg = self._make_message("取消")
        session = self._make_session()
        reply = self.engine.generate(Intent.CANCEL, msg, session, {})
        assert reply.user_id == "user1"

    def test_unknown_reply(self):
        msg = self._make_message("随机内容")
        session = self._make_session()
        reply = self.engine.generate(Intent.UNKNOWN, msg, session, {})
        assert reply.user_id == "user1"

    def test_submit_url_reply(self):
        msg = self._make_message("https://example.com")
        session = self._make_session()
        context = {"urls": ["https://example.com"]}
        reply = self.engine.generate(Intent.SUBMIT_URL, msg, session, context)
        assert "9.9" in reply.content
        assert "确认" in reply.content

    def test_submit_url_multi_auto_upgrade(self):
        msg = self._make_message()
        session = self._make_session()
        context = {"urls": ["https://a.com", "https://b.com"]}
        reply = self.engine.generate(Intent.SUBMIT_URL, msg, session, context)
        assert "39.9" in reply.content

    def test_confirm_order_no_pending(self):
        msg = self._make_message("确认")
        session = self._make_session()
        reply = self.engine.generate(Intent.CONFIRM_ORDER, msg, session, {})
        assert "没有待确认" in reply.content

    def test_confirm_order_with_pending(self):
        msg = self._make_message("确认")
        session = self._make_session()
        session.pending_order = PendingOrder(urls=["https://example.com"])
        reply = self.engine.generate(Intent.CONFIRM_ORDER, msg, session, {})
        assert "9.9" in reply.content
