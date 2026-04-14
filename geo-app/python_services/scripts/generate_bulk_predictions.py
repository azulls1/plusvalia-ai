"""
Generador masivo de predicciones para todas las 219 ciudades.

Genera una grilla de puntos por ciudad, predice precio/m² y plusvalía
con el modelo jerárquico v4.0, e inserta los resultados en
iainmobiliaria_predictions en Supabase.

Uso:
    python -m scripts.generate_bulk_predictions
    python -m scripts.generate_bulk_predictions --points-per-city 100
    python -m scripts.generate_bulk_predictions --dry-run
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

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
    DATA_DIR, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY,
    TABLE_PREDICTIONS,
)

# Áreas típicas para generar predicciones (m²)
SAMPLE_AREAS = [80, 120, 150, 200, 300, 500, 1000, 2000]

# Tipos de propiedad
PROPERTY_TYPES = ["terreno", "casa", "departamento"]


def load_cities() -> List[Dict]:
    """Carga todas las ciudades desde cities_mexico_32_states.json."""
    cities_path = DATA_DIR / "cities_mexico_32_states.json"
    with open(cities_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    cities = []
    for state_obj in data.get("states", []):
        state_name = state_obj["name"]
        # Normalizar "Estado de México" -> "Estado de México"
        if state_name == "Estado de México":
            state_name = "Estado de México"
        for city in state_obj.get("cities", []):
            cities.append({
                "name": city["name"],
                "state": state_name,
                "lat": city["lat"],
                "lon": city["lon"],
                "population": city.get("population", 100000),
            })
    return cities


def generate_grid_points(
    center_lat: float,
    center_lon: float,
    population: int,
    n_points: int,
    rng: np.random.Generator,
) -> List[Dict]:
    """Genera puntos en una grilla con dispersión proporcional a la población."""
    # Ciudades grandes: mayor dispersión (~8km), pequeñas: ~2km
    spread = 0.015 + (population / 15_000_000) * 0.07  # en grados

    points = []
    # Mezcla de grilla regular + puntos aleatorios para cobertura natural
    n_grid = int(n_points * 0.6)
    n_random = n_points - n_grid

    # Grilla regular
    side = max(2, int(np.sqrt(n_grid)))
    lats = np.linspace(center_lat - spread, center_lat + spread, side)
    lons = np.linspace(center_lon - spread, center_lon + spread, side)
    for lat in lats:
        for lon in lons:
            if len(points) >= n_grid:
                break
            # Pequeña perturbación para evitar grilla perfecta
            points.append({
                "lat": round(float(lat + rng.normal(0, spread * 0.05)), 6),
                "lon": round(float(lon + rng.normal(0, spread * 0.05)), 6),
            })

    # Puntos aleatorios (distribución normal alrededor del centro)
    for _ in range(n_random):
        points.append({
            "lat": round(float(center_lat + rng.normal(0, spread * 0.6)), 6),
            "lon": round(float(center_lon + rng.normal(0, spread * 0.6)), 6),
        })

    return points[:n_points]


def compute_plusvalia_score(
    predicted_price_m2: float,
    city_avg_price: float,
    distance_to_center: float,
    population: int,
) -> float:
    """Calcula score de plusvalía (0-100) basado en precio relativo y ubicación."""
    # Factor precio: mayor precio relativo = mayor plusvalía
    if city_avg_price > 0:
        price_ratio = predicted_price_m2 / city_avg_price
    else:
        price_ratio = 1.0

    # Factor ubicación: más cerca del centro = más plusvalía
    distance_factor = max(0, 1.0 - (distance_to_center / 15.0))

    # Factor población: ciudades grandes = más plusvalía potencial
    pop_factor = min(1.0, population / 2_000_000)

    # Score combinado
    score = (
        price_ratio * 35 +          # 35% peso precio
        distance_factor * 30 +       # 30% peso ubicación
        pop_factor * 20 +            # 20% peso tamaño ciudad
        15                           # 15% base
    )

    return max(0, min(100, round(score, 1)))


def get_growth_potential(score: float) -> str:
    """Clasifica potencial de crecimiento."""
    if score >= 70:
        return "alto"
    elif score >= 40:
        return "medio"
    return "bajo"


def main(points_per_city: int = 80, dry_run: bool = False, batch_size: int = 500):
    """Genera predicciones masivas para todas las ciudades."""
    start_time = time.time()

    logger.info("=" * 70)
    logger.info("GENERACIÓN MASIVA DE PREDICCIONES")
    logger.info(f"  Puntos por ciudad: {points_per_city}")
    logger.info(f"  Dry run: {dry_run}")
    logger.info("=" * 70)

    # 1. Cargar modelo
    logger.info("Paso 1: Cargando modelo v4.0...")
    from ml_model.hierarchical_model import HierarchicalPredictor

    model = HierarchicalPredictor(model_version="4.0")
    model_loaded = False

    # Buscar el modelo más reciente
    from config import MODELS_DIR
    model_files = sorted(MODELS_DIR.glob("hierarchical_v4.0_*.pkl"), reverse=True)
    if not model_files:
        model_files = sorted(MODELS_DIR.glob("hierarchical_*.pkl"), reverse=True)

    if model_files:
        model.load_model(str(model_files[0]))
        model_loaded = True
        logger.info(f"  Modelo cargado: {model_files[0].name}")
    else:
        logger.error("No se encontró modelo entrenado. Ejecuta el entrenamiento primero.")
        return

    # 2. Cargar ciudades
    logger.info("Paso 2: Cargando ciudades...")
    cities = load_cities()
    logger.info(f"  {len(cities)} ciudades en {len(set(c['state'] for c in cities))} estados")

    total_predictions = len(cities) * points_per_city
    logger.info(f"  Predicciones a generar: ~{total_predictions:,}")

    # 3. Conectar a Supabase
    if not dry_run:
        logger.info("Paso 3: Conectando a Supabase...")
        from supabase import create_client
        sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

        # Limpiar predicciones antiguas del modelo 4.0 para evitar duplicados
        logger.info("  Limpiando predicciones anteriores del modelo 4.0...")
        try:
            sb.table(TABLE_PREDICTIONS).delete().like(
                "model_version", "%4.0%"
            ).execute()
            logger.info("  Predicciones anteriores eliminadas")
        except Exception as e:
            logger.warning(f"  No se pudieron limpiar predicciones anteriores: {e}")

    # 4. Generar predicciones
    logger.info("Paso 4: Generando predicciones...")
    rng = np.random.default_rng(seed=42)
    timestamp = datetime.now().isoformat()
    all_records = []
    cities_processed = 0
    cities_failed = 0

    for city_info in cities:
        city_name = city_info["name"]
        state = city_info["state"]
        center_lat = city_info["lat"]
        center_lon = city_info["lon"]
        population = city_info["population"]

        # Generar puntos de grilla
        points = generate_grid_points(
            center_lat, center_lon, population, points_per_city, rng
        )

        # Preparar DataFrame para predicción batch
        rows = []
        for pt in points:
            area = float(rng.choice(SAMPLE_AREAS))
            rows.append({
                "lat": pt["lat"],
                "lon": pt["lon"],
                "area_m2": area,
                "price_mxn": area * 5000,  # placeholder
                "city": city_name,
                "state": state,
                "collection_date": "2026-04-01",
            })

        df_input = pd.DataFrame(rows)

        try:
            # Preparar features y predecir con el modelo
            df_features = model.prepare_features(df_input)
            feature_cols = [c for c in model.feature_names if c in df_features.columns]

            X = df_features[feature_cols].fillna(0)
            X_scaled = pd.DataFrame(
                model.scaler.transform(X),
                columns=feature_cols,
                index=X.index,
            )

            # Predicción vectorizada
            states_series = pd.Series([state] * len(X_scaled), index=X_scaled.index)
            predictions = model._predict_batch_internal(X_scaled, states_series)

            # Calcular promedios para la ciudad
            city_avg_price = float(np.mean(predictions[predictions > 0]))

            # Construir registros para insertar
            for i, (_, row) in enumerate(df_input.iterrows()):
                predicted_price = max(500, float(predictions[i]))
                dist = np.sqrt(
                    (row["lat"] - center_lat) ** 2 +
                    (row["lon"] - center_lon) ** 2
                ) * 111  # aprox km

                score = compute_plusvalia_score(
                    predicted_price, city_avg_price, dist, population
                )

                all_records.append({
                    "lat": row["lat"],
                    "lon": row["lon"],
                    "city": city_name,
                    "state": state,
                    "predicted_price_m2": round(predicted_price, 2),
                    "plusvalia_score": score,
                    "growth_potential": get_growth_potential(score),
                    "model_version": "v4.0_32_states",
                    "model_confidence": round(min(95, 60 + score * 0.35), 1),
                    "prediction_date": timestamp,
                    "created_at": timestamp,
                })

            cities_processed += 1

            if cities_processed % 20 == 0:
                logger.info(
                    f"  Progreso: {cities_processed}/{len(cities)} ciudades "
                    f"({len(all_records):,} predicciones)"
                )

        except Exception as e:
            cities_failed += 1
            logger.warning(f"  Error en {city_name}, {state}: {e}")
            continue

    logger.info(f"  Total: {len(all_records):,} predicciones generadas "
                f"({cities_processed} ciudades OK, {cities_failed} fallidas)")

    # 5. Insertar en Supabase
    if dry_run:
        logger.info("Paso 5: DRY RUN — no se insertaron datos")
        # Guardar como CSV para revisión
        df_out = pd.DataFrame(all_records)
        out_path = DATA_DIR / "bulk_predictions_preview.csv"
        df_out.to_csv(out_path, index=False)
        logger.info(f"  Preview guardado en {out_path}")
    else:
        logger.info(f"Paso 5: Insertando {len(all_records):,} predicciones en Supabase...")
        inserted = 0
        failed_batches = 0

        for i in range(0, len(all_records), batch_size):
            batch = all_records[i:i + batch_size]
            try:
                sb.table(TABLE_PREDICTIONS).insert(batch).execute()
                inserted += len(batch)
                if (i // batch_size) % 10 == 0:
                    logger.info(f"  Insertados: {inserted:,} / {len(all_records):,}")
            except Exception as e:
                failed_batches += 1
                logger.error(f"  Error insertando batch {i//batch_size}: {e}")
                # Intentar uno por uno si el batch falla
                for record in batch:
                    try:
                        sb.table(TABLE_PREDICTIONS).insert(record).execute()
                        inserted += 1
                    except Exception:
                        pass

        logger.info(f"  Insertados exitosamente: {inserted:,} / {len(all_records):,}")
        if failed_batches > 0:
            logger.warning(f"  Batches fallidos: {failed_batches}")

    # 6. Resumen
    elapsed = time.time() - start_time
    logger.info("\n" + "=" * 70)
    logger.info("RESUMEN")
    logger.info("=" * 70)
    logger.info(f"  Ciudades procesadas: {cities_processed}/{len(cities)}")
    logger.info(f"  Predicciones generadas: {len(all_records):,}")
    logger.info(f"  Estados cubiertos: {len(set(r['state'] for r in all_records))}")
    logger.info(f"  Tiempo total: {elapsed/60:.1f} minutos")

    # Stats por estado
    df_stats = pd.DataFrame(all_records)
    if not df_stats.empty:
        logger.info(f"\n{'Estado':<30s} {'Predicciones':>12s} {'Avg $/m²':>12s} {'Avg Score':>10s}")
        logger.info("-" * 68)
        for state, group in df_stats.groupby("state"):
            logger.info(
                f"  {state:<28s} {len(group):>12,} "
                f"${group['predicted_price_m2'].mean():>10,.0f} "
                f"{group['plusvalia_score'].mean():>9.1f}"
            )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generar predicciones masivas")
    parser.add_argument("--points-per-city", type=int, default=80,
                        help="Puntos de predicción por ciudad (default: 80)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Solo generar, no insertar en DB")
    parser.add_argument("--batch-size", type=int, default=500,
                        help="Tamaño de batch para inserción (default: 500)")
    args = parser.parse_args()

    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level:<8}</level> | <level>{message}</level>",
        level="INFO",
    )

    main(
        points_per_city=args.points_per_city,
        dry_run=args.dry_run,
        batch_size=args.batch_size,
    )
