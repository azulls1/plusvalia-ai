"""Stats and health endpoints for the ML API."""

from fastapi import APIRouter, HTTPException
from datetime import datetime
from loguru import logger

from api.deps import model, supabase
from api.schemas import HealthResponse

router = APIRouter(tags=["General"])


@router.get("/", tags=["General"])
async def root():
    """Endpoint raíz."""
    return {
        "message": "API de Análisis de Mercado Inmobiliario",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Enhanced health check with dependency verification."""
    import psutil

    checks = {
        "model_loaded": model.price_model is not None,
        "model_version": model.model_version,
        "api_version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
    }

    # Check Supabase connectivity
    try:
        result = supabase.table("iainmobiliaria_predictions").select("id").limit(1).execute()
        checks["database"] = "connected"
    except Exception as e:
        checks["database"] = f"error: {str(e)[:100]}"

    # Check Redis
    try:
        from middleware.redis_client import get_redis
        r = get_redis()
        checks["redis"] = "connected" if r and r.ping() else "not_available"
    except Exception:
        checks["redis"] = "not_available"

    # System resources
    checks["memory_percent"] = psutil.virtual_memory().percent
    checks["disk_percent"] = psutil.disk_usage('/').percent

    # Overall status
    healthy = checks["model_loaded"] and checks.get("database") == "connected"
    checks["status"] = "healthy" if healthy else "degraded"

    return checks


@router.get("/stats", tags=["Statistics"])
async def get_statistics():
    """Obtiene estadísticas generales del sistema."""
    try:
        comparables_response = supabase.table("iainmobiliaria_comparables").select("*", count="exact").execute()
        predictions_response = supabase.table("iainmobiliaria_predictions").select("*", count="exact").execute()
        amenities_response = supabase.table("iainmobiliaria_amenities").select("*", count="exact").execute()
    except Exception as e:  # Supabase client may raise various errors
        logger.error(f"Error obteniendo estadísticas: {e}")
        raise HTTPException(status_code=500, detail="Error consultando estadísticas del sistema")

    return {
        "comparables": len(comparables_response.data) if comparables_response.data else 0,
        "predictions": len(predictions_response.data) if predictions_response.data else 0,
        "amenities": len(amenities_response.data) if amenities_response.data else 0,
        "model_loaded": model.price_model is not None,
        "model_version": model.model_version,
        "timestamp": datetime.now().isoformat(),
    }
