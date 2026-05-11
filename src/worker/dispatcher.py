import asyncio
import uuid
from datetime import datetime
from typing import Optional, Callable, Awaitable

from .models import Task, TaskStatus, TaskPriority, TaskType
from .store import task_store


class TaskDispatcher:
    def __init__(self, max_concurrent: int = 3):
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._max_concurrent = max_concurrent
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._running = False
        self._active_tasks: dict[str, asyncio.Task] = {}
        self._handlers: dict[TaskType, Callable[[Task], Awaitable[None]]] = {}
        self._on_complete: Optional[Callable[[Task], Awaitable[None]]] = None

    def register_handler(self, task_type: TaskType, handler: Callable[[Task], Awaitable[None]]):
        self._handlers[task_type] = handler

    def on_task_complete(self, callback: Callable[[Task], Awaitable[None]]):
        self._on_complete = callback

    async def submit(
        self,
        task_type: TaskType,
        payload: dict,
        priority: TaskPriority = TaskPriority.NORMAL,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        max_retries: int = 3,
    ) -> Task:
        task = Task(
            id=f"task_{uuid.uuid4().hex[:12]}",
            task_type=task_type,
            status=TaskStatus.PENDING,
            priority=priority,
            payload=payload,
            user_id=user_id,
            session_id=session_id,
            max_retries=max_retries,
        )

        task_store.save(task)
        await self._queue.put((-priority.value, task.created_at, task))
        return task

    async def start(self):
        self._running = True
        asyncio.create_task(self._process_queue())

    async def stop(self):
        self._running = False
        for task in self._active_tasks.values():
            task.cancel()

    async def _process_queue(self):
        while self._running:
            try:
                _, _, task = await asyncio.wait_for(self._queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue

            async with self._semaphore:
                if task.status == TaskStatus.CANCELLED:
                    continue

                coro = self._execute_task(task)
                async_task = asyncio.create_task(coro)
                self._active_tasks[task.id] = async_task

    async def _execute_task(self, task: Task):
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now().isoformat()
        task_store.update_status(task.id, TaskStatus.RUNNING, started_at=task.started_at)

        try:
            handler = self._handlers.get(task.task_type)
            if handler is None:
                raise ValueError(f"No handler registered for task type: {task.task_type}")

            await handler(task)

            task.status = TaskStatus.COMPLETED
            task.finished_at = datetime.now().isoformat()
            task.progress = 1.0
            task_store.update_status(
                task.id, TaskStatus.COMPLETED,
                finished_at=task.finished_at,
                progress=1.0,
                result=task.result,
            )

        except Exception as e:
            task.error_message = str(e)

            if task.can_retry:
                task.retry_count += 1
                task.status = TaskStatus.RETRYING
                task_store.update_status(
                    task.id, TaskStatus.RETRYING,
                    retry_count=task.retry_count,
                    error_message=task.error_message,
                )
                await self._queue.put((-task.priority.value, task.created_at, task))
            else:
                task.status = TaskStatus.FAILED
                task.finished_at = datetime.now().isoformat()
                task_store.update_status(
                    task.id, TaskStatus.FAILED,
                    finished_at=task.finished_at,
                    error_message=task.error_message,
                )

        finally:
            self._active_tasks.pop(task.id, None)

            if self._on_complete:
                try:
                    await self._on_complete(task)
                except Exception:
                    pass

    async def cancel_task(self, task_id: str) -> bool:
        task = task_store.get(task_id)
        if task is None:
            return False

        if task.is_terminal:
            return False

        task.status = TaskStatus.CANCELLED
        task.finished_at = datetime.now().isoformat()
        task_store.update_status(task.id, TaskStatus.CANCELLED, finished_at=task.finished_at)

        active = self._active_tasks.pop(task_id, None)
        if active:
            active.cancel()

        return True

    def get_queue_length(self) -> int:
        return self._queue.qsize()

    def get_active_count(self) -> int:
        return len(self._active_tasks)


task_dispatcher = TaskDispatcher(max_concurrent=3)
