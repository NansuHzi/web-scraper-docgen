import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
import threading

logger = logging.getLogger(__name__)


class DocumentCache:
    """文档缓存管理器 - 支持TTL过期和LRU清理"""

    def __init__(self, ttl_hours: int = 24, max_entries: int = 100):
        self.cache: Dict[str, dict] = {}
        self.ttl = timedelta(hours=ttl_hours)
        self.max_entries = max_entries
        self._lock = threading.Lock()
        self._cleanup_thread = None
        self._running = False

    def _generate_key(self, url: str, doc_type: str) -> str:
        content = f"{url}_{doc_type}"
        return hashlib.md5(content.encode()).hexdigest()

    def get(self, url: str, doc_type: str) -> Optional[str]:
        key = self._generate_key(url, doc_type)
        with self._lock:
            if key in self.cache:
                entry = self.cache[key]
                if datetime.now() - entry['timestamp'] < self.ttl:
                    entry['access_count'] += 1
                    entry['last_access'] = datetime.now()
                    return entry['content']
                else:
                    del self.cache[key]
        return None

    def set(self, url: str, doc_type: str, content: str):
        key = self._generate_key(url, doc_type)
        with self._lock:
            if len(self.cache) >= self.max_entries:
                self._evict_lru()
            self.cache[key] = {
                'content': content,
                'timestamp': datetime.now(),
                'last_access': datetime.now(),
                'access_count': 0,
                'url': url,
                'doc_type': doc_type
            }

    def _evict_lru(self):
        if not self.cache:
            return
        lru_key = min(
            self.cache.keys(),
            key=lambda k: (self.cache[k]['last_access'], self.cache[k]['access_count'])
        )
        del self.cache[lru_key]

    def cleanup_expired(self):
        with self._lock:
            now = datetime.now()
            expired_keys = [
                key for key, entry in self.cache.items()
                if now - entry['timestamp'] >= self.ttl
            ]
            for key in expired_keys:
                del self.cache[key]
            return len(expired_keys)

    def start_auto_cleanup(self, interval_hours: int = 1):
        if self._running:
            return
        self._running = True
        self._cleanup_thread = threading.Thread(target=self._auto_cleanup, args=(interval_hours,))
        self._cleanup_thread.daemon = True
        self._cleanup_thread.start()

    def stop_auto_cleanup(self):
        self._running = False
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=5)

    def _auto_cleanup(self, interval_hours: int):
        interval_seconds = interval_hours * 3600
        while self._running:
            try:
                cleaned = self.cleanup_expired()
                if cleaned > 0:
                    logger.info("缓存清理: 删除%d个过期条目", cleaned)
            except Exception as e:
                logger.error("缓存清理错误: %s", e)
            import time
            time.sleep(interval_seconds)

    def get_stats(self) -> dict:
        with self._lock:
            total_entries = len(self.cache)
            oldest = min((e['timestamp'] for e in self.cache.values()), default=None)
            newest = max((e['timestamp'] for e in self.cache.values()), default=None)
            return {
                'total_entries': total_entries,
                'max_entries': self.max_entries,
                'ttl_hours': self.ttl.total_seconds() / 3600,
                'oldest_entry': oldest.isoformat() if oldest else None,
                'newest_entry': newest.isoformat() if newest else None
            }


document_cache = DocumentCache(ttl_hours=24, max_entries=100)
document_cache.start_auto_cleanup(interval_hours=1)