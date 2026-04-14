"""
API routes for Celery task management.
Allows triggering and monitoring background tasks.
"""
from fastapi import APIRouter, Depends
from loguru import logger

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/train")
async def start_training(force: bool = False):
    """Start model training as background task."""
    try:
        from tasks.training_tasks import train_model
        task = train_model.delay(force_retrain=force)
        return {"task_id": task.id, "status": "queued", "check_url": f"/tasks/status/{task.id}"}
    except Exception as e:
        return {"status": "error", "message": f"Could not queue task: {e}. Is Redis/Celery running?"}


@router.post("/predict-batch")
async def start_batch_predictions(limit: int = 5000):
    """Generate batch predictions as background task."""
    try:
        from tasks.training_tasks import generate_predictions
        task = generate_predictions.delay(limit=limit)
        return {"task_id": task.id, "status": "queued"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/enrich")
async def start_enrichment(limit: int = 5000, batch_size: int = 100):
    """Start feature enrichment as background task."""
    try:
        from tasks.enrichment_tasks import enrich_all
        task = enrich_all.delay(batch_size=batch_size, limit=limit)
        return {"task_id": task.id, "status": "queued"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """Get status of a background task."""
    try:
        from celery.result import AsyncResult
        from celery_app import app as celery_app
        result = AsyncResult(task_id, app=celery_app)
        return {
            "task_id": task_id,
            "status": result.status,
            "ready": result.ready(),
            "result": result.result if result.ready() else None,
            "info": str(result.info) if result.info and not result.ready() else None,
        }
    except Exception as e:
        return {"task_id": task_id, "status": "unknown", "error": str(e)}


@router.get("/active")
async def get_active_tasks():
    """List active Celery tasks."""
    try:
        from celery_app import app as celery_app
        inspector = celery_app.control.inspect()
        active = inspector.active() or {}
        scheduled = inspector.scheduled() or {}
        return {
            "active": {k: len(v) for k, v in active.items()},
            "scheduled": {k: len(v) for k, v in scheduled.items()},
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/redis-status")
async def redis_status():
    """Check Redis connection and stats."""
    try:
        from middleware.redis_client import get_redis
        r = get_redis()
        if r:
            info = r.info(section="memory")
            return {
                "status": "connected",
                "used_memory_human": info.get("used_memory_human", "unknown"),
                "connected_clients": r.info(section="clients").get("connected_clients", 0),
                "keys": r.dbsize(),
            }
        return {"status": "not_available"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
