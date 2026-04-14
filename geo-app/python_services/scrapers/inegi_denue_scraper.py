"""
INEGI DENUE (Directorio Estadistico Nacional de Unidades Economicas) Scraper.

Uses the official INEGI DENUE API to query business establishments near
each city in the 32-state coverage list.  This provides authoritative
amenity/POI counts that feed the ML model's feature engineering.

API pattern:
  https://www.inegi.org.mx/app/api/denue/v1/consulta/BuscarAreaActEstr/
  {lat}/{lon}/{meters}/{actividad}/0/{token}

Activity codes (SCIAN classification):
  611        Schools (educational services)
  621,622    Hospitals & clinics
  522        Banks (credit institutions)
  722        Restaurants
  461,462    Supermarkets & grocery stores
  468        Gas stations

Requires: INEGI_API_TOKEN in .env (free registration at inegi.org.mx)
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)

from config import DATA_DIR, INEGI_API_TOKEN

# ── Constants ────────────────────────────────────────────────────────────────

DENUE_BASE = "https://www.inegi.org.mx/app/api/denue/v1/consulta"
CITIES_FILE = DATA_DIR / "cities_mexico_32_states.json"

# Activity codes to query (SCIAN classification)
ACTIVITY_CODES: Dict[str, str] = {
    "schools": "611",
    "hospitals": "621,622",
    "banks": "522",
    "restaurants": "722",
    "supermarkets": "461,462",
    "gas_stations": "468",
}

# Search radius in meters (2 km default, balances coverage vs API load)
DEFAULT_RADIUS_M = 2000

# Well-known city coordinates (used when cities_mexico_32_states.json
# doesn't include lat/lon)
CITY_COORDS: Dict[str, Tuple[float, float]] = {
    "Aguascalientes": (21.8818, -102.2916),
    "Tijuana": (32.5149, -117.0382),
    "Mexicali": (32.6245, -115.4523),
    "Ensenada": (31.8667, -116.5964),
    "La Paz": (24.1426, -110.3128),
    "Cabo San Lucas": (22.8905, -109.9167),
    "Campeche": (19.8301, -90.5349),
    "Ciudad del Carmen": (18.6539, -91.8075),
    "Tuxtla Gutiérrez": (16.7528, -93.1152),
    "Tapachula": (14.9039, -92.2572),
    "Chihuahua": (28.6353, -106.0889),
    "Ciudad Juárez": (31.6904, -106.4245),
    "Ciudad de México": (19.4326, -99.1332),
    "Saltillo": (25.4232, -100.9925),
    "Torreón": (25.5428, -103.4068),
    "Colima": (19.2433, -103.7247),
    "Manzanillo": (19.0500, -104.3167),
    "Durango": (24.0277, -104.6532),
    "León": (21.1250, -101.6860),
    "Irapuato": (20.6767, -101.3554),
    "Celaya": (20.5236, -100.8155),
    "Acapulco": (16.8531, -99.8237),
    "Chilpancingo": (17.5477, -99.5050),
    "Pachuca": (20.1011, -98.7591),
    "Guadalajara": (20.6597, -103.3496),
    "Zapopan": (20.7167, -103.4000),
    "Tlaquepaque": (20.6400, -103.3100),
    "Tonalá": (20.6250, -103.2333),
    "Toluca": (19.2826, -99.6557),
    "Ecatepec": (19.6017, -99.0500),
    "Naucalpan": (19.4783, -99.2388),
    "Morelia": (19.7060, -101.1950),
    "Cuernavaca": (18.9186, -99.2342),
    "Tepic": (21.5010, -104.8943),
    "Monterrey": (25.6866, -100.3161),
    "Apodaca": (25.7833, -100.1833),
    "San Nicolás de los Garza": (25.7500, -100.2833),
    "Oaxaca": (17.0732, -96.7266),
    "Puebla": (19.0414, -98.2063),
    "Cholula": (19.0633, -98.3064),
    "Querétaro": (20.5888, -100.3899),
    "Cancún": (21.1619, -86.8515),
    "Playa del Carmen": (20.6274, -87.0739),
    "San Luis Potosí": (22.1565, -100.9855),
    "Culiacán": (24.8049, -107.3940),
    "Mazatlán": (23.2494, -106.4111),
    "Hermosillo": (29.0729, -110.9559),
    "Nogales": (31.3186, -110.9465),
    "Villahermosa": (17.9892, -92.9475),
    "Reynosa": (26.0923, -98.2775),
    "Matamoros": (25.8697, -97.5028),
    "Tlaxcala": (19.3182, -98.2375),
    "Veracruz": (19.2026, -96.1533),
    "Xalapa": (19.5438, -96.9102),
    "Mérida": (20.9674, -89.5926),
    "Zacatecas": (22.7709, -102.5833),
}


class INEGIDenueScraper:
    """
    Queries the INEGI DENUE API for business establishments (amenities)
    near each city, producing counts and details used as ML features.
    """

    def __init__(
        self,
        token: Optional[str] = None,
        radius_m: int = DEFAULT_RADIUS_M,
        delay: float = 1.0,
    ):
        self.token = token or INEGI_API_TOKEN or os.getenv("INEGI_API_TOKEN", "")
        self.radius_m = radius_m
        self.delay = delay

        if not self.token:
            logger.warning(
                "INEGI_API_TOKEN not set. DENUE API calls will fail.\n"
                "Register for a free token at: https://www.inegi.org.mx/app/api/denue/v1/"
            )

        self.cities: List[Dict[str, Any]] = []
        self._load_cities()

    def _load_cities(self):
        """Load city list with coordinates."""
        if not CITIES_FILE.exists():
            logger.warning(f"Cities file not found: {CITIES_FILE}")
            return

        with open(CITIES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        for estado in data.get("estados", []):
            state_name = estado["state"]
            for ciudad in estado.get("ciudades", []):
                city_name = ciudad["city"]
                # Try to get coords from JSON, fallback to lookup table
                lat = ciudad.get("lat")
                lon = ciudad.get("lon")
                if lat is None or lon is None:
                    coords = CITY_COORDS.get(city_name)
                    if coords:
                        lat, lon = coords
                    else:
                        logger.warning(
                            f"  No coordinates for {city_name}, {state_name} — skipping"
                        )
                        continue

                self.cities.append(
                    {
                        "city": city_name,
                        "state": state_name,
                        "lat": lat,
                        "lon": lon,
                    }
                )

        logger.info(f"Loaded {len(self.cities)} cities with coordinates")

    # ── API query ────────────────────────────────────────────────────────

    async def _query_denue(
        self,
        client: httpx.AsyncClient,
        lat: float,
        lon: float,
        activity: str,
        max_retries: int = 3,
    ) -> List[Dict]:
        """
        Query the DENUE API for establishments near a point.

        URL pattern:
          /BuscarAreaActEstr/{lat}/{lon}/{meters}/{actividad}/0/{token}
        """
        url = (
            f"{DENUE_BASE}/BuscarAreaActEstr/"
            f"{lat}/{lon}/{self.radius_m}/{activity}/0/{self.token}"
        )

        for attempt in range(max_retries):
            try:
                resp = await client.get(url, timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    if isinstance(data, list):
                        return data
                    elif isinstance(data, dict) and "error" in str(data).lower():
                        logger.debug(f"API error: {data}")
                        return []
                    return []
                elif resp.status_code == 429:
                    wait = 2 ** (attempt + 1)
                    logger.warning(f"Rate limited, waiting {wait}s")
                    await asyncio.sleep(wait)
                else:
                    logger.debug(f"HTTP {resp.status_code} for activity={activity}")
                    return []
            except (httpx.TimeoutException, httpx.ConnectError, OSError) as exc:
                logger.debug(f"Request error: {exc} (attempt {attempt+1})")
                await asyncio.sleep(2 ** attempt)

        return []

    # ── Scrape all cities ────────────────────────────────────────────────

    async def scrape_all_amenities(
        self,
        cities: Optional[List[Dict]] = None,
    ) -> pd.DataFrame:
        """
        For each city, query DENUE for all amenity types and build
        a comprehensive amenities dataset.

        Returns DataFrame with columns:
          city, state, lat, lon, amenity_type, business_name,
          business_activity, business_lat, business_lon, distance_m
        """
        target_cities = cities or self.cities

        if not self.token:
            logger.error(
                "Cannot proceed without INEGI_API_TOKEN. "
                "Set it in .env or pass token= to the constructor."
            )
            return pd.DataFrame()

        logger.info("=" * 70)
        logger.info("INEGI DENUE AMENITIES SCRAPER")
        logger.info(f"  Cities: {len(target_cities)}")
        logger.info(f"  Amenity types: {list(ACTIVITY_CODES.keys())}")
        logger.info(f"  Radius: {self.radius_m}m")
        logger.info("=" * 70)

        all_rows: List[Dict] = []
        # Also build a summary table: counts per city per amenity type
        summary_rows: List[Dict] = []

        async with httpx.AsyncClient(
            headers={
                "Accept": "application/json",
                "User-Agent": "IAInmobiliaria-GeoApp/1.0 (research)",
            },
            follow_redirects=True,
        ) as client:

            for idx, city_info in enumerate(target_cities, 1):
                city_name = city_info["city"]
                state_name = city_info["state"]
                lat = city_info["lat"]
                lon = city_info["lon"]

                logger.info(
                    f"\n[{idx}/{len(target_cities)}] {city_name}, {state_name} "
                    f"({lat}, {lon})"
                )

                city_summary = {
                    "city": city_name,
                    "state": state_name,
                    "lat": lat,
                    "lon": lon,
                }

                for amenity_name, activity_code in ACTIVITY_CODES.items():
                    establishments = await self._query_denue(
                        client, lat, lon, activity_code
                    )

                    count = len(establishments)
                    city_summary[f"count_{amenity_name}"] = count

                    for est in establishments:
                        # DENUE returns fields like:
                        # Nombre, Razon_social, Clase_actividad,
                        # Latitud, Longitud, etc.
                        est_lat = est.get("Latitud") or est.get("latitud")
                        est_lon = est.get("Longitud") or est.get("longitud")
                        est_name = (
                            est.get("Nombre")
                            or est.get("nombre")
                            or est.get("Razon_social")
                            or ""
                        )
                        est_activity = (
                            est.get("Clase_actividad")
                            or est.get("clase_actividad")
                            or ""
                        )

                        try:
                            est_lat_f = float(est_lat) if est_lat else None
                            est_lon_f = float(est_lon) if est_lon else None
                        except (ValueError, TypeError):
                            est_lat_f = None
                            est_lon_f = None

                        all_rows.append(
                            {
                                "city": city_name,
                                "state": state_name,
                                "city_lat": lat,
                                "city_lon": lon,
                                "amenity_type": amenity_name,
                                "activity_code": activity_code,
                                "business_name": str(est_name)[:200],
                                "business_activity": str(est_activity)[:200],
                                "business_lat": est_lat_f,
                                "business_lon": est_lon_f,
                                "collection_date": datetime.now().strftime(
                                    "%Y-%m-%d"
                                ),
                            }
                        )

                    logger.info(f"  {amenity_name}: {count} establishments")
                    await asyncio.sleep(self.delay)

                summary_rows.append(city_summary)

        # Build DataFrames
        df_detail = pd.DataFrame(all_rows)
        df_summary = pd.DataFrame(summary_rows)

        logger.info(f"\nTotal establishment records: {len(df_detail)}")
        logger.info(f"Cities processed: {len(df_summary)}")

        return df_detail, df_summary

    # ── Save ─────────────────────────────────────────────────────────────

    def save_csv(
        self,
        df_detail: pd.DataFrame,
        df_summary: pd.DataFrame,
        detail_filename: Optional[str] = None,
        summary_filename: Optional[str] = None,
    ) -> Tuple[Path, Path]:
        """Save detail and summary CSVs."""
        timestamp = datetime.now().strftime("%Y%m%d")

        if detail_filename is None:
            detail_filename = f"denue_amenities_{timestamp}.csv"
        if summary_filename is None:
            summary_filename = f"denue_amenities_summary_{timestamp}.csv"

        detail_path = DATA_DIR / detail_filename
        summary_path = DATA_DIR / summary_filename

        df_detail.to_csv(detail_path, index=False, encoding="utf-8-sig")
        df_summary.to_csv(summary_path, index=False, encoding="utf-8-sig")

        logger.info(f"Detail saved: {detail_path} ({len(df_detail)} records)")
        logger.info(f"Summary saved: {summary_path} ({len(df_summary)} records)")

        return detail_path, summary_path


# ── CLI entry point ──────────────────────────────────────────────────────────

async def main():
    """Run the DENUE amenities scraper."""
    scraper = INEGIDenueScraper()

    result = await scraper.scrape_all_amenities()

    if isinstance(result, tuple):
        df_detail, df_summary = result
    else:
        df_detail = result
        df_summary = pd.DataFrame()

    if df_detail.empty:
        logger.warning("No results obtained.")
        return

    scraper.save_csv(df_detail, df_summary)

    # Coverage report
    logger.info("\n" + "=" * 60)
    logger.info("COVERAGE REPORT — INEGI DENUE AMENITIES")
    logger.info("=" * 60)

    if not df_summary.empty:
        count_cols = [c for c in df_summary.columns if c.startswith("count_")]
        for _, row in df_summary.iterrows():
            total = sum(row.get(c, 0) for c in count_cols)
            logger.info(
                f"  {row['city']:<25s} {row['state']:<20s} total={total:>5,}"
            )

    state_counts = df_detail.groupby("state").size().sort_values(ascending=False)
    logger.info("\nBy state:")
    for state, count in state_counts.items():
        logger.info(f"  {state:<30s} {count:>6,}")

    amenity_counts = df_detail.groupby("amenity_type").size()
    logger.info("\nBy amenity type:")
    for amenity, count in amenity_counts.items():
        logger.info(f"  {amenity:<20s} {count:>6,}")


if __name__ == "__main__":
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level:<8}</level> | <level>{message}</level>",
        level="INFO",
    )
    asyncio.run(main())
