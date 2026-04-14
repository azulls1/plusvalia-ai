"""
Mercado Libre Real Estate Scraper — PUBLIC REST API.

Uses the Mercado Libre public search API (no auth required) to fetch
real estate listings across all 32 Mexican states.

API docs: https://developers.mercadolibre.com/es_ar/items-y-busquedas
Site: MLM (Mexico)
Categories:
  MLM1459  Inmuebles (root)
  MLM1466  Terrenos
  MLM1467  Casas
  MLM1468  Departamentos

Rate limit: ~1 req/s (respectful default).
Max pagination depth: offset 0-980 (API hard cap at 1000 results per query).
To exceed 1000: combine state + category + price-range filters.
"""

import asyncio
import csv
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

from config import DATA_DIR, SCRAPER_DELAY

# ── Constants ────────────────────────────────────────────────────────────────

BASE_URL = "https://api.mercadolibre.com"
SITE_ID = "MLM"

CATEGORIES = {
    "terrenos": "MLM1466",
    "casas": "MLM1467",
    "departamentos": "MLM1468",
}

# Mercado Libre state codes for Mexico (MLM-XXX)
MLM_STATE_CODES: Dict[str, str] = {
    "Aguascalientes": "TUxNUEFHVWE0MDkx",
    "Baja California": "TUxNUEJBSmE1MjQ1",
    "Baja California Sur": "TUxNUEJBSmI4ZmMz",
    "Campeche": "TUxNUENBTW8xMTNiOA",
    "Chiapas": "TUxNUENIUGEzNTY4",
    "Chihuahua": "TUxNUENISWE5OTU3",
    "Ciudad de México": "TUxNUERJU28xMzMzMQ",
    "Coahuila": "TUxNUENPQWg2OTVi",
    "Colima": "TUxNUENPTG8yNjI2",
    "Durango": "TUxNUERVUmExMDE1Mg",
    "Guanajuato": "TUxNUEdVQWo1Nzcz",
    "Guerrero": "TUxNUEdSTzg0NTU",
    "Hidalgo": "TUxNUEhJRGFkYzAz",
    "Jalisco": "TUxNUEpBTGFiNTlm",
    "México": "TUxNUE1FWGFiMjgw",
    "Michoacán": "TUxNUE1JQ2ExMTg0MQ",
    "Morelos": "TUxNUE1PUmE5NjI4",
    "Nayarit": "TUxNUE5BWXMzNTAy",
    "Nuevo León": "TUxNUE5VRWE0MDMy",
    "Oaxaca": "TUxNUE9BWGEyMDI5",
    "Puebla": "TUxNUFBVRWExMzY0MQ",
    "Querétaro": "TUxNUFFVRWE5ODE",
    "Quintana Roo": "TUxNUFFVSW4zYjgy",
    "San Luis Potosí": "TUxNUFNBTm8xMDI5Mg",
    "Sinaloa": "TUxNUFNJTmExMDMwNA",
    "Sonora": "TUxNUFNPTm8xMTg0NA",
    "Tabasco": "TUxNUFRBQm8xMDkwMw",
    "Tamaulipas": "TUxNUFRBTWE3NTg2",
    "Tlaxcala": "TUxNUFRMQWE5Njky",
    "Veracruz": "TUxNUFZFUmE1MjE",
    "Yucatán": "TUxNUFlVQ2ExMzg5Nw",
    "Zacatecas": "TUxNUFpBQ2E0MDMz",
}

# Simpler approach: use the textual state filter which MeLi accepts
MLM_STATE_IDS: Dict[str, str] = {
    "Aguascalientes": "MLM-AGU",
    "Baja California": "MLM-BCN",
    "Baja California Sur": "MLM-BCS",
    "Campeche": "MLM-CAM",
    "Chiapas": "MLM-CHP",
    "Chihuahua": "MLM-CHH",
    "Ciudad de México": "MLM-CMX",
    "Coahuila": "MLM-COA",
    "Colima": "MLM-COL",
    "Durango": "MLM-DUR",
    "Guanajuato": "MLM-GUA",
    "Guerrero": "MLM-GRO",
    "Hidalgo": "MLM-HID",
    "Jalisco": "MLM-JAL",
    "México": "MLM-MEX",
    "Michoacán": "MLM-MIC",
    "Morelos": "MLM-MOR",
    "Nayarit": "MLM-NAY",
    "Nuevo León": "MLM-NLE",
    "Oaxaca": "MLM-OAX",
    "Puebla": "MLM-PUE",
    "Querétaro": "MLM-QUE",
    "Quintana Roo": "MLM-ROO",
    "San Luis Potosí": "MLM-SLP",
    "Sinaloa": "MLM-SIN",
    "Sonora": "MLM-SON",
    "Tabasco": "MLM-TAB",
    "Tamaulipas": "MLM-TAM",
    "Tlaxcala": "MLM-TLA",
    "Veracruz": "MLM-VER",
    "Yucatán": "MLM-YUC",
    "Zacatecas": "MLM-ZAC",
}

# USD to MXN approximate rate (updated periodically)
USD_TO_MXN = 17.2

# Price range buckets to exceed the 1000-result API cap per state
PRICE_RANGES_MXN: List[Tuple[int, int]] = [
    (0, 500_000),
    (500_000, 1_000_000),
    (1_000_000, 2_000_000),
    (2_000_000, 5_000_000),
    (5_000_000, 10_000_000),
    (10_000_000, 50_000_000),
    (50_000_000, 999_999_999),
]


class MercadoLibreScraper:
    """
    Scraper for Mercado Libre Mexico real estate listings using the public
    REST search API.  No authentication token is required for search queries.
    """

    def __init__(
        self,
        delay: float = max(SCRAPER_DELAY, 1.0),
        categories: Optional[List[str]] = None,
    ):
        self.delay = delay
        self.categories = categories or ["terrenos", "casas", "departamentos"]
        self.results: List[Dict[str, Any]] = []
        self._seen_ids: set = set()

    # ── HTTP helper ──────────────────────────────────────────────────────

    _HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "es-MX,es;q=0.9,en;q=0.8",
        "Referer": "https://inmuebles.mercadolibre.com.mx/",
    }

    async def _get_json(
        self,
        client: httpx.AsyncClient,
        url: str,
        params: Dict[str, Any],
        max_retries: int = 3,
    ) -> Optional[Dict]:
        """GET request with retries and rate limiting."""
        for attempt in range(max_retries):
            try:
                resp = await client.get(url, params=params, headers=self._HEADERS, timeout=30)
                if resp.status_code == 200:
                    return resp.json()
                elif resp.status_code == 429:
                    wait = 2 ** (attempt + 1)
                    logger.warning(f"Rate-limited (429). Waiting {wait}s...")
                    await asyncio.sleep(wait)
                else:
                    logger.warning(
                        f"HTTP {resp.status_code} for {url} (attempt {attempt+1})"
                    )
            except (httpx.TimeoutException, httpx.ConnectError, OSError) as exc:
                logger.warning(f"Request error: {exc} (attempt {attempt+1})")
                await asyncio.sleep(2 ** attempt)
        return None

    # ── Core: paginate one query ─────────────────────────────────────────

    async def _paginate_search(
        self,
        client: httpx.AsyncClient,
        params: Dict[str, Any],
        state_name: str,
        category_name: str,
        max_results: int = 1000,
    ) -> List[Dict]:
        """Paginate through search results for a single query."""
        items: List[Dict] = []
        offset = 0
        limit = 50  # MeLi max per page

        while offset < max_results:
            params_page = {**params, "offset": offset, "limit": limit}
            data = await self._get_json(
                client, f"{BASE_URL}/sites/{SITE_ID}/search", params_page
            )
            if data is None:
                break

            results = data.get("results", [])
            if not results:
                break

            total = data.get("paging", {}).get("total", 0)

            for item in results:
                item_id = item.get("id", "")
                if item_id in self._seen_ids:
                    continue
                self._seen_ids.add(item_id)

                parsed = self._parse_item(item, state_name, category_name)
                if parsed:
                    items.append(parsed)

            offset += limit

            # Don't exceed actual total
            if offset >= min(total, max_results):
                break

            await asyncio.sleep(self.delay)

        return items

    # ── Parse a single item ──────────────────────────────────────────────

    def _parse_item(
        self, item: Dict, state_name: str, category_name: str
    ) -> Optional[Dict]:
        """Extract relevant fields from an API item."""
        try:
            price = item.get("price", 0) or 0
            currency = item.get("currency_id", "MXN")

            # Convert USD to MXN
            if currency == "USD":
                price_mxn = price * USD_TO_MXN
            else:
                price_mxn = price

            if price_mxn <= 0:
                return None

            # Extract area from attributes
            area_m2 = 0.0
            attributes = item.get("attributes", [])
            for attr in attributes:
                attr_id = attr.get("id", "")
                if attr_id in (
                    "TOTAL_AREA",
                    "COVERED_AREA",
                    "LAND_AREA",
                    "SURFACE",
                ):
                    try:
                        val = attr.get("value_name", "0")
                        area_m2 = float(
                            val.replace(" m²", "")
                            .replace(",", "")
                            .replace(" ", "")
                        )
                        if area_m2 > 0:
                            break
                    except (ValueError, TypeError):
                        continue

            # Extract lat/lon from location
            location = item.get("location", {}) or {}
            lat = location.get("latitude")
            lon = location.get("longitude")

            # City from location
            city_data = location.get("city", {}) or {}
            city_name = city_data.get("name", "")
            state_data = location.get("state", {}) or {}
            api_state_name = state_data.get("name", state_name)

            # Address / neighborhood
            neighborhood = location.get("neighborhood", {}) or {}
            address_parts = [
                neighborhood.get("name", ""),
                city_name,
                api_state_name,
            ]
            address = ", ".join(p for p in address_parts if p)

            price_m2 = round(price_mxn / area_m2, 2) if area_m2 > 0 else 0.0

            return {
                "id_source": item.get("id", ""),
                "title": (item.get("title", "") or "")[:200],
                "price_mxn": round(price_mxn, 2),
                "currency_original": currency,
                "price_original": price,
                "area_m2": area_m2,
                "price_m2": price_m2,
                "address": address,
                "city": city_name,
                "state": api_state_name,
                "lat": lat,
                "lon": lon,
                "property_type": category_name,
                "source": "mercadolibre",
                "source_url": item.get("permalink", ""),
                "collection_date": datetime.now().strftime("%Y-%m-%d"),
                "scraped_at": datetime.now().isoformat(),
            }
        except (KeyError, TypeError, ValueError) as exc:
            logger.debug(f"Parse error: {exc}")
            return None

    # ── Scrape one state ─────────────────────────────────────────────────

    async def scrape_state(
        self,
        client: httpx.AsyncClient,
        state_name: str,
    ) -> List[Dict]:
        """Scrape all categories for a single state, using price-range buckets."""
        state_id = MLM_STATE_CODES.get(state_name)
        if not state_id:
            logger.warning(f"No state code for {state_name}, skipping")
            return []

        state_items: List[Dict] = []

        for cat_name in self.categories:
            cat_id = CATEGORIES.get(cat_name)
            if not cat_id:
                continue

            logger.info(
                f"  [{state_name}] category={cat_name} ({cat_id})"
            )

            for price_min, price_max in PRICE_RANGES_MXN:
                params = {
                    "category": cat_id,
                    "state": state_id,
                    "price": f"{price_min}-{price_max}",
                    "sort": "relevance",
                }
                items = await self._paginate_search(
                    client, params, state_name, cat_name
                )
                state_items.extend(items)

                if items:
                    logger.info(
                        f"    price {price_min:>12,}-{price_max:>12,}: "
                        f"{len(items)} items"
                    )
                await asyncio.sleep(self.delay * 0.5)

        logger.info(
            f"  [{state_name}] total: {len(state_items)} items"
        )
        return state_items

    # ── Scrape all 32 states ─────────────────────────────────────────────

    async def scrape_all_states(
        self,
        states: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        Scrape real estate listings for all (or selected) Mexican states.

        Args:
            states: List of state names to scrape.  None = all 32.

        Returns:
            DataFrame with all listings.
        """
        target_states = states or list(MLM_STATE_CODES.keys())

        logger.info("=" * 70)
        logger.info("MERCADO LIBRE REAL ESTATE SCRAPER")
        logger.info(f"  States: {len(target_states)}")
        logger.info(f"  Categories: {self.categories}")
        logger.info(f"  Delay: {self.delay}s")
        logger.info("=" * 70)

        async with httpx.AsyncClient(
            headers={
                "Accept": "application/json",
                "User-Agent": "IAInmobiliaria-GeoApp/1.0 (research)",
            },
            follow_redirects=True,
        ) as client:
            for idx, state_name in enumerate(target_states, 1):
                logger.info(
                    f"\n[{idx}/{len(target_states)}] Scraping {state_name}..."
                )
                items = await self.scrape_state(client, state_name)
                self.results.extend(items)

                logger.info(
                    f"  Running total: {len(self.results)} items"
                )

        df = pd.DataFrame(self.results)

        if not df.empty:
            # Deduplicate on source id
            before = len(df)
            df = df.drop_duplicates(subset=["id_source"], keep="first")
            logger.info(
                f"Deduplication: {before} -> {len(df)} "
                f"(removed {before - len(df)})"
            )

        return df

    # ── Save ─────────────────────────────────────────────────────────────

    def save_csv(self, df: pd.DataFrame, filename: Optional[str] = None) -> Path:
        """Save results to CSV."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d")
            filename = f"mercadolibre_{timestamp}.csv"
        filepath = DATA_DIR / filename
        df.to_csv(filepath, index=False, encoding="utf-8-sig")
        logger.info(f"Saved {len(df)} records to {filepath}")
        return filepath


# ── CLI entry point ──────────────────────────────────────────────────────────

async def main():
    """Run the Mercado Libre scraper for all 32 states."""
    scraper = MercadoLibreScraper(delay=1.0)
    df = await scraper.scrape_all_states()

    if df.empty:
        logger.warning("No results obtained.")
        return

    filepath = scraper.save_csv(df)

    # Coverage report
    logger.info("\n" + "=" * 60)
    logger.info("COVERAGE REPORT — Mercado Libre")
    logger.info("=" * 60)
    state_counts = df.groupby("state").size().sort_values(ascending=False)
    for state, count in state_counts.items():
        marker = "OK" if count >= 100 else "LOW"
        logger.info(f"  {state:<30s} {count:>6,}  [{marker}]")
    logger.info(f"\n  TOTAL: {len(df):,} listings across {df['state'].nunique()} states")

    cat_counts = df.groupby("property_type").size()
    logger.info("\nBy property type:")
    for cat, count in cat_counts.items():
        logger.info(f"  {cat:<20s} {count:>6,}")

    with_coords = df[df["lat"].notna() & df["lon"].notna()]
    logger.info(f"\nWith coordinates: {len(with_coords):,} / {len(df):,}")
    with_area = df[df["area_m2"] > 0]
    logger.info(f"With area_m2:     {len(with_area):,} / {len(df):,}")


if __name__ == "__main__":
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level:<8}</level> | <level>{message}</level>",
        level="INFO",
    )
    asyncio.run(main())
