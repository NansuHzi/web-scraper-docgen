import asyncio
import json
import logging
import os
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from croniter import croniter

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent.parent / "data"
JOBS_FILE = DATA_DIR / "scheduler_jobs.json"
HISTORY_FILE = DATA_DIR / "scheduler_history.json"


class SchedulerManager:
    """定时任务管理器 — 支持 cron 和 interval 调度，所有任务在主事件循环上异步执行"""

    def __init__(self):
        self._jobs: dict[str, dict] = {}
        self._history: dict[str, list[dict]] = {}
        self._timers: dict[str, threading.Timer] = {}
        self._lock = threading.Lock()
        self._running = False
        self._main_loop: Optional[asyncio.AbstractEventLoop] = None
        self._active_tasks: set[asyncio.Task] = set()

    def set_event_loop(self, loop: asyncio.AbstractEventLoop):
        """绑定主事件循环（在 FastAPI startup 中调用）"""
        self._main_loop = loop

    def start(self):
        if self._running:
            return
        self._running = True
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._load_jobs()
        self._load_history()
        for job_id, job in self._jobs.items():
            if job.get("enabled", True):
                self._schedule_job(job_id)
        logger.info("SchedulerManager started: %d jobs loaded, %d active",
                     len(self._jobs),
                     sum(1 for j in self._jobs.values() if j.get('enabled', True)))

    def stop(self):
        self._running = False
        with self._lock:
            for timer in self._timers.values():
                timer.cancel()
            self._timers.clear()
        if self._main_loop and not self._main_loop.is_closed():
            for task in list(self._active_tasks):
                if not task.done():
                    task.cancel()
            self._active_tasks.clear()
        logger.info("SchedulerManager stopped")

    def create_job(self, data: dict) -> dict:
        job_id = str(uuid.uuid4())[:8]
        now = datetime.now().isoformat()

        schedule_type = data["schedule_type"]
        if schedule_type == "cron":
            cron_expression = data.get("cron_expression", "")
            if not cron_expression:
                raise ValueError("cron jobs require cron_expression")
            try:
                croniter(cron_expression)
            except Exception:
                raise ValueError(f"Invalid cron expression: {cron_expression}")
            next_run = self._compute_next_cron(cron_expression)
        elif schedule_type == "interval":
            interval_seconds = data.get("interval_seconds", 3600)
            if interval_seconds < 60:
                raise ValueError("interval_seconds must be >= 60")
            next_run = self._compute_next_interval(interval_seconds)
        else:
            raise ValueError(f"Unknown schedule_type: {schedule_type}")

        job = {
            "id": job_id,
            "name": data["name"],
            "url": data["url"],
            "doc_type": data.get("doc_type", "tech_doc"),
            "format": data.get("format", "md"),
            "schedule_type": schedule_type,
            "cron_expression": data.get("cron_expression"),
            "interval_seconds": data.get("interval_seconds"),
            "enabled": data.get("enabled", True),
            "last_run": None,
            "next_run": next_run,
            "total_runs": 0,
            "success_runs": 0,
            "failed_runs": 0,
            "created_at": now,
            "updated_at": now,
        }

        with self._lock:
            self._jobs[job_id] = job
            self._history[job_id] = []

        if job["enabled"]:
            self._schedule_job(job_id)

        self._save_jobs()
        return self._job_to_response(job)

    def update_job(self, job_id: str, data: dict) -> dict | None:
        with self._lock:
            if job_id not in self._jobs:
                return None
            job = self._jobs[job_id]

            if "name" in data:
                job["name"] = data["name"]
            if "url" in data:
                job["url"] = data["url"]
            if "doc_type" in data:
                job["doc_type"] = data["doc_type"]
            if "format" in data:
                job["format"] = data["format"]
            if "cron_expression" in data:
                job["cron_expression"] = data["cron_expression"]
            if "interval_seconds" in data:
                job["interval_seconds"] = data["interval_seconds"]
            if "enabled" in data:
                job["enabled"] = data["enabled"]

            self._cancel_timer(job_id)

            if job["schedule_type"] == "cron" and job.get("cron_expression"):
                try:
                    croniter(job["cron_expression"])
                except Exception:
                    raise ValueError(f"Invalid cron expression: {job['cron_expression']}")
                job["next_run"] = self._compute_next_cron(job["cron_expression"])
            elif job["schedule_type"] == "interval" and job.get("interval_seconds"):
                if job["interval_seconds"] < 60:
                    raise ValueError("interval_seconds must be >= 60")
                job["next_run"] = self._compute_next_interval(job["interval_seconds"])

            job["updated_at"] = datetime.now().isoformat()

        if job["enabled"]:
            self._schedule_job(job_id)

        self._save_jobs()
        return self._job_to_response(job)

    def delete_job(self, job_id: str) -> bool:
        with self._lock:
            if job_id not in self._jobs:
                return False
            self._cancel_timer(job_id)
            del self._jobs[job_id]
            self._history.pop(job_id, None)
        self._save_jobs()
        self._save_history()
        return True

    def get_job(self, job_id: str) -> dict | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            return self._job_to_response(job)

    def list_jobs(self) -> list[dict]:
        with self._lock:
            return [self._job_to_response(j) for j in sorted(
                self._jobs.values(), key=lambda x: x.get("created_at", ""), reverse=True
            )]

    def trigger_job(self, job_id: str) -> str | None:
        with self._lock:
            if job_id not in self._jobs:
                return None
        execution_id = f"exec_{int(datetime.now().timestamp())}"
        self._submit_to_main_loop(job_id, execution_id)
        return execution_id

    def get_history(self, job_id: str, limit: int = 20) -> dict:
        with self._lock:
            records = self._history.get(job_id, [])
            total = len(records)
            return {"history": records[-limit:], "total": total}

    def get_stats(self) -> dict:
        with self._lock:
            total_jobs = len(self._jobs)
            active_jobs = sum(1 for j in self._jobs.values() if j.get("enabled"))
            total_executions = sum(j.get("total_runs", 0) for j in self._jobs.values())
            success = sum(j.get("success_runs", 0) for j in self._jobs.values())
            failed = sum(j.get("failed_runs", 0) for j in self._jobs.values())
            active_now = sum(1 for t in self._active_tasks if not t.done())
            return {
                "total_jobs": total_jobs,
                "active_jobs": active_jobs,
                "total_executions": total_executions,
                "success_executions": success,
                "failed_executions": failed,
                "running_now": active_now,
            }

    def _submit_to_main_loop(self, job_id: str, execution_id: str):
        """将任务提交到主事件循环执行（不阻塞调用线程）"""
        if self._main_loop and not self._main_loop.is_closed():
            future = asyncio.run_coroutine_threadsafe(
                self._execute_job_async(job_id, execution_id), self._main_loop
            )
            def _done_cb(fut):
                try:
                    fut.result()
                except Exception as e:
                    logger.error("Scheduled job [%s] unhandled error: %s", job_id, e)
            future.add_done_callback(_done_cb)
        else:
            logger.warning("Main event loop not available, job [%s] skipped", job_id)

    async def _execute_job_async(self, job_id: str, execution_id: str):
        """在主事件循环上异步执行任务（不创建新循环，不阻塞）"""
        from ..api.scraper import process_document_generation, document_store

        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return

            started_at = datetime.now().isoformat()
            record = {
                "id": execution_id,
                "job_id": job_id,
                "status": "running",
                "started_at": started_at,
                "finished_at": None,
                "duration_ms": None,
                "document_id": None,
                "error_message": None,
            }
            self._history.setdefault(job_id, []).append(record)
            self._save_history()

        document_id = f"doc_{int(datetime.now().timestamp())}"
        started = time.time()

        try:
            await process_document_generation(
                document_id, job["url"], job["doc_type"], job.get("format", "md"), use_qwen=True
            )

            finished_at = datetime.now().isoformat()
            duration_ms = int((time.time() - started) * 1000)

            doc_data = document_store.get(document_id, {})
            if doc_data.get("status") == "failed" or doc_data.get("error"):
                raise Exception(doc_data.get("error", "Document generation failed"))

            with self._lock:
                if job_id in self._jobs:
                    j = self._jobs[job_id]
                    j["last_run"] = finished_at
                    j["total_runs"] = j.get("total_runs", 0) + 1
                    j["success_runs"] = j.get("success_runs", 0) + 1
                    j["updated_at"] = finished_at

                if job_id in self._history:
                    for rec in reversed(self._history[job_id]):
                        if rec["id"] == execution_id:
                            rec["status"] = "success"
                            rec["finished_at"] = finished_at
                            rec["duration_ms"] = duration_ms
                            rec["document_id"] = document_id
                            break

            self._save_jobs()
            self._save_history()
            logger.info("Scheduled job [%s] completed successfully: %s", job_id, document_id)

        except asyncio.CancelledError:
            logger.info("Scheduled job [%s] cancelled", job_id)
            with self._lock:
                if job_id in self._history:
                    for rec in reversed(self._history[job_id]):
                        if rec["id"] == execution_id:
                            rec["status"] = "cancelled"
                            rec["finished_at"] = datetime.now().isoformat()
                            break
            self._save_history()
        except Exception as e:
            error_msg = str(e)
            finished_at = datetime.now().isoformat()
            duration_ms = int((time.time() - started) * 1000)

            with self._lock:
                if job_id in self._jobs:
                    j = self._jobs[job_id]
                    j["last_run"] = finished_at
                    j["total_runs"] = j.get("total_runs", 0) + 1
                    j["failed_runs"] = j.get("failed_runs", 0) + 1
                    j["updated_at"] = finished_at

                if job_id in self._history:
                    for rec in reversed(self._history[job_id]):
                        if rec["id"] == execution_id:
                            rec["status"] = "failed"
                            rec["finished_at"] = finished_at
                            rec["duration_ms"] = duration_ms
                            rec["error_message"] = error_msg
                            break

            self._save_jobs()
            self._save_history()
            logger.error("Scheduled job [%s] failed: %s", job_id, error_msg)

    def _schedule_job(self, job_id: str):
        with self._lock:
            job = self._jobs.get(job_id)
            if not job or not job.get("enabled"):
                return

            if job["schedule_type"] == "cron" and job.get("cron_expression"):
                delay = self._seconds_until_next_cron(job["cron_expression"])
            elif job["schedule_type"] == "interval" and job.get("interval_seconds"):
                delay = job["interval_seconds"]
            else:
                return

            if delay <= 0:
                delay = 60

            timer = threading.Timer(delay, self._on_timer_fire, args=[job_id])
            timer.daemon = True
            self._timers[job_id] = timer
            timer.start()

    def _on_timer_fire(self, job_id: str):
        execution_id = f"exec_{int(datetime.now().timestamp())}"
        self._submit_to_main_loop(job_id, execution_id)
        if self._running:
            self._schedule_job(job_id)

    def _cancel_timer(self, job_id: str):
        timer = self._timers.pop(job_id, None)
        if timer:
            timer.cancel()

    def _compute_next_cron(self, expression: str) -> str:
        c = croniter(expression, datetime.now())
        return c.get_next(datetime).isoformat()

    def _seconds_until_next_cron(self, expression: str) -> float:
        c = croniter(expression, datetime.now())
        next_dt = c.get_next(datetime)
        return max((next_dt - datetime.now()).total_seconds(), 1)

    def _compute_next_interval(self, seconds: int) -> str:
        from datetime import timedelta
        return (datetime.now() + timedelta(seconds=seconds)).isoformat()

    def _job_to_response(self, job: dict) -> dict:
        return {
            "id": job["id"],
            "name": job["name"],
            "url": job["url"],
            "doc_type": job["doc_type"],
            "format": job.get("format", "md"),
            "schedule_type": job["schedule_type"],
            "cron_expression": job.get("cron_expression"),
            "interval_seconds": job.get("interval_seconds"),
            "enabled": job.get("enabled", True),
            "last_run": job.get("last_run"),
            "next_run": job.get("next_run"),
            "total_runs": job.get("total_runs", 0),
            "success_runs": job.get("success_runs", 0),
            "failed_runs": job.get("failed_runs", 0),
            "created_at": job["created_at"],
            "updated_at": job["updated_at"],
        }

    def _save_jobs(self):
        try:
            with self._lock:
                jobs_data = {jid: self._serialize_job(j) for jid, j in self._jobs.items()}
            with open(JOBS_FILE, "w", encoding="utf-8") as f:
                json.dump(jobs_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error("Failed to save scheduler jobs: %s", e)

    def _load_jobs(self):
        if not JOBS_FILE.exists():
            return
        try:
            with open(JOBS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            with self._lock:
                self._jobs = {jid: self._deserialize_job(j) for jid, j in data.items()}
        except Exception as e:
            logger.error("Failed to load scheduler jobs: %s", e)

    def _save_history(self):
        try:
            with self._lock:
                history_data = dict(self._history)
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(history_data, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            logger.error("Failed to save scheduler history: %s", e)

    def _load_history(self):
        if not HISTORY_FILE.exists():
            return
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            with self._lock:
                self._history = data
        except Exception as e:
            logger.error("Failed to load scheduler history: %s", e)

    @staticmethod
    def _serialize_job(job: dict) -> dict:
        return {k: v for k, v in job.items() if k not in ("_timer",)}

    @staticmethod
    def _deserialize_job(job: dict) -> dict:
        return job


scheduler_manager = SchedulerManager()
