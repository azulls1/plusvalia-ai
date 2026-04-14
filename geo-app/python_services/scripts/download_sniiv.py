"""
Download and process SNIIV (SEDATU) Mexican government housing data.

Source: Sistema Nacional de Información e Indicadores de Vivienda
API: https://sniiv.sedatu.gob.mx/api/CuboAPI/

Data cubes used:
  - Financiamiento: Housing credits with monetary amounts per municipality
  - Registro de Vivienda: Housing registration counts per municipality/segment
  - Inventario de Vivienda: Housing inventory per municipality

License: Open data, attribution required (SEDATU/CONAVI)
"""
import pandas as pd
import numpy as np
import requests
import json
import time
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)

# ── Paths ────────────────────────────────────────────────────────────────────
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
SNIIV_DIR = DATA_DIR / "sniiv"
SNIIV_DIR.mkdir(exist_ok=True)

# ── SNIIV API Configuration ─────────────────────────────────────────────────
BASE_URL = "https://sniiv.sedatu.gob.mx/api/CuboAPI"

# INEGI state codes → state names (2-digit codes used by SNIIV clave_municipio)
# The API returns municipality names directly, but clave_municipio is a 3-digit
# code within each state. The state is inferred from the sequential ordering.
INEGI_STATE_CODES = {
    "01": "Aguascalientes", "02": "Baja California", "03": "Baja California Sur",
    "04": "Campeche", "05": "Coahuila", "06": "Colima",
    "07": "Chiapas", "08": "Chihuahua", "09": "Ciudad de México",
    "10": "Durango", "11": "Guanajuato", "12": "Guerrero",
    "13": "Hidalgo", "14": "Jalisco", "15": "Estado de México",
    "16": "Michoacán", "17": "Morelos", "18": "Nayarit",
    "19": "Nuevo León", "20": "Oaxaca", "21": "Puebla",
    "22": "Querétaro", "23": "Quintana Roo", "24": "San Luis Potosí",
    "25": "Sinaloa", "26": "Sonora", "27": "Tabasco",
    "28": "Tamaulipas", "29": "Tlaxcala", "30": "Veracruz",
    "31": "Yucatán", "32": "Zacatecas",
}

# Housing segment → approximate price range in MXN (CONAVI 2024 UMA-based)
# These segments are defined by CONAVI in terms of UMA (Unidad de Medida y Actualización)
# 1 UMA ≈ $108.57 MXN/day → monthly ≈ $3,300 MXN (2024)
SEGMENT_PRICE_RANGES = {
    "Económica":          (200_000, 450_000),      # < 128 VSMM
    "Popular hasta 128":  (200_000, 450_000),
    "Popular hasta 158":  (450_000, 560_000),
    "Popular hasta 200":  (560_000, 710_000),
    "Popular":            (350_000, 710_000),       # Generic popular
    "Tradicional":        (710_000, 1_200_000),
    "Media":              (1_200_000, 2_500_000),
    "Residencial":        (2_500_000, 5_000_000),
    "Residencial plus":   (5_000_000, 15_000_000),
}

# Approximate area_m2 by segment (construction area, not land)
SEGMENT_AREA_M2 = {
    "Económica":          45,
    "Popular hasta 128":  45,
    "Popular hasta 158":  55,
    "Popular hasta 200":  65,
    "Popular":            55,
    "Tradicional":        80,
    "Media":              120,
    "Residencial":        180,
    "Residencial plus":   250,
}

# Major municipality coordinates (lat, lon) for the most important cities
# Used when the API doesn't provide coordinates
MUNICIPALITY_COORDS = {
    "Aguascalientes": (21.8818, -102.2916),
    "Mexicali": (32.6245, -115.4523),
    "Tijuana": (32.5149, -117.0382),
    "Ensenada": (31.8667, -116.5964),
    "La Paz": (24.1426, -110.3128),
    "Los Cabos": (22.8905, -109.9167),
    "Campeche": (19.8301, -90.5349),
    "Ciudad del Carmen": (18.6539, -91.8075),
    "Tuxtla Gutiérrez": (16.7528, -93.1152),
    "Tapachula": (14.9039, -92.2572),
    "San Cristóbal de las Casas": (16.7370, -92.6376),
    "Chihuahua": (28.6353, -106.0889),
    "Ciudad Juárez": (31.6904, -106.4245),
    "Saltillo": (25.4232, -100.9925),
    "Torreón": (25.5428, -103.4068),
    "Monclova": (26.9069, -101.4200),
    "Colima": (19.2433, -103.7247),
    "Manzanillo": (19.0500, -104.3167),
    "Ciudad de México": (19.4326, -99.1332),
    "Álvaro Obregón": (19.3550, -99.2000),
    "Benito Juárez": (19.3984, -99.1576),
    "Coyoacán": (19.3467, -99.1617),
    "Cuauhtémoc": (19.4450, -99.1500),
    "Gustavo A. Madero": (19.4833, -99.1167),
    "Iztapalapa": (19.3550, -99.0833),
    "Miguel Hidalgo": (19.4333, -99.1833),
    "Tlalpan": (19.2967, -99.1683),
    "Xochimilco": (19.2633, -99.1033),
    "Durango": (24.0277, -104.6532),
    "León": (21.1250, -101.6860),
    "Irapuato": (20.6767, -101.3554),
    "Celaya": (20.5236, -100.8155),
    "Guanajuato": (21.0190, -101.2574),
    "Acapulco de Juárez": (16.8531, -99.8237),
    "Chilpancingo de los Bravo": (17.5477, -99.5050),
    "Pachuca de Soto": (20.1011, -98.7591),
    "Tizayuca": (19.8411, -98.9815),
    "Guadalajara": (20.6597, -103.3496),
    "Zapopan": (20.7167, -103.4000),
    "Tlaquepaque": (20.6400, -103.3100),
    "Tonalá": (20.6250, -103.2333),
    "Puerto Vallarta": (20.6534, -105.2253),
    "Tlajomulco de Zúñiga": (20.4750, -103.4417),
    "Toluca": (19.2826, -99.6557),
    "Ecatepec de Morelos": (19.6017, -99.0500),
    "Naucalpan de Juárez": (19.4783, -99.2388),
    "Nezahualcóyotl": (19.4006, -98.9884),
    "Tlalnepantla de Baz": (19.5367, -99.1950),
    "Atizapán de Zaragoza": (19.5600, -99.2700),
    "Chalco": (19.2617, -98.8983),
    "Cuautitlán Izcalli": (19.6333, -99.2167),
    "Tecámac": (19.7131, -98.9682),
    "Morelia": (19.7060, -101.1950),
    "Uruapan": (19.4178, -102.0637),
    "Cuernavaca": (18.9186, -99.2342),
    "Tepic": (21.5010, -104.8943),
    "Monterrey": (25.6866, -100.3161),
    "San Pedro Garza García": (25.6583, -100.4017),
    "Guadalupe": (25.6783, -100.2567),
    "Apodaca": (25.7833, -100.1833),
    "San Nicolás de los Garza": (25.7500, -100.2833),
    "General Escobedo": (25.7833, -100.3167),
    "Santa Catarina": (25.6733, -100.4583),
    "Oaxaca de Juárez": (17.0732, -96.7266),
    "Puebla": (19.0414, -98.2063),
    "Querétaro": (20.5888, -100.3899),
    "San Juan del Río": (20.3871, -99.9962),
    "Cancún": (21.1619, -86.8515),
    "Benito Juárez": (21.1619, -86.8515),
    "Solidaridad": (20.6274, -87.0739),
    "Playa del Carmen": (20.6274, -87.0739),
    "San Luis Potosí": (22.1565, -100.9855),
    "Culiacán": (24.8049, -107.3940),
    "Mazatlán": (23.2494, -106.4111),
    "Los Mochis": (25.7903, -108.9939),
    "Hermosillo": (29.0729, -110.9559),
    "Ciudad Obregón": (27.4828, -109.9414),
    "Nogales": (31.3186, -110.9465),
    "Villahermosa": (17.9892, -92.9475),
    "Tampico": (22.2331, -97.8611),
    "Ciudad Victoria": (23.7369, -99.1411),
    "Reynosa": (26.0923, -98.2775),
    "Matamoros": (25.8697, -97.5028),
    "Nuevo Laredo": (27.4761, -99.5466),
    "Tlaxcala": (19.3182, -98.2375),
    "Veracruz": (19.2026, -96.1533),
    "Xalapa": (19.5438, -96.9102),
    "Coatzacoalcos": (18.1500, -94.4333),
    "Mérida": (20.9674, -89.5926),
    "Zacatecas": (22.7709, -102.5833),
    "Fresnillo": (23.1747, -102.8697),
}


def api_get(endpoint: str, max_retries: int = 3) -> Optional[list]:
    """Make a GET request to the SNIIV API with retries."""
    url = f"{BASE_URL}/{endpoint}"
    for attempt in range(max_retries):
        try:
            logger.info(f"  GET {url}")
            response = requests.get(url, timeout=60, headers={
                "Accept": "application/json",
                "User-Agent": "IAInmobiliaria-GeoApp/1.0 (research)"
            })
            if response.status_code == 200:
                data = response.json()
                logger.info(f"  → {len(data)} records")
                return data
            else:
                logger.warning(f"  HTTP {response.status_code}")
        except requests.exceptions.Timeout:
            logger.warning(f"  Timeout (attempt {attempt + 1}/{max_retries})")
            time.sleep(2 ** attempt)
        except Exception as e:
            logger.warning(f"  Error: {e}")
            time.sleep(2 ** attempt)
    return None


# ── 1. Download Financing Data ──────────────────────────────────────────────

def download_financiamiento(years: str = "2015,2016,2017,2018,2019,2020,2021,2022,2023,2024,2025") -> Optional[pd.DataFrame]:
    """
    Download housing financing data from SNIIV.

    This gives us: municipality, organism, credit destination, value segment,
    number of credits (acciones), and total amount (monto).

    Average housing price = monto / acciones per municipality+segment.
    """
    logger.info("=" * 60)
    logger.info("Downloading SNIIV Financiamiento (Housing Credits)")
    logger.info("=" * 60)

    # Query 1: By municipality + value segment (to get price categories)
    logger.info("[1/2] Financing by municipality + housing value segment...")
    data_by_value = api_get(
        f"GetFinanciamiento/{years}/00/000/entidad,municipio,valor_vivienda"
    )

    # Query 2: By municipality + credit destination (to get new vs existing)
    logger.info("[2/2] Financing by municipality + credit destination...")
    data_by_dest = api_get(
        f"GetFinanciamiento/{years}/00/000/entidad,municipio,destino_credito"
    )

    frames = []

    if data_by_value:
        df_val = pd.DataFrame(data_by_value)
        df_val["query_type"] = "by_value_segment"
        frames.append(df_val)
        logger.info(f"  Financing by value: {len(df_val)} records")

    if data_by_dest:
        df_dest = pd.DataFrame(data_by_dest)
        df_dest["query_type"] = "by_destination"
        frames.append(df_dest)
        logger.info(f"  Financing by destination: {len(df_dest)} records")

    if not frames:
        logger.error("No financing data retrieved.")
        return None

    df = pd.concat(frames, ignore_index=True)

    # Save raw
    raw_path = SNIIV_DIR / "financiamiento_raw.csv"
    df.to_csv(raw_path, index=False, encoding="utf-8-sig")
    logger.info(f"  Saved raw: {raw_path} ({len(df)} records)")

    return df


# ── 2. Download Housing Registry Data ───────────────────────────────────────

def download_registro(years: str = "2015,2016,2017,2018,2019,2020,2021,2022,2023,2024,2025") -> Optional[pd.DataFrame]:
    """
    Download housing registration data from SNIIV.

    Gives us: municipality, segment, housing type, bedroom count, unit count.
    """
    logger.info("=" * 60)
    logger.info("Downloading SNIIV Registro de Vivienda (Housing Registry)")
    logger.info("=" * 60)

    data = api_get(
        f"GetRegistro/{years}/00/000/entidad,municipio,tipo_vivienda,segmento"
    )

    if not data:
        logger.error("No registry data retrieved.")
        return None

    df = pd.DataFrame(data)
    raw_path = SNIIV_DIR / "registro_raw.csv"
    df.to_csv(raw_path, index=False, encoding="utf-8-sig")
    logger.info(f"  Saved raw: {raw_path} ({len(df)} records)")

    return df


# ── 3. Download Housing Inventory Data ──────────────────────────────────────

def download_inventario(year_month: str = "2024,6") -> Optional[pd.DataFrame]:
    """
    Download housing inventory data from SNIIV.

    Gives us: municipality, segment, housing type, subsidy status, unit count.
    """
    logger.info("=" * 60)
    logger.info("Downloading SNIIV Inventario de Vivienda (Housing Inventory)")
    logger.info("=" * 60)

    data = api_get(
        f"GetInventario/{year_month}/00/000/entidad,municipio,tipo_vivienda,segmento"
    )

    if not data:
        logger.error("No inventory data retrieved.")
        return None

    df = pd.DataFrame(data)
    raw_path = SNIIV_DIR / "inventario_raw.csv"
    df.to_csv(raw_path, index=False, encoding="utf-8-sig")
    logger.info(f"  Saved raw: {raw_path} ({len(df)} records)")

    return df


# ── 4. Process Into Model Format ────────────────────────────────────────────

def infer_state_from_clave(clave_municipio: str, municipio: str) -> str:
    """
    Try to infer state from municipality code.

    SNIIV clave_municipio is a 3-digit code that restarts per state.
    Since the API returns data ordered by state, we can map based on
    known municipalities.
    """
    # Known municipality → state mappings
    KNOWN_MUNICIPALITIES = {}
    for state, coords in []:
        pass  # filled dynamically

    # Use coordinates lookup as a proxy
    return "Unknown"


def process_financiamiento(df: pd.DataFrame) -> pd.DataFrame:
    """Process financing data into model-ready format."""
    logger.info("Processing financing data...")

    # Focus on the value-segment query which has housing value categories
    df_val = df[df["query_type"] == "by_value_segment"].copy()

    if df_val.empty:
        # Fall back to destination query
        df_val = df[df["query_type"] == "by_destination"].copy()

    # Calculate average housing price per credit
    df_val["avg_price_mxn"] = np.where(
        df_val["acciones"] > 0,
        df_val["monto"] / df_val["acciones"],
        0
    )

    # Filter out zero-action records
    df_val = df_val[df_val["acciones"] > 0].copy()

    # Map segment to area estimate
    segment_col = "valor_vivienda" if "valor_vivienda" in df_val.columns else "destino_credito"
    df_val["estimated_area_m2"] = df_val[segment_col].map(SEGMENT_AREA_M2).fillna(80)

    # Calculate price per m2
    df_val["price_m2"] = df_val["avg_price_mxn"] / df_val["estimated_area_m2"]

    # Add coordinates from lookup
    df_val["lat"] = df_val["municipio"].map(
        lambda m: MUNICIPALITY_COORDS.get(m, (None, None))[0]
    )
    df_val["lon"] = df_val["municipio"].map(
        lambda m: MUNICIPALITY_COORDS.get(m, (None, None))[1]
    )

    return df_val


def process_registro(df: pd.DataFrame) -> pd.DataFrame:
    """Process registry data to get housing supply by municipality+segment."""
    logger.info("Processing registry data...")

    # Map segment to price estimate (midpoint of range)
    df["estimated_price_mxn"] = df["segmento"].map(
        lambda s: np.mean(SEGMENT_PRICE_RANGES.get(s, (500_000, 500_000)))
    )
    df["estimated_area_m2"] = df["segmento"].map(SEGMENT_AREA_M2).fillna(80)
    df["price_m2"] = df["estimated_price_mxn"] / df["estimated_area_m2"]

    # Add coordinates
    df["lat"] = df["municipio"].map(
        lambda m: MUNICIPALITY_COORDS.get(m, (None, None))[0]
    )
    df["lon"] = df["municipio"].map(
        lambda m: MUNICIPALITY_COORDS.get(m, (None, None))[1]
    )

    return df


def build_unified_dataset(
    df_fin: Optional[pd.DataFrame],
    df_reg: Optional[pd.DataFrame],
    df_inv: Optional[pd.DataFrame],
) -> pd.DataFrame:
    """
    Build a unified dataset combining financing and registry data.

    Output columns: price_mxn, area_m2, price_m2, city, state, lat, lon,
                    segment, housing_type, source, source_detail
    """
    logger.info("=" * 60)
    logger.info("Building unified SNIIV dataset")
    logger.info("=" * 60)

    rows = []

    # ── From Financing (best price data: actual monto/acciones) ──
    if df_fin is not None:
        df_f = process_financiamiento(df_fin)
        segment_col = "valor_vivienda" if "valor_vivienda" in df_f.columns else "destino_credito"

        for _, r in df_f.iterrows():
            rows.append({
                "title": f"Vivienda {r.get(segment_col, 'N/A')}",
                "price_mxn": round(r["avg_price_mxn"], 2),
                "area_m2": r["estimated_area_m2"],
                "price_m2": round(r["price_m2"], 2),
                "address": "",
                "city": r["municipio"],
                "state": "",  # Will be enriched below
                "lat": r["lat"],
                "lon": r["lon"],
                "segment": r.get(segment_col, ""),
                "housing_type": "",
                "num_credits": int(r["acciones"]),
                "total_monto_mxn": round(r["monto"], 2),
                "collection_date": datetime.now().strftime("%Y-%m-%d"),
                "source": "sniiv_financiamiento",
                "source_url": "https://sniiv.sedatu.gob.mx",
            })
        logger.info(f"  From financing: {len(df_f)} records")

    # ── From Registry (housing supply counts with segment→price estimate) ──
    if df_reg is not None:
        df_r = process_registro(df_reg)

        for _, r in df_r.iterrows():
            rows.append({
                "title": f"Vivienda {r.get('segmento', 'N/A')} {r.get('tipo_vivienda', '')}",
                "price_mxn": round(r["estimated_price_mxn"], 2),
                "area_m2": r["estimated_area_m2"],
                "price_m2": round(r["price_m2"], 2),
                "address": "",
                "city": r["municipio"],
                "state": "",
                "lat": r["lat"],
                "lon": r["lon"],
                "segment": r.get("segmento", ""),
                "housing_type": r.get("tipo_vivienda", ""),
                "num_credits": int(r.get("viviendas", 0)),
                "total_monto_mxn": 0,
                "collection_date": datetime.now().strftime("%Y-%m-%d"),
                "source": "sniiv_registro",
                "source_url": "https://sniiv.sedatu.gob.mx",
            })
        logger.info(f"  From registry: {len(df_r)} records")

    # ── From Inventory ──
    if df_inv is not None:
        df_i = df_inv.copy()
        df_i["estimated_price_mxn"] = df_i["segmento"].map(
            lambda s: np.mean(SEGMENT_PRICE_RANGES.get(s, (500_000, 500_000)))
        )
        df_i["estimated_area_m2"] = df_i["segmento"].map(SEGMENT_AREA_M2).fillna(80)
        df_i["lat"] = df_i["municipio"].map(
            lambda m: MUNICIPALITY_COORDS.get(m, (None, None))[0]
        )
        df_i["lon"] = df_i["municipio"].map(
            lambda m: MUNICIPALITY_COORDS.get(m, (None, None))[1]
        )

        for _, r in df_i.iterrows():
            price = r["estimated_price_mxn"]
            area = r["estimated_area_m2"]
            rows.append({
                "title": f"Inventario {r.get('segmento', 'N/A')} {r.get('tipo_vivienda', '')}",
                "price_mxn": round(price, 2),
                "area_m2": area,
                "price_m2": round(price / area, 2) if area > 0 else 0,
                "address": "",
                "city": r["municipio"],
                "state": "",
                "lat": r["lat"],
                "lon": r["lon"],
                "segment": r.get("segmento", ""),
                "housing_type": r.get("tipo_vivienda", ""),
                "num_credits": int(r.get("viviendas", 0)),
                "total_monto_mxn": 0,
                "collection_date": datetime.now().strftime("%Y-%m-%d"),
                "source": "sniiv_inventario",
                "source_url": "https://sniiv.sedatu.gob.mx",
            })
        logger.info(f"  From inventory: {len(df_i)} records")

    if not rows:
        logger.error("No data to build unified dataset.")
        return pd.DataFrame()

    df_all = pd.DataFrame(rows)

    # ── Enrich: infer state from coordinates ──
    # Load cities file for state mapping
    cities_file = DATA_DIR / "cities_mexico_32_states.json"
    city_to_state = {}
    if cities_file.exists():
        with open(cities_file, "r", encoding="utf-8") as f:
            cities_data = json.load(f)
        for estado in cities_data.get("estados", []):
            state_name = estado["state"]
            for ciudad in estado.get("ciudades", []):
                city_to_state[ciudad["city"]] = state_name

    df_all["state"] = df_all["city"].map(city_to_state).fillna("")

    # ── Filter: only rows with coordinates ──
    df_with_coords = df_all.dropna(subset=["lat", "lon"]).copy()
    df_without_coords = df_all[df_all["lat"].isna() | df_all["lon"].isna()]

    logger.info(f"  Records with coordinates: {len(df_with_coords)}")
    logger.info(f"  Records without coordinates: {len(df_without_coords)}")
    if not df_without_coords.empty:
        missing_cities = df_without_coords["city"].unique()
        logger.info(f"  Municipalities without coords (sample): {list(missing_cities[:20])}")

    # ── Filter valid prices ──
    df_with_coords = df_with_coords[df_with_coords["price_mxn"] > 50_000]
    df_with_coords = df_with_coords[df_with_coords["price_mxn"] < 50_000_000]
    df_with_coords = df_with_coords[df_with_coords["price_m2"] > 500]
    df_with_coords = df_with_coords[df_with_coords["price_m2"] < 200_000]

    logger.info(f"  After price filtering: {len(df_with_coords)} records")

    return df_with_coords


# ── 5. Per-State Detailed Queries ───────────────────────────────────────────

def download_per_state_financing(
    years: str = "2015,2016,2017,2018,2019,2020,2021,2022,2023,2024,2025",
    states: Optional[list] = None,
) -> Optional[pd.DataFrame]:
    """
    Download financing data state-by-state for more granular data.
    Each state query returns municipality-level data within that state,
    which helps us map clave_municipio → state correctly.
    """
    logger.info("=" * 60)
    logger.info("Downloading per-state financing data")
    logger.info("=" * 60)

    if states is None:
        states = list(INEGI_STATE_CODES.keys())

    all_frames = []
    for state_code in states:
        state_name = INEGI_STATE_CODES[state_code]
        logger.info(f"  State {state_code}: {state_name}")

        data = api_get(
            f"GetFinanciamiento/{years}/{state_code}/000/municipio,valor_vivienda"
        )
        if data:
            df = pd.DataFrame(data)
            df["state_code"] = state_code
            df["state"] = state_name
            all_frames.append(df)

        # Be gentle with the API
        time.sleep(0.5)

    if not all_frames:
        return None

    df_all = pd.concat(all_frames, ignore_index=True)
    raw_path = SNIIV_DIR / "financiamiento_per_state_raw.csv"
    df_all.to_csv(raw_path, index=False, encoding="utf-8-sig")
    logger.info(f"  Saved: {raw_path} ({len(df_all)} records)")

    return df_all


def download_per_state_registro(
    years: str = "2015,2016,2017,2018,2019,2020,2021,2022,2023,2024,2025",
    states: Optional[list] = None,
) -> Optional[pd.DataFrame]:
    """
    Download housing registry data state-by-state for municipality-level
    granularity across all 32 states.
    """
    logger.info("=" * 60)
    logger.info("Downloading per-state registry data (all 32 states)")
    logger.info("=" * 60)

    if states is None:
        states = list(INEGI_STATE_CODES.keys())

    all_frames = []
    for state_code in states:
        state_name = INEGI_STATE_CODES[state_code]
        logger.info(f"  State {state_code}: {state_name}")

        data = api_get(
            f"GetRegistro/{years}/{state_code}/000/municipio,tipo_vivienda,segmento"
        )
        if data:
            df = pd.DataFrame(data)
            df["state_code"] = state_code
            df["state"] = state_name
            all_frames.append(df)

        # Be gentle with the API
        time.sleep(0.5)

    if not all_frames:
        return None

    df_all = pd.concat(all_frames, ignore_index=True)
    raw_path = SNIIV_DIR / "registro_per_state_raw.csv"
    df_all.to_csv(raw_path, index=False, encoding="utf-8-sig")
    logger.info(f"  Saved: {raw_path} ({len(df_all)} records)")

    return df_all


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    """Download all SNIIV data and create unified dataset."""
    logger.info("SNIIV Data Downloader for IAInmobiliaria GeoApp")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info(f"Output dir: {SNIIV_DIR}")

    # Download from all three cubes
    df_fin = download_financiamiento()
    df_reg = download_registro()
    df_inv = download_inventario()

    # Build unified dataset
    df_unified = build_unified_dataset(df_fin, df_reg, df_inv)

    if df_unified.empty:
        logger.error("No unified data produced.")
        return

    # Save processed data
    timestamp = datetime.now().strftime("%Y%m%d")
    output_path = DATA_DIR / f"sniiv_processed_{timestamp}.csv"
    df_unified.to_csv(output_path, index=False, encoding="utf-8-sig")
    logger.info(f"\nFinal processed dataset: {output_path}")
    logger.info(f"  Total records: {len(df_unified)}")
    logger.info(f"  Unique cities: {df_unified['city'].nunique()}")
    logger.info(f"  Sources: {df_unified['source'].value_counts().to_dict()}")
    logger.info(f"  Price range: ${df_unified['price_mxn'].min():,.0f} - ${df_unified['price_mxn'].max():,.0f} MXN")
    logger.info(f"  Price/m² range: ${df_unified['price_m2'].min():,.0f} - ${df_unified['price_m2'].max():,.0f}/m²")

    # Also save the full dataset (including records without coords)
    full_path = SNIIV_DIR / f"sniiv_all_records_{timestamp}.csv"
    # Re-build without coord filtering for reference
    df_fin_proc = process_financiamiento(df_fin) if df_fin is not None else None
    if df_fin_proc is not None:
        df_fin_proc.to_csv(SNIIV_DIR / "financiamiento_processed.csv", index=False, encoding="utf-8-sig")

    # Per-state detailed download — always run for full 32-state coverage
    logger.info("\n--- Per-state download (all 32 states, 2015-2025) ---")

    df_per_state = download_per_state_financing()
    if df_per_state is not None:
        # Process per-state data (already has state names)
        df_per_state["avg_price_mxn"] = np.where(
            df_per_state["acciones"] > 0,
            df_per_state["monto"] / df_per_state["acciones"],
            0
        )
        per_state_path = DATA_DIR / f"sniiv_per_state_{timestamp}.csv"
        df_per_state.to_csv(per_state_path, index=False, encoding="utf-8-sig")
        logger.info(f"Per-state data: {per_state_path} ({len(df_per_state)} records)")

        # State coverage report
        if "state" in df_per_state.columns:
            logger.info("\nPer-state coverage:")
            state_counts = df_per_state.groupby("state").size().sort_values(ascending=False)
            for state, count in state_counts.items():
                marker = "OK" if count >= 100 else "LOW"
                logger.info(f"  {state:<30s} {count:>6,}  [{marker}]")

    # Per-state registry download
    logger.info("\n--- Per-state registry download (all 32 states) ---")
    df_per_state_reg = download_per_state_registro()
    if df_per_state_reg is not None:
        reg_state_path = DATA_DIR / f"sniiv_registro_per_state_{timestamp}.csv"
        df_per_state_reg.to_csv(reg_state_path, index=False, encoding="utf-8-sig")
        logger.info(f"Per-state registry: {reg_state_path} ({len(df_per_state_reg)} records)")

    logger.info("\nDone!")


if __name__ == "__main__":
    main()
