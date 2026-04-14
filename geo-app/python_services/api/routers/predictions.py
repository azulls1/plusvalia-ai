"""Prediction endpoints for the ML API."""

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from typing import Optional
from datetime import datetime
from math import radians, sin, cos, sqrt, atan2
from pathlib import Path
from loguru import logger
import asyncio
import os
import numpy as np
import time as _time

# Cache en memoria para endpoints pesados (TTL 5 min)
_cache: dict = {}
_cache_ttl = 300  # 5 minutos

def _get_cached(key: str):
    """Retorna valor cacheado si existe y no expiró."""
    entry = _cache.get(key)
    if entry and _time.time() - entry["ts"] < _cache_ttl:
        return entry["data"]
    return None

def _set_cached(key: str, data):
    """Guarda en cache con timestamp."""
    _cache[key] = {"data": data, "ts": _time.time()}

from api.deps import model, supabase
from api.schemas import PredictionRequest, PredictionResponse, ExplainResponse
from middleware.circuit_breaker import CircuitBreakerRegistry


def get_inference_cost(inference_ms: float, memory_mb: float = 0) -> dict:
    """Estimate cost per inference based on resource usage."""
    # Based on typical cloud pricing: $0.05/hour for 2 vCPU, 2GB RAM
    hourly_cost = 0.05  # USD
    cost_per_ms = hourly_cost / 3_600_000
    estimated_cost = inference_ms * cost_per_ms

    return {
        "inference_ms": round(inference_ms, 1),
        "estimated_cost_usd": round(estimated_cost, 8),
        "cost_model": "compute-time-based",
        "note": "Estimated based on 2vCPU/2GB @ $0.05/hr",
    }


router = APIRouter(prefix="/predictions", tags=["Predictions"])

# Mapeo de todas las variantes de nombre de estado → ID del GeoJSON
NAME_TO_GEOID = {
    "Aguascalientes": "MX-AGU",
    "Baja California": "MX-BCN",
    "Baja California Sur": "MX-BCS",
    "Campeche": "MX-CAM",
    "Chiapas": "MX-CHP",
    "Chihuahua": "MX-CHH",
    "Ciudad de México": "MX-CMX", "Ciudad de Mexico": "MX-CMX", "Distrito Federal": "MX-CMX",
    "Coahuila": "MX-COA", "Coahuila de Zaragoza": "MX-COA",
    "Colima": "MX-COL",
    "Durango": "MX-DUR",
    "Estado de México": "MX-MEX", "México": "MX-MEX",
    "Guanajuato": "MX-GUA",
    "Guerrero": "MX-GRO",
    "Hidalgo": "MX-HID",
    "Jalisco": "MX-JAL",
    "Michoacán": "MX-MIC", "Michoacán de Ocampo": "MX-MIC",
    "Morelos": "MX-MOR",
    "Nayarit": "MX-NAY",
    "Nuevo León": "MX-NLE",
    "Oaxaca": "MX-OAX",
    "Puebla": "MX-PUE",
    "Querétaro": "MX-QUE",
    "Quintana Roo": "MX-ROO",
    "San Luis Potosí": "MX-SLP",
    "Sinaloa": "MX-SIN",
    "Sonora": "MX-SON",
    "Tabasco": "MX-TAB",
    "Tamaulipas": "MX-TAM",
    "Tlaxcala": "MX-TLA",
    "Veracruz": "MX-VER", "Veracruz de Ignacio de la Llave": "MX-VER",
    "Yucatán": "MX-YUC",
    "Zacatecas": "MX-ZAC",
}

# Circuit breaker for Supabase calls
supabase_cb = CircuitBreakerRegistry.get("supabase", failure_threshold=5, recovery_timeout=30)


async def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")):
    """Verify the API key from request header."""
    expected = os.getenv("ML_API_KEY", "")
    if not expected or x_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return x_api_key

# Redis-backed prediction cache with in-memory fallback
from middleware.redis_cache import PredictionCache
_prediction_cache = PredictionCache(max_memory_size=1000, ttl=300)


def _cache_key(lat: float, lon: float, area_m2: float) -> str:
    """Generate cache key by rounding coordinates and bucketing area."""
    return f"{round(lat, 3)}:{round(lon, 3)}:{int(area_m2 / 50) * 50}"


def _get_cached_prediction(key: str) -> dict | None:
    """Return cached prediction if not expired."""
    return _prediction_cache.get(key)


def _set_cached_prediction(key: str, data: dict) -> None:
    """Store prediction in cache."""
    _prediction_cache.set(key, data)


async def _retry_supabase(fn, max_retries=3, initial_delay=0.5):
    """Retry a Supabase operation with exponential backoff."""
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            return fn()
        except Exception as e:  # Supabase client may raise various errors
            last_error = e
            if attempt < max_retries:
                delay = initial_delay * (2 ** attempt)
                logger.warning(f"Supabase query failed (attempt {attempt + 1}), retrying in {delay}s: {e}")
                await asyncio.sleep(delay)
    raise last_error


@router.post("/predict", response_model=PredictionResponse, tags=["Predictions"])
async def predict(
    request: PredictionRequest,
    save_to_db: bool = Query(True, description="Guardar predicción en base de datos"),
    api_key: str = Depends(verify_api_key),
):
    """Predice el precio y score de plusvalía para un terreno."""
    if model.price_model is None:
        raise HTTPException(status_code=503, detail="Modelo no entrenado. Ejecutar /train primero.")

    # Sanitize string inputs
    city = request.city.strip()[:100]
    state = request.state.strip()[:100]

    # Check cache
    cache_key = _cache_key(request.lat, request.lon, request.area_m2)
    cached = _get_cached_prediction(cache_key)
    if cached:
        logger.info("Predicción servida desde cache")
        return PredictionResponse(**cached, prediction_id=None, timestamp=datetime.now().isoformat())

    logger.info(f"Predicción solicitada: {city}, {state} - {request.area_m2}m²")

    start_time = _time.perf_counter()
    try:
        prediction = model.predict_price(
            lat=request.lat,
            lon=request.lon,
            area_m2=request.area_m2,
            city=city,
            state=state,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    inference_ms = (_time.perf_counter() - start_time) * 1000
    logger.info(f"Inference completed in {inference_ms:.1f}ms for {city}")

    prediction["inference_ms"] = round(inference_ms, 1)
    prediction["cost_info"] = get_inference_cost(inference_ms)

    # Cache the prediction
    _set_cached_prediction(cache_key, prediction)

    prediction_id = None
    if save_to_db:
        try:
            insert_data = {
                "lat": request.lat,
                "lon": request.lon,
                "city": city,
                "state": state,
                "predicted_price_m2": prediction["predicted_price_m2"],
                "plusvalia_score": prediction["plusvalia_score"],
                "growth_potential": prediction["growth_potential"],
                "current_price_m2": None,
                "distance_to_center_km": prediction["features_used"].get("distance_to_center", 0),
                "amenities_count": 0,
                "model_version": prediction["model_version"],
                "model_confidence": prediction["confidence"],
            }
            result = await supabase_cb.execute(
                lambda: supabase.table("iainmobiliaria_predictions").insert(insert_data).execute()
            )
            if result.data:
                prediction_id = result.data[0]["id"]
                logger.info(f"Predicción guardada con ID: {prediction_id}")
        except Exception as e:  # Supabase client may raise various errors
            logger.error(f"Error guardando predicción en DB: {e}")

    return PredictionResponse(
        **prediction,
        prediction_id=prediction_id,
        timestamp=datetime.now().isoformat(),
    )


@router.post("/explain", response_model=ExplainResponse, tags=["Predictions"])
async def explain_prediction(request: PredictionRequest, api_key: str = Depends(verify_api_key)):
    """Genera explicación SHAP de por qué el modelo predice cierto precio."""
    if model.price_model is None:
        raise HTTPException(status_code=503, detail="Modelo no entrenado. Ejecutar /train primero.")

    city = request.city.strip()[:100]
    state = request.state.strip()[:100]

    try:
        explanation = model.explain_prediction(
            lat=request.lat,
            lon=request.lon,
            area_m2=request.area_m2,
            city=city,
            state=state,
        )
    except ImportError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return ExplainResponse(**explanation)


@router.get("/history")
async def get_predictions_history(
    limit: int = Query(100, ge=1, le=1000),
    city: Optional[str] = None,
    state: Optional[str] = None,
):
    """Obtiene el historial de predicciones."""
    try:
        query = supabase.table("iainmobiliaria_predictions").select("*")
        if city:
            query = query.eq("city", city)
        if state:
            query = query.eq("state", state)
        query = query.order("created_at", desc=True).limit(limit)
        response = await supabase_cb.execute(
            lambda: query.execute(),
            fallback=lambda: type("R", (), {"data": []})(),
        )
    except Exception as e:  # Supabase client may raise various errors
        logger.error(f"Error obteniendo historial: {e}")
        raise HTTPException(status_code=500, detail="Error consultando historial de predicciones")

    return {"predictions": response.data, "count": len(response.data), "filters": {"city": city, "state": state}}


@router.get("/heatmap")
async def get_heatmap_data(
    city: Optional[str] = None,
    min_score: Optional[float] = Query(None, ge=0, le=100),
    limit: int = Query(20000, ge=1, le=200000),
):
    """Obtiene predicciones en formato optimizado para heatmap."""
    try:
        query = supabase.table("iainmobiliaria_predictions").select("lat, lon, plusvalia_score")
        if city:
            query = query.eq("city", city)
        if min_score is not None:
            query = query.gte("plusvalia_score", min_score)
        query = query.limit(limit)
        response = await supabase_cb.execute(
            lambda: query.execute(),
            fallback=lambda: type("R", (), {"data": []})(),
        )
    except Exception as e:  # Supabase client may raise various errors
        logger.error(f"Error obteniendo datos de heatmap: {e}")
        raise HTTPException(status_code=500, detail="Error consultando datos de heatmap")

    heatmap_points = []
    if response.data:
        # Normalización rápida con percentiles
        scores = [p.get("plusvalia_score", 50) for p in response.data]
        scores_sorted = sorted(scores)
        n = len(scores_sorted)
        p10 = scores_sorted[n // 10] if n > 10 else 0
        p90 = scores_sorted[n * 9 // 10] if n > 10 else 100
        rng = max(1, p90 - p10)

        # Formato compacto: [lat, lon, intensity] con 4 decimales
        for pred in response.data:
            raw = pred.get("plusvalia_score", 50)
            intensity = max(0.05, min(1.0, (raw - p10) / rng))
            heatmap_points.append([
                round(pred["lat"], 4),
                round(pred["lon"], 4),
                round(intensity, 2)
            ])

    return {"points": heatmap_points, "count": len(heatmap_points), "filters": {"city": city, "min_score": min_score}}


@router.get("/stats-by-state")
async def get_stats_by_state():
    """Devuelve score promedio, conteo y precio promedio por estado (para coroplético)."""
    cached = _get_cached("stats_by_state")
    if cached:
        return cached
    try:
        response = await supabase_cb.execute(
            lambda: supabase.table("iainmobiliaria_predictions")
                .select("state, plusvalia_score, predicted_price_m2")
                .limit(50000)
                .execute(),
            fallback=lambda: type("R", (), {"data": []})(),
        )
    except Exception as e:
        logger.error(f"Error stats by state: {e}")
        raise HTTPException(status_code=500, detail="Error consultando stats por estado")

    # Agrupar por GeoJSON ID
    geo_data: dict = {}
    for row in response.data:
        s = row.get("state", "")
        if not s:
            continue
        geo_id = NAME_TO_GEOID.get(s)
        if not geo_id:
            # Intentar match parcial
            for name, gid in NAME_TO_GEOID.items():
                if name in s or s in name:
                    geo_id = gid
                    break
        if not geo_id:
            continue

        if geo_id not in geo_data:
            geo_data[geo_id] = {"scores": [], "prices": []}
        geo_data[geo_id]["scores"].append(row.get("plusvalia_score", 0))
        price = row.get("predicted_price_m2", 0)
        if price and price > 0:
            geo_data[geo_id]["prices"].append(price)

    result = {}
    for geo_id, data in geo_data.items():
        scores = data["scores"]
        prices = data["prices"]
        result[geo_id] = {
            "avg_score": round(sum(scores) / len(scores), 1) if scores else 0,
            "count": len(scores),
            "avg_price_m2": round(sum(prices) / len(prices), 0) if prices else 0,
        }

    response_data = {"states": result}
    _set_cached("stats_by_state", response_data)
    return response_data


@router.get("/nearby")
async def get_nearby_predictions(
    lat: float = Query(..., description="Latitud"),
    lon: float = Query(..., description="Longitud"),
    radius_km: float = Query(2.0, ge=0.1, le=50, description="Radio en kilómetros"),
    limit: int = Query(50, ge=1, le=500),
):
    """Obtiene predicciones cercanas a una ubicación."""
    try:
        lat_range = radius_km / 111.0
        lon_range = radius_km / (111.0 * abs(np.cos(np.radians(lat))))
        response = (
            supabase.table("iainmobiliaria_predictions")
            .select("*")
            .gte("lat", lat - lat_range)
            .lte("lat", lat + lat_range)
            .gte("lon", lon - lon_range)
            .lte("lon", lon + lon_range)
            .limit(limit)
            .execute()
        )
    except Exception as e:  # Supabase client may raise various errors (incl. 504 timeout)
        logger.warning(f"Supabase timeout/error en nearby predictions: {e}")
        return {"predictions": [], "count": 0, "center": {"lat": lat, "lon": lon}, "radius_km": radius_km}

    nearby = []
    if response.data:
        for pred in response.data:
            dlat = abs(pred["lat"] - lat)
            dlon = abs(pred["lon"] - lon)
            if dlat <= lat_range and dlon <= lon_range:
                R = 6371
                lat1, lon1, lat2, lon2 = map(radians, [lat, lon, pred["lat"], pred["lon"]])
                dlat_r = lat2 - lat1
                dlon_r = lon2 - lon1
                a = sin(dlat_r / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon_r / 2) ** 2
                c = 2 * atan2(sqrt(a), sqrt(1 - a))
                distance = R * c
                if distance <= radius_km:
                    pred["distance_km"] = round(distance, 2)
                    nearby.append(pred)

    nearby.sort(key=lambda x: x["distance_km"])
    nearby = nearby[:limit]
    return {"predictions": nearby, "count": len(nearby), "center": {"lat": lat, "lon": lon}, "radius_km": radius_km}


@router.get("/bbox")
async def get_predictions_in_bbox(
    min_lat: float = Query(..., description="Latitud mínima"),
    max_lat: float = Query(..., description="Latitud máxima"),
    min_lon: float = Query(..., description="Longitud mínima"),
    max_lon: float = Query(..., description="Longitud máxima"),
    limit: int = Query(5000, ge=1, le=20000),
):
    """Obtiene predicciones dentro de un bounding box."""
    try:
        response = (
            supabase.table("iainmobiliaria_predictions")
            .select("*")
            .gte("lat", min_lat)
            .lte("lat", max_lat)
            .gte("lon", min_lon)
            .lte("lon", max_lon)
            .limit(limit)
            .execute()
        )
    except Exception as e:  # Supabase client may raise various errors
        logger.error(f"Error consultando predicciones en bbox: {e}")
        raise HTTPException(status_code=500, detail="Error consultando predicciones")

    predictions_in_bbox = response.data or []

    return {
        "predictions": predictions_in_bbox,
        "count": len(predictions_in_bbox),
        "bbox": {"min_lat": min_lat, "max_lat": max_lat, "min_lon": min_lon, "max_lon": max_lon},
    }


@router.get("/stats-by-city", tags=["Statistics"])
async def get_predictions_stats_by_city():
    """Obtiene estadísticas de predicciones agrupadas por ciudad."""
    cached = _get_cached("stats_by_city")
    if cached:
        return cached
    try:
        response = supabase.table("iainmobiliaria_predictions").select("city, state, predicted_price_m2, plusvalia_score, growth_potential").limit(50000).execute()
    except Exception as e:  # Supabase client may raise various errors
        logger.error(f"Error obteniendo estadísticas por ciudad: {e}")
        raise HTTPException(status_code=500, detail="Error consultando estadísticas")

    if not response.data:
        return {"cities": [], "total": 0}

    cities_stats = {}
    for pred in response.data:
        city = pred["city"]
        if city not in cities_stats:
            cities_stats[city] = {
                "city": city,
                "state": pred["state"],
                "count": 0,
                "prices": [],
                "scores": [],
                "potentials": {"alto": 0, "medio": 0, "bajo": 0},
            }
        cities_stats[city]["count"] += 1
        cities_stats[city]["prices"].append(pred["predicted_price_m2"])
        cities_stats[city]["scores"].append(pred["plusvalia_score"])
        potential = (pred.get("growth_potential") or "").lower()
        if potential in cities_stats[city]["potentials"]:
            cities_stats[city]["potentials"][potential] += 1

    cities_list = []
    for city, data in cities_stats.items():
        avg_price = sum(data["prices"]) / len(data["prices"])
        cities_list.append({
            "city": city,
            "state": data["state"],
            "predictions_count": data["count"],
            "avg_price_m2": round(avg_price, 2),
            "min_price_m2": round(min(data["prices"]), 2),
            "max_price_m2": round(max(data["prices"]), 2),
            "avg_plusvalia_score": round(sum(data["scores"]) / len(data["scores"]), 2),
            "potential_distribution": data["potentials"],
        })

    cities_list.sort(key=lambda x: x["avg_price_m2"], reverse=True)
    response_data = {"cities": cities_list, "total_predictions": len(response.data), "cities_count": len(cities_list)}
    _set_cached("stats_by_city", response_data)
    return response_data


@router.get("/drift-status")
async def check_drift_status():
    """Check current data drift status against baseline."""
    from ml_model.monitoring.drift_detector import DriftDetector
    try:
        detector = DriftDetector()
        # Load baseline if exists
        baseline_path = Path(__file__).parent.parent.parent / "ml_model" / "monitoring" / "baseline_stats.json"
        if not baseline_path.exists():
            return {"status": "no_baseline", "message": "No baseline computed yet. Run /drift-compute-baseline first."}

        detector = DriftDetector(baseline_stats_path=str(baseline_path))

        # Get recent predictions from Supabase
        from api.deps import get_supabase
        sb = get_supabase()
        result = sb.table("iainmobiliaria_predictions").select("*").order("created_at", desc=True).limit(500).execute()

        if not result.data or len(result.data) < 50:
            return {"status": "insufficient_data", "message": f"Need at least 50 recent predictions, got {len(result.data or [])}"}

        import pandas as pd
        df = pd.DataFrame(result.data)
        report = detector.check_drift(df)

        return {
            "status": "ok",
            "drift_report": {
                "drift_detected": report.drift_detected,
                "overall_severity": report.severity,
                "feature_drifts": report.feature_drifts,
                "prediction_drift": report.prediction_drift,
                "recommendations": report.recommendations,
                "checked_at": report.timestamp,
            }
        }
    except Exception as e:
        logger.error(f"Error checking drift status: {e}")
        raise HTTPException(status_code=500, detail=f"Error checking drift status: {e}")


@router.post("/drift-compute-baseline")
async def compute_drift_baseline(api_key: str = Depends(verify_api_key)):
    """Compute drift baseline from current data. Requires API key."""
    from ml_model.monitoring.drift_detector import DriftDetector
    try:
        detector = DriftDetector()
        from api.deps import get_supabase
        sb = get_supabase()
        result = sb.table("iainmobiliaria_predictions").select("*").order("created_at", desc=True).limit(2000).execute()

        if not result.data or len(result.data) < 50:
            raise HTTPException(status_code=422, detail=f"Need at least 50 predictions for baseline, got {len(result.data or [])}")

        import pandas as pd
        df = pd.DataFrame(result.data)
        baseline_path = Path(__file__).parent.parent.parent / "ml_model" / "monitoring" / "baseline_stats.json"
        detector.compute_baseline(df)
        detector.save_baseline(str(baseline_path))

        return {"status": "ok", "message": f"Baseline computed from {len(df)} records", "path": str(baseline_path)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error computing drift baseline: {e}")
        raise HTTPException(status_code=500, detail=f"Error computing drift baseline: {e}")


@router.get("/bias-report")
async def get_bias_report():
    """Run bias evaluation on current model predictions."""
    from ml_model.bias_evaluator import BiasEvaluator
    try:
        evaluator = BiasEvaluator()
        from api.deps import get_supabase
        sb = get_supabase()
        result = sb.table("iainmobiliaria_predictions").select("*").limit(2000).execute()

        if not result.data or len(result.data) < 50:
            return {"status": "insufficient_data", "message": f"Need at least 50 predictions, got {len(result.data or [])}"}

        import pandas as pd
        from dataclasses import asdict
        df = pd.DataFrame(result.data)
        report = evaluator.evaluate(df)

        return {
            "status": "ok",
            "bias_report": asdict(report)
        }
    except Exception as e:
        logger.error(f"Error generating bias report: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating bias report: {e}")


@router.get("/models/registry")
async def get_model_registry():
    """Get all model versions and their metrics."""
    from ml_model.model_registry import ModelRegistry
    registry = ModelRegistry(str(Path(__file__).parent.parent.parent / "ml_model" / "models"))
    return registry.get_registry()


@router.get("/prompts/versions")
async def get_prompt_versions():
    """Get all chatbot prompt versions."""
    from integrations.prompt_registry import get_all_versions, get_active_prompt
    return {
        "active": get_active_prompt(),
        "versions": get_all_versions(),
    }


@router.get("/circuit-breakers")
async def get_circuit_breaker_status():
    """Get status of all circuit breakers."""
    return CircuitBreakerRegistry.get_all_status()
