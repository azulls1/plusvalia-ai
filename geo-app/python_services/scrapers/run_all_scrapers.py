"""
Orchestrator: Run all data source scrapers and produce a unified dataset.

Executes the following scrapers in sequence:
  1. Mercado Libre (public REST API — all 32 states)
  2. INFONAVIT open data (credit originations → property values)
  3. SNIIV / SEDATU (government housing data, expanded 2015-2025)
  4. INEGI DENUE amenities (optional, for feature enrichment)

After all scrapers finish, combines results into a single CSV and
prints a coverage report showing records per state and per source.

Usage:
    python -m scrapers.run_all_scrapers
    python -m scrapers.run_all_scrapers --skip-denue   # skip amenities
    python -m scrapers.run_all_scrapers --only mercadolibre infonavit
"""

import argparse
import asyncio
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)

from config import DATA_DIR

# ── Target: 5,000 records minimum per state ─────────────────────────────────

TARGET_PER_STATE = 5_000

ALL_32_STATES = [
    "Aguascalientes", "Baja California", "Baja California Sur", "Campeche",
    "Chiapas", "Chihuahua", "Ciudad de México", "Coahuila", "Colima",
    "Durango", "Guanajuato", "Guerrero", "Hidalgo", "Jalisco", "México",
    "Michoacán", "Morelos", "Nayarit", "Nuevo León", "Oaxaca", "Puebla",
    "Querétaro", "Quintana Roo", "San Luis Potosí", "Sinaloa", "Sonora",
    "Tabasco", "Tamaulipas", "Tlaxcala", "Veracruz", "Yucatán", "Zacatecas",
]


def _normalize_state(s: str) -> str:
    """Normalize state name for consistent grouping."""
    if not isinstance(s, str):
        return ""
    mapping = {
        "estado de mexico": "México",
        "estado de méxico": "México",
        "cdmx": "Ciudad de México",
        "distrito federal": "Ciudad de México",
        "ciudad de mexico": "Ciudad de México",
    }
    return mapping.get(s.strip().lower(), s.strip())


# ── 1. Mercado Libre ────────────────────────────────────────────────────────

async def run_mercadolibre() -> Optional[pd.DataFrame]:
    """Run the Mercado Libre real estate scraper."""
    logger.info("\n" + "=" * 70)
    logger.info("SCRAPER 1/3: MERCADO LIBRE")
    logger.info("=" * 70)

    try:
        from scrapers.mercadolibre_scraper import MercadoLibreScraper

        scraper = MercadoLibreScraper(delay=1.0)
        df = await scraper.scrape_all_states()

        if not df.empty:
            filepath = scraper.save_csv(df)
            logger.info(f"Mercado Libre: {len(df)} records saved to {filepath}")
        else:
            logger.warning("Mercado Libre: no results")

        return df

    except Exception as exc:
        logger.error(f"Mercado Libre scraper failed: {exc}")
        import traceback
        logger.error(traceback.format_exc())
        return None


# ── 2. INFONAVIT ────────────────────────────────────────────────────────────

async def run_infonavit() -> Optional[pd.DataFrame]:
    """Run the INFONAVIT open data downloader."""
    logger.info("\n" + "=" * 70)
    logger.info("SCRAPER 2/3: INFONAVIT OPEN DATA")
    logger.info("=" * 70)

    try:
        from scrapers.infonavit_scraper import InfonavitScraper

        scraper = InfonavitScraper()
        df = await scraper.download_and_process()

        if not df.empty:
            filepath = scraper.save_csv(df)
            logger.info(f"INFONAVIT: {len(df)} records saved to {filepath}")
        else:
            logger.warning("INFONAVIT: no results")

        return df

    except Exception as exc:
        logger.error(f"INFONAVIT scraper failed: {exc}")
        import traceback
        logger.error(traceback.format_exc())
        return None


# ── 3. SNIIV ────────────────────────────────────────────────────────────────

def run_sniiv() -> Optional[pd.DataFrame]:
    """Run the SNIIV downloader (synchronous)."""
    logger.info("\n" + "=" * 70)
    logger.info("SCRAPER 3/3: SNIIV (SEDATU)")
    logger.info("=" * 70)

    try:
        from scripts.download_sniiv import main as sniiv_main

        # SNIIV main() saves files and prints stats; we read them back
        sniiv_main()

        # Load the processed output
        timestamp = datetime.now().strftime("%Y%m%d")
        sniiv_path = DATA_DIR / f"sniiv_processed_{timestamp}.csv"

        if sniiv_path.exists():
            df = pd.read_csv(sniiv_path)
            logger.info(f"SNIIV: {len(df)} records loaded from {sniiv_path}")
            return df

        # Try per-state file
        per_state_path = DATA_DIR / f"sniiv_per_state_{timestamp}.csv"
        if per_state_path.exists():
            df = pd.read_csv(per_state_path)
            logger.info(f"SNIIV per-state: {len(df)} records loaded")
            return df

        logger.warning("SNIIV: no output files found")
        return None

    except Exception as exc:
        logger.error(f"SNIIV scraper failed: {exc}")
        import traceback
        logger.error(traceback.format_exc())
        return None


# ── 4. INEGI DENUE (optional) ───────────────────────────────────────────────

async def run_denue() -> Optional[pd.DataFrame]:
    """Run the INEGI DENUE amenities scraper (optional)."""
    logger.info("\n" + "=" * 70)
    logger.info("OPTIONAL: INEGI DENUE AMENITIES")
    logger.info("=" * 70)

    try:
        from scrapers.inegi_denue_scraper import INEGIDenueScraper

        scraper = INEGIDenueScraper()

        if not scraper.token:
            logger.warning(
                "INEGI_API_TOKEN not configured. Skipping DENUE scraper.\n"
                "Set INEGI_API_TOKEN in .env to enable amenity data collection."
            )
            return None

        result = await scraper.scrape_all_amenities()
        if isinstance(result, tuple):
            df_detail, df_summary = result
        else:
            df_detail = result
            df_summary = pd.DataFrame()

        if not df_detail.empty:
            scraper.save_csv(df_detail, df_summary)
            logger.info(f"DENUE: {len(df_detail)} amenity records saved")

        return df_summary  # Summary is more useful for the unified dataset

    except Exception as exc:
        logger.error(f"DENUE scraper failed: {exc}")
        import traceback
        logger.error(traceback.format_exc())
        return None


# ── Combine all sources ─────────────────────────────────────────────────────

def combine_all_sources(
    dfs: Dict[str, Optional[pd.DataFrame]],
) -> pd.DataFrame:
    """
    Combine DataFrames from all sources into a single unified dataset.

    Normalizes column names, fills missing values, and deduplicates.
    """
    logger.info("\n" + "=" * 70)
    logger.info("COMBINING ALL DATA SOURCES")
    logger.info("=" * 70)

    # Standard columns for the unified dataset
    STANDARD_COLS = [
        "title", "price_mxn", "area_m2", "price_m2",
        "address", "city", "state", "lat", "lon",
        "property_type", "source", "source_url", "collection_date",
    ]

    frames: List[pd.DataFrame] = []

    for source_name, df in dfs.items():
        if df is None or df.empty:
            logger.info(f"  {source_name}: SKIPPED (no data)")
            continue

        logger.info(f"  {source_name}: {len(df)} records")

        # Ensure standard columns exist
        for col in STANDARD_COLS:
            if col not in df.columns:
                df[col] = ""

        # Ensure source is set
        if "source" not in df.columns or df["source"].isna().all():
            df["source"] = source_name

        # Normalize state names
        df["state"] = df["state"].apply(_normalize_state)

        # Calculate price_m2 if missing
        mask = (df["price_m2"].isna() | (df["price_m2"] == 0)) & (df["area_m2"] > 0)
        df.loc[mask, "price_m2"] = df.loc[mask, "price_mxn"] / df.loc[mask, "area_m2"]

        frames.append(df[STANDARD_COLS].copy())

    if not frames:
        logger.error("No data from any source!")
        return pd.DataFrame()

    df_all = pd.concat(frames, ignore_index=True)

    # Deduplicate: same title + price + city is likely the same listing
    before = len(df_all)
    df_all = df_all.drop_duplicates(
        subset=["title", "price_mxn", "city"],
        keep="first",
    )
    logger.info(f"  Deduplication: {before} -> {len(df_all)} records")

    # Filter invalid records
    df_all = df_all[df_all["price_mxn"] > 0]
    df_all = df_all[df_all["state"] != ""]

    logger.info(f"  Final: {len(df_all)} valid records")
    return df_all


# ── Coverage report ─────────────────────────────────────────────────────────

def print_coverage_report(df: pd.DataFrame):
    """Print a detailed coverage report by state and source."""
    logger.info("\n" + "=" * 70)
    logger.info("COVERAGE REPORT — ALL SOURCES COMBINED")
    logger.info("=" * 70)

    if df.empty:
        logger.warning("No data to report.")
        return

    # By state
    logger.info(f"\n{'State':<30s} {'Records':>8s} {'Sources':>10s} {'Status':>10s}")
    logger.info("-" * 62)

    state_counts = df.groupby("state").agg(
        records=("state", "size"),
        sources=("source", "nunique"),
    ).sort_values("records", ascending=False)

    states_ok = 0
    states_low = 0

    for state in ALL_32_STATES:
        if state in state_counts.index:
            row = state_counts.loc[state]
            count = int(row["records"])
            n_sources = int(row["sources"])
            status = "OK" if count >= TARGET_PER_STATE else "UNDER"
        else:
            count = 0
            n_sources = 0
            status = "MISSING"

        if count >= TARGET_PER_STATE:
            states_ok += 1
        else:
            states_low += 1

        logger.info(f"  {state:<28s} {count:>8,}  {n_sources:>6}     [{status}]")

    logger.info("-" * 62)
    logger.info(f"  TOTAL RECORDS: {len(df):>8,}")
    logger.info(f"  STATES >= {TARGET_PER_STATE:,}: {states_ok}/32")
    logger.info(f"  STATES < {TARGET_PER_STATE:,}: {states_low}/32")

    # By source
    logger.info(f"\n{'Source':<25s} {'Records':>10s} {'States':>8s}")
    logger.info("-" * 47)
    source_counts = df.groupby("source").agg(
        records=("source", "size"),
        states=("state", "nunique"),
    ).sort_values("records", ascending=False)

    for source, row in source_counts.iterrows():
        logger.info(f"  {source:<23s} {int(row['records']):>10,} {int(row['states']):>8}")

    # Records with coordinates
    with_coords = df[df["lat"].notna() & (df["lat"] != 0) & df["lon"].notna() & (df["lon"] != 0)]
    pct = len(with_coords) / len(df) * 100 if len(df) > 0 else 0
    logger.info(f"\n  With coordinates: {len(with_coords):,} / {len(df):,} ({pct:.1f}%)")

    with_area = df[df["area_m2"] > 0]
    pct_a = len(with_area) / len(df) * 100 if len(df) > 0 else 0
    logger.info(f"  With area_m2:     {len(with_area):,} / {len(df):,} ({pct_a:.1f}%)")

    # States that still need more data
    under_states = [
        s for s in ALL_32_STATES
        if s not in state_counts.index or state_counts.loc[s, "records"] < TARGET_PER_STATE
    ]
    if under_states:
        logger.info(f"\n  States still under {TARGET_PER_STATE:,} records ({len(under_states)}):")
        for s in under_states:
            count = int(state_counts.loc[s, "records"]) if s in state_counts.index else 0
            deficit = TARGET_PER_STATE - count
            logger.info(f"    {s:<28s} has {count:>6,}, needs {deficit:>6,} more")


# ── Main ─────────────────────────────────────────────────────────────────────

async def main():
    """Run all scrapers and produce the unified dataset."""
    parser = argparse.ArgumentParser(description="Run all data source scrapers")
    parser.add_argument(
        "--skip-denue", action="store_true",
        help="Skip the INEGI DENUE amenities scraper"
    )
    parser.add_argument(
        "--only", nargs="+", choices=["mercadolibre", "infonavit", "sniiv", "denue"],
        help="Run only specified scrapers"
    )

    args, _ = parser.parse_known_args()

    start_time = time.time()
    timestamp = datetime.now().strftime("%Y%m%d")

    logger.info("=" * 70)
    logger.info("IAInmobiliaria — UNIFIED DATA COLLECTION PIPELINE")
    logger.info(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"  Target: {TARGET_PER_STATE:,} records per state, 32 states")
    logger.info("=" * 70)

    scrapers_to_run = args.only or ["mercadolibre", "infonavit", "sniiv"]

    results: Dict[str, Optional[pd.DataFrame]] = {}

    # 1. Mercado Libre
    if "mercadolibre" in scrapers_to_run:
        results["mercadolibre"] = await run_mercadolibre()
    else:
        logger.info("Skipping Mercado Libre")

    # 2. INFONAVIT
    if "infonavit" in scrapers_to_run:
        results["infonavit"] = await run_infonavit()
    else:
        logger.info("Skipping INFONAVIT")

    # 3. SNIIV (synchronous)
    if "sniiv" in scrapers_to_run:
        results["sniiv"] = run_sniiv()
    else:
        logger.info("Skipping SNIIV")

    # 4. DENUE (optional)
    if "denue" in scrapers_to_run and not args.skip_denue:
        results["denue"] = await run_denue()

    # Combine
    df_unified = combine_all_sources(results)

    if not df_unified.empty:
        # Save unified dataset
        output_path = DATA_DIR / f"unified_all_sources_{timestamp}.csv"
        df_unified.to_csv(output_path, index=False, encoding="utf-8-sig")
        logger.info(f"\nUnified dataset saved: {output_path}")

        # Coverage report
        print_coverage_report(df_unified)
    else:
        logger.error("No data collected from any source.")

    elapsed = time.time() - start_time
    logger.info(f"\nTotal elapsed time: {elapsed/60:.1f} minutes")


if __name__ == "__main__":
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level:<8}</level> | <level>{message}</level>",
        level="INFO",
    )
    logger.add(
        str(Path(__file__).parent.parent / "logs" / "scraper_run_{time:YYYYMMDD}.log"),
        rotation="10 MB",
        level="DEBUG",
    )

    asyncio.run(main())
