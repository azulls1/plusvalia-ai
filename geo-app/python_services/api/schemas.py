"""Pydantic schemas for the ML API."""

from pydantic import BaseModel, Field
from typing import Optional, Dict


class PredictionRequest(BaseModel):
    """Request para predicción de precio y plusvalía."""
    lat: float = Field(..., description="Latitud", ge=-90, le=90)
    lon: float = Field(..., description="Longitud", ge=-180, le=180)
    area_m2: float = Field(..., description="Superficie en m²", gt=0)
    city: str = Field(..., description="Ciudad")
    state: str = Field(..., description="Estado")

    class Config:
        json_schema_extra = {
            "example": {
                "lat": 20.5888,
                "lon": -100.3899,
                "area_m2": 500,
                "city": "Querétaro",
                "state": "Querétaro",
            }
        }


class InferenceCost(BaseModel):
    """Cost breakdown for a single inference."""
    inference_ms: float
    estimated_cost_usd: float
    cost_model: str
    note: str


class PredictionResponse(BaseModel):
    """Response con predicción."""
    predicted_price_m2: float
    predicted_total_price: float
    plusvalia_score: float
    growth_potential: str
    confidence: float
    model_version: str
    features_used: Dict
    prediction_id: Optional[int] = None
    timestamp: str
    inference_ms: Optional[float] = None
    cost_info: Optional[InferenceCost] = None


class ExplainResponse(BaseModel):
    """Response con explicación SHAP de una predicción."""
    predicted_price_m2: float
    base_value: float
    feature_explanations: list
    top_positive_factors: list
    top_negative_factors: list
    model_version: str
    explanation_method: str


class TrainRequest(BaseModel):
    """Request para re-entrenar el modelo."""
    min_samples: Optional[int] = 100
    force_retrain: bool = False


class HealthResponse(BaseModel):
    """Response de health check."""
    status: str
    model_loaded: bool
    model_version: Optional[str] = None
    api_version: str
    timestamp: str
    database: Optional[str] = None
    memory_percent: Optional[float] = None
    disk_percent: Optional[float] = None
