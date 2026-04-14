#!/usr/bin/env python3
# ================================================================
# CLEAN TRAINING DATA PIPELINE
# ================================================================
# This script cleans the unified training data by:
# 1. Removing all synthetic/generated records
# 2. Adding `year` feature from collection_date
# 3. Applying INPC inflation adjustment to Properati data (2013-2026)
# 4. Applying cadastral-to-market correction for CDMX catastro
# 5. Adding `property_type` column from title field
# 6. Cleaning corrupted state entries
# 7. Removing price outliers
# 8. Saving cleaned data with full summary
# ================================================================

import sys
import re
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
from loguru import logger

# ================================================================
# INPC CUMULATIVE INFLATION FACTORS (base year = 2026)
# Source: Banco de Mexico / INEGI INPC index
# Each factor converts that year's MXN to 2026 MXN equivalent.
# Example: 1 MXN in 2013 = 1.70 MXN in 2026
# ================================================================
INPC_FACTORS = {
    2013: 1.70,
    2014: 1.63,
    2015: 1.59,
    2016: 1.54,
    2017: 1.44,
    2018: 1.37,
    2019: 1.32,
    2020: 1.28,
    2021: 1.19,
    2022: 1.10,
    2023: 1.05,
    2024: 1.02,
    2025: 1.00,
    2026: 1.00,
}

# Cadastral-to-market correction multiplier
# CDMX catastro values are typically 30-60% below market
# Using 2.5x as conservative assessed-to-market ratio
CATASTRO_MARKET_FACTOR = 2.5

# Outlier thresholds for price per m2 (MXN)
MIN_PRICE_M2 = 100
MAX_PRICE_M2 = 200_000

# Valid Mexican states (canonical names)
VALID_STATES = {
    'Aguascalientes', 'Baja California', 'Baja California Sur',
    'Campeche', 'Chiapas', 'Chihuahua', 'Ciudad de Mexico',
    'Ciudad de México', 'Coahuila', 'Coahuila de Zaragoza',
    'Colima', 'Distrito Federal', 'Durango',
    'Estado de México', 'Estado de Mexico', 'Guanajuato',
    'Guerrero', 'Hidalgo', 'Jalisco', 'México', 'Mexico',
    'Michoacán', 'Michoacan', 'Morelos', 'Nayarit',
    'Nuevo León', 'Nuevo Leon', 'Oaxaca', 'Puebla',
    'Querétaro', 'Queretaro', 'Quintana Roo',
    'San Luis Potosí', 'San Luis Potosi', 'Sinaloa',
    'Sonora', 'Tabasco', 'Tamaulipas', 'Tlaxcala',
    'Veracruz', 'Veracruz de Ignacio de la Llave',
    'Yucatán', 'Yucatan', 'Zacatecas',
}


def find_latest_training_csv(data_dir: Path) -> Path:
    """Find the most recent training_ready_*.csv or unified_training_data_*.csv."""
    candidates = sorted(data_dir.glob('training_ready_*.csv'), reverse=True)
    if candidates:
        return candidates[0]
    candidates = sorted(data_dir.glob('unified_training_data_*.csv'), reverse=True)
    if candidates:
        return candidates[0]
    raise FileNotFoundError(
        f"No training CSV found in {data_dir}. "
        "Expected training_ready_*.csv or unified_training_data_*.csv"
    )


def load_data(csv_path: Path) -> pd.DataFrame:
    """Load CSV with proper dtypes."""
    logger.info(f"Loading data from: {csv_path}")
    df = pd.read_csv(csv_path, low_memory=False)
    logger.info(f"Loaded {len(df):,} records with {len(df.columns)} columns")
    logger.info(f"Columns: {list(df.columns)}")
    return df


def remove_synthetic(df: pd.DataFrame) -> pd.DataFrame:
    """Remove all synthetic/generated records.

    Identifies synthetic data by:
    - source == 'synthetic'
    - source containing 'pipeline_32' or 'generated'
    - title starting with 'Terreno en' AND source == 'synthetic'
    """
    before = len(df)

    # Build mask for synthetic records
    is_synthetic = (
        df['source'].str.lower().str.contains('synthetic', na=False) |
        df['source'].str.lower().str.contains('pipeline_32', na=False) |
        df['source'].str.lower().str.contains('generated', na=False)
    )

    n_synthetic = is_synthetic.sum()
    df_clean = df[~is_synthetic].copy()

    logger.info(
        f"Removed {n_synthetic:,} synthetic records "
        f"({n_synthetic/before*100:.1f}% of data). "
        f"Remaining: {len(df_clean):,}"
    )
    return df_clean


def add_year_feature(df: pd.DataFrame) -> pd.DataFrame:
    """Extract year from collection_date and add as feature."""
    df['collection_date_parsed'] = pd.to_datetime(
        df['collection_date'], errors='coerce'
    )
    df['year'] = df['collection_date_parsed'].dt.year

    # Fill missing years with median year from the dataset
    median_year = int(df['year'].median()) if df['year'].notna().any() else 2020
    missing_count = df['year'].isna().sum()
    if missing_count > 0:
        logger.warning(
            f"{missing_count:,} records have unparseable collection_date. "
            f"Filling year with median={median_year}"
        )
        df['year'] = df['year'].fillna(median_year).astype(int)
    else:
        df['year'] = df['year'].astype(int)

    logger.info(f"Year feature added. Range: {df['year'].min()}-{df['year'].max()}")
    return df


def apply_inpc_adjustment(df: pd.DataFrame) -> pd.DataFrame:
    """Apply INPC inflation adjustment to Properati records.

    Properati data spans 2013-2016. Prices must be adjusted to 2026 MXN
    using cumulative INPC inflation factors from Banco de Mexico.
    """
    is_properati = df['source'].str.lower().str.contains('properati', na=False)
    n_properati = is_properati.sum()

    if n_properati == 0:
        logger.info("No Properati records found to adjust")
        return df

    logger.info(f"Applying INPC inflation adjustment to {n_properati:,} Properati records...")

    # Map year to INPC factor, default 1.0 for unknown years
    df['inpc_factor'] = df['year'].map(INPC_FACTORS).fillna(1.0)

    # Only adjust Properati records
    mask = is_properati
    df.loc[mask, 'price_mxn_original'] = df.loc[mask, 'price_mxn']
    df.loc[mask, 'price_m2_original'] = df.loc[mask, 'price_m2']
    df.loc[mask, 'price_mxn'] = df.loc[mask, 'price_mxn'] * df.loc[mask, 'inpc_factor']
    df.loc[mask, 'price_m2'] = df.loc[mask, 'price_m2'] * df.loc[mask, 'inpc_factor']

    # Log adjustment stats by year
    adjusted = df.loc[mask].groupby('year').agg(
        count=('price_m2', 'count'),
        factor=('inpc_factor', 'first'),
        avg_price_m2_adjusted=('price_m2', 'mean'),
    )
    for year, row in adjusted.iterrows():
        logger.info(
            f"  Year {year}: {row['count']:,} records x {row['factor']:.2f} -> "
            f"avg price_m2 = ${row['avg_price_m2_adjusted']:,.0f}"
        )

    return df


def apply_catastro_correction(df: pd.DataFrame) -> pd.DataFrame:
    """Apply cadastral-to-market value correction for CDMX catastro records.

    Catastro (assessed) values in Mexico are typically 30-60% below
    market values. We multiply by CATASTRO_MARKET_FACTOR to estimate
    market price.
    """
    is_catastro = df['source'].str.lower().str.contains('catastro', na=False)
    n_catastro = is_catastro.sum()

    if n_catastro == 0:
        logger.info("No catastro records found to correct")
        return df

    logger.info(
        f"Applying cadastral-to-market correction (x{CATASTRO_MARKET_FACTOR}) "
        f"to {n_catastro:,} CDMX catastro records..."
    )

    avg_before = df.loc[is_catastro, 'price_m2'].mean()

    df.loc[is_catastro, 'price_mxn_original'] = df.loc[is_catastro, 'price_mxn']
    df.loc[is_catastro, 'price_m2_original'] = df.loc[is_catastro, 'price_m2']
    df.loc[is_catastro, 'price_mxn'] *= CATASTRO_MARKET_FACTOR
    df.loc[is_catastro, 'price_m2'] *= CATASTRO_MARKET_FACTOR

    avg_after = df.loc[is_catastro, 'price_m2'].mean()
    logger.info(
        f"  Catastro avg price_m2: ${avg_before:,.0f} -> ${avg_after:,.0f} "
        f"(x{CATASTRO_MARKET_FACTOR})"
    )

    return df


def classify_property_type(title: str) -> str:
    """Classify property type from the title field.

    Categories:
    - terreno: land, lote, terreno, predio
    - casa: house, casa, residencia
    - departamento: apartment, departamento, depto, condominio
    - comercial: store, local, oficina, comercial, bodega, nave
    - otro: anything else
    """
    if not isinstance(title, str):
        return 'otro'

    t = title.lower().strip()

    # Terreno / Land
    if re.search(r'\b(terreno|lote|predio|parcela|tierra|land)\b', t):
        return 'terreno'

    # Departamento / Apartment
    if re.search(r'\b(departamento|depto|apartment|condominio|pent[h]?ouse|flat)\b', t):
        return 'departamento'

    # Casa / House
    if re.search(r'\b(casa|house|residencia|chalet|villa|bungalow)\b', t):
        return 'casa'

    # Comercial / Commercial
    if re.search(
        r'\b(local|oficina|comercial|bodega|nave|store|industrial|'
        r'consultorio|taller|hotel|plaza)\b', t
    ):
        return 'comercial'

    # Habitacional (from catastro titles like "Habitacional - ...")
    if t.startswith('habitacional'):
        if 'comercial' in t:
            return 'comercial'
        return 'casa'  # Habitacional without further detail -> residential

    # Fallback by first word (properati uses type as title)
    first_word = t.split()[0] if t.split() else ''
    if first_word == 'house':
        return 'casa'
    if first_word == 'apartment':
        return 'departamento'
    if first_word == 'store':
        return 'comercial'

    return 'otro'


def add_property_type(df: pd.DataFrame) -> pd.DataFrame:
    """Add property_type column based on title classification."""
    df['property_type'] = df['title'].apply(classify_property_type)

    counts = df['property_type'].value_counts()
    logger.info("Property type classification:")
    for ptype, count in counts.items():
        logger.info(f"  {ptype}: {count:,} ({count/len(df)*100:.1f}%)")

    return df


def clean_state_column(df: pd.DataFrame) -> pd.DataFrame:
    """Clean corrupted state entries.

    Removes patterns like:
    - "CP 12000" (postal codes leaking into state)
    - Random address fragments
    - Empty or null states
    """
    before = len(df)

    # Remove "CP XXXXX" pattern from state
    cp_pattern = r'^\s*CP\s*\d+'
    is_cp_corrupted = df['state'].str.contains(cp_pattern, na=True, regex=True)
    n_cp = is_cp_corrupted.sum()
    if n_cp > 0:
        logger.warning(f"Removing {n_cp:,} records with 'CP XXXXX' in state column")
        df = df[~is_cp_corrupted].copy()

    # Remove records where state is not in the valid set and looks like garbage
    def is_valid_state(s):
        if pd.isna(s) or not isinstance(s, str):
            return False
        s_clean = s.strip()
        if s_clean in VALID_STATES:
            return True
        # Allow partial matches (e.g. "Michoacan de Ocampo")
        for valid in VALID_STATES:
            if valid.lower() in s_clean.lower() or s_clean.lower() in valid.lower():
                return True
        return False

    invalid_state = ~df['state'].apply(is_valid_state)
    n_invalid = invalid_state.sum()
    if n_invalid > 0:
        logger.warning(
            f"Removing {n_invalid:,} records with invalid/corrupted state values"
        )
        # Log sample invalid states
        bad_states = df.loc[invalid_state, 'state'].value_counts().head(10)
        for state_val, count in bad_states.items():
            logger.warning(f"  Invalid state: '{state_val}' ({count:,} records)")
        df = df[~invalid_state].copy()

    removed = before - len(df)
    if removed > 0:
        logger.info(f"State cleaning removed {removed:,} records total")
    else:
        logger.info("No corrupted state entries found")

    return df


def remove_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """Remove obvious price outliers."""
    before = len(df)

    # Ensure price_m2 is numeric
    df['price_m2'] = pd.to_numeric(df['price_m2'], errors='coerce')

    # Remove rows with null price_m2
    null_price = df['price_m2'].isna()
    n_null = null_price.sum()
    if n_null > 0:
        logger.warning(f"Removing {n_null:,} records with null price_m2")
        df = df[~null_price].copy()

    # Apply bounds
    too_low = df['price_m2'] < MIN_PRICE_M2
    too_high = df['price_m2'] > MAX_PRICE_M2

    n_low = too_low.sum()
    n_high = too_high.sum()

    if n_low > 0:
        logger.info(f"Removing {n_low:,} records with price_m2 < ${MIN_PRICE_M2:,}")
    if n_high > 0:
        logger.info(f"Removing {n_high:,} records with price_m2 > ${MAX_PRICE_M2:,}")

    df = df[~too_low & ~too_high].copy()

    removed = before - len(df)
    logger.info(
        f"Outlier removal: {removed:,} records removed. "
        f"Remaining: {len(df):,}"
    )

    return df


def print_summary(df: pd.DataFrame):
    """Print comprehensive summary of cleaned data."""
    logger.info("=" * 70)
    logger.info("CLEANED DATA SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Total records: {len(df):,}")
    logger.info(f"Columns: {list(df.columns)}")
    logger.info(f"Price_m2 range: ${df['price_m2'].min():,.0f} - ${df['price_m2'].max():,.0f}")
    logger.info(f"Price_m2 median: ${df['price_m2'].median():,.0f}")
    logger.info(f"Price_m2 mean: ${df['price_m2'].mean():,.0f}")

    logger.info("")
    logger.info("--- Records per DATA SOURCE ---")
    source_counts = df['source'].value_counts()
    for source, count in source_counts.items():
        logger.info(f"  {source}: {count:,}")

    logger.info("")
    logger.info("--- Records per PROPERTY TYPE ---")
    type_counts = df['property_type'].value_counts()
    for ptype, count in type_counts.items():
        logger.info(f"  {ptype}: {count:,} ({count/len(df)*100:.1f}%)")

    logger.info("")
    logger.info("--- Records per YEAR ---")
    year_counts = df['year'].value_counts().sort_index()
    for year, count in year_counts.items():
        logger.info(f"  {year}: {count:,}")

    logger.info("")
    logger.info("--- Records per STATE (top 15) ---")
    state_counts = df['state'].value_counts().head(15)
    for state, count in state_counts.items():
        logger.info(f"  {state}: {count:,}")

    if len(df['state'].unique()) > 15:
        logger.info(f"  ... and {len(df['state'].unique()) - 15} more states")

    logger.info("")
    logger.info("--- AVG PRICE/M2 per PROPERTY TYPE ---")
    for ptype in df['property_type'].unique():
        avg = df.loc[df['property_type'] == ptype, 'price_m2'].mean()
        med = df.loc[df['property_type'] == ptype, 'price_m2'].median()
        logger.info(f"  {ptype}: mean=${avg:,.0f}, median=${med:,.0f}")


def main():
    """Main pipeline: load, clean, save."""
    data_dir = Path(__file__).resolve().parent.parent / 'data'

    logger.info("=" * 70)
    logger.info("TRAINING DATA CLEANING PIPELINE")
    logger.info(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 70)

    # 1. Load data
    csv_path = find_latest_training_csv(data_dir)
    df = load_data(csv_path)
    initial_count = len(df)

    # 2. Remove synthetic records
    logger.info("")
    logger.info("--- STEP 1: Remove synthetic data ---")
    df = remove_synthetic(df)

    # 3. Add year feature
    logger.info("")
    logger.info("--- STEP 2: Add year feature ---")
    df = add_year_feature(df)

    # 4. Apply INPC inflation adjustment to Properati
    logger.info("")
    logger.info("--- STEP 3: INPC inflation adjustment (Properati) ---")
    df = apply_inpc_adjustment(df)

    # 5. Apply cadastral-to-market correction
    logger.info("")
    logger.info("--- STEP 4: Cadastral-to-market correction (CDMX Catastro) ---")
    df = apply_catastro_correction(df)

    # 6. Add property_type
    logger.info("")
    logger.info("--- STEP 5: Classify property types ---")
    df = add_property_type(df)

    # 7. Clean state column
    logger.info("")
    logger.info("--- STEP 6: Clean corrupted state entries ---")
    df = clean_state_column(df)

    # 8. Remove outliers
    logger.info("")
    logger.info("--- STEP 7: Remove price outliers ---")
    df = remove_outliers(df)

    # 9. Drop helper columns, keep clean output
    cols_to_drop = ['collection_date_parsed', 'inpc_factor']
    df = df.drop(columns=[c for c in cols_to_drop if c in df.columns])

    # 10. Save
    today = datetime.now().strftime('%Y%m%d')
    output_path = data_dir / f'training_clean_{today}.csv'
    df.to_csv(output_path, index=False)
    logger.success(f"Saved cleaned data to: {output_path}")
    logger.info(f"Final: {len(df):,} records (removed {initial_count - len(df):,} from original {initial_count:,})")

    # 11. Summary
    logger.info("")
    print_summary(df)

    return df


if __name__ == '__main__':
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )

    try:
        df_clean = main()
    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
