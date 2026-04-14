"""
Genera una grilla DENSA de predicciones cubriendo TODO el territorio mexicano.

Usa un poligono real (40+ vertices) del contorno de Mexico en vez de
rectangulos simples, con un paso de 0.08 grados (~9km) para eliminar
cualquier hueco blanco en el mapa.

Target: 40,000-50,000 puntos cubriendo costas, fronteras, peninsulas
y todo el interior sin falsos negativos.

Uso:
    python -m scripts.generate_dense_grid
    python -m scripts.generate_dense_grid --step 0.08
    python -m scripts.generate_dense_grid --step 0.06 --dry-run
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

# ================================================================
# Mexico territory polygon (~50 vertices, clockwise)
#
# This traces Mexico's actual border including:
#   - US border (Tijuana to Matamoros)
#   - Gulf of Mexico coast
#   - Yucatan peninsula
#   - Guatemala/Belize border
#   - Pacific coast (Chiapas, Oaxaca, Guerrero, Michoacan, Jalisco)
#   - Baja California peninsula (separate polygon)
# ================================================================

# Continental Mexico polygon (clockwise, lat/lon pairs)
MEXICO_MAINLAND = [
    # --- US Border (west to east) ---
    (32.54, -117.03),   # Tijuana
    (32.72, -115.50),   # Mexicali
    (31.75, -113.00),   # Sonora desert border
    (31.33, -110.94),   # Nogales
    (31.33, -109.05),   # Agua Prieta
    (31.78, -106.44),   # Ciudad Juarez
    (31.00, -105.00),   # Big Bend area
    (29.80, -104.40),   # Chihuahua border bend
    (29.40, -103.30),   # Border along Rio Grande
    (29.00, -102.40),   # Coahuila border
    (28.70, -100.50),   # Eagle Pass / Piedras Negras
    (27.50, -99.50),    # Laredo / Nuevo Laredo
    (26.50, -98.80),    # McAllen / Reynosa
    (25.95, -97.15),    # Matamoros

    # --- Gulf of Mexico coast (south) ---
    (24.80, -97.50),    # Tamaulipas coast
    (23.80, -97.80),    # South Tamaulipas
    (22.30, -97.80),    # North Veracruz
    (21.50, -97.40),    # Tuxpan area
    (20.60, -96.90),    # Veracruz mid
    (19.80, -96.40),    # Veracruz city
    (19.20, -96.10),    # South Veracruz
    (18.65, -95.60),    # Coatzacoalcos
    (18.45, -94.80),    # Tabasco west
    (18.20, -93.40),    # Tabasco coast
    (18.50, -92.60),    # Tabasco/Campeche border
    (18.70, -91.50),    # Campeche

    # --- Yucatan peninsula ---
    (19.60, -90.60),    # Campeche city
    (20.50, -90.30),    # Merida area
    (21.30, -90.00),    # North Yucatan coast
    (21.50, -89.20),    # Progreso
    (21.50, -88.20),    # NE Yucatan
    (21.20, -87.40),    # Holbox area
    (21.20, -86.80),    # Cancun

    # --- East coast Quintana Roo ---
    (20.50, -87.30),    # Riviera Maya
    (19.60, -87.40),    # Tulum
    (18.50, -88.30),    # Chetumal

    # --- Guatemala / Belize border ---
    (17.80, -89.10),    # Peten border
    (16.10, -90.50),    # Guatemala border west
    (15.70, -91.40),    # Chiapas Guatemala border
    (14.55, -92.20),    # SE Chiapas tip

    # --- Pacific coast (east to west) ---
    (14.80, -92.70),    # Chiapas Pacific coast
    (15.40, -93.20),    # Tonala, Chiapas
    (15.80, -94.20),    # Istmo Tehuantepec (Pacific side)
    (15.90, -95.30),    # Huatulco area
    (16.10, -96.50),    # Puerto Escondido
    (16.50, -98.20),    # Oaxaca coast
    (16.80, -99.80),    # Acapulco area
    (17.60, -101.40),   # Ixtapa, Guerrero
    (18.00, -102.60),   # Lazaro Cardenas
    (18.50, -103.50),   # Colima coast
    (18.90, -104.30),   # Jalisco south coast
    (19.70, -105.20),   # Puerto Vallarta
    (20.60, -105.50),   # Nayarit coast
    (21.50, -105.30),   # Mazatlan area
    (22.80, -106.00),   # South Sinaloa
    (23.20, -106.50),   # Mazatlan north
    (24.80, -108.00),   # Los Mochis area
    (26.00, -109.30),   # South Sonora coast
    (27.50, -110.30),   # Guaymas area
    (28.80, -111.50),   # Hermosillo coast
    (30.00, -112.80),   # Puerto Penasco area
    (31.30, -113.50),   # NW Sonora coast
    (32.54, -117.03),   # Back to Tijuana (close polygon)
]

# Baja California peninsula (separate polygon, clockwise)
BAJA_CALIFORNIA = [
    (32.54, -117.10),   # Tijuana Pacific side
    (32.20, -117.15),   # Rosarito
    (30.80, -116.60),   # Ensenada
    (29.00, -115.50),   # San Quintin
    (27.50, -114.50),   # Guerrero Negro area
    (26.00, -113.00),   # Mulegue
    (24.50, -112.00),   # Loreto
    (23.50, -110.50),   # La Paz
    (22.90, -109.90),   # Cabo San Lucas
    (23.00, -109.60),   # San Jose del Cabo
    (23.70, -109.80),   # East Cape
    (24.20, -110.10),   # La Paz east
    (25.00, -110.80),   # Loreto east coast
    (26.50, -111.50),   # Santa Rosalia
    (27.80, -112.80),   # Bahia de los Angeles
    (28.80, -113.20),   # NE Baja
    (29.50, -114.00),   # San Felipe
    (30.50, -114.70),   # NE Baja California
    (31.50, -115.50),   # Tecate area
    (32.50, -116.50),   # Tijuana east
    (32.54, -117.10),   # Close polygon
]

# Bounding box for quick rejection
MEX_LAT_MIN = 14.5
MEX_LAT_MAX = 32.8
MEX_LON_MIN = -118.0
MEX_LON_MAX = -86.5


# ================================================================
# Point-in-polygon (ray-casting algorithm)
# ================================================================

def _point_in_polygon(lat: float, lon: float, polygon: List[Tuple[float, float]]) -> bool:
    """Ray-casting algorithm for point-in-polygon test.

    Uses the even-odd rule: cast a ray from (lat, lon) to the right
    and count how many polygon edges it crosses. Odd = inside.
    """
    n = len(polygon)
    inside = False
    j = n - 1
    for i in range(n):
        yi, xi = polygon[i]
        yj, xj = polygon[j]
        if ((yi > lat) != (yj > lat)) and (lon < (xj - xi) * (lat - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


def point_in_mexico(lat: float, lon: float) -> bool:
    """Check if a point falls within Mexico's territory.

    Tests against mainland polygon and Baja California peninsula.
    Uses bounding-box pre-filter for speed.
    """
    # Quick bounding-box rejection
    if lat < MEX_LAT_MIN or lat > MEX_LAT_MAX:
        return False
    if lon < MEX_LON_MIN or lon > MEX_LON_MAX:
        return False

    # Test mainland first (most points)
    if _point_in_polygon(lat, lon, MEXICO_MAINLAND):
        return True

    # Test Baja California peninsula
    if _point_in_polygon(lat, lon, BAJA_CALIFORNIA):
        return True

    return False


# ================================================================
# Nearest-city lookup with KD-tree for speed
# ================================================================

def build_city_index(cities: List[Dict]) -> Tuple[np.ndarray, List[Dict]]:
    """Build a numpy array of city coordinates for vectorized nearest lookup."""
    coords = np.array([[c["lat"], c["lon"]] for c in cities])
    return coords, cities


def find_nearest_city_batch(
    lats: np.ndarray,
    lons: np.ndarray,
    city_coords: np.ndarray,
    cities: List[Dict],
) -> Tuple[List[str], List[str], np.ndarray]:
    """Find nearest city for a batch of points using vectorized distance.

    Returns (city_names, state_names, distances_km).
    """
    # Shape: (n_points, 1) vs (1, n_cities) -> broadcast to (n_points, n_cities)
    dlat = lats[:, None] - city_coords[None, :, 0]
    dlon = lons[:, None] - city_coords[None, :, 1]
    # Approximate km using Euclidean * 111 (good enough for nearest lookup)
    dist_sq = dlat ** 2 + dlon ** 2
    nearest_idx = np.argmin(dist_sq, axis=1)
    nearest_dist_km = np.sqrt(dist_sq[np.arange(len(lats)), nearest_idx]) * 111.0

    city_names = [cities[i]["name"] for i in nearest_idx]
    state_names = [cities[i]["state"] for i in nearest_idx]
    return city_names, state_names, nearest_dist_km


def find_nearest_city(lat: float, lon: float, cities: List[Dict]) -> Tuple[str, str, float]:
    """Single-point fallback: find nearest city."""
    best_dist = float("inf")
    best_city = "Rural"
    best_state = "Unknown"
    for c in cities:
        d = math.sqrt((lat - c["lat"]) ** 2 + (lon - c["lon"]) ** 2) * 111
        if d < best_dist:
            best_dist = d
            best_city = c["name"]
            best_state = c["state"]
    return best_city, best_state, best_dist


# ================================================================
# Main generation routine
# ================================================================

def main(step_deg: float = 0.08, batch_size: int = 500, dry_run: bool = False):
    """Generate a dense national prediction grid covering all of Mexico.

    Args:
        step_deg: Grid spacing in degrees. 0.08 ~ 9km -> ~45k points.
        batch_size: Supabase insert batch size.
        dry_run: If True, generate grid and predict but do NOT write to DB.
    """
    start = time.time()

    logger.info("=" * 70)
    logger.info("GRILLA DENSA NACIONAL - POLIGONO REAL DE MEXICO")
    logger.info(f"  Step: {step_deg} deg (~{step_deg * 111:.1f} km)")
    logger.info(f"  Bbox: ({MEX_LAT_MIN}, {MEX_LON_MIN}) -> ({MEX_LAT_MAX}, {MEX_LON_MAX})")
    logger.info(f"  Mainland vertices: {len(MEXICO_MAINLAND)}")
    logger.info(f"  Baja vertices: {len(BAJA_CALIFORNIA)}")
    logger.info(f"  Dry run: {dry_run}")
    logger.info("=" * 70)

    # ------------------------------------------------------------------
    # 1. Load cities
    # ------------------------------------------------------------------
    cities_path = DATA_DIR / "cities_mexico_32_states.json"
    with open(cities_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    cities: List[Dict] = []
    for state_obj in data.get("states", []):
        for city in state_obj.get("cities", []):
            cities.append({
                "name": city["name"],
                "state": state_obj["name"],
                "lat": city["lat"],
                "lon": city["lon"],
                "population": city.get("population", 50000),
            })

    logger.info(f"  {len(cities)} ciudades de referencia cargadas")
    city_coords_np, cities_list = build_city_index(cities)

    # ------------------------------------------------------------------
    # 2. Generate grid with real polygon test
    # ------------------------------------------------------------------
    logger.info("\nGenerando grilla con poligono real...")

    grid_lats = []
    grid_lons = []

    lat = MEX_LAT_MIN
    while lat <= MEX_LAT_MAX:
        lon = MEX_LON_MIN
        while lon <= MEX_LON_MAX:
            if point_in_mexico(lat, lon):
                grid_lats.append(round(lat, 4))
                grid_lons.append(round(lon, 4))
            lon += step_deg
        lat += step_deg

    n_points = len(grid_lats)
    grid_lats_np = np.array(grid_lats)
    grid_lons_np = np.array(grid_lons)

    logger.info(f"  Puntos generados: {n_points:,}")

    if n_points < 30000:
        logger.warning(f"  ADVERTENCIA: Solo {n_points:,} puntos. Considera reducir --step")
    elif n_points > 70000:
        logger.warning(f"  ADVERTENCIA: {n_points:,} puntos (muy denso). Considera aumentar --step")
    else:
        logger.info(f"  Densidad OK para cobertura completa")

    # ------------------------------------------------------------------
    # 3. Batch nearest-city lookup (vectorized)
    # ------------------------------------------------------------------
    logger.info("\nAsignando ciudad mas cercana a cada punto...")

    CITY_BATCH = 5000
    all_city_names = []
    all_state_names = []
    all_dist_km = []

    for i in range(0, n_points, CITY_BATCH):
        end = min(i + CITY_BATCH, n_points)
        c_names, s_names, dists = find_nearest_city_batch(
            grid_lats_np[i:end],
            grid_lons_np[i:end],
            city_coords_np,
            cities_list,
        )
        all_city_names.extend(c_names)
        all_state_names.extend(s_names)
        all_dist_km.extend(dists.tolist())

    # Count states covered
    unique_states = set(all_state_names)
    logger.info(f"  Estados cubiertos: {len(unique_states)}")
    for st in sorted(unique_states):
        cnt = all_state_names.count(st)
        logger.info(f"    {st}: {cnt:,} puntos")

    # ------------------------------------------------------------------
    # 4. Load model
    # ------------------------------------------------------------------
    logger.info("\nCargando modelo...")
    from ml_model.hierarchical_model import HierarchicalPredictor

    model = HierarchicalPredictor(model_version="6.0")
    model_files = sorted(MODELS_DIR.glob("hierarchical_v6.0_*.pkl"), reverse=True)
    if not model_files:
        model_files = sorted(MODELS_DIR.glob("hierarchical_*.pkl"), reverse=True)
    if not model_files:
        logger.error("No se encontro archivo de modelo! Abortando.")
        return

    model.load_model(str(model_files[0]))
    logger.info(f"  Modelo cargado: {model_files[0].name}")

    # ------------------------------------------------------------------
    # 5. Predict in chunks
    # ------------------------------------------------------------------
    logger.info("\nGenerando predicciones...")
    rng = np.random.default_rng(seed=42)
    timestamp = datetime.now().isoformat()
    AREAS = [120, 150, 200, 300, 500]
    chunk_size = 500
    all_records: List[Dict] = []
    errors = 0

    for i in range(0, n_points, chunk_size):
        end = min(i + chunk_size, n_points)

        rows = []
        for j in range(i, end):
            area = float(rng.choice(AREAS))
            rows.append({
                "lat": grid_lats[j],
                "lon": grid_lons[j],
                "area_m2": area,
                "price_mxn": area * 5000,  # Dummy seed price
                "city": all_city_names[j],
                "state": all_state_names[j],
                "collection_date": "2026-04-03",
            })

        df_in = pd.DataFrame(rows)

        try:
            df_feat = model.prepare_features(df_in)
            fcols = [c for c in model.feature_names if c in df_feat.columns]
            X = df_feat[fcols].fillna(0)
            X_s = pd.DataFrame(
                model.scaler.transform(X), columns=fcols, index=X.index
            )
            st_s = pd.Series(
                [r["state"] for r in rows], index=X_s.index
            )
            preds = model._predict_batch_internal(X_s, st_s)

            for j_local, j_global in enumerate(range(i, end)):
                pp = max(500, float(preds[j_local]))
                dist_km = all_dist_km[j_global]

                # Plusvalia score: higher near cities + higher prices
                urban_factor = max(0.3, min(1.0, 1.0 - dist_km / 50.0))
                score = max(10, min(95, round(50 + pp / 500 * urban_factor, 1)))
                growth = "alto" if score >= 70 else ("medio" if score >= 40 else "bajo")

                all_records.append({
                    "lat": grid_lats[j_global],
                    "lon": grid_lons[j_global],
                    "city": all_city_names[j_global],
                    "state": all_state_names[j_global],
                    "predicted_price_m2": round(pp, 2),
                    "plusvalia_score": score,
                    "growth_potential": growth,
                    "model_version": "v6.0_dense_grid",
                    "model_confidence": round(min(90, 50 + urban_factor * 40), 1),
                    "prediction_date": timestamp,
                    "created_at": timestamp,
                })
        except Exception as e:
            errors += 1
            if errors <= 5:
                logger.warning(f"  Error chunk {i}-{end}: {e}")

        # Progress logging every 20 chunks
        chunk_num = i // chunk_size
        if chunk_num % 20 == 0 and i > 0:
            pct = i / n_points * 100
            logger.info(
                f"  Progreso: {i:,}/{n_points:,} ({pct:.0f}%) "
                f"-> {len(all_records):,} predicciones"
            )

    logger.info(f"\n  Total predicciones: {len(all_records):,}")
    logger.info(f"  Errores: {errors}")

    # ------------------------------------------------------------------
    # 6. Stats summary
    # ------------------------------------------------------------------
    df_stats = pd.DataFrame(all_records)
    logger.info(f"\n  {'Estado':<28} {'Puntos':>8} {'Avg $/m2':>12} {'Min':>10} {'Max':>10}")
    logger.info("  " + "-" * 72)
    for state in sorted(df_stats["state"].unique()):
        g = df_stats[df_stats["state"] == state]
        logger.info(
            f"  {state:<28} {len(g):>8,} "
            f"${g['predicted_price_m2'].mean():>10,.0f} "
            f"${g['predicted_price_m2'].min():>8,.0f} "
            f"${g['predicted_price_m2'].max():>8,.0f}"
        )

    # ------------------------------------------------------------------
    # 7. Insert into Supabase
    # ------------------------------------------------------------------
    if dry_run:
        logger.info(f"\n  DRY RUN: No se insertaron datos. "
                     f"Se generarian {len(all_records):,} filas.")
        elapsed = time.time() - start
        logger.info(f"  Completado en {elapsed / 60:.1f} minutos")
        return

    logger.info(f"\nInsertando {len(all_records):,} predicciones en Supabase...")
    from supabase import create_client
    sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

    # Delete previous dense grid AND old national grid
    for old_version in ["v6.0_dense_grid", "v6.0_grid_national"]:
        try:
            sb.table(TABLE_PREDICTIONS).delete().eq(
                "model_version", old_version
            ).execute()
            logger.info(f"  Grilla anterior '{old_version}' eliminada")
        except Exception as e:
            logger.warning(f"  No se pudo borrar '{old_version}': {e}")

    inserted = 0
    failed_batches = 0
    for i in range(0, len(all_records), batch_size):
        batch = all_records[i : i + batch_size]
        try:
            sb.table(TABLE_PREDICTIONS).insert(batch).execute()
            inserted += len(batch)
        except Exception as e:
            failed_batches += 1
            if failed_batches <= 3:
                logger.warning(f"  Error batch {i}: {e}")
            # Fallback: insert one-by-one
            for rec in batch:
                try:
                    sb.table(TABLE_PREDICTIONS).insert(rec).execute()
                    inserted += 1
                except Exception:
                    pass

        if (i // batch_size) % 20 == 0 and i > 0:
            logger.info(f"    Insertados: {inserted:,} / {len(all_records):,}")

    logger.info(f"  Insertados exitosamente: {inserted:,}")
    if failed_batches > 0:
        logger.warning(f"  Batches con error: {failed_batches}")

    elapsed = time.time() - start
    logger.info(f"\n  Completado en {elapsed / 60:.1f} minutos")
    logger.info(f"  Cobertura: {len(unique_states)} estados, {n_points:,} puntos")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Genera grilla densa de predicciones sobre todo Mexico"
    )
    parser.add_argument(
        "--step", type=float, default=0.08,
        help="Paso en grados (0.08 = ~9km, default)"
    )
    parser.add_argument(
        "--batch-size", type=int, default=500,
        help="Tamano de batch para insercion en Supabase (default 500)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Solo generar grilla y predecir, sin insertar en DB"
    )
    args = parser.parse_args()

    try:
        logger.remove()
        logger.add(
            sys.stdout,
            format="<green>{time:HH:mm:ss}</green> | <level>{level:<8}</level> | <level>{message}</level>",
            level="INFO",
        )
    except Exception:
        pass

    main(step_deg=args.step, batch_size=args.batch_size, dry_run=args.dry_run)
