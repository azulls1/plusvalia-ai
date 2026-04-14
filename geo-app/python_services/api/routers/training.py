"""Training endpoints for the ML API."""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from loguru import logger
import pandas as pd

from api.deps import model, supabase
from api.schemas import TrainRequest
from middleware.auth import verify_api_key

router = APIRouter(tags=["Model Management"])


@router.post("/train")
async def train_model(request: TrainRequest, background_tasks: BackgroundTasks, api_key: str = Depends(verify_api_key)):
    """Entrena o re-entrena el modelo con datos de Supabase."""
    logger.info("Iniciando entrenamiento del modelo")

    if model.price_model is not None and not request.force_retrain:
        return {
            "message": "Modelo ya entrenado. Usar force_retrain=true para re-entrenar",
            "model_version": model.model_version,
            "status": "skipped",
        }

    try:
        logger.info("Obteniendo datos de entrenamiento...")
        response = supabase.table("iainmobiliaria_comparables").select("*").execute()
    except Exception as e:  # Supabase client may raise various errors
        logger.error(f"Error conectando a Supabase: {e}")
        raise HTTPException(status_code=503, detail="Error conectando a la base de datos")

    if not response.data or len(response.data) < request.min_samples:
        raise HTTPException(
            status_code=400,
            detail=f"Datos insuficientes. Se requieren al menos {request.min_samples} muestras.",
        )

    df = pd.DataFrame(response.data)
    logger.info(f"Datos obtenidos: {len(df)} registros")

    try:
        metrics = model.train(df)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    logger.info("Modelo entrenado exitosamente")
    return {"message": "Modelo entrenado exitosamente", "model_version": model.model_version, "metrics": metrics, "status": "success"}
