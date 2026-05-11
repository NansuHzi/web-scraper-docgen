import hashlib
import json
import os
import sqlite3
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class ContentHash:
    url: str
    hash_value: str
    title: str
    content_length: int
    last_checked: str = field(default_factory=lambda: datetime.now().isoformat())
    last_changed: Optional[str] = None
    change_count: int = 0


class IncrementalTracker:
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                'data', 'incremental_tracker.db'
            )

        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        with self._lock:
            conn = sqlite3.connect(self._db_path)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS content_hashes (
                    url TEXT PRIMARY KEY,
                    hash_value TEXT NOT NULL,
                    title TEXT DEFAULT '',
                    content_length INTEGER DEFAULT 0,
                    last_checked TEXT NOT NULL,
                    last_changed TEXT,
                    change_count INTEGER DEFAULT 0
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS change_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    old_hash TEXT,
                    new_hash TEXT NOT NULL,
                    detected_at TEXT NOT NULL,
                    content_diff_summary TEXT DEFAULT ''
                )
            """)
            conn.commit()
            conn.close()

    def compute_hash(self, content: str) -> str:
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def check_changed(self, url: str, content: str, title: str = "") -> tuple[bool, Optional[ContentHash]]:
        new_hash = self.compute_hash(content)
        now = datetime.now().isoformat()

        with self._lock:
            conn = sqlite3.connect(self._db_path)
            row = conn.execute(
                "SELECT hash_value, change_count FROM content_hashes WHERE url = ?", (url,)
            ).fetchone()

            if row is None:
                entry = ContentHash(
                    url=url,
                    hash_value=new_hash,
                    title=title,
                    content_length=len(content),
                    last_checked=now,
                    change_count=0,
                )
                self._insert_hash(conn, entry)
                conn.commit()
                conn.close()
                return True, entry

            old_hash, change_count = row

            if old_hash == new_hash:
                conn.execute(
                    "UPDATE content_hashes SET last_checked = ? WHERE url = ?",
                    (now, url)
                )
                conn.commit()
                conn.close()
                return False, None

            new_change_count = change_count + 1
            conn.execute(
                """UPDATE content_hashes 
                   SET hash_value = ?, last_checked = ?, last_changed = ?, change_count = ?
                   WHERE url = ?""",
                (new_hash, now, now, new_change_count, url)
            )
            conn.execute(
                "INSERT INTO change_log (url, old_hash, new_hash, detected_at) VALUES (?, ?, ?, ?)",
                (url, old_hash, new_hash, now)
            )
            conn.commit()

            entry = ContentHash(
                url=url,
                hash_value=new_hash,
                title=title,
                content_length=len(content),
                last_checked=now,
                last_changed=now,
                change_count=new_change_count,
            )
            conn.close()
            return True, entry

    def _insert_hash(self, conn, entry: ContentHash):
        conn.execute(
            """INSERT OR REPLACE INTO content_hashes 
               (url, hash_value, title, content_length, last_checked, last_changed, change_count)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (entry.url, entry.hash_value, entry.title, entry.content_length,
             entry.last_checked, entry.last_changed, entry.change_count)
        )

    def get_hash(self, url: str) -> Optional[ContentHash]:
        with self._lock:
            conn = sqlite3.connect(self._db_path)
            row = conn.execute(
                "SELECT * FROM content_hashes WHERE url = ?", (url,)
            ).fetchone()
            conn.close()

            if row:
                return ContentHash(
                    url=row[0], hash_value=row[1], title=row[2],
                    content_length=row[3], last_checked=row[4],
                    last_changed=row[5], change_count=row[6],
                )
            return None

    def get_change_history(self, url: str, limit: int = 20) -> list[dict]:
        with self._lock:
            conn = sqlite3.connect(self._db_path)
            rows = conn.execute(
                "SELECT * FROM change_log WHERE url = ? ORDER BY detected_at DESC LIMIT ?",
                (url, limit)
            ).fetchall()
            conn.close()

            return [
                {
                    'id': r[0], 'url': r[1], 'old_hash': r[2],
                    'new_hash': r[3], 'detected_at': r[4], 'summary': r[5],
                }
                for r in rows
            ]

    def get_all_tracked(self) -> list[ContentHash]:
        with self._lock:
            conn = sqlite3.connect(self._db_path)
            rows = conn.execute("SELECT * FROM content_hashes ORDER BY last_checked DESC").fetchall()
            conn.close()

            return [
                ContentHash(
                    url=r[0], hash_value=r[1], title=r[2],
                    content_length=r[3], last_checked=r[4],
                    last_changed=r[5], change_count=r[6],
                )
                for r in rows
            ]

    def remove(self, url: str):
        with self._lock:
            conn = sqlite3.connect(self._db_path)
            conn.execute("DELETE FROM content_hashes WHERE url = ?", (url,))
            conn.execute("DELETE FROM change_log WHERE url = ?", (url,))
            conn.commit()
            conn.close()

    def get_stats(self) -> dict:
        with self._lock:
            conn = sqlite3.connect(self._db_path)
            total = conn.execute("SELECT COUNT(*) FROM content_hashes").fetchone()[0]
            changed = conn.execute(
                "SELECT COUNT(*) FROM content_hashes WHERE change_count > 0"
            ).fetchone()[0]
            conn.close()

            return {
                'total_tracked': total,
                'urls_with_changes': changed,
                'db_path': self._db_path,
            }


incremental_tracker = IncrementalTracker()
