"""
INFONAVIT Open Data Downloader and Processor.

Downloads publicly available credit origination datasets from INFONAVIT's
open data portal and normalizes them to the standard property format used
by the IAInmobiliaria ML pipeline.

Data source: https://portaldatosabiertos.infonavit.org.mx/
Available datasets:
  - Creditos originados (credit originations with property values)
  - Creditos ejercidos (exercised credits)
  - Colocacion de creditos (credit placement)

Each record represents a housing credit with: state, municipality,
property value, housing type, credit year, and sometimes area.

The scraper:
  1. Downloads CSV/XLSX files from the portal
  2. Extracts relevant columns
  3. Normalizes to standard format (title, price_mxn, area_m2, etc.)
  4. Geocodes via lookup table from cities_mexico_32_states.json
  5. Saves to data/infonavit_YYYYMMDD.csv
"""

import asyncio
import io
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin

import httpx
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

# ── Paths ────────────────────────────────────────────────────────────────────

INFONAVIT_DIR = DATA_DIR / "infonavit"
INFONAVIT_DIR.mkdir(exist_ok=True)

CITIES_FILE = DATA_DIR / "cities_mexico_32_states.json"

# ── Known INFONAVIT open-data download URLs ──────────────────────────────────
#
# The portal publishes datasets as downloadable CSV/XLSX.  The exact URLs can
# change when new quarterly releases are published, so we probe several known
# patterns. If a URL 404s we skip it gracefully.
#
# The most reliable datasets are:
#   "Creditos_Originados" — one row per credit, has valor_vivienda column
#   "Colocacion" — aggregated by state/municipality
#   "TuCasa" — some property listings from INFONAVIT marketplace

INFONAVIT_PORTAL_BASE = "https://portaldatosabiertos.infonavit.org.mx"

KNOWN_DATASET_URLS = [
    # Creditos originados — bulk CSV (most valuable: has property values)
    "https://portaldatosabiertos.infonavit.org.mx/downloads/creditos_originados.csv",
    "https://portaldatosabiertos.infonavit.org.mx/downloads/creditos_colocados.csv",
    # Alternative paths that INFONAVIT has used historically
    "https://portaldatosabiertos.infonavit.org.mx/dataset/creditos-originados",
    "https://portaldatosabiertos.infonavit.org.mx/dataset/colocacion-de-creditos",
]

# Fallback: INFONAVIT CKAN API endpoint for dataset discovery
CKAN_API = "https://portaldatosabiertos.infonavit.org.mx/api/3/action"

# ── State normalization ──────────────────────────────────────────────────────

STATE_ALIASES: Dict[str, str] = {
    "AGUASCALIENTES": "Aguascalientes",
    "BAJA CALIFORNIA": "Baja California",
    "BAJA CALIFORNIA SUR": "Baja California Sur",
    "CAMPECHE": "Campeche",
    "CHIAPAS": "Chiapas",
    "CHIHUAHUA": "Chihuahua",
    "CIUDAD DE MEXICO": "Ciudad de México",
    "CIUDAD DE MÉXICO": "Ciudad de México",
    "CDMX": "Ciudad de México",
    "DISTRITO FEDERAL": "Ciudad de México",
    "COAHUILA": "Coahuila",
    "COAHUILA DE ZARAGOZA": "Coahuila",
    "COLIMA": "Colima",
    "DURANGO": "Durango",
    "GUANAJUATO": "Guanajuato",
    "GUERRERO": "Guerrero",
    "HIDALGO": "Hidalgo",
    "JALISCO": "Jalisco",
    "MEXICO": "México",
    "MÉXICO": "México",
    "ESTADO DE MEXICO": "México",
    "ESTADO DE MÉXICO": "México",
    "MICHOACAN": "Michoacán",
    "MICHOACÁN": "Michoacán",
    "MICHOACAN DE OCAMPO": "Michoacán",
    "MICHOACÁN DE OCAMPO": "Michoacán",
    "MORELOS": "Morelos",
    "NAYARIT": "Nayarit",
    "NUEVO LEON": "Nuevo León",
    "NUEVO LEÓN": "Nuevo León",
    "OAXACA": "Oaxaca",
    "PUEBLA": "Puebla",
    "QUERETARO": "Querétaro",
    "QUERÉTARO": "Querétaro",
    "QUINTANA ROO": "Quintana Roo",
    "SAN LUIS POTOSI": "San Luis Potosí",
    "SAN LUIS POTOSÍ": "San Luis Potosí",
    "SINALOA": "Sinaloa",
    "SONORA": "Sonora",
    "TABASCO": "Tabasco",
    "TAMAULIPAS": "Tamaulipas",
    "TLAXCALA": "Tlaxcala",
    "VERACRUZ": "Veracruz",
    "VERACRUZ DE IGNACIO DE LA LLAVE": "Veracruz",
    "YUCATAN": "Yucatán",
    "YUCATÁN": "Yucatán",
    "ZACATECAS": "Zacatecas",
}

# Housing type → approximate area (m2)
HOUSING_TYPE_AREA: Dict[str, float] = {
    "economica": 42,
    "popular": 55,
    "tradicional": 80,
    "media": 120,
    "residencial": 180,
    "residencial plus": 250,
    "conjunto habitacional": 65,
    "vivienda usada": 80,
    "vivienda nueva": 75,
    "lote con servicios": 150,
    "pie de casa": 40,
    "mejora de vivienda": 60,
    "pago de pasivos": 75,
    "cofinanciamiento": 90,
    "apoyo infonavit": 70,
}


class InfonavitScraper:
    """
    Downloads and processes INFONAVIT open-data credit datasets into
    a normalized real-estate property format.
    """

    def __init__(self):
        self.city_coords: Dict[str, Tuple[float, float]] = {}
        self.city_to_state: Dict[str, str] = {}
        self._load_cities_lookup()

    # ── City/coord lookup ────────────────────────────────────────────────

    def _load_cities_lookup(self):
        """Load city coordinates and state mappings from the JSON file."""
        if not CITIES_FILE.exists():
            logger.warning(f"Cities file not found: {CITIES_FILE}")
            return

        with open(CITIES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        for estado in data.get("estados", []):
            state_name = estado["state"]
            for ciudad in estado.get("ciudades", []):
                city_name = ciudad["city"]
                self.city_to_state[city_name] = state_name
                self.city_to_state[city_name.upper()] = state_name
                # Use lat/lon if provided in the JSON, otherwise from
                # the SNIIV municipality coords as fallback
                if "lat" in ciudad and "lon" in ciudad:
                    self.city_coords[city_name] = (ciudad["lat"], ciudad["lon"])

        # Add well-known municipality coordinates
        from scripts.download_sniiv import MUNICIPALITY_COORDS
        for muni, coords in MUNICIPALITY_COORDS.items():
            if muni not in self.city_coords:
                self.city_coords[muni] = coords
            upper = muni.upper()
            if upper not in self.city_coords:
                self.city_coords[upper] = coords

        logger.info(
            f"Loaded {len(self.city_coords)} city coordinates, "
            f"{len(self.city_to_state)} city→state mappings"
        )

    def _geocode_city(self, city: str) -> Tuple[Optional[float], Optional[float]]:
        """Look up coordinates for a city name."""
        coords = self.city_coords.get(city)
        if coords:
            return coords
        coords = self.city_coords.get(city.upper())
        if coords:
            return coords
        # Try partial match
        city_upper = city.upper()
        for key, val in self.city_coords.items():
            if isinstance(key, str) and city_upper in key.upper():
                return val
        return (None, None)

    def _normalize_state(self, raw: str) -> str:
        """Normalize a raw state string to canonical name."""
        if not raw or not isinstance(raw, str):
            return ""
        cleaned = raw.strip().upper()
        return STATE_ALIASES.get(cleaned, raw.strip().title())

    # ── Download helpers ─────────────────────────────────────────────────

    async def _download_file(
        self, client: httpx.AsyncClient, url: str
    ) -> Optional[bytes]:
        """Download a file, return bytes or None."""
        try:
            logger.info(f"  Downloading: {url}")
            resp = await client.get(url, timeout=120, follow_redirects=True)
            if resp.status_code == 200:
                logger.info(f"  Downloaded {len(resp.content):,} bytes")
                return resp.content
            else:
                logger.warning(f"  HTTP {resp.status_code} for {url}")
        except (httpx.TimeoutException, httpx.ConnectError, OSError) as exc:
            logger.warning(f"  Download error: {exc}")
        return None

    async def _discover_datasets_ckan(
        self, client: httpx.AsyncClient
    ) -> List[str]:
        """Use the CKAN API to discover downloadable resource URLs."""
        urls = []
        try:
            # Search for credit-related datasets
            resp = await client.get(
                f"{CKAN_API}/package_search",
                params={"q": "creditos", "rows": 20},
                timeout=30,
            )
            if resp.status_code != 200:
                return urls

            data = resp.json()
            results = data.get("result", {}).get("results", [])

            for dataset in results:
                for resource in dataset.get("resources", []):
                    fmt = (resource.get("format") or "").lower()
                    if fmt in ("csv", "xlsx", "xls"):
                        download_url = resource.get("url", "")
                        if download_url:
                            urls.append(download_url)
                            logger.info(
                                f"  Discovered: {resource.get('name', 'unnamed')} "
                                f"({fmt}) → {download_url}"
                            )
        except Exception as exc:
            logger.warning(f"CKAN discovery failed: {exc}")

        return urls

    # ── Parse downloaded data ────────────────────────────────────────────

    def _parse_csv_content(self, content: bytes, source_url: str) -> pd.DataFrame:
        """Try to parse CSV content into a DataFrame."""
        # Try multiple encodings
        for encoding in ["utf-8", "latin-1", "cp1252", "utf-8-sig"]:
            try:
                df = pd.read_csv(
                    io.BytesIO(content),
                    encoding=encoding,
                    low_memory=False,
                    on_bad_lines="skip",
                )
                if len(df) > 0 and len(df.columns) > 2:
                    logger.info(
                        f"  Parsed CSV: {len(df)} rows, {len(df.columns)} columns "
                        f"(encoding={encoding})"
                    )
                    return df
            except Exception:
                continue
        return pd.DataFrame()

    def _parse_xlsx_content(self, content: bytes, source_url: str) -> pd.DataFrame:
        """Try to parse XLSX content into a DataFrame."""
        try:
            df = pd.read_excel(io.BytesIO(content), engine="openpyxl")
            if len(df) > 0:
                logger.info(f"  Parsed XLSX: {len(df)} rows, {len(df.columns)} columns")
                return df
        except Exception as exc:
            logger.warning(f"  XLSX parse error: {exc}")
        return pd.DataFrame()

    def _identify_columns(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        Identify which columns in the DataFrame map to our required fields.
        INFONAVIT datasets use varying column names across releases.
        """
        col_lower = {c: c.lower().strip() for c in df.columns}
        mapping = {}

        # State column
        for col, low in col_lower.items():
            if any(
                kw in low
                for kw in ["entidad", "estado", "nom_ent", "entidad_federativa", "edo"]
            ):
                mapping["state"] = col
                break

        # Municipality/city column
        for col, low in col_lower.items():
            if any(
                kw in low
                for kw in [
                    "municipio",
                    "nom_mun",
                    "delegacion",
                    "municipio_delegacion",
                    "alcaldia",
                ]
            ):
                mapping["city"] = col
                break

        # Property value
        for col, low in col_lower.items():
            if any(
                kw in low
                for kw in [
                    "valor_vivienda",
                    "valor_avaluo",
                    "monto_credito",
                    "valor_de_la_vivienda",
                    "precio",
                    "monto",
                    "valor",
                ]
            ):
                mapping["price_mxn"] = col
                break

        # Housing type
        for col, low in col_lower.items():
            if any(
                kw in low
                for kw in [
                    "tipo_vivienda",
                    "tipo_de_vivienda",
                    "segmento",
                    "tipo_credito",
                    "programa",
                    "destino",
                ]
            ):
                mapping["housing_type"] = col
                break

        # Year
        for col, low in col_lower.items():
            if any(kw in low for kw in ["anio", "año", "year", "periodo", "ejercicio"]):
                mapping["year"] = col
                break

        # Area
        for col, low in col_lower.items():
            if any(
                kw in low
                for kw in ["superficie", "area", "m2", "metros"]
            ):
                mapping["area_m2"] = col
                break

        logger.info(f"  Column mapping: {mapping}")
        return mapping

    # ── Normalize to standard format ─────────────────────────────────────

    def _normalize_dataset(
        self, df: pd.DataFrame, source_url: str
    ) -> pd.DataFrame:
        """Normalize an INFONAVIT dataset to the standard property format."""
        if df.empty:
            return pd.DataFrame()

        col_map = self._identify_columns(df)

        if "price_mxn" not in col_map and "state" not in col_map:
            logger.warning("  Cannot identify key columns, skipping dataset")
            logger.info(f"  Available columns: {list(df.columns)}")
            return pd.DataFrame()

        rows: List[Dict] = []

        for _, row in df.iterrows():
            try:
                # State
                state_raw = str(row.get(col_map.get("state", ""), ""))
                state = self._normalize_state(state_raw)

                # City/municipality
                city_raw = str(row.get(col_map.get("city", ""), ""))
                city = city_raw.strip().title() if city_raw else ""

                # Price
                price_raw = row.get(col_map.get("price_mxn", ""), 0)
                try:
                    price_mxn = float(
                        str(price_raw)
                        .replace(",", "")
                        .replace("$", "")
                        .replace(" ", "")
                    )
                except (ValueError, TypeError):
                    price_mxn = 0

                if price_mxn <= 10_000:
                    continue  # Skip invalid prices

                # Housing type
                housing_type_raw = str(
                    row.get(col_map.get("housing_type", ""), "")
                ).strip()
                housing_type = housing_type_raw.lower() if housing_type_raw else ""

                # Area
                if "area_m2" in col_map:
                    try:
                        area_m2 = float(
                            str(row.get(col_map["area_m2"], 0))
                            .replace(",", "")
                            .replace(" ", "")
                        )
                    except (ValueError, TypeError):
                        area_m2 = 0
                else:
                    area_m2 = 0

                # Estimate area from housing type if not available
                if area_m2 <= 0:
                    area_m2 = HOUSING_TYPE_AREA.get(housing_type, 75)

                # Year
                year_raw = row.get(col_map.get("year", ""), "")
                try:
                    year = int(float(str(year_raw)))
                except (ValueError, TypeError):
                    year = datetime.now().year

                # Geocode
                lat, lon = self._geocode_city(city)
                if lat is None:
                    lat, lon = self._geocode_city(city_raw)

                price_m2 = round(price_mxn / area_m2, 2) if area_m2 > 0 else 0

                title = f"INFONAVIT {housing_type_raw} - {city}"

                rows.append(
                    {
                        "title": title[:200],
                        "price_mxn": round(price_mxn, 2),
                        "area_m2": area_m2,
                        "price_m2": price_m2,
                        "address": f"{city}, {state}",
                        "city": city,
                        "state": state,
                        "lat": lat,
                        "lon": lon,
                        "property_type": housing_type_raw or "vivienda",
                        "housing_type": housing_type_raw,
                        "credit_year": year,
                        "source": "infonavit",
                        "source_url": source_url,
                        "collection_date": datetime.now().strftime("%Y-%m-%d"),
                        "scraped_at": datetime.now().isoformat(),
                    }
                )

            except Exception as exc:
                logger.debug(f"Row parse error: {exc}")
                continue

        result = pd.DataFrame(rows)
        logger.info(f"  Normalized: {len(result)} valid records from {len(df)} rows")
        return result

    # ── Main download pipeline ───────────────────────────────────────────

    async def download_and_process(self) -> pd.DataFrame:
        """
        Download all available INFONAVIT datasets, normalize, and combine.

        Returns a DataFrame in standard property format.
        """
        logger.info("=" * 70)
        logger.info("INFONAVIT OPEN DATA DOWNLOADER")
        logger.info(f"  Portal: {INFONAVIT_PORTAL_BASE}")
        logger.info(f"  Output dir: {INFONAVIT_DIR}")
        logger.info("=" * 70)

        all_frames: List[pd.DataFrame] = []

        async with httpx.AsyncClient(
            headers={
                "User-Agent": "IAInmobiliaria-GeoApp/1.0 (research)",
                "Accept": "*/*",
            },
            follow_redirects=True,
        ) as client:

            # 1. Try known direct URLs
            logger.info("\n[1/2] Trying known dataset URLs...")
            for url in KNOWN_DATASET_URLS:
                content = await self._download_file(client, url)
                if content is None:
                    continue

                # Save raw file
                ext = "csv" if ".csv" in url.lower() else "xlsx"
                safe_name = re.sub(r"[^a-zA-Z0-9_]", "_", url.split("/")[-1])[:50]
                raw_path = INFONAVIT_DIR / f"raw_{safe_name}.{ext}"
                raw_path.write_bytes(content)

                # Parse
                if ext == "csv":
                    df_raw = self._parse_csv_content(content, url)
                else:
                    df_raw = self._parse_xlsx_content(content, url)

                if not df_raw.empty:
                    df_norm = self._normalize_dataset(df_raw, url)
                    if not df_norm.empty:
                        all_frames.append(df_norm)

                await asyncio.sleep(2)

            # 2. Discover via CKAN API
            logger.info("\n[2/2] Discovering datasets via CKAN API...")
            discovered_urls = await self._discover_datasets_ckan(client)

            for url in discovered_urls:
                # Skip already-tried URLs
                if url in KNOWN_DATASET_URLS:
                    continue

                content = await self._download_file(client, url)
                if content is None:
                    continue

                ext = "xlsx" if any(
                    x in url.lower() for x in [".xlsx", ".xls"]
                ) else "csv"

                if ext in ("xlsx", "xls"):
                    df_raw = self._parse_xlsx_content(content, url)
                else:
                    df_raw = self._parse_csv_content(content, url)

                if not df_raw.empty:
                    df_norm = self._normalize_dataset(df_raw, url)
                    if not df_norm.empty:
                        all_frames.append(df_norm)

                await asyncio.sleep(2)

        # Combine all datasets
        if not all_frames:
            logger.warning("No INFONAVIT data was downloaded successfully.")
            logger.info(
                "This may be due to portal changes. Check URLs manually at:\n"
                f"  {INFONAVIT_PORTAL_BASE}"
            )
            return pd.DataFrame()

        df_all = pd.concat(all_frames, ignore_index=True)

        # Deduplicate
        before = len(df_all)
        df_all = df_all.drop_duplicates(
            subset=["price_mxn", "city", "state", "housing_type", "credit_year"],
            keep="first",
        )
        logger.info(f"Deduplication: {before} -> {len(df_all)}")

        # Filter valid prices
        df_all = df_all[df_all["price_mxn"] > 50_000]
        df_all = df_all[df_all["price_mxn"] < 50_000_000]

        return df_all

    # ── Save ─────────────────────────────────────────────────────────────

    def save_csv(self, df: pd.DataFrame, filename: Optional[str] = None) -> Path:
        """Save processed data to CSV."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d")
            filename = f"infonavit_{timestamp}.csv"
        filepath = DATA_DIR / filename
        df.to_csv(filepath, index=False, encoding="utf-8-sig")
        logger.info(f"Saved {len(df)} records to {filepath}")
        return filepath


# ── CLI entry point ──────────────────────────────────────────────────────────

async def main():
    """Download and process all INFONAVIT open data."""
    scraper = InfonavitScraper()
    df = await scraper.download_and_process()

    if df.empty:
        logger.warning("No results obtained.")
        return

    filepath = scraper.save_csv(df)

    # Coverage report
    logger.info("\n" + "=" * 60)
    logger.info("COVERAGE REPORT — INFONAVIT")
    logger.info("=" * 60)

    state_counts = df.groupby("state").size().sort_values(ascending=False)
    for state, count in state_counts.items():
        logger.info(f"  {state:<30s} {count:>8,}")

    logger.info(f"\n  TOTAL: {len(df):,} records across {df['state'].nunique()} states")

    with_coords = df[df["lat"].notna() & df["lon"].notna()]
    logger.info(f"  With coordinates: {len(with_coords):,} / {len(df):,}")

    if "credit_year" in df.columns:
        year_counts = df.groupby("credit_year").size()
        logger.info("\nBy year:")
        for year, count in year_counts.items():
            logger.info(f"  {int(year)}: {count:>8,}")


if __name__ == "__main__":
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level:<8}</level> | <level>{message}</level>",
        level="INFO",
    )
    asyncio.run(main())
