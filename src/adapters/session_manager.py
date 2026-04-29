import uuid
import threading
from datetime import datetime, timedelta
from typing import Dict, Optional


class SessionManager:
    """会话管理器 - 基于IP的用户隔离"""

    def __init__(self):
        self._sessions: Dict[str, dict] = {}
        self._lock = threading.Lock()
        self._cleanup_thread = None
        self._running = False
        self._session_ttl = timedelta(hours=24)

    def get_or_create_session(self, client_ip: str) -> str:
        """获取或创建会话ID"""
        with self._lock:
            for session_id, data in self._sessions.items():
                if data["client_ip"] == client_ip:
                    data["last_access"] = datetime.now()
                    return session_id

            session_id = str(uuid.uuid4())
            self._sessions[session_id] = {
                "client_ip": client_ip,
                "created_at": datetime.now(),
                "last_access": datetime.now()
            }
            return session_id

    def validate_session(self, session_id: str, client_ip: str) -> bool:
        """验证会话是否属于该IP"""
        with self._lock:
            if session_id not in self._sessions:
                return False
            return self._sessions[session_id]["client_ip"] == client_ip

    def get_session(self, session_id: str) -> Optional[dict]:
        """获取会话信息"""
        with self._lock:
            return self._sessions.get(session_id)

    def start_cleanup(self):
        """启动定期清理"""
        self._running = True
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()

    def stop_cleanup(self):
        """停止定期清理"""
        self._running = False
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=5)

    def _cleanup_loop(self):
        """定期清理过期会话"""
        while self._running:
            try:
                self._cleanup_expired()
            except Exception:
                pass
            import time
            time.sleep(300)

    def _cleanup_expired(self):
        """清理过期会话"""
        with self._lock:
            now = datetime.now()
            expired = [
                sid for sid, data in self._sessions.items()
                if now - data["last_access"] > self._session_ttl
            ]
            for sid in expired:
                del self._sessions[sid]


session_manager = SessionManager()
session_manager.start_cleanup()
