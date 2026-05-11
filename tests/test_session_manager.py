"""会话管理器单元测试"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.adapters.session_manager import SessionManager


class TestSessionManager:
    """会话管理器测试"""

    def setup_method(self):
        self.sm = SessionManager()

    def test_get_or_create_session_same_ip(self):
        sid1 = self.sm.get_or_create_session("192.168.1.1")
        sid2 = self.sm.get_or_create_session("192.168.1.1")
        assert sid1 == sid2

    def test_get_or_create_session_diff_ip(self):
        sid1 = self.sm.get_or_create_session("192.168.1.1")
        sid2 = self.sm.get_or_create_session("192.168.1.2")
        assert sid1 != sid2

    def test_validate_session_valid(self):
        sid = self.sm.get_or_create_session("192.168.1.100")
        assert self.sm.validate_session(sid, "192.168.1.100") is True

    def test_validate_session_invalid_ip(self):
        sid = self.sm.get_or_create_session("192.168.1.100")
        assert self.sm.validate_session(sid, "192.168.1.200") is False

    def test_validate_session_nonexistent(self):
        assert self.sm.validate_session("nonexistent-id", "192.168.1.1") is False

    def test_get_session_exists(self):
        sid = self.sm.get_or_create_session("10.0.0.1")
        session = self.sm.get_session(sid)
        assert session is not None
        assert session["client_ip"] == "10.0.0.1"

    def test_get_session_not_exists(self):
        assert self.sm.get_session("no-such-id") is None

    def test_last_access_updated(self):
        import time
        sid = self.sm.get_or_create_session("10.0.0.1")
        first_access = self.sm.get_session(sid)["last_access"]
        time.sleep(0.01)
        self.sm.get_or_create_session("10.0.0.1")  # re-access
        second_access = self.sm.get_session(sid)["last_access"]
        assert second_access >= first_access
