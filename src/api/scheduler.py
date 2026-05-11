from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Literal
from ..adapters.scheduler_manager import scheduler_manager

router = APIRouter()


class ScheduleJobCreate(BaseModel):
    name: str
    url: str
    doc_type: str = "tech_doc"
    format: str = "md"
    schedule_type: Literal["cron", "interval"]
    cron_expression: Optional[str] = None
    interval_seconds: Optional[int] = None
    enabled: bool = True


class ScheduleJobUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    doc_type: Optional[str] = None
    format: Optional[str] = None
    cron_expression: Optional[str] = None
    interval_seconds: Optional[int] = None
    enabled: Optional[bool] = None


@router.post("/scheduler/jobs")
async def create_job(request: ScheduleJobCreate):
    try:
        valid_doc_types = ["tech_doc", "api_doc", "readme", "summary"]
        if request.doc_type not in valid_doc_types:
            raise ValueError(f"Invalid doc_type. Must be one of: {', '.join(valid_doc_types)}")

        valid_formats = ["md", "txt", "ppt"]
        if request.format not in valid_formats:
            raise ValueError(f"Invalid format. Must be one of: {', '.join(valid_formats)}")

        if request.schedule_type == "interval" and (not request.interval_seconds or request.interval_seconds < 60):
            raise ValueError("interval_seconds must be >= 60")

        if request.schedule_type == "cron" and not request.cron_expression:
            raise ValueError("cron jobs require cron_expression")

        job = scheduler_manager.create_job(request.model_dump())
        return {"success": True, "job": job}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scheduler/jobs")
async def list_jobs():
    try:
        jobs = scheduler_manager.list_jobs()
        return {"jobs": jobs, "total": len(jobs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scheduler/jobs/{job_id}")
async def get_job(job_id: str):
    job = scheduler_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job": job}


@router.put("/scheduler/jobs/{job_id}")
async def update_job(job_id: str, request: ScheduleJobUpdate):
    try:
        update_data = request.model_dump(exclude_none=True)
        if not update_data:
            raise ValueError("No fields to update")

        if "doc_type" in update_data:
            valid_doc_types = ["tech_doc", "api_doc", "readme", "summary"]
            if update_data["doc_type"] not in valid_doc_types:
                raise ValueError(f"Invalid doc_type")

        if "format" in update_data:
            valid_formats = ["md", "txt", "ppt"]
            if update_data["format"] not in valid_formats:
                raise ValueError(f"Invalid format")

        job = scheduler_manager.update_job(job_id, update_data)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return {"success": True, "job": job}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/scheduler/jobs/{job_id}")
async def delete_job(job_id: str):
    deleted = scheduler_manager.delete_job(job_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"success": True}


@router.post("/scheduler/jobs/{job_id}/trigger")
async def trigger_job(job_id: str):
    execution_id = scheduler_manager.trigger_job(job_id)
    if not execution_id:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"success": True, "execution_id": execution_id}


@router.get("/scheduler/jobs/{job_id}/history")
async def get_job_history(job_id: str, limit: int = 20):
    job = scheduler_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return scheduler_manager.get_history(job_id, limit)


@router.get("/scheduler/stats")
async def get_stats():
    return scheduler_manager.get_stats()
