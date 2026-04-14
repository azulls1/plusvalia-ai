"""
API FastAPI — Servicio de Predicciones ML

Thin app factory that imports routers and configures middleware.
"""

import os
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from pathlib import Path

sys.path.append("..")

from config import API_HOST, API_PORT

# ==================== APP CONFIGURATION ====================

PRODUCTION = os.getenv("ENVIRONMENT", "development").lower() == "production"

app = FastAPI(
    title="Análisis de Mercado Inmobiliario - API ML",
    description="API para predicción de plusvalía y análisis de terrenos",
    version="1.0.0",
    docs_url="/docs" if not PRODUCTION else None,
    redoc_url="/redoc" if not PRODUCTION else None,
)

# CORS
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS", "http://localhost:4200,http://localhost:52130"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],
)

# Security middleware
from middleware.security import (
    SecurityHeadersMiddleware,
    RequestSizeLimitMiddleware,
    ContentTypeValidationMiddleware,
    RateLimitMiddleware,
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestSizeLimitMiddleware, max_body_size=5 * 1024 * 1024)
app.add_middleware(ContentTypeValidationMiddleware)
app.add_middleware(RateLimitMiddleware, max_requests=200, window_seconds=60)

# ==================== PROMETHEUS METRICS ====================

from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
    should_respect_env_var=False,
    excluded_handlers=["/health", "/metrics"],
    env_var_name="ENABLE_METRICS",
).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

# ==================== ROUTERS ====================

from api.routers.stats import router as stats_router
from api.routers.predictions import router as predictions_router
from api.routers.training import router as training_router
from api.routers.tasks import router as tasks_router

app.include_router(stats_router)
app.include_router(predictions_router)
app.include_router(training_router)
app.include_router(tasks_router)

# ==================== STARTUP ====================


@app.on_event("startup")
async def check_redis():
    """Check Redis connectivity on startup."""
    from middleware.redis_client import is_redis_available
    if is_redis_available():
        logger.info("Redis connection OK")
    else:
        logger.warning("Redis not available — using in-memory fallback for cache and rate limiting")


@app.on_event("startup")
async def startup_event():
    """Inicialización al arrancar la API."""
    from api.deps import model

    logger.info("Iniciando API de Predicciones ML")
    try:
        base_dir = Path("/app")
        models_dir = base_dir / "ml_model" / "models"
        if models_dir.exists():
            model_files = list(models_dir.glob("plusvalia_model_*.pkl"))
            if model_files:
                latest_model = sorted(model_files)[-1]
                model.load_model(str(latest_model))
                logger.info(f"Modelo cargado: {latest_model.name}")
            else:
                logger.warning("No se encontró modelo pre-entrenado")
        else:
            logger.warning(f"Directorio de modelos no existe: {models_dir}")
    except FileNotFoundError as e:
        logger.error(f"Archivo de modelo no encontrado: {e}")
    except Exception as e:  # Intentional broad catch: top-level startup handler
        logger.error(f"Error cargando modelo: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Graceful shutdown handler."""
    logger.info("Application shutting down gracefully...")
    # Flush any pending analytics/logs


# ==================== MAIN ====================

if __name__ == "__main__":
    import uvicorn

    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO",
    )

    # File-based audit logging
    LOG_DIR = Path(__file__).parent.parent / "logs"
    LOG_DIR.mkdir(exist_ok=True)
    logger.add(
        str(LOG_DIR / "api_{time:YYYY-MM-DD}.log"),
        rotation="1 day",
        retention="30 days",
        compression="gz",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
    )

    logger.info(f"Iniciando servidor en {API_HOST}:{API_PORT}")

    uvicorn.run(
        "main:app",
        host=API_HOST,
        port=API_PORT,
        reload=True,
        log_level="info",
    )
