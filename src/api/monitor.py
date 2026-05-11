import time
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Request

router = APIRouter()

STARTUP_TIME = time.time()


@router.get("/monitor/dashboard")
async def get_dashboard(http_request: Request):
    """系统概览仪表盘 — 聚合全部运行时统计数据"""
    now = datetime.now().isoformat()

    return {
        "system": _get_system_info(),
        "documents": _get_document_stats(),
        "scheduler": _get_scheduler_stats(),
        "cache": _get_cache_stats(),
        "rag": _get_rag_stats(),
        "sessions": _get_session_stats(),
        "recent": _get_recent_activity(),
        "generated_at": now,
    }


def _get_system_info() -> dict:
    import platform
    uptime_seconds = int(time.time() - STARTUP_TIME)
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return {
        "python_version": platform.python_version(),
        "platform": platform.system(),
        "uptime_seconds": uptime_seconds,
        "uptime_display": f"{hours}h {minutes}m {seconds}s",
        "started_at": datetime.fromtimestamp(STARTUP_TIME).isoformat(),
    }


def _get_document_stats() -> dict:
    try:
        from ..api.scraper import document_store
        total = len(document_store)
        completed = sum(1 for d in document_store.values() if d.get("status") == "completed")
        failed = sum(1 for d in document_store.values() if d.get("status") == "failed")
        processing = sum(1 for d in document_store.values() if d.get("status") == "processing")
        cached = sum(1 for d in document_store.values() if d.get("from_cache"))

        doc_types = {}
        formats = {}
        for d in document_store.values():
            dt = d.get("doc_type", "unknown")
            doc_types[dt] = doc_types.get(dt, 0) + 1
            fmt = d.get("format", "md")
            formats[fmt] = formats.get(fmt, 0) + 1

        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "processing": processing,
            "cached": cached,
            "doc_types": doc_types,
            "formats": formats,
        }
    except Exception as e:
        return {"error": str(e), "total": 0}


def _get_scheduler_stats() -> dict:
    try:
        from ..adapters.scheduler_manager import scheduler_manager
        stats = scheduler_manager.get_stats()
        jobs = scheduler_manager.list_jobs()
        stats["jobs"] = jobs[:10]
        return stats
    except Exception as e:
        return {"error": str(e), "total_jobs": 0}


def _get_cache_stats() -> dict:
    try:
        from ..adapters.document_cache import document_cache
        return document_cache.get_stats()
    except Exception as e:
        return {"error": str(e), "total_entries": 0}


def _get_rag_stats() -> dict:
    try:
        from ..api.rag import rag_store_status
        total = len(rag_store_status)
        total_chunks = sum(s.get("chunk_count", 0) for s in rag_store_status.values())
        return {
            "total_stores": total,
            "total_chunks": total_chunks,
            "recent": sorted(
                rag_store_status.values(),
                key=lambda x: x.get("created_at", ""),
                reverse=True,
            )[:5],
        }
    except Exception as e:
        return {"error": str(e), "total_stores": 0}


def _get_session_stats() -> dict:
    try:
        from ..adapters.session_manager import session_manager
        with session_manager._lock:
            total = len(session_manager._sessions)
            ips = list({s.get("client_ip", "unknown") for s in session_manager._sessions.values()})
            now = datetime.now()
            active_24h = sum(
                1 for s in session_manager._sessions.values()
                if now - s.get("last_access", now) < session_manager._session_ttl
            )
        return {"total_sessions": total, "unique_ips": len(ips), "active_24h": active_24h}
    except Exception as e:
        return {"error": str(e), "total_sessions": 0}


def _get_recent_activity() -> dict:
    recent_docs = []
    try:
        from ..api.scraper import document_store
        sorted_docs = sorted(
            document_store.items(),
            key=lambda x: x[1].get("created_at", ""),
            reverse=True,
        )
        for doc_id, data in sorted_docs[:10]:
            recent_docs.append({
                "document_id": doc_id,
                "url": data.get("url", ""),
                "doc_type": data.get("doc_type", ""),
                "status": data.get("status", ""),
                "created_at": data.get("created_at", ""),
                "from_cache": data.get("from_cache", False),
            })
    except Exception:
        pass

    recent_executions = []
    try:
        from ..adapters.scheduler_manager import scheduler_manager
        with scheduler_manager._lock:
            all_history = []
            for job_id, records in scheduler_manager._history.items():
                job = scheduler_manager._jobs.get(job_id, {})
                for r in records:
                    r_copy = dict(r)
                    r_copy["job_name"] = job.get("name", job_id)
                    all_history.append(r_copy)
            sorted_history = sorted(
                all_history,
                key=lambda x: x.get("started_at", ""),
                reverse=True,
            )
            for h in sorted_history[:10]:
                recent_executions.append({
                    "job_name": h.get("job_name", ""),
                    "status": h.get("status", ""),
                    "started_at": h.get("started_at", ""),
                    "duration_ms": h.get("duration_ms"),
                    "error_message": h.get("error_message"),
                })
    except Exception:
        pass

    return {
        "recent_documents": recent_docs,
        "recent_executions": recent_executions,
    }
