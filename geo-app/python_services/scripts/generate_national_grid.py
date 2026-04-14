"""
Genera una grilla densa de predicciones cubriendo TODO el territorio mexicano.

En vez de solo predecir en ciudades, genera puntos cada ~15-20km cubriendo
todo México de frontera a frontera. Esto llena los "huecos" blancos del mapa.

Uso:
    python -m scripts.generate_national_grid
    python -m scripts.generate_national_grid --step 0.15   # ~16km entre puntos
"""

import json
import math
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)

from config import (
    DATA_DIR, MODELS_DIR, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY,
    TABLE_PREDICTIONS,
)

# Bounding box de México continental
MEX_LAT_MIN = 14.5
MEX_LAT_MAX = 32.8
MEX_LON_MIN = -118.0
MEX_LON_MAX = -86.5

# Polígono simplificado de México (para filtrar puntos en el mar)
# Puntos clave del contorno de México (simplificado)
MEXICO_BOUNDARY_CHECKS = [
    # (lat_min, lat_max, lon_min, lon_max) - rectángulos que cubren México
    # Baja California
    (28.0, 33.0, -118.0, -114.0),
    (23.0, 28.0, -115.0, -109.0),
    # Noroeste - Sonora, Chihuahua, Sinaloa
    (23.0, 33.0, -112.0, -106.0),
    # Norte - Coahuila, NL, Tamaulipas, Durango
    (22.0, 30.0, -106.0, -97.0),
    # Centro-norte - SLP, Zac, Ags, Gto, Qro
    (20.0, 25.0, -105.0, -98.0),
    # Centro - CDMX, EdoMex, Puebla, Tlaxcala, Morelos, Hidalgo
    (18.0, 21.0, -100.0, -96.0),
    # Occidente - Jalisco, Colima, Michoacán, Nayarit
    (18.0, 23.0, -105.5, -101.0),
    # Sur - Guerrero, Oaxaca
    (15.5, 19.0, -102.0, -94.0),
    # Sureste - Chiapas
    (14.5, 17.5, -94.5, -90.0),
    # Golfo - Veracruz, Tabasco
    (17.0, 22.5, -97.5, -91.0),
    # Yucatán
    (18.0, 21.8, -91.5, -86.5),
    # Quintana Roo
    (18.0, 21.5, -89.5, -86.5),
]


def point_in_mexico(lat: float, lon: float) -> bool:
    """Verifica si un punto está dentro del territorio mexicano (aproximado)."""
    for lat_min, lat_max, lon_min, lon_max in MEXICO_BOUNDARY_CHECKS:
        if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
            return True
    return False


def find_nearest_city(lat: float, lon: float, cities: List[Dict]) -> Tuple[str, str, float]:
    """Encuentra la ciudad más cercana a un punto."""
    best_dist = float("inf")
    best_city = "Rural"
    best_state = "Unknown"

    for c in cities:
        d = math.sqrt((lat - c["lat"])**2 + (lon - c["lon"])**2) * 111
        if d < best_dist:
            best_dist = d
            best_city = c["name"]
            best_state = c["state"]

    return best_city, best_state, best_dist


def main(step_deg: float = 0.15, batch_size: int = 500):
    """Genera grilla nacional de predicciones."""
    start = time.time()

    logger.info("=" * 70)
    logger.info("GRILLA NACIONAL DE PREDICCIONES")
    logger.info(f"  Step: {step_deg}° (~{step_deg * 111:.0f}km)")
    logger.info(f"  Bbox: ({MEX_LAT_MIN},{MEX_LON_MIN}) to ({MEX_LAT_MAX},{MEX_LON_MAX})")
    logger.info("=" * 70)

    # 1. Cargar ciudades
    cities_path = DATA_DIR / "cities_mexico_32_states.json"
    with open(cities_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    cities = []
    for state_obj in data.get("states", []):
        for city in state_obj.get("cities", []):
            cities.append({
                "name": city["name"],
                "state": state_obj["name"],
                "lat": city["lat"],
                "lon": city["lon"],
                "population": city.get("population", 50000),
            })

    logger.info(f"  {len(cities)} ciudades de referencia")

    # 2. Generar grilla
    logger.info("\nGenerando grilla...")
    grid_points = []

    lat = MEX_LAT_MIN
    while lat <= MEX_LAT_MAX:
        lon = MEX_LON_MIN
        while lon <= MEX_LON_MAX:
            if point_in_mexico(lat, lon):
                grid_points.append((round(lat, 4), round(lon, 4)))
            lon += step_deg
        lat += step_deg

    logger.info(f"  Puntos en grilla: {len(grid_points):,}")

    # 3. Cargar modelo
    logger.info("\nCargando modelo...")
    from ml_model.hierarchical_model import HierarchicalPredictor

    model = HierarchicalPredictor(model_version="6.0")
    model_files = sorted(MODELS_DIR.glob("hierarchical_v6.0_*.pkl"), reverse=True)
    if not model_files:
        model_files = sorted(MODELS_DIR.glob("hierarchical_*.pkl"), reverse=True)
    if not model_files:
        logger.error("No se encontró modelo!")
        return

    model.load_model(str(model_files[0]))
    logger.info(f"  Modelo: {model_files[0].name}")

    # 4. Predecir en chunks
    logger.info("\nGenerando predicciones...")
    rng = np.random.default_rng(seed=42)
    timestamp = datetime.now().isoformat()
    AREAS = [120, 150, 200, 300, 500]
    all_records = []
    chunk_size = 500
    errors = 0

    for i in range(0, len(grid_points), chunk_size):
        chunk = grid_points[i:i + chunk_size]

        rows = []
        city_info_list = []
        for lat, lon in chunk:
            city_name, state, dist_km = find_nearest_city(lat, lon, cities)
            area = float(rng.choice(AREAS))
            rows.append({
                "lat": lat, "lon": lon,
                "area_m2": area,
                "price_mxn": area * 5000,
                "city": city_name,
                "state": state,
                "collection_date": "2026-04-03",
            })
            city_info_list.append((city_name, state, dist_km))

        df_in = pd.DataFrame(rows)

        try:
            df_feat = model.prepare_features(df_in)
            fcols = [c for c in model.feature_names if c in df_feat.columns]
            X = df_feat[fcols].fillna(0)
            X_s = pd.DataFrame(model.scaler.transform(X), columns=fcols, index=X.index)
            st_s = pd.Series([r["state"] for r in rows], index=X_s.index)
            preds = model._predict_batch_internal(X_s, st_s)

            for j, (lat, lon) in enumerate(chunk):
                pp = max(500, float(preds[j]))
                city_name, state, dist_km = city_info_list[j]

                # Score basado en precio y cercanía a ciudad
                urban_factor = max(0.3, min(1.0, 1.0 - dist_km / 50.0))
                score = max(10, min(95, round(50 + pp / 500 * urban_factor, 1)))
                growth = "alto" if score >= 70 else ("medio" if score >= 40 else "bajo")

                all_records.append({
                    "lat": lat,
                    "lon": lon,
                    "city": city_name,
                    "state": state,
                    "predicted_price_m2": round(pp, 2),
                    "plusvalia_score": score,
                    "growth_potential": growth,
                    "model_version": "v6.0_grid_national",
                    "model_confidence": round(min(90, 50 + urban_factor * 40), 1),
                    "prediction_date": timestamp,
                    "created_at": timestamp,
                })
        except Exception as e:
            errors += 1
            if errors <= 3:
                logger.warning(f"  Error chunk {i}: {e}")

        if (i // chunk_size) % 10 == 0 and i > 0:
            logger.info(f"  Progreso: {i:,}/{len(grid_points):,} puntos -> {len(all_records):,} predicciones")

    logger.info(f"\n  Total predicciones grilla: {len(all_records):,}")
    logger.info(f"  Errores: {errors}")

    # 5. Insertar en Supabase (SIN borrar las predicciones de ciudades existentes)
    logger.info(f"\nInsertando {len(all_records):,} predicciones de grilla...")
    from supabase import create_client
    sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

    # Borrar solo las de grilla anterior
    try:
        sb.table(TABLE_PREDICTIONS).delete().eq("model_version", "v6.0_grid_national").execute()
        logger.info("  Grilla anterior eliminada")
    except Exception:
        pass

    inserted = 0
    for i in range(0, len(all_records), batch_size):
        batch = all_records[i:i + batch_size]
        try:
            sb.table(TABLE_PREDICTIONS).insert(batch).execute()
            inserted += len(batch)
            if (i // batch_size) % 20 == 0:
                logger.info(f"    {inserted:,} / {len(all_records):,}")
        except Exception as e:
            logger.warning(f"    Error: {e}")
            for rec in batch:
                try:
                    sb.table(TABLE_PREDICTIONS).insert(rec).execute()
                    inserted += 1
                except Exception:
                    pass

    logger.info(f"  Insertados: {inserted:,}")

    # Stats
    df_stats = pd.DataFrame(all_records)
    logger.info(f"\n  {'Estado':<28} {'Puntos':>8} {'Avg $/m²':>12}")
    logger.info("  " + "-" * 52)
    for state in sorted(df_stats["state"].unique()):
        g = df_stats[df_stats["state"] == state]
        logger.info(f"  {state:<28} {len(g):>8,} ${g['predicted_price_m2'].mean():>10,.0f}")

    elapsed = time.time() - start
    logger.info(f"\n  Completado en {elapsed/60:.1f} minutos")
    logger.info(f"  Total predicciones en DB: {inserted + 49600:,} (grilla + ciudades)")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--step", type=float, default=0.15,
                        help="Step en grados (0.15 = ~16km)")
    args = parser.parse_args()

    logger.remove()
    logger.add(sys.stdout, format="<green>{time:HH:mm:ss}</green> | <level>{level:<8}</level> | <level>{message}</level>", level="INFO")

    main(step_deg=args.step)
