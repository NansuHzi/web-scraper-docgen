import json
import os
import sqlite3
import threading
from datetime import datetime
from typing import Optional

from .models import Task, TaskStatus, TaskPriority, TaskType


class TaskStore:
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                'data', 'task_store.db'
            )

        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        with self._lock:
            conn = sqlite3.connect(self._db_path)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    task_type TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    priority INTEGER NOT NULL DEFAULT 1,
                    payload TEXT NOT NULL DEFAULT '{}',
                    result TEXT,
                    error_message TEXT,
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    finished_at TEXT,
                    retry_count INTEGER NOT NULL DEFAULT 0,
                    max_retries INTEGER NOT NULL DEFAULT 3,
                    user_id TEXT,
                    session_id TEXT,
                    progress REAL NOT NULL DEFAULT 0.0,
                    progress_message TEXT NOT NULL DEFAULT ''
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_user ON tasks(user_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_created ON tasks(created_at)
            """)
            conn.commit()
            conn.close()

    def save(self, task: Task):
        with self._lock:
            conn = sqlite3.connect(self._db_path)
            conn.execute(
                """INSERT OR REPLACE INTO tasks 
                   (id, task_type, status, priority, payload, result, error_message,
                    created_at, started_at, finished_at, retry_count, max_retries,
                    user_id, session_id, progress, progress_message)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    task.id, task.task_type.value, task.status.value, task.priority.value,
                    json.dumps(task.payload, ensure_ascii=False),
                    json.dumps(task.result, ensure_ascii=False) if task.result else None,
                    task.error_message,
                    task.created_at, task.started_at, task.finished_at,
                    task.retry_count, task.max_retries,
                    task.user_id, task.session_id,
                    task.progress, task.progress_message,
                )
            )
            conn.commit()
            conn.close()

    def get(self, task_id: str) -> Optional[Task]:
        with self._lock:
            conn = sqlite3.connect(self._db_path)
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
            conn.close()

            if row is None:
                return None
            return self._row_to_task(row)

    def get_by_user(self, user_id: str, limit: int = 50) -> list[Task]:
        with self._lock:
            conn = sqlite3.connect(self._db_path)
            rows = conn.execute(
                "SELECT * FROM tasks WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                (user_id, limit)
            ).fetchall()
            conn.close()
            return [self._row_to_task(r) for r in rows]

    def get_pending(self, limit: int = 10) -> list[Task]:
        with self._lock:
            conn = sqlite3.connect(self._db_path)
            rows = conn.execute(
                """SELECT * FROM tasks 
                   WHERE status IN ('pending', 'queued', 'retrying')
                   ORDER BY priority DESC, created_at ASC 
                   LIMIT ?""",
                (limit,)
            ).fetchall()
            conn.close()
            return [self._row_to_task(r) for r in rows]

    def get_active(self) -> list[Task]:
        with self._lock:
            conn = sqlite3.connect(self._db_path)
            rows = conn.execute(
                "SELECT * FROM tasks WHERE status IN ('queued', 'running', 'retrying')"
            ).fetchall()
            conn.close()
            return [self._row_to_task(r) for r in rows]

    def update_status(self, task_id: str, status: TaskStatus, **kwargs):
        with self._lock:
            conn = sqlite3.connect(self._db_path)
            updates = ["status = ?"]
            params = [status.value]

            for key, value in kwargs.items():
                if key in ('started_at', 'finished_at', 'error_message', 'progress', 'progress_message', 'retry_count', 'result'):
                    updates.append(f"{key} = ?")
                    if key == 'result' and value is not None:
                        params.append(json.dumps(value, ensure_ascii=False))
                    else:
                        params.append(value)

            params.append(task_id)
            conn.execute(
                f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?",
                params
            )
            conn.commit()
            conn.close()

    def delete(self, task_id: str):
        with self._lock:
            conn = sqlite3.connect(self._db_path)
            conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            conn.commit()
            conn.close()

    def get_stats(self) -> dict:
        with self._lock:
            conn = sqlite3.connect(self._db_path)
            total = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
            by_status = {}
            for row in conn.execute("SELECT status, COUNT(*) FROM tasks GROUP BY status").fetchall():
                by_status[row[0]] = row[1]
            conn.close()

            return {
                'total': total,
                'by_status': by_status,
                'db_path': self._db_path,
            }

    def _row_to_task(self, row) -> Task:
        payload = json.loads(row[4]) if row[4] else {}
        result = json.loads(row[5]) if row[5] else None

        return Task(
            id=row[0],
            task_type=TaskType(row[1]),
            status=TaskStatus(row[2]),
            priority=TaskPriority(row[3]),
            payload=payload,
            result=result,
            error_message=row[6],
            created_at=row[7],
            started_at=row[8],
            finished_at=row[9],
            retry_count=row[10],
            max_retries=row[11],
            user_id=row[12],
            session_id=row[13],
            progress=row[14],
            progress_message=row[15],
        )


task_store = TaskStore()
