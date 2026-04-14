"""
Enriquecedor de datos de entrenamiento para estados con pocos registros.

Estrategia:
1. Normaliza nombres de estados duplicados en datos existentes
2. Para estados con <3000 registros, genera datos sintéticos basados en
   precios reales oficiales (SHF, CONAVI) + coordenadas reales de ciudades
3. Combina todo en un dataset unificado listo para entrenamiento

Fuentes de precios reales usados como base:
- SHF (Sociedad Hipotecaria Federal): índice de precios por zona metropolitana
- CONAVI/SNIIV: precios por segmento de vivienda por estado
- Properati: distribución de precios observada por estado
- INFONAVIT: valores de crédito por municipio

Uso:
    python -m scripts.enrich_training_data
    python -m scripts.enrich_training_data --target-per-state 5000
"""

import json
import sys
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

from config import DATA_DIR

# ── Normalización de estados ──────────────────────────────────────────────

STATE_NORMALIZATION: Dict[str, str] = {
    # Variantes conocidas -> nombre canónico
    "distrito federal": "Ciudad de México",
    "cdmx": "Ciudad de México",
    "ciudad de mexico": "Ciudad de México",
    "d.f.": "Ciudad de México",
    "df": "Ciudad de México",
    "estado de mexico": "Estado de México",
    "estado de méxico": "Estado de México",
    "mexico": "Estado de México",
    "méxico": "Estado de México",
    "veracruz de ignacio de la llave": "Veracruz",
    "veracruz": "Veracruz",
    "michoacan de ocampo": "Michoacán",
    "michoacán de ocampo": "Michoacán",
    "michoacan": "Michoacán",
    "michoacán": "Michoacán",
    "coahuila de zaragoza": "Coahuila",
    "coahuila": "Coahuila",
    "queretaro": "Querétaro",
    "querétaro": "Querétaro",
    "nuevo leon": "Nuevo León",
    "nuevo león": "Nuevo León",
    "yucatan": "Yucatán",
    "yucatán": "Yucatán",
    "san luis potosi": "San Luis Potosí",
    "san luis potosí": "San Luis Potosí",
    "quintana roo": "Quintana Roo",
    "baja california sur": "Baja California Sur",
    "baja california": "Baja California",
    "aguascalientes": "Aguascalientes",
    "campeche": "Campeche",
    "chiapas": "Chiapas",
    "chihuahua": "Chihuahua",
    "ciudad de méxico": "Ciudad de México",
    "colima": "Colima",
    "durango": "Durango",
    "guanajuato": "Guanajuato",
    "guerrero": "Guerrero",
    "hidalgo": "Hidalgo",
    "jalisco": "Jalisco",
    "morelos": "Morelos",
    "nayarit": "Nayarit",
    "oaxaca": "Oaxaca",
    "puebla": "Puebla",
    "sinaloa": "Sinaloa",
    "sonora": "Sonora",
    "tabasco": "Tabasco",
    "tamaulipas": "Tamaulipas",
    "tlaxcala": "Tlaxcala",
    "zacatecas": "Zacatecas",
}

# Precios reales de referencia por estado (MXN/m²) — basados en SHF 2025,
# CONAVI, y Properati observados. Terreno / Casa / Departamento.
# Formato: (media_terreno, std_terreno, media_casa, std_casa, media_depto, std_depto)
STATE_PRICE_PROFILES: Dict[str, Dict] = {
    "Aguascalientes":       {"terreno": (4500, 2200), "casa": (12000, 5000), "depto": (15000, 6000)},
    "Baja California":      {"terreno": (6000, 3500), "casa": (14000, 7000), "depto": (16000, 7000)},
    "Baja California Sur":  {"terreno": (8000, 5000), "casa": (18000, 9000), "depto": (22000, 10000)},
    "Campeche":             {"terreno": (2500, 1500), "casa": (8000, 4000), "depto": (10000, 4500)},
    "Chiapas":              {"terreno": (2000, 1200), "casa": (7000, 3500), "depto": (9000, 4000)},
    "Chihuahua":            {"terreno": (4000, 2500), "casa": (11000, 5500), "depto": (13000, 6000)},
    "Ciudad de México":     {"terreno": (25000, 15000), "casa": (35000, 18000), "depto": (40000, 20000)},
    "Coahuila":             {"terreno": (3500, 2000), "casa": (10000, 5000), "depto": (12000, 5500)},
    "Colima":               {"terreno": (4000, 2000), "casa": (10000, 4500), "depto": (12000, 5000)},
    "Durango":              {"terreno": (2800, 1500), "casa": (8500, 4000), "depto": (10000, 4500)},
    "Estado de México":     {"terreno": (8000, 5000), "casa": (15000, 8000), "depto": (18000, 9000)},
    "Guanajuato":           {"terreno": (4500, 2500), "casa": (11000, 5000), "depto": (14000, 6000)},
    "Guerrero":             {"terreno": (5000, 4000), "casa": (10000, 6000), "depto": (14000, 7000)},
    "Hidalgo":              {"terreno": (3000, 1800), "casa": (8000, 4000), "depto": (10000, 4500)},
    "Jalisco":              {"terreno": (8000, 5000), "casa": (16000, 8000), "depto": (20000, 9000)},
    "Michoacán":            {"terreno": (3000, 1800), "casa": (8500, 4200), "depto": (11000, 5000)},
    "Morelos":              {"terreno": (5000, 3000), "casa": (12000, 6000), "depto": (15000, 7000)},
    "Nayarit":              {"terreno": (5000, 3500), "casa": (10000, 5000), "depto": (14000, 6500)},
    "Nuevo León":           {"terreno": (8000, 5000), "casa": (18000, 9000), "depto": (22000, 10000)},
    "Oaxaca":               {"terreno": (2500, 1500), "casa": (7500, 3800), "depto": (10000, 4500)},
    "Puebla":               {"terreno": (4000, 2500), "casa": (10000, 5000), "depto": (13000, 6000)},
    "Querétaro":            {"terreno": (7000, 4000), "casa": (15000, 7000), "depto": (18000, 8000)},
    "Quintana Roo":         {"terreno": (10000, 7000), "casa": (18000, 10000), "depto": (25000, 12000)},
    "San Luis Potosí":      {"terreno": (3500, 2000), "casa": (9000, 4500), "depto": (12000, 5500)},
    "Sinaloa":              {"terreno": (4000, 2500), "casa": (10000, 5000), "depto": (13000, 6000)},
    "Sonora":               {"terreno": (3500, 2000), "casa": (10000, 5000), "depto": (12000, 5500)},
    "Tabasco":              {"terreno": (2500, 1500), "casa": (8000, 4000), "depto": (10000, 4500)},
    "Tamaulipas":           {"terreno": (3500, 2200), "casa": (9500, 5000), "depto": (12000, 5500)},
    "Tlaxcala":             {"terreno": (2500, 1500), "casa": (7500, 3500), "depto": (9000, 4000)},
    "Veracruz":             {"terreno": (3000, 2000), "casa": (8500, 4500), "depto": (11000, 5000)},
    "Yucatán":              {"terreno": (5000, 3000), "casa": (12000, 6000), "depto": (16000, 7500)},
    "Zacatecas":            {"terreno": (2200, 1200), "casa": (7000, 3500), "depto": (9000, 4000)},
}

# Distribución de tipos de propiedad por estado (terreno, casa, depto)
PROPERTY_TYPE_WEIGHTS = {
    "default": [0.30, 0.45, 0.25],
    "Ciudad de México": [0.10, 0.35, 0.55],
    "Quintana Roo": [0.35, 0.30, 0.35],
    "Baja California Sur": [0.35, 0.30, 0.35],
}

# Rangos de áreas típicas por tipo (m²)
AREA_RANGES = {
    "terreno":      (120, 5000, 2.0),   # min, max, lognormal_sigma
    "casa":         (60, 800, 0.8),
    "depto":        (40, 300, 0.6),
}


def normalize_state(state: str) -> str:
    """Normaliza un nombre de estado a su forma canónica."""
    if not isinstance(state, str):
        return ""
    key = state.strip().lower()
    return STATE_NORMALIZATION.get(key, state.strip())


def load_cities() -> Dict[str, List[Dict]]:
    """Carga las ciudades desde cities_mexico_32_states.json."""
    cities_path = DATA_DIR / "cities_mexico_32_states.json"
    if not cities_path.exists():
        logger.error(f"No se encontró {cities_path}")
        return {}

    with open(cities_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    cities_by_state: Dict[str, List[Dict]] = {}
    for state_obj in data.get("states", []):
        state_name = normalize_state(state_obj["name"])
        cities_by_state[state_name] = state_obj.get("cities", [])

    return cities_by_state


def generate_records_for_state(
    state: str,
    cities: List[Dict],
    n_records: int,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """
    Genera registros sintéticos basados en precios reales oficiales
    para un estado específico.
    """
    profile = STATE_PRICE_PROFILES.get(state)
    if not profile:
        logger.warning(f"Sin perfil de precios para {state}, usando defaults")
        profile = {"terreno": (4000, 2500), "casa": (10000, 5000), "depto": (13000, 6000)}

    weights = PROPERTY_TYPE_WEIGHTS.get(state, PROPERTY_TYPE_WEIGHTS["default"])
    prop_types = ["terreno", "casa", "departamento"]

    # Distribuir registros entre ciudades proporcionalmente a su población
    total_pop = sum(c.get("population", 100000) for c in cities)
    city_records: List[Tuple[Dict, int]] = []
    remaining = n_records

    for i, city in enumerate(cities):
        pop = city.get("population", 100000)
        if i == len(cities) - 1:
            n = remaining
        else:
            n = max(50, int(n_records * pop / total_pop))
            n = min(n, remaining)
        remaining -= n
        city_records.append((city, n))

    rows = []
    timestamp = datetime.now().strftime("%Y-%m-%d")

    for city, n_city in city_records:
        if n_city <= 0:
            continue

        city_lat = city["lat"]
        city_lon = city["lon"]
        city_name = city["name"]

        # Elegir tipo de propiedad para cada registro
        types_chosen = rng.choice(prop_types, size=n_city, p=weights)

        for prop_type in types_chosen:
            # Precio por m² — distribución lognormal basada en datos reales
            mean_price, std_price = profile[prop_type.replace("departamento", "depto")]
            # Usar lognormal para simular distribución real de precios
            log_mean = np.log(mean_price) - 0.5 * np.log(1 + (std_price / mean_price) ** 2)
            log_std = np.sqrt(np.log(1 + (std_price / mean_price) ** 2))
            price_m2 = float(rng.lognormal(log_mean, log_std))

            # Limitar a rangos razonables
            price_m2 = max(500, min(price_m2, 150000))

            # Área — distribución lognormal
            area_key = "depto" if prop_type == "departamento" else prop_type
            area_min, area_max, area_sigma = AREA_RANGES[area_key]
            area_median = (area_min + area_max) / 3  # sesgado hacia áreas menores
            area_m2 = float(rng.lognormal(np.log(area_median), area_sigma))
            area_m2 = max(area_min, min(area_m2, area_max))
            area_m2 = round(area_m2, 1)

            # Precio total
            price_mxn = round(price_m2 * area_m2, 0)

            # Coordenadas — dispersión realista alrededor del centro de la ciudad
            # Ciudades grandes: mayor dispersión (~5km)
            # Ciudades pequeñas: menor dispersión (~2km)
            pop = city.get("population", 100000)
            spread = 0.02 + (pop / 10_000_000) * 0.08  # ~2-10 km en grados
            lat = city_lat + float(rng.normal(0, spread))
            lon = city_lon + float(rng.normal(0, spread))

            # Dirección simulada
            colonias = [
                "Centro", "Norte", "Sur", "Poniente", "Oriente",
                "Industrial", "Residencial", "Jardines", "Lomas",
                "Las Palmas", "San José", "Santa Fe", "Vista Hermosa",
                "Del Valle", "La Paz", "Independencia", "Reforma",
                "Progreso", "Moderna", "Nueva", "Juárez",
            ]
            colonia = rng.choice(colonias)
            address = f"Col. {colonia}, {city_name}, {state}"

            rows.append({
                "title": f"{prop_type.capitalize()} en {colonia}, {city_name}",
                "price_mxn": price_mxn,
                "area_m2": area_m2,
                "price_m2": round(price_m2, 2),
                "address": address,
                "city": city_name,
                "state": state,
                "lat": round(lat, 6),
                "lon": round(lon, 6),
                "property_type": prop_type,
                "source": "shf_conavi_enriched",
                "source_url": "",
                "collection_date": timestamp,
            })

    return pd.DataFrame(rows)


def main(target_per_state: int = 5000):
    """Pipeline principal de enriquecimiento de datos."""
    logger.info("=" * 70)
    logger.info("ENRIQUECIMIENTO DE DATOS DE ENTRENAMIENTO")
    logger.info(f"  Target: {target_per_state:,} registros por estado")
    logger.info("=" * 70)

    # 1. Cargar dataset existente
    existing_path = DATA_DIR / "unified_training_data_20260325.csv"
    if not existing_path.exists():
        # Buscar el más reciente
        candidates = sorted(DATA_DIR.glob("unified_*.csv"), reverse=True)
        if candidates:
            existing_path = candidates[0]
        else:
            candidates = sorted(DATA_DIR.glob("training_ready_*.csv"), reverse=True)
            if candidates:
                existing_path = candidates[0]

    if existing_path.exists():
        df_existing = pd.read_csv(existing_path)
        logger.info(f"Dataset existente: {len(df_existing):,} registros de {existing_path.name}")
    else:
        logger.warning("No se encontró dataset existente, creando desde cero")
        df_existing = pd.DataFrame()

    # 2. Normalizar estados
    if not df_existing.empty and "state" in df_existing.columns:
        before_states = df_existing["state"].nunique()
        df_existing["state"] = df_existing["state"].apply(normalize_state)
        after_states = df_existing["state"].nunique()
        logger.info(f"Normalización: {before_states} -> {after_states} estados únicos")

        # Quitar registros sin estado
        df_existing = df_existing[df_existing["state"] != ""]

    # 3. Cargar ciudades
    cities_by_state = load_cities()
    logger.info(f"Ciudades cargadas: {sum(len(v) for v in cities_by_state.values())} ciudades en {len(cities_by_state)} estados")

    # 4. Identificar estados deficitarios
    if not df_existing.empty:
        state_counts = df_existing["state"].value_counts().to_dict()
    else:
        state_counts = {}

    all_states = list(STATE_PRICE_PROFILES.keys())
    rng = np.random.default_rng(seed=42)

    new_frames: List[pd.DataFrame] = []
    total_generated = 0

    logger.info(f"\n{'Estado':<30s} {'Existentes':>10s} {'Necesarios':>10s} {'Generar':>10s}")
    logger.info("-" * 65)

    for state in sorted(all_states):
        current = state_counts.get(state, 0)
        deficit = max(0, target_per_state - current)

        if deficit > 0:
            cities = cities_by_state.get(state, [])
            if not cities:
                # Mapeo alternativo para "Estado de México" -> "México"
                for alt_name in [state, state.replace("Estado de ", "")]:
                    cities = cities_by_state.get(alt_name, [])
                    if cities:
                        break

            if not cities:
                logger.warning(f"  {state}: sin ciudades configuradas, saltando")
                continue

            df_new = generate_records_for_state(state, cities, deficit, rng)
            new_frames.append(df_new)
            total_generated += len(df_new)
            logger.info(f"  {state:<28s} {current:>10,} {target_per_state:>10,} {deficit:>10,}")
        else:
            logger.info(f"  {state:<28s} {current:>10,} {target_per_state:>10,}          0")

    # 5. Combinar
    if new_frames:
        df_generated = pd.concat(new_frames, ignore_index=True)
        logger.info(f"\nTotal registros generados: {total_generated:,}")

        if not df_existing.empty:
            df_final = pd.concat([df_existing, df_generated], ignore_index=True)
        else:
            df_final = df_generated
    else:
        df_final = df_existing
        logger.info("\nTodos los estados tienen suficientes registros")

    # 6. Deduplicar
    before = len(df_final)
    df_final = df_final.drop_duplicates(
        subset=["title", "price_mxn", "city"],
        keep="first",
    )
    logger.info(f"Deduplicación: {before:,} -> {len(df_final):,}")

    # 7. Filtrar inválidos
    df_final = df_final[df_final["price_mxn"] > 0]
    df_final = df_final[df_final["state"] != ""]

    # 8. Guardar
    timestamp = datetime.now().strftime("%Y%m%d")
    output_path = DATA_DIR / f"unified_training_enriched_{timestamp}.csv"
    df_final.to_csv(output_path, index=False, encoding="utf-8-sig")
    logger.info(f"\nDataset enriquecido guardado: {output_path}")
    logger.info(f"Total final: {len(df_final):,} registros")

    # 9. Reporte final
    logger.info("\n" + "=" * 70)
    logger.info("REPORTE FINAL POR ESTADO")
    logger.info("=" * 70)

    final_counts = df_final["state"].value_counts()
    states_ok = 0
    states_low = 0

    logger.info(f"\n{'Estado':<30s} {'Registros':>10s} {'Status':>10s}")
    logger.info("-" * 55)

    for state in sorted(all_states):
        count = final_counts.get(state, 0)
        status = "OK" if count >= target_per_state else "BAJO"
        if count >= target_per_state:
            states_ok += 1
        else:
            states_low += 1
        logger.info(f"  {state:<28s} {count:>10,}  [{status}]")

    logger.info("-" * 55)
    logger.info(f"  TOTAL: {len(df_final):>10,}")
    logger.info(f"  Estados >= {target_per_state:,}: {states_ok}/32")
    logger.info(f"  Estados < {target_per_state:,}: {states_low}/32")

    # Por fuente
    logger.info(f"\n{'Fuente':<30s} {'Registros':>10s}")
    logger.info("-" * 45)
    for src, cnt in df_final["source"].value_counts().items():
        logger.info(f"  {src:<28s} {cnt:>10,}")

    # Con coordenadas
    with_coords = df_final[
        df_final["lat"].notna() & (df_final["lat"] != 0) &
        df_final["lon"].notna() & (df_final["lon"] != 0)
    ]
    pct = len(with_coords) / len(df_final) * 100
    logger.info(f"\n  Con coordenadas: {len(with_coords):,} / {len(df_final):,} ({pct:.1f}%)")

    return output_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Enriquecer datos de entrenamiento")
    parser.add_argument("--target-per-state", type=int, default=5000,
                        help="Registros mínimos por estado (default: 5000)")
    args = parser.parse_args()

    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level:<8}</level> | <level>{message}</level>",
        level="INFO",
    )

    main(target_per_state=args.target_per_state)
