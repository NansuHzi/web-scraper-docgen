import pytest
from src.bot.models import Message, Reply, Session, SessionState, PendingOrder, MessageType


class TestMessage:
    def test_create_text_message(self):
        msg = Message(id="m1", user_id="u1", content="hello")
        assert msg.id == "m1"
        assert msg.user_id == "u1"
        assert msg.content == "hello"
        assert msg.message_type == MessageType.TEXT

    def test_create_image_message(self):
        msg = Message(id="m2", user_id="u1", content="img.jpg", message_type=MessageType.IMAGE)
        assert msg.message_type == MessageType.IMAGE


class TestReply:
    def test_create_reply(self):
        reply = Reply(user_id="u1", content="world")
        assert reply.user_id == "u1"
        assert reply.content == "world"


class TestSession:
    def test_default_state(self):
        session = Session(user_id="u1")
        assert session.state == SessionState.IDLE

    def test_with_pending_order(self):
        order = PendingOrder(urls=["https://example.com"])
        session = Session(user_id="u1", pending_order=order)
        assert session.pending_order is not None
        assert len(session.pending_order.urls) == 1


class TestPendingOrder:
    def test_defaults(self):
        order = PendingOrder(urls=["https://example.com"])
        assert order.tier == "basic"
        assert order.format == "md"
        assert order.use_qwen is True

    def test_custom_tier(self):
        order = PendingOrder(urls=["https://example.com"], tier="advanced")
        assert order.tier == "advanced"
