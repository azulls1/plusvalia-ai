"""
Pipeline completo: Descargar datos → Reentrenar modelo → Regenerar predicciones.

1. Descarga los 54K+ comparables de Supabase
2. Limpia y prepara datos de entrenamiento
3. Entrena modelo jerárquico v6.0
4. Genera predicciones densas para todas las ciudades
5. Inserta predicciones en Supabase

Uso:
    python -m scripts.retrain_and_predict
    python -m scripts.retrain_and_predict --points-per-city 200
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List

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
    TABLE_COMPARABLES, TABLE_PREDICTIONS,
)

MODEL_VERSION = "6.0"


# ── Paso 1: Descargar datos ──────────────────────────────────────────────────

def download_training_data() -> pd.DataFrame:
    """Descarga todos los comparables de Supabase con paginación por id."""
    from supabase import create_client
    sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

    logger.info("Paso 1: Descargando datos de entrenamiento de Supabase...")

    count_r = sb.table(TABLE_COMPARABLES).select("id", count="exact").execute()
    total = count_r.count or 0
    logger.info(f"  Total en DB: {total:,}")

    all_data = []
    last_id = 0
    page_size = 999

    while True:
        try:
            r = (sb.table(TABLE_COMPARABLES)
                 .select("*")
                 .gt("id", last_id)
                 .order("id")
                 .limit(page_size)
                 .execute())
            if not r.data:
                break
            all_data.extend(r.data)
            last_id = r.data[-1]["id"]
            if len(all_data) % 5000 < page_size:
                logger.info(f"    Descargados: {len(all_data):,} / {total:,}")
            if len(r.data) < page_size:
                break
        except Exception as e:
            logger.warning(f"    Error paginación id>{last_id}: {e}")
            break

    df = pd.DataFrame(all_data)
    logger.info(f"  Descargados: {len(df):,} registros")
    if not df.empty:
        logger.info(f"  Estados: {df['state'].nunique()}")
        logger.info(f"  Ciudades: {df['city'].nunique()}")

    return df


# ── Paso 2: Limpieza ────────────────────────────────────────────────────────

def clean_training_data(df: pd.DataFrame) -> pd.DataFrame:
    """Limpia datos para entrenamiento."""
    logger.info("\nPaso 2: Limpiando datos de entrenamiento...")
    initial = len(df)

    # Normalizar estados
    state_map = {
        "Distrito Federal": "Ciudad de México",
        "México": "Estado de México",
        "Coahuila de Zaragoza": "Coahuila",
        "Veracruz de Ignacio de la Llave": "Veracruz",
        "Michoacán de Ocampo": "Michoacán",
    }
    df["state"] = df["state"].map(lambda s: state_map.get(s, s) if isinstance(s, str) else s)

    # Filtros básicos
    df = df.dropna(subset=["price_mxn", "lat", "lon"])
    df = df[df["price_mxn"] > 50000].copy()
    df = df[df["price_mxn"] < 500_000_000].copy()

    # Coordenadas dentro de México
    df = df[(df["lat"] >= 14) & (df["lat"] <= 33)].copy()
    df = df[(df["lon"] >= -118.5) & (df["lon"] <= -86)].copy()

    # Calcular price_m2 si falta
    if "price_m2" not in df.columns or df["price_m2"].isna().all():
        df["price_m2"] = np.where(
            df["area_m2"] > 0,
            df["price_mxn"] / df["area_m2"],
            np.nan,
        )

    # Asegurar area_m2 válida
    df.loc[df["area_m2"].isna() | (df["area_m2"] <= 0), "area_m2"] = 150.0

    # Filtrar price_m2 extremos (percentiles 1-99)
    df = df[df["price_m2"] > 0].copy()
    p01 = df["price_m2"].quantile(0.01)
    p99 = df["price_m2"].quantile(0.99)
    df = df[(df["price_m2"] >= p01) & (df["price_m2"] <= p99)].copy()

    # Asegurar collection_date
    if "collection_date" not in df.columns:
        df["collection_date"] = "2026-04-03"

    logger.info(f"  Limpieza: {initial:,} -> {len(df):,} registros")
    logger.info(f"  Price/m² rango: ${df['price_m2'].min():,.0f} - ${df['price_m2'].max():,.0f}")
    logger.info(f"  Price/m² promedio: ${df['price_m2'].mean():,.0f}")

    # Stats por estado
    logger.info(f"\n  {'Estado':<28} {'Registros':>8} {'Avg $/m²':>12}")
    logger.info("  " + "-" * 52)
    for state in sorted(df["state"].unique()):
        g = df[df["state"] == state]
        logger.info(f"  {state:<28} {len(g):>8,} ${g['price_m2'].mean():>10,.0f}")

    # Guardar CSV
    csv_path = DATA_DIR / f"training_data_v{MODEL_VERSION}_{datetime.now().strftime('%Y%m%d')}.csv"
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    logger.info(f"\n  CSV guardado: {csv_path.name}")

    return df


# ── Paso 3: Entrenamiento ───────────────────────────────────────────────────

def train_model(df: pd.DataFrame) -> object:
    """Entrena modelo jerárquico v6.0."""
    logger.info(f"\nPaso 3: Entrenando modelo jerárquico v{MODEL_VERSION}...")
    logger.info(f"  Registros: {len(df):,}")
    logger.info(f"  Features: área, ubicación, demografía, espaciales, temporales")

    from ml_model.hierarchical_model import HierarchicalPredictor

    model = HierarchicalPredictor(model_version=MODEL_VERSION)

    start = time.time()
    metrics = model.train(df, target_col="price_m2", test_size=0.2)
    elapsed = time.time() - start

    logger.info(f"\n  Entrenamiento completado en {elapsed:.1f}s")
    logger.info(f"  Métricas globales:")
    if "global" in metrics:
        gm = metrics["global"]
        logger.info(f"    R² = {gm.get('r2', 'N/A')}")
        logger.info(f"    MAE = ${gm.get('mae', 0):,.0f}")
        logger.info(f"    RMSE = ${gm.get('rmse', 0):,.0f}")

    # Guardar modelo
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_path = MODELS_DIR / f"hierarchical_v{MODEL_VERSION}_{timestamp}.pkl"
    model.save_model(str(model_path))
    logger.info(f"  Modelo guardado: {model_path.name}")

    # Guardar métricas
    metrics_path = model_path.with_suffix(".metrics.json")
    import json
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2, default=str)

    return model


# ── Paso 4: Generar predicciones ────────────────────────────────────────────

def generate_predictions(model, points_per_city: int = 200):
    """Genera predicciones densas para todas las ciudades."""
    logger.info(f"\nPaso 4: Generando predicciones ({points_per_city} pts/ciudad)...")

    # Cargar ciudades
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

    logger.info(f"  {len(cities)} ciudades, ~{len(cities) * points_per_city:,} predicciones")

    rng = np.random.default_rng(seed=42)
    timestamp = datetime.now().isoformat()
    all_records = []
    SAMPLE_AREAS = [80, 120, 150, 200, 300, 500, 1000, 2000]
    ok = 0
    fail = 0

    for idx, city_info in enumerate(cities):
        city_name = city_info["name"]
        state = city_info["state"]
        clat = city_info["lat"]
        clon = city_info["lon"]
        pop = city_info["population"]

        spread = 0.015 + (min(pop, 5_000_000) / 15_000_000) * 0.07
        n_grid = int(points_per_city * 0.6)
        side = max(2, int(np.sqrt(n_grid)))

        points = []
        for lat_g in np.linspace(clat - spread, clat + spread, side):
            for lon_g in np.linspace(clon - spread, clon + spread, side):
                if len(points) >= n_grid:
                    break
                points.append((
                    round(float(lat_g + rng.normal(0, spread * 0.05)), 6),
                    round(float(lon_g + rng.normal(0, spread * 0.05)), 6),
                ))

        for _ in range(points_per_city - len(points)):
            points.append((
                round(float(clat + rng.normal(0, spread * 0.5)), 6),
                round(float(clon + rng.normal(0, spread * 0.5)), 6),
            ))

        points = points[:points_per_city]

        rows = [{
            "lat": p[0], "lon": p[1],
            "area_m2": float(rng.choice(SAMPLE_AREAS)),
            "price_mxn": float(rng.choice(SAMPLE_AREAS)) * 5000,
            "city": city_name, "state": state,
            "collection_date": "2026-04-03",
        } for p in points]

        df_in = pd.DataFrame(rows)

        try:
            df_feat = model.prepare_features(df_in)
            fcols = [c for c in model.feature_names if c in df_feat.columns]
            X = df_feat[fcols].fillna(0)
            X_s = pd.DataFrame(model.scaler.transform(X), columns=fcols, index=X.index)
            st_s = pd.Series([state] * len(X_s), index=X_s.index)
            preds = model._predict_batch_internal(X_s, st_s)

            city_avg = float(np.mean(preds[preds > 0])) if np.any(preds > 0) else 5000

            for i, (_, row) in enumerate(df_in.iterrows()):
                pp = max(500, float(preds[i]))
                dist = np.sqrt((row["lat"] - clat)**2 + (row["lon"] - clon)**2) * 111
                pr = pp / city_avg if city_avg > 0 else 1.0
                df_val = max(0, 1.0 - (dist / 15.0))
                pf = min(1.0, pop / 2_000_000)
                score = max(0, min(100, round(pr * 35 + df_val * 30 + pf * 20 + 15, 1)))
                growth = "alto" if score >= 70 else ("medio" if score >= 40 else "bajo")

                all_records.append({
                    "lat": row["lat"], "lon": row["lon"],
                    "city": city_name, "state": state,
                    "predicted_price_m2": round(pp, 2),
                    "plusvalia_score": score,
                    "growth_potential": growth,
                    "model_version": f"v{MODEL_VERSION}_national",
                    "model_confidence": round(min(95, 60 + score * 0.35), 1),
                    "prediction_date": timestamp,
                    "created_at": timestamp,
                })
            ok += 1
        except Exception as e:
            fail += 1
            if fail <= 3:
                logger.warning(f"  Error {city_name}: {e}")

        if (idx + 1) % 25 == 0:
            logger.info(f"  Progreso: {idx+1}/{len(cities)} ({len(all_records):,} preds)")

    logger.info(f"\n  Total: {len(all_records):,} predicciones ({ok} OK, {fail} fail)")
    return all_records


# ── Paso 5: Insertar ────────────────────────────────────────────────────────

def insert_predictions(records: List[Dict]):
    """Limpia predicciones viejas e inserta nuevas."""
    from supabase import create_client
    sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

    logger.info(f"\nPaso 5: Insertando {len(records):,} predicciones...")

    # Limpiar viejas
    logger.info("  Limpiando predicciones anteriores...")
    STATES_32 = [
        "Aguascalientes", "Baja California", "Baja California Sur", "Campeche",
        "Chiapas", "Chihuahua", "Ciudad de México", "Coahuila", "Colima",
        "Durango", "Estado de México", "Guanajuato", "Guerrero", "Hidalgo",
        "Jalisco", "Michoacán", "Morelos", "Nayarit", "Nuevo León", "Oaxaca",
        "Puebla", "Querétaro", "Quintana Roo", "San Luis Potosí", "Sinaloa",
        "Sonora", "Tabasco", "Tamaulipas", "Tlaxcala", "Veracruz", "Yucatán", "Zacatecas",
    ]
    for state in STATES_32:
        try:
            sb.table(TABLE_PREDICTIONS).delete().eq("state", state).execute()
        except Exception:
            pass

    # Insertar nuevas
    inserted = 0
    batch = 500
    for i in range(0, len(records), batch):
        chunk = records[i:i + batch]
        try:
            sb.table(TABLE_PREDICTIONS).insert(chunk).execute()
            inserted += len(chunk)
            if (i // batch) % 10 == 0:
                logger.info(f"    {inserted:,} / {len(records):,}")
        except Exception as e:
            logger.warning(f"    Error batch: {e}")
            for rec in chunk:
                try:
                    sb.table(TABLE_PREDICTIONS).insert(rec).execute()
                    inserted += 1
                except Exception:
                    pass

    logger.info(f"  Insertados: {inserted:,}")
    return inserted


# ── Main ────────────────────────────────────────────────────────────────────

def main(points_per_city: int = 200):
    start = time.time()

    logger.info("=" * 70)
    logger.info(f"PIPELINE COMPLETO: RETRAIN + PREDICT v{MODEL_VERSION}")
    logger.info(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    logger.info("=" * 70)

    # 1. Descargar
    df_raw = download_training_data()

    # 2. Limpiar
    df_clean = clean_training_data(df_raw)

    # 3. Entrenar
    model = train_model(df_clean)

    # 4. Predecir
    records = generate_predictions(model, points_per_city=points_per_city)

    # 5. Insertar
    insert_predictions(records)

    elapsed = time.time() - start
    logger.info(f"\n{'=' * 70}")
    logger.info(f"COMPLETADO en {elapsed/60:.1f} minutos")
    logger.info(f"  Datos entrenamiento: {len(df_clean):,}")
    logger.info(f"  Predicciones: {len(records):,}")
    logger.info(f"  Modelo: v{MODEL_VERSION}")
    logger.info("=" * 70)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--points-per-city", type=int, default=200)
    args = parser.parse_args()

    logger.remove()
    logger.add(sys.stdout, format="<green>{time:HH:mm:ss}</green> | <level>{level:<8}</level> | <level>{message}</level>", level="INFO")

    main(points_per_city=args.points_per_city)
