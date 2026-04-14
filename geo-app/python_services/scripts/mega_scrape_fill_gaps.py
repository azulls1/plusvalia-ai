"""
Mega-scraper: Llena huecos de datos en los 32 estados de México.

Proceso:
  1. Diagnostica cobertura actual en iainmobiliaria_comparables
  2. Scrape Mercado Libre (API pública) enfocado en estados con pocos datos
  3. Limpia, normaliza y deduplica
  4. Inserta en iainmobiliaria_comparables (Supabase)
  5. Regenera predicciones con cobertura nacional completa

Uso:
    python -m scripts.mega_scrape_fill_gaps
    python -m scripts.mega_scrape_fill_gaps --skip-scrape   # solo regenerar predicciones
    python -m scripts.mega_scrape_fill_gaps --only-scrape   # solo scraping, no predicciones
"""

import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

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

# ── Constantes ────────────────────────────────────────────────────────────────

TARGET_MIN_PER_STATE = 800  # mínimo deseado por estado
BATCH_SIZE = 200

# Normalización de nombres de estado
STATE_NORMALIZE: Dict[str, str] = {
    "Distrito Federal": "Ciudad de México",
    "CDMX": "Ciudad de México",
    "México": "Estado de México",
    "Estado de Mexico": "Estado de México",
    "Coahuila de Zaragoza": "Coahuila",
    "Veracruz de Ignacio de la Llave": "Veracruz",
    "Michoacán de Ocampo": "Michoacán",
}

CANONICAL_STATES = [
    "Aguascalientes", "Baja California", "Baja California Sur", "Campeche",
    "Chiapas", "Chihuahua", "Ciudad de México", "Coahuila", "Colima",
    "Durango", "Estado de México", "Guanajuato", "Guerrero", "Hidalgo",
    "Jalisco", "Michoacán", "Morelos", "Nayarit", "Nuevo León", "Oaxaca",
    "Puebla", "Querétaro", "Quintana Roo", "San Luis Potosí", "Sinaloa",
    "Sonora", "Tabasco", "Tamaulipas", "Tlaxcala", "Veracruz", "Yucatán", "Zacatecas",
]

# Mapeo de estados canónicos a nombres de Mercado Libre
CANON_TO_ML: Dict[str, str] = {
    "Ciudad de México": "Ciudad de México",
    "Estado de México": "México",
    "Coahuila": "Coahuila",
    "Veracruz": "Veracruz",
    "Michoacán": "Michoacán",
}


def normalize_state(s: str) -> str:
    """Normaliza nombre de estado a forma canónica."""
    if not isinstance(s, str):
        return ""
    s = s.strip()
    return STATE_NORMALIZE.get(s, s)


# ── Paso 1: Diagnóstico ──────────────────────────────────────────────────────

def diagnose_coverage() -> Dict[str, int]:
    """Consulta Supabase para contar comparables por estado."""
    from supabase import create_client
    sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

    logger.info("=" * 70)
    logger.info("PASO 1: DIAGNÓSTICO DE COBERTURA")
    logger.info("=" * 70)

    # Consultar con las variantes de nombre
    all_variants = list(CANONICAL_STATES) + list(STATE_NORMALIZE.keys())
    state_counts: Dict[str, int] = {s: 0 for s in CANONICAL_STATES}

    for variant in set(all_variants):
        try:
            r = sb.table(TABLE_COMPARABLES).select("id", count="exact").eq("state", variant).execute()
            canon = normalize_state(variant)
            if canon in state_counts:
                state_counts[canon] += (r.count or 0)
        except Exception as e:
            logger.warning(f"  Error consultando {variant}: {e}")

    logger.info(f"\n{'Estado':<28} {'Registros':>10} {'Status':>15}")
    logger.info("-" * 58)

    gap_states = []
    for state in CANONICAL_STATES:
        count = state_counts[state]
        if count < 100:
            status = "CRITICO"
            gap_states.append((state, TARGET_MIN_PER_STATE - count))
        elif count < TARGET_MIN_PER_STATE:
            status = "BAJO"
            gap_states.append((state, TARGET_MIN_PER_STATE - count))
        elif count < 1000:
            status = "MEDIO"
        else:
            status = "OK"
        logger.info(f"  {state:<26} {count:>10,} {status:>15}")

    total = sum(state_counts.values())
    logger.info(f"\n  TOTAL: {total:,}")
    logger.info(f"  Estados que necesitan datos: {len(gap_states)}")

    if gap_states:
        logger.info("\n  PLAN DE SCRAPING:")
        for state, needed in sorted(gap_states, key=lambda x: -x[1]):
            logger.info(f"    {state:<26} necesita ~{needed:,} registros más")

    return state_counts


# ── Paso 2: Scraping Mercado Libre ───────────────────────────────────────────

async def scrape_missing_states(
    state_counts: Dict[str, int],
) -> pd.DataFrame:
    """Ejecuta scraper de Mercado Libre solo en estados con pocos datos."""
    from scrapers.mercadolibre_scraper import MercadoLibreScraper

    logger.info("\n" + "=" * 70)
    logger.info("PASO 2: SCRAPING MERCADO LIBRE — ESTADOS FALTANTES")
    logger.info("=" * 70)

    # Identificar estados que necesitan datos
    states_to_scrape = []
    for state in CANONICAL_STATES:
        count = state_counts.get(state, 0)
        if count < TARGET_MIN_PER_STATE:
            # Usar nombre de ML si es diferente
            ml_name = CANON_TO_ML.get(state, state)
            states_to_scrape.append(ml_name)
            logger.info(f"  -> {state} (actual: {count}, scrapeando como '{ml_name}')")

    if not states_to_scrape:
        logger.info("  Todos los estados tienen suficientes datos!")
        return pd.DataFrame()

    logger.info(f"\n  Scrapeando {len(states_to_scrape)} estados...")

    scraper = MercadoLibreScraper(
        delay=1.0,
        categories=["terrenos", "casas", "departamentos"],
    )

    df = await scraper.scrape_all_states(states=states_to_scrape)

    if not df.empty:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filepath = DATA_DIR / f"mercadolibre_gap_fill_{timestamp}.csv"
        df.to_csv(filepath, index=False, encoding="utf-8-sig")
        logger.info(f"  Scraping completado: {len(df):,} registros -> {filepath.name}")

        # Cobertura por estado
        state_dist = df.groupby("state").size().sort_values(ascending=False)
        for state, count in state_dist.items():
            logger.info(f"    {state:<30} {count:>6,}")
    else:
        logger.warning("  No se obtuvieron resultados del scraping")

    return df


# ── Paso 3: Limpieza y normalización ─────────────────────────────────────────

def clean_and_normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Limpia, normaliza y filtra datos para inserción."""
    if df.empty:
        return df

    logger.info("\n" + "=" * 70)
    logger.info("PASO 3: LIMPIEZA Y NORMALIZACIÓN")
    logger.info("=" * 70)

    initial = len(df)

    # Normalizar estados
    df["state"] = df["state"].apply(normalize_state)

    # Filtrar registros sin precio
    df = df[df["price_mxn"] > 0].copy()
    logger.info(f"  Después filtro precio > 0: {len(df):,}")

    # Filtrar precios absurdos
    df = df[(df["price_mxn"] >= 50_000) & (df["price_mxn"] <= 500_000_000)].copy()
    logger.info(f"  Después filtro precio razonable: {len(df):,}")

    # Filtrar si tiene coordenadas válidas (México bbox)
    if "lat" in df.columns and "lon" in df.columns:
        mask_coords = (
            df["lat"].notna() & df["lon"].notna() &
            (df["lat"] >= 14.0) & (df["lat"] <= 33.0) &
            (df["lon"] >= -118.5) & (df["lon"] <= -86.0)
        )
        df = df[mask_coords].copy()
        logger.info(f"  Después filtro coordenadas México: {len(df):,}")

    # Calcular price_m2 si falta
    if "area_m2" in df.columns:
        mask = (df["area_m2"] > 0) & (df["price_m2"].isna() | (df["price_m2"] <= 0))
        df.loc[mask, "price_m2"] = df.loc[mask, "price_mxn"] / df.loc[mask, "area_m2"]

    # Filtrar price_m2 absurdo
    if "price_m2" in df.columns:
        mask_pm2 = (df["price_m2"] > 0) & (df["price_m2"] >= 100) & (df["price_m2"] <= 500_000)
        df = df[mask_pm2 | (df["price_m2"] == 0)].copy()
        logger.info(f"  Después filtro price_m2 razonable: {len(df):,}")

    # Deduplicar
    if "id_source" in df.columns:
        before = len(df)
        df = df.drop_duplicates(subset=["id_source"], keep="first")
        logger.info(f"  Deduplicación por id_source: {before} -> {len(df)}")

    # Asegurar columnas necesarias
    required_cols = [
        "title", "price_mxn", "price_m2", "area_m2", "address",
        "city", "state", "lat", "lon", "property_type", "source",
        "source_url", "collection_date", "scraped_at",
    ]
    for col in required_cols:
        if col not in df.columns:
            df[col] = "" if col in ("title", "address", "source_url", "property_type") else None

    # Asegurar tipos
    df["collection_date"] = df["collection_date"].fillna(datetime.now().strftime("%Y-%m-%d"))
    df["scraped_at"] = df["scraped_at"].fillna(datetime.now().isoformat())
    df["source"] = df["source"].fillna("mercadolibre")

    logger.info(f"  Final: {len(df):,} registros (de {initial:,} originales)")
    return df


# ── Paso 4: Inserción en Supabase ───────────────────────────────────────────

def insert_to_supabase(df: pd.DataFrame) -> int:
    """Inserta registros limpios en iainmobiliaria_comparables."""
    if df.empty:
        return 0

    logger.info("\n" + "=" * 70)
    logger.info("PASO 4: INSERCIÓN EN SUPABASE")
    logger.info("=" * 70)

    from supabase import create_client
    sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

    # Columnas a insertar (las que la tabla acepta)
    insert_cols = [
        "title", "price_mxn", "price_m2", "area_m2", "address",
        "city", "state", "lat", "lon", "property_type", "source",
        "source_url", "collection_date", "scraped_at",
    ]

    # Convertir NaN a None para JSON
    df_insert = df[insert_cols].copy()
    df_insert = df_insert.where(pd.notna(df_insert), None)

    # Convertir floats que son NaN
    for col in ["price_mxn", "price_m2", "area_m2", "lat", "lon"]:
        if col in df_insert.columns:
            df_insert[col] = df_insert[col].apply(
                lambda x: round(float(x), 6) if pd.notna(x) and x is not None else None
            )

    records = df_insert.to_dict("records")
    inserted = 0
    failed = 0

    logger.info(f"  Insertando {len(records):,} registros en {TABLE_COMPARABLES}...")

    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]
        try:
            sb.table(TABLE_COMPARABLES).insert(batch).execute()
            inserted += len(batch)
            if (i // BATCH_SIZE) % 5 == 0:
                logger.info(f"    Progreso: {inserted:,} / {len(records):,}")
        except Exception as e:
            logger.warning(f"    Error batch {i//BATCH_SIZE}: {e}")
            # Insertar uno a uno
            for record in batch:
                try:
                    sb.table(TABLE_COMPARABLES).insert(record).execute()
                    inserted += 1
                except Exception:
                    failed += 1

    logger.info(f"  Insertados: {inserted:,} | Fallidos: {failed}")
    return inserted


# ── Paso 5: Regenerar predicciones ──────────────────────────────────────────

def regenerate_predictions(points_per_city: int = 150):
    """Regenera predicciones para todas las ciudades con más densidad."""
    logger.info("\n" + "=" * 70)
    logger.info("PASO 5: REGENERACIÓN DE PREDICCIONES")
    logger.info("=" * 70)

    # Cargar ciudades
    cities_path = DATA_DIR / "cities_mexico_32_states.json"
    with open(cities_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    cities = []
    for state_obj in data.get("states", []):
        state_name = state_obj["name"]
        for city in state_obj.get("cities", []):
            cities.append({
                "name": city["name"],
                "state": state_name,
                "lat": city["lat"],
                "lon": city["lon"],
                "population": city.get("population", 100000),
            })

    logger.info(f"  {len(cities)} ciudades en {len(set(c['state'] for c in cities))} estados")
    logger.info(f"  {points_per_city} puntos por ciudad = ~{len(cities) * points_per_city:,} predicciones")

    # Cargar modelo
    logger.info("  Cargando modelo...")
    from ml_model.hierarchical_model import HierarchicalPredictor

    model = HierarchicalPredictor(model_version="5.0")
    model_files = sorted(MODELS_DIR.glob("hierarchical_v5.0_*.pkl"), reverse=True)
    if not model_files:
        model_files = sorted(MODELS_DIR.glob("hierarchical_*.pkl"), reverse=True)

    if not model_files:
        logger.error("No se encontró modelo entrenado!")
        return

    model.load_model(str(model_files[0]))
    logger.info(f"  Modelo cargado: {model_files[0].name}")

    # Conectar Supabase
    from supabase import create_client
    sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

    # Limpiar predicciones anteriores
    logger.info("  Limpiando predicciones anteriores...")
    try:
        # Borrar en batches por estado para no timeout
        for state in CANONICAL_STATES:
            sb.table(TABLE_PREDICTIONS).delete().eq("state", state).execute()
        logger.info("  Predicciones anteriores eliminadas")
    except Exception as e:
        logger.warning(f"  Error limpiando: {e}")

    # Generar predicciones
    rng = np.random.default_rng(seed=42)
    timestamp = datetime.now().isoformat()
    all_records = []
    cities_ok = 0
    cities_fail = 0

    SAMPLE_AREAS = [80, 120, 150, 200, 300, 500, 1000, 2000]

    for idx, city_info in enumerate(cities):
        city_name = city_info["name"]
        state = city_info["state"]
        center_lat = city_info["lat"]
        center_lon = city_info["lon"]
        population = city_info["population"]

        # Dispersión proporcional a población
        spread = 0.015 + (population / 15_000_000) * 0.07

        # Generar puntos: 60% grilla + 40% aleatorio
        n_grid = int(points_per_city * 0.6)
        n_random = points_per_city - n_grid
        side = max(2, int(np.sqrt(n_grid)))

        points = []
        lats_grid = np.linspace(center_lat - spread, center_lat + spread, side)
        lons_grid = np.linspace(center_lon - spread, center_lon + spread, side)

        for lat in lats_grid:
            for lon in lons_grid:
                if len(points) >= n_grid:
                    break
                points.append({
                    "lat": round(float(lat + rng.normal(0, spread * 0.05)), 6),
                    "lon": round(float(lon + rng.normal(0, spread * 0.05)), 6),
                })

        for _ in range(n_random):
            points.append({
                "lat": round(float(center_lat + rng.normal(0, spread * 0.6)), 6),
                "lon": round(float(center_lon + rng.normal(0, spread * 0.6)), 6),
            })

        points = points[:points_per_city]

        # Preparar input
        rows = []
        for pt in points:
            area = float(rng.choice(SAMPLE_AREAS))
            rows.append({
                "lat": pt["lat"], "lon": pt["lon"],
                "area_m2": area, "price_mxn": area * 5000,
                "city": city_name, "state": state,
                "collection_date": "2026-04-03",
            })

        df_input = pd.DataFrame(rows)

        try:
            df_features = model.prepare_features(df_input)
            feature_cols = [c for c in model.feature_names if c in df_features.columns]
            X = df_features[feature_cols].fillna(0)
            X_scaled = pd.DataFrame(
                model.scaler.transform(X), columns=feature_cols, index=X.index,
            )

            states_series = pd.Series([state] * len(X_scaled), index=X_scaled.index)
            predictions = model._predict_batch_internal(X_scaled, states_series)

            city_avg = float(np.mean(predictions[predictions > 0])) if np.any(predictions > 0) else 5000

            for i, (_, row) in enumerate(df_input.iterrows()):
                pred_price = max(500, float(predictions[i]))
                dist = np.sqrt(
                    (row["lat"] - center_lat) ** 2 + (row["lon"] - center_lon) ** 2
                ) * 111

                # Plusvalía score
                price_ratio = pred_price / city_avg if city_avg > 0 else 1.0
                distance_factor = max(0, 1.0 - (dist / 15.0))
                pop_factor = min(1.0, population / 2_000_000)
                score = max(0, min(100, round(
                    price_ratio * 35 + distance_factor * 30 + pop_factor * 20 + 15, 1
                )))

                growth = "alto" if score >= 70 else ("medio" if score >= 40 else "bajo")

                all_records.append({
                    "lat": row["lat"],
                    "lon": row["lon"],
                    "city": city_name,
                    "state": state,
                    "predicted_price_m2": round(pred_price, 2),
                    "plusvalia_score": score,
                    "growth_potential": growth,
                    "model_version": "v5.0_national",
                    "model_confidence": round(min(95, 60 + score * 0.35), 1),
                    "prediction_date": timestamp,
                    "created_at": timestamp,
                })

            cities_ok += 1
        except Exception as e:
            cities_fail += 1
            if cities_fail <= 5:
                logger.warning(f"  Error en {city_name}, {state}: {e}")

        if (idx + 1) % 25 == 0:
            logger.info(f"  Progreso: {idx+1}/{len(cities)} ciudades ({len(all_records):,} predicciones)")

    logger.info(f"\n  Generadas: {len(all_records):,} predicciones "
                f"({cities_ok} OK, {cities_fail} fallidas)")

    # Insertar predicciones
    logger.info(f"  Insertando {len(all_records):,} predicciones...")
    inserted = 0
    batch_size = 500

    for i in range(0, len(all_records), batch_size):
        batch = all_records[i:i + batch_size]
        try:
            sb.table(TABLE_PREDICTIONS).insert(batch).execute()
            inserted += len(batch)
            if (i // batch_size) % 10 == 0:
                logger.info(f"    Insertados: {inserted:,} / {len(all_records):,}")
        except Exception as e:
            logger.warning(f"    Error batch {i//batch_size}: {e}")
            for record in batch:
                try:
                    sb.table(TABLE_PREDICTIONS).insert(record).execute()
                    inserted += 1
                except Exception:
                    pass

    logger.info(f"  Predicciones insertadas: {inserted:,}")

    # Estadísticas por estado
    df_stats = pd.DataFrame(all_records)
    if not df_stats.empty:
        logger.info(f"\n  {'Estado':<28} {'Predicciones':>12} {'Avg $/m²':>12} {'Avg Score':>10}")
        logger.info("  " + "-" * 66)
        for state in sorted(df_stats["state"].unique()):
            g = df_stats[df_stats["state"] == state]
            logger.info(
                f"  {state:<28} {len(g):>12,} "
                f"${g['predicted_price_m2'].mean():>10,.0f} "
                f"{g['plusvalia_score'].mean():>9.1f}"
            )

    return len(all_records)


# ── Main ────────────────────────────────────────────────────────────────────

async def main(skip_scrape: bool = False, only_scrape: bool = False,
               points_per_city: int = 150):
    """Pipeline completo."""
    start = time.time()

    logger.info("=" * 70)
    logger.info("MEGA-SCRAPER: COBERTURA NACIONAL COMPLETA")
    logger.info(f"  Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    logger.info(f"  Skip scrape: {skip_scrape}")
    logger.info(f"  Only scrape: {only_scrape}")
    logger.info(f"  Points per city: {points_per_city}")
    logger.info("=" * 70)

    # Paso 1: Diagnóstico
    state_counts = diagnose_coverage()

    # Paso 2-4: Scraping e inserción
    if not skip_scrape:
        df_scraped = await scrape_missing_states(state_counts)

        if not df_scraped.empty:
            # Paso 3: Limpieza
            df_clean = clean_and_normalize(df_scraped)

            # Paso 4: Inserción
            if not df_clean.empty:
                inserted = insert_to_supabase(df_clean)
                logger.info(f"\n  Nuevos registros insertados: {inserted:,}")
            else:
                logger.info("  No hay registros limpios para insertar")
        else:
            logger.info("  No se obtuvieron datos del scraping")

        # Diagnóstico post-scraping
        logger.info("\n  COBERTURA POST-SCRAPING:")
        diagnose_coverage()

    # Paso 5: Regenerar predicciones
    if not only_scrape:
        regenerate_predictions(points_per_city=points_per_city)

    elapsed = time.time() - start
    logger.info("\n" + "=" * 70)
    logger.info(f"COMPLETADO en {elapsed/60:.1f} minutos")
    logger.info("=" * 70)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Mega-scraper cobertura nacional")
    parser.add_argument("--skip-scrape", action="store_true",
                        help="Saltar scraping, solo regenerar predicciones")
    parser.add_argument("--only-scrape", action="store_true",
                        help="Solo scraping, no regenerar predicciones")
    parser.add_argument("--points-per-city", type=int, default=150,
                        help="Puntos de predicción por ciudad (default: 150)")
    args = parser.parse_args()

    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level:<8}</level> | <level>{message}</level>",
        level="INFO",
    )

    asyncio.run(main(
        skip_scrape=args.skip_scrape,
        only_scrape=args.only_scrape,
        points_per_city=args.points_per_city,
    ))
