"""
Process downloaded Mexican government open data into standardized CSV format.
Sources:
  1. CDMX Cadastral data (16 boroughs) - datos.cdmx.gob.mx
  2. BIS Property Price Index (Mexico) - bis.org
  3. CDMX Viviendas Unifamiliares (earthquake reconstruction) - datos.cdmx.gob.mx
"""
import pandas as pd
import os
import glob
from datetime import datetime

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
TODAY = datetime.now().strftime("%Y-%m-%d")
COLLECTION_DATE = TODAY

STANDARD_COLUMNS = [
    "title", "price_mxn", "area_m2", "price_m2",
    "address", "city", "state", "lat", "lon",
    "collection_date", "source", "source_url"
]


def process_cdmx_catastro():
    """Process all 16 CDMX cadastral CSV files into one standardized file."""
    pattern = os.path.join(DATA_DIR, "raw_cdmx_catastro_*.csv")
    files = glob.glob(pattern)
    print(f"\n=== CDMX Catastro: Found {len(files)} files ===")

    all_dfs = []
    for f in sorted(files):
        fname = os.path.basename(f)
        print(f"  Processing {fname}...", end=" ")
        try:
            df = pd.read_csv(f, low_memory=False)
            print(f"{len(df)} rows")
            all_dfs.append(df)
        except Exception as e:
            print(f"ERROR: {e}")

    if not all_dfs:
        print("No catastro data loaded!")
        return None

    raw = pd.concat(all_dfs, ignore_index=True)
    print(f"  Total raw rows: {len(raw)}")
    print(f"  Columns: {list(raw.columns)}")

    # Map to standard format
    # Source columns: codigo_postal, superficie_terreno, superficie_construccion,
    # uso_construccion, clave_rango_nivel, anio_construccion, instalaciones_especiales,
    # valor_unitario_suelo, valor_suelo, clave_valor_unitario_suelo, subsidio,
    # latitud, longitud, colonia, alcaldia

    out = pd.DataFrame()
    out["title"] = (
        raw["uso_construccion"].fillna("Propiedad") + " - " +
        raw["colonia"].fillna("") + ", " +
        raw["alcaldia"].fillna("")
    )
    # valor_suelo is the total land value (valor_unitario_suelo * superficie_terreno)
    out["price_mxn"] = pd.to_numeric(raw["valor_suelo"], errors="coerce")
    out["area_m2"] = pd.to_numeric(raw["superficie_terreno"], errors="coerce")
    out["price_m2"] = pd.to_numeric(raw["valor_unitario_suelo"], errors="coerce")
    out["address"] = raw["colonia"].fillna("") + ", CP " + raw["codigo_postal"].astype(str)
    out["city"] = "Ciudad de Mexico"
    out["state"] = "Ciudad de Mexico"
    out["lat"] = pd.to_numeric(raw["latitud"], errors="coerce")
    out["lon"] = pd.to_numeric(raw["longitud"], errors="coerce")
    out["collection_date"] = COLLECTION_DATE
    out["source"] = "CDMX Catastro - " + raw["alcaldia"].fillna("CDMX")
    out["source_url"] = "https://datos.cdmx.gob.mx/dataset/informacion-catastral-de-la-ciudad-de-mexico"

    # Filter: keep only rows with valid price and area
    mask = (out["price_mxn"] > 0) & (out["area_m2"] > 0) & out["lat"].notna() & out["lon"].notna()
    out = out[mask].copy()
    print(f"  After filtering: {len(out)} rows")

    # Sample to keep file manageable (take a representative sample per alcaldia)
    # For the full dataset, we'll save a separate file
    out_full = out[STANDARD_COLUMNS]

    # Save full dataset
    full_path = os.path.join(DATA_DIR, f"gobierno_cdmx_catastro_full_{TODAY}.csv")
    out_full.to_csv(full_path, index=False)
    print(f"  Saved full: {full_path} ({len(out_full)} rows)")

    # Save a manageable sample (stratified by alcaldia, ~5000 per borough)
    sampled = out.groupby("source", group_keys=False).apply(
        lambda x: x.sample(n=min(5000, len(x)), random_state=42)
    )
    sample_path = os.path.join(DATA_DIR, f"gobierno_cdmx_catastro_{TODAY}.csv")
    sampled[STANDARD_COLUMNS].to_csv(sample_path, index=False)
    print(f"  Saved sample: {sample_path} ({len(sampled)} rows)")

    return out_full


def process_bis_property_prices():
    """Process BIS property price index Excel for Mexico data."""
    xlsx_path = os.path.join(DATA_DIR, "raw_bis_property_prices.xlsx")
    if not os.path.exists(xlsx_path):
        print("\n=== BIS Property Prices: File not found, skipping ===")
        return None

    print("\n=== BIS Property Prices ===")
    try:
        # Read the Excel file - BIS format has metadata rows at top
        xl = pd.ExcelFile(xlsx_path)
        print(f"  Sheets: {xl.sheet_names}")

        # Try to find Mexico data
        for sheet in xl.sheet_names:
            df = pd.read_excel(xlsx_path, sheet_name=sheet, header=None, nrows=10)
            # Check if this sheet has data
            flat = df.astype(str).values.flatten()
            if any("Mexico" in str(v) or "MX" in str(v) for v in flat):
                print(f"  Found Mexico data in sheet: {sheet}")
                # Read the full sheet
                df_full = pd.read_excel(xlsx_path, sheet_name=sheet, header=None)
                print(f"  Shape: {df_full.shape}")

                # Find Mexico rows/columns
                for i in range(min(20, len(df_full))):
                    row_str = " | ".join(str(v) for v in df_full.iloc[i].values[:10])
                    if "Mexico" in row_str or "MX" in row_str:
                        print(f"  Row {i}: {row_str}")

                # Extract Mexico property price index data
                # BIS format typically has dates as columns, countries as rows
                # or vice versa. Let's handle both.
                mexico_data = []
                for idx, row in df_full.iterrows():
                    row_vals = [str(v) for v in row.values]
                    if any("Mexico" in v or "MX:" in v for v in row_vals):
                        mexico_data.append(row.values)

                if mexico_data:
                    # Try to extract date headers
                    # Usually first few rows are headers
                    header_row = None
                    for i in range(min(10, len(df_full))):
                        vals = df_full.iloc[i].values
                        date_count = sum(1 for v in vals if isinstance(v, (pd.Timestamp, datetime)))
                        if date_count > 5:
                            header_row = i
                            break

                    if header_row is not None:
                        dates = df_full.iloc[header_row].values
                        for mrow in mexico_data:
                            for j, (date, val) in enumerate(zip(dates, mrow)):
                                if isinstance(date, (pd.Timestamp, datetime)) and pd.notna(val):
                                    try:
                                        mexico_data.append({
                                            "date": date,
                                            "value": float(val)
                                        })
                                    except (ValueError, TypeError):
                                        pass

                    print(f"  Mexico data points found: {len(mexico_data)}")

                break

        # Create a simpler output - BIS index data as reference
        # Since this is an index (not property listings), format differently
        out = pd.DataFrame({
            "title": ["Mexico Property Price Index (BIS)"],
            "price_mxn": [None],
            "area_m2": [None],
            "price_m2": [None],
            "address": ["National"],
            "city": ["National"],
            "state": ["National"],
            "lat": [23.6345],  # Center of Mexico
            "lon": [-102.5528],
            "collection_date": [COLLECTION_DATE],
            "source": ["BIS - Bank for International Settlements"],
            "source_url": ["https://www.bis.org/statistics/pp/pp_detailed.xlsx"]
        })

        path = os.path.join(DATA_DIR, f"gobierno_bis_property_index_{TODAY}.csv")
        out.to_csv(path, index=False)
        print(f"  Saved: {path}")
        return out

    except Exception as e:
        print(f"  Error processing BIS data: {e}")
        return None


def process_viviendas_unifamiliares():
    """Process earthquake reconstruction housing data."""
    csv_path = os.path.join(DATA_DIR, "raw_cdmx_viviendas_unifamiliares.csv")
    if not os.path.exists(csv_path):
        print("\n=== Viviendas Unifamiliares: File not found, skipping ===")
        return None

    print("\n=== CDMX Viviendas Unifamiliares (Reconstruccion) ===")
    try:
        df = pd.read_csv(csv_path, low_memory=False)
        print(f"  Raw rows: {len(df)}")
        print(f"  Columns: {list(df.columns)}")

        # This dataset has location info for houses, though no prices
        # Still useful for address/location data
        out = pd.DataFrame()
        out["title"] = "Vivienda Unifamiliar - " + df["tipo_intervencion"].fillna("Reconstruccion")
        out["price_mxn"] = None  # No price data in this source
        out["area_m2"] = None
        out["price_m2"] = None
        out["address"] = (
            df["calle_inmueble"].fillna("") + " " +
            df["exterior_inmueble"].fillna("") + ", " +
            df["colonia_inmueble"].fillna("")
        )
        out["city"] = "Ciudad de Mexico"
        out["state"] = "Ciudad de Mexico"
        out["lat"] = pd.to_numeric(df["latitud"], errors="coerce")
        out["lon"] = pd.to_numeric(df["longitud"], errors="coerce")
        out["collection_date"] = COLLECTION_DATE
        out["source"] = "CDMX Reconstruccion - " + df["alcaldia_inmueble"].fillna("CDMX")
        out["source_url"] = "https://datos.cdmx.gob.mx/dataset/reconstruccion-viviendas-unifamiliares"

        mask = out["lat"].notna() & out["lon"].notna()
        out = out[mask][STANDARD_COLUMNS]
        print(f"  After filtering: {len(out)} rows")

        path = os.path.join(DATA_DIR, f"gobierno_cdmx_viviendas_{TODAY}.csv")
        out.to_csv(path, index=False)
        print(f"  Saved: {path}")
        return out

    except Exception as e:
        print(f"  Error: {e}")
        return None


def print_summary():
    """Print summary of all generated files."""
    print("\n" + "=" * 60)
    print("SUMMARY OF GENERATED FILES")
    print("=" * 60)
    pattern = os.path.join(DATA_DIR, "gobierno_*.csv")
    files = sorted(glob.glob(pattern))
    total_rows = 0
    for f in files:
        try:
            n = sum(1 for _ in open(f, encoding="utf-8")) - 1  # subtract header
            size_mb = os.path.getsize(f) / (1024 * 1024)
            print(f"  {os.path.basename(f)}: {n:,} rows ({size_mb:.1f} MB)")
            total_rows += n
        except Exception as e:
            print(f"  {os.path.basename(f)}: ERROR - {e}")

    print(f"\n  TOTAL: {total_rows:,} rows across {len(files)} files")
    print(f"  Output directory: {DATA_DIR}")

    # Print column format
    print(f"\n  Standard columns: {STANDARD_COLUMNS}")


if __name__ == "__main__":
    print(f"Processing government data - {TODAY}")
    print(f"Data directory: {DATA_DIR}")

    process_cdmx_catastro()
    process_bis_property_prices()
    process_viviendas_unifamiliares()
    print_summary()
