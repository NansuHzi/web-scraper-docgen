from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any


class TaskStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class TaskPriority(int, Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3


class TaskType(str, Enum):
    CRAWL_SINGLE = "crawl_single"
    CRAWL_BATCH = "crawl_batch"
    GENERATE_DOCUMENT = "generate_document"
    BUILD_RAG = "build_rag"
    HOT_TOPICS = "hot_topics"


@dataclass
class Task:
    id: str
    task_type: TaskType
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.NORMAL
    payload: dict = field(default_factory=dict)
    result: Optional[Any] = None
    error_message: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    progress: float = 0.0
    progress_message: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "task_type": self.task_type.value,
            "status": self.status.value,
            "priority": self.priority.value,
            "payload": self.payload,
            "result": self.result,
            "error_message": self.error_message,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "progress": self.progress,
            "progress_message": self.progress_message,
        }

    @property
    def is_terminal(self) -> bool:
        return self.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED)

    @property
    def can_retry(self) -> bool:
        return self.retry_count < self.max_retries and self.status == TaskStatus.FAILED
