from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from ..worker.models import TaskType, TaskPriority
from ..worker.dispatcher import task_dispatcher
from ..worker.store import task_store

router = APIRouter()


class SubmitTaskRequest(BaseModel):
    task_type: str
    payload: dict
    priority: str = "normal"
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    max_retries: int = 3


@router.post("/tasks/submit")
async def submit_task(request: SubmitTaskRequest):
    try:
        try:
            task_type = TaskType(request.task_type)
        except ValueError:
            valid_types = [t.value for t in TaskType]
            raise HTTPException(status_code=400, detail=f"无效的任务类型。可选: {valid_types}")

        try:
            priority = TaskPriority[request.priority.upper()]
        except KeyError:
            priority = TaskPriority.NORMAL

        task = await task_dispatcher.submit(
            task_type=task_type,
            payload=request.payload,
            priority=priority,
            user_id=request.user_id,
            session_id=request.session_id,
            max_retries=request.max_retries,
        )

        return {
            "success": True,
            "task": task.to_dict(),
            "message": f"任务已提交: {task.id}",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"提交任务失败: {str(e)}")


@router.get("/tasks/{task_id}")
async def get_task(task_id: str):
    task = task_store.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")

    return {"task": task.to_dict()}


@router.get("/tasks")
async def list_tasks(
    user_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    try:
        if user_id:
            tasks = task_store.get_by_user(user_id, limit)
        else:
            tasks = task_store.get_pending(limit)
            tasks += task_store.get_active()

        if status:
            from ..worker.models import TaskStatus
            try:
                status_enum = TaskStatus(status)
                tasks = [t for t in tasks if t.status == status_enum]
            except ValueError:
                pass

        return {
            "tasks": [t.to_dict() for t in tasks[:limit]],
            "total": len(tasks),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务列表失败: {str(e)}")


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(task_id: str):
    success = await task_dispatcher.cancel_task(task_id)
    if not success:
        raise HTTPException(status_code=400, detail="无法取消任务（可能已完成或不存在）")

    return {"success": True, "message": f"任务已取消: {task_id}"}


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    task = task_store.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")

    if not task.is_terminal:
        await task_dispatcher.cancel_task(task_id)

    task_store.delete(task_id)
    return {"success": True, "message": f"任务已删除: {task_id}"}


@router.get("/tasks/stats")
async def get_task_stats():
    stats = task_store.get_stats()
    queue_length = task_dispatcher.get_queue_length()
    active_count = task_dispatcher.get_active_count()

    return {
        **stats,
        "queue_length": queue_length,
        "active_count": active_count,
    }
