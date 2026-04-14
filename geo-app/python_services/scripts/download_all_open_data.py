"""
Download ALL free (no-auth) open data sources for the Mexican real estate ML platform.
Saves everything as CSV into the data/ directory.
"""

import os
import sys
import time
import io
from pathlib import Path
from datetime import datetime

import httpx
import pandas as pd

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

TIMEOUT = httpx.Timeout(60.0, connect=30.0)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) GeoApp-DataPipeline/1.0"
}

TODAY = datetime.now().strftime("%Y%m%d")
results: list[dict] = []


def log(msg: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def save_csv(df: pd.DataFrame, filename: str) -> Path:
    path = DATA_DIR / filename
    df.to_csv(path, index=False, encoding="utf-8-sig")
    return path


def record(filename: str, path: Path | None, rows: int = 0, status: str = "OK"):
    size = path.stat().st_size if path and path.exists() else 0
    results.append({
        "file": filename,
        "rows": rows,
        "size_kb": round(size / 1024, 1),
        "status": status,
    })


# ---------------------------------------------------------------------------
# 1. SNIIV API (JSON -> CSV)
# ---------------------------------------------------------------------------
SNIIV_SOURCES = {
    "sniiv_financiamiento": (
        "https://sniiv.sedatu.gob.mx/api/CuboAPI/GetFinanciamiento/"
        "2015,2016,2017,2018,2019,2020,2021,2022,2023,2024,2025/0/0/"
        "anio,estado,municipio,valor_vivienda,acciones,monto"
    ),
    "sniiv_infonavit": (
        "https://sniiv.sedatu.gob.mx/api/CuboAPI/GetINFONAVIT/"
        "2015,2016,2017,2018,2019,2020,2021,2022,2023,2024,2025/0/0/"
        "anio,estado,acciones,monto"
    ),
    "sniiv_inventario": (
        "https://sniiv.sedatu.gob.mx/api/CuboAPI/GetInventario/"
        "2022,2/0/0/estado,segmento,tipo_vivienda"
    ),
    "sniiv_registro": (
        "https://sniiv.sedatu.gob.mx/api/CuboAPI/GetRegistro/"
        "2015,2016,2017,2018,2019,2020,2021,2022,2023,2024,2025/0/0/"
        "anio,estado,municipio,tipo_vivienda,segmento"
    ),
}


def download_sniiv():
    log("=== SNIIV API ===")
    with httpx.Client(timeout=TIMEOUT, headers=HEADERS, verify=False) as client:
        for name, url in SNIIV_SOURCES.items():
            fname = f"{name}_{TODAY}.csv"
            try:
                log(f"  Downloading {name}...")
                resp = client.get(url)
                resp.raise_for_status()
                data = resp.json()
                if isinstance(data, list):
                    df = pd.DataFrame(data)
                elif isinstance(data, dict) and "data" in data:
                    df = pd.DataFrame(data["data"])
                elif isinstance(data, dict):
                    # Try the first list-valued key
                    for v in data.values():
                        if isinstance(v, list):
                            df = pd.DataFrame(v)
                            break
                    else:
                        df = pd.DataFrame([data])
                else:
                    df = pd.DataFrame()
                path = save_csv(df, fname)
                log(f"    -> {fname}: {len(df)} rows, {path.stat().st_size/1024:.1f} KB")
                record(fname, path, len(df))
            except Exception as e:
                log(f"    FAILED {name}: {e}")
                record(fname, None, 0, f"FAILED: {e}")


# ---------------------------------------------------------------------------
# 2. CONAVI Subsidios (direct CSV)
# ---------------------------------------------------------------------------
CONAVI_URLS = {
    "conavi_subsidios_2024": "https://repodatos.atdt.gob.mx/api_update/conavi/reporte_general_subsidios/CONAVI_1_Subsidios_2024.csv",
    "conavi_subsidios_2023": "https://repodatos.atdt.gob.mx/api_update/conavi/reporte_general_subsidios/Subsidios_2023.csv",
    "conavi_subsidios_2022": "https://repodatos.atdt.gob.mx/api_update/conavi/reporte_general_subsidios/Subsidios_2022.csv",
    "conavi_subsidios_2021": "https://repodatos.atdt.gob.mx/api_update/conavi/reporte_general_subsidios/Subsidios_2021.csv",
    "conavi_subsidios_2020": "https://repodatos.atdt.gob.mx/api_update/conavi/reporte_general_subsidios/Subsidios_2020.csv",
    "conavi_subsidios_2019": "https://repodatos.atdt.gob.mx/api_update/conavi/reporte_general_subsidios/Subsidios_2019.csv",
}


def download_conavi():
    log("=== CONAVI Subsidios ===")
    with httpx.Client(timeout=TIMEOUT, headers=HEADERS, verify=False, follow_redirects=True) as client:
        for name, url in CONAVI_URLS.items():
            fname = f"{name}.csv"
            try:
                log(f"  Downloading {name}...")
                resp = client.get(url)
                resp.raise_for_status()
                # Try multiple encodings
                for enc in ["utf-8", "latin-1", "cp1252"]:
                    try:
                        df = pd.read_csv(io.BytesIO(resp.content), encoding=enc, on_bad_lines="skip")
                        break
                    except Exception:
                        continue
                else:
                    df = pd.DataFrame()
                path = save_csv(df, fname)
                log(f"    -> {fname}: {len(df)} rows, {path.stat().st_size/1024:.1f} KB")
                record(fname, path, len(df))
            except Exception as e:
                log(f"    FAILED {name}: {e}")
                record(fname, None, 0, f"FAILED: {e}")


# ---------------------------------------------------------------------------
# 3. SHF Housing Price Index (XLSX -> CSV)
# ---------------------------------------------------------------------------
def download_shf():
    log("=== SHF Housing Price Index ===")
    url = "https://www.gob.mx/cms/uploads/attachment/file/1055836/Indice_SHF_datos_abiertos_4_trim_2025.xlsx"
    fname = f"shf_housing_price_index_{TODAY}.csv"
    try:
        log("  Downloading SHF XLSX...")
        with httpx.Client(timeout=TIMEOUT, headers=HEADERS, verify=False, follow_redirects=True) as client:
            resp = client.get(url)
            resp.raise_for_status()
        # Read all sheets and concatenate
        xlsx = pd.ExcelFile(io.BytesIO(resp.content), engine="openpyxl")
        log(f"    Sheets found: {xlsx.sheet_names}")
        frames = []
        for sheet in xlsx.sheet_names:
            df_sheet = xlsx.parse(sheet)
            df_sheet["_sheet"] = sheet
            frames.append(df_sheet)
        df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
        path = save_csv(df, fname)
        log(f"    -> {fname}: {len(df)} rows, {path.stat().st_size/1024:.1f} KB")
        record(fname, path, len(df))
    except Exception as e:
        log(f"    FAILED SHF: {e}")
        record(fname, None, 0, f"FAILED: {e}")


# ---------------------------------------------------------------------------
# 4. FRED Housing Index (CSV)
# ---------------------------------------------------------------------------
FRED_URLS = {
    "fred_mexico_real_house_price": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=QMXR628BIS",
    "fred_mexico_nominal_house_price": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=QMXN628BIS",
}


def download_fred():
    log("=== FRED Housing Index ===")
    with httpx.Client(timeout=TIMEOUT, headers=HEADERS, verify=False, follow_redirects=True) as client:
        for name, url in FRED_URLS.items():
            fname = f"{name}_{TODAY}.csv"
            try:
                log(f"  Downloading {name}...")
                resp = client.get(url)
                resp.raise_for_status()
                df = pd.read_csv(io.StringIO(resp.text))
                path = save_csv(df, fname)
                log(f"    -> {fname}: {len(df)} rows, {path.stat().st_size/1024:.1f} KB")
                record(fname, path, len(df))
            except Exception as e:
                log(f"    FAILED {name}: {e}")
                record(fname, None, 0, f"FAILED: {e}")


# ---------------------------------------------------------------------------
# 5. CONEVAL Rezago Social (CSV)
# ---------------------------------------------------------------------------
def download_coneval():
    log("=== CONEVAL Rezago Social ===")
    url = "https://www.coneval.org.mx/Informes/Pobreza/Datos_abiertos/Rezago-social-2000-2005-2010_mun_DA.csv"
    fname = f"coneval_rezago_social_{TODAY}.csv"
    try:
        log("  Downloading CONEVAL...")
        with httpx.Client(timeout=TIMEOUT, headers=HEADERS, verify=False, follow_redirects=True) as client:
            resp = client.get(url)
            resp.raise_for_status()
        for enc in ["utf-8", "latin-1", "cp1252"]:
            try:
                df = pd.read_csv(io.BytesIO(resp.content), encoding=enc, on_bad_lines="skip")
                break
            except Exception:
                continue
        else:
            df = pd.DataFrame()
        path = save_csv(df, fname)
        log(f"    -> {fname}: {len(df)} rows, {path.stat().st_size/1024:.1f} KB")
        record(fname, path, len(df))
    except Exception as e:
        log(f"    FAILED CONEVAL: {e}")
        record(fname, None, 0, f"FAILED: {e}")


# ---------------------------------------------------------------------------
# 6. CNSF Credit Insurance (CSV)
# ---------------------------------------------------------------------------
CNSF_URLS = {
    "cnsf_credito_vivienda_asegurado": (
        "https://repodatos.atdt.gob.mx/api_update/csnf/"
        "informacion_estadistica_credito_vivienda_sector_asegurador/"
        "51_Informacion_estadistica_Credito_Vivienda_Datos_Credito_Asegurado_ok.csv"
    ),
    "cnsf_credito_vivienda_clientes": (
        "https://repodatos.atdt.gob.mx/api_update/csnf/"
        "informacion_estadistica_credito_vivienda_sector_asegurador/"
        "52_Informacion_estadistica_Credito_Vivienda_Clientes_ok.csv"
    ),
}


def download_cnsf():
    log("=== CNSF Credit Insurance ===")
    with httpx.Client(timeout=TIMEOUT, headers=HEADERS, verify=False, follow_redirects=True) as client:
        for name, url in CNSF_URLS.items():
            fname = f"{name}_{TODAY}.csv"
            try:
                log(f"  Downloading {name}...")
                resp = client.get(url)
                resp.raise_for_status()
                for enc in ["utf-8", "latin-1", "cp1252"]:
                    try:
                        df = pd.read_csv(io.BytesIO(resp.content), encoding=enc, on_bad_lines="skip")
                        break
                    except Exception:
                        continue
                else:
                    df = pd.DataFrame()
                path = save_csv(df, fname)
                log(f"    -> {fname}: {len(df)} rows, {path.stat().st_size/1024:.1f} KB")
                record(fname, path, len(df))
            except Exception as e:
                log(f"    FAILED {name}: {e}")
                record(fname, None, 0, f"FAILED: {e}")


# ---------------------------------------------------------------------------
# 7. BIS Global House Prices (CSV from GitHub)
# ---------------------------------------------------------------------------
def download_bis():
    log("=== BIS Global House Prices ===")
    url = "https://raw.githubusercontent.com/datasets/house-prices-global/main/data/real_index.csv"
    fname = f"bis_global_house_prices_{TODAY}.csv"
    try:
        log("  Downloading BIS from GitHub...")
        with httpx.Client(timeout=TIMEOUT, headers=HEADERS, verify=False, follow_redirects=True) as client:
            resp = client.get(url)
            resp.raise_for_status()
        df = pd.read_csv(io.StringIO(resp.text))
        # Filter to Mexico only for a focused dataset, but keep original too
        path_full = save_csv(df, fname)
        log(f"    -> {fname}: {len(df)} rows, {path_full.stat().st_size/1024:.1f} KB")
        record(fname, path_full, len(df))

        # Also save Mexico-only subset — column name may vary
        country_col = next((c for c in df.columns if c.lower() == "country"), None)
        mx_df = df[df[country_col].str.contains("Mexico", case=False, na=False)] if country_col else pd.DataFrame()
        if not mx_df.empty:
            fname_mx = f"bis_house_prices_mexico_{TODAY}.csv"
            path_mx = save_csv(mx_df, fname_mx)
            log(f"    -> {fname_mx}: {len(mx_df)} rows (Mexico only)")
            record(fname_mx, path_mx, len(mx_df))
    except Exception as e:
        log(f"    FAILED BIS: {e}")
        record(fname, None, 0, f"FAILED: {e}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    start = time.time()
    log(f"Starting open data download pipeline — {TODAY}")
    log(f"Data directory: {DATA_DIR}\n")

    download_sniiv()
    download_conavi()
    download_shf()
    download_fred()
    download_coneval()
    download_cnsf()
    download_bis()

    elapsed = time.time() - start
    log(f"\n{'='*70}")
    log(f"DOWNLOAD SUMMARY  (elapsed: {elapsed:.1f}s)")
    log(f"{'='*70}")
    log(f"{'File':<55} {'Rows':>8} {'Size KB':>10} {'Status':>10}")
    log(f"{'-'*55} {'-'*8} {'-'*10} {'-'*10}")

    ok_count = 0
    fail_count = 0
    total_rows = 0
    total_kb = 0.0
    for r in results:
        status_short = "OK" if r["status"] == "OK" else "FAIL"
        log(f"{r['file']:<55} {r['rows']:>8} {r['size_kb']:>10.1f} {status_short:>10}")
        if r["status"] == "OK":
            ok_count += 1
            total_rows += r["rows"]
            total_kb += r["size_kb"]
        else:
            fail_count += 1

    log(f"{'-'*55} {'-'*8} {'-'*10} {'-'*10}")
    log(f"{'TOTAL':<55} {total_rows:>8} {total_kb:>10.1f}")
    log(f"\nSuccessful: {ok_count}  |  Failed: {fail_count}  |  Total files: {len(results)}")


if __name__ == "__main__":
    main()
