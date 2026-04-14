# ================================================================
# TEST API DEMO - API de predicciones SIN modelo ML entrenado
# Para demostración cuando no hay suficientes datos
# ================================================================

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict
from datetime import datetime
import sys

# Importar configuración
sys.path.append('.')
from config import API_HOST, API_PORT

app = FastAPI(
    title="API ML - Modo Demo",
    description="API de predicciones (modo demostración sin modelo entrenado)",
    version="1.0.0-demo"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PredictionRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    area_m2: float = Field(..., gt=0)
    city: str
    state: str

class PredictionResponse(BaseModel):
    predicted_price_m2: float
    predicted_total_price: float
    plusvalia_score: float
    growth_potential: str
    confidence: float
    model_version: str
    features_used: Dict
    prediction_id: int = None
    timestamp: str
    is_demo: bool = True

@app.get("/")
async def root():
    return {
        "message": "API ML - Modo Demo",
        "status": "demo_mode",
        "note": "Usando predicciones simuladas. Cargar más datos para entrenar modelo real.",
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "model_loaded": False,
        "model_version": "demo",
        "api_version": "1.0.0-demo",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """
    Predice precio usando algoritmo simple (sin ML real)
    """
    # Precios base por ciudad (MXN/m²)
    city_prices = {
        "querétaro": 8500,
        "guadalajara": 9200,
        "monterrey": 12000,
        "ciudad de méxico": 15000,
        "puebla": 6500,
        "león": 7000
    }
    
    # Obtener precio base
    city_key = request.city.lower()
    base_price = city_prices.get(city_key, 8000)
    
    # Ajustar por área (lotes grandes más baratos por m²)
    if request.area_m2 > 1000:
        area_factor = 0.85
    elif request.area_m2 > 500:
        area_factor = 0.95
    else:
        area_factor = 1.0
    
    # Calcular precio estimado
    predicted_price_m2 = base_price * area_factor
    predicted_total = predicted_price_m2 * request.area_m2
    
    # Calcular score de plusvalía (simulado)
    plusvalia_score = min(100, (predicted_price_m2 / 8000) * 50 + 30)
    
    # Categorizar potencial
    if plusvalia_score >= 75:
        growth_potential = 'muy_alto'
    elif plusvalia_score >= 60:
        growth_potential = 'alto'
    elif plusvalia_score >= 40:
        growth_potential = 'medio'
    else:
        growth_potential = 'bajo'
    
    return PredictionResponse(
        predicted_price_m2=round(predicted_price_m2, 2),
        predicted_total_price=round(predicted_total, 2),
        plusvalia_score=round(plusvalia_score, 2),
        growth_potential=growth_potential,
        confidence=50.0,  # Baja confianza en demo
        model_version="demo-1.0",
        features_used={
            "area_m2": request.area_m2,
            "city": request.city,
            "state": request.state,
            "base_price": base_price
        },
        timestamp=datetime.now().isoformat(),
        is_demo=True
    )

@app.get("/stats")
async def stats():
    return {
        "message": "Estadísticas no disponibles en modo demo",
        "model_loaded": False,
        "demo_mode": True
    }

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 50)
    print("API ML - MODO DEMO")
    print("=" * 50)
    print(f"URL: http://{API_HOST}:{API_PORT}")
    print(f"Docs: http://{API_HOST}:{API_PORT}/docs")
    print("")
    print("NOTA: Usando predicciones simuladas")
    print("Cargar mas datos para entrenar modelo real")
    print("=" * 50)
    
    uvicorn.run(
        "test_api_demo:app",
        host=API_HOST,
        port=API_PORT,
        reload=False
    )

