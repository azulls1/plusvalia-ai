"""
Download and process Properati Mexico real estate dataset.
Source: properati.com (public dataset)
"""
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from loguru import logger
import requests
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# Known Properati dataset URLs (ordered by likelihood of working)
PROPERATI_URLS = [
    # datamx.io (Codeando Mexico) - confirmed accessible, large CSV (~200k records)
    "https://datamx.io/dataset/d99ba59c-a96c-420e-8d47-71ecdadb0d80/resource/b175bf00-8214-4293-95f4-9f8aa4ee63b3/download/properatimx20160901propertiessell.csv",
    # Alternative domain for same dataset
    "https://datamx.codeandomexico.org/dataset/d99ba59c-a96c-420e-8d47-71ecdadb0d80/resource/b175bf00-8214-4293-95f4-9f8aa4ee63b3/download/properatimx20160901propertiessell.csv",
    # Fallback: original S3/GCS URLs (may be deprecated)
    "https://properati-data-mx.s3.amazonaws.com/mx_properties.csv.gz",
    "https://storage.googleapis.com/properati-data-public/mx_properties.csv.gz",
]

def _fetch_url(url: str, timeout: int = 120):
    """Fetch a URL, retrying without SSL verification if needed."""
    try:
        return requests.get(url, timeout=timeout, stream=True, verify=True)
    except requests.exceptions.SSLError:
        logger.info("SSL error, retrying without verification...")
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        try:
            return requests.get(url, timeout=timeout, stream=True, verify=False)
        except Exception as e:
            logger.warning(f"Failed even without SSL: {e}")
            return None
    except Exception as e:
        logger.warning(f"Request error: {e}")
        return None


def download_properati():
    """Try to download the Properati Mexico dataset."""
    output_path = DATA_DIR / "properati_mx_raw.csv"

    if output_path.exists():
        logger.info(f"Dataset already downloaded: {output_path}")
        return output_path

    for url in PROPERATI_URLS:
        logger.info(f"Trying: {url}")
        try:
            response = _fetch_url(url)
            if response is None:
                continue
            if response.status_code != 200:
                logger.warning(f"HTTP {response.status_code} from {url}")
                continue

            is_gzip = url.endswith('.gz')
            if is_gzip:
                gz_path = DATA_DIR / "properati_mx.csv.gz"
                with open(gz_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                df = pd.read_csv(gz_path, compression='gzip')
            else:
                tmp_path = DATA_DIR / "properati_mx_download.csv"
                with open(tmp_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                df = pd.read_csv(tmp_path, low_memory=False)

            df.to_csv(output_path, index=False)
            logger.info(f"Downloaded {len(df)} records to {output_path}")
            logger.info(f"Source URL: {url}")
            return output_path
        except Exception as e:
            logger.warning(f"Failed: {url} - {e}")

    logger.error("Could not download from any URL. Creating from alternative sources...")
    return None


def process_for_model(input_path: Path = None) -> Path:
    """Process raw Properati data into model-ready format."""

    if input_path and input_path.exists():
        logger.info(f"Processing {input_path}")
        df = pd.read_csv(input_path)
    else:
        logger.info("No raw file found. Generating from web scraping...")
        return None

    logger.info(f"Raw records: {len(df)}")
    logger.info(f"Columns: {list(df.columns)}")

    # --- Parse location from place_with_parent_names ---
    # Format: |Mexico|State|Municipality|City|Neighborhood|
    def parse_place(val):
        if pd.isna(val):
            return 'Unknown', 'Unknown'
        parts = [p for p in str(val).split('|') if p]
        state = parts[1] if len(parts) > 1 else 'Unknown'
        # City is typically index 2 (municipality) or 3
        city = parts[3] if len(parts) > 3 else (parts[2] if len(parts) > 2 else state)
        return state, city

    place_parsed = df['place_with_parent_names'].apply(parse_place)
    df['_state'] = place_parsed.apply(lambda x: x[0])
    df['_city'] = place_parsed.apply(lambda x: x[1])

    # --- Normalize prices to MXN ---
    # Dataset has price_aprox_local_currency (MXN) for all records
    if 'price_aprox_local_currency' in df.columns:
        df['price_mxn'] = df['price_aprox_local_currency']
    else:
        # Fallback: convert USD prices manually (approx rate)
        df['price_mxn'] = np.where(
            df['currency'] == 'USD',
            df['price'] * 18.0,  # approximate USD->MXN
            df['price']
        )

    # Filter: sale only, with coordinates and valid prices
    if 'operation' in df.columns:
        df = df[df['operation'] == 'sell']

    # Drop rows without essential data
    df = df.dropna(subset=['price_mxn', 'lat', 'lon'])

    # Filter valid coordinates (Mexico bounding box)
    df = df[(df['lat'] >= 14) & (df['lat'] <= 33)]
    df = df[(df['lon'] >= -118) & (df['lon'] <= -86)]

    # Filter valid MXN prices (100k - 500M MXN)
    df = df[(df['price_mxn'] > 100000) & (df['price_mxn'] < 500000000)]

    # Calculate area and price per m2
    area_col = 'surface_total_in_m2' if 'surface_total_in_m2' in df.columns else 'surface_total'
    covered_col = 'surface_covered_in_m2' if 'surface_covered_in_m2' in df.columns else 'surface_covered'

    if area_col in df.columns:
        df['area_m2'] = df[area_col]
        if covered_col in df.columns:
            df['area_m2'] = df['area_m2'].fillna(df[covered_col])
        df['area_m2'] = df['area_m2'].clip(10, 50000)
        df['price_m2'] = df['price_mxn'] / df['area_m2']
        # Filter extreme price_m2
        df = df[(df['price_m2'] > 500) & (df['price_m2'] < 200000)]
    else:
        df['area_m2'] = np.nan
        df['price_m2'] = np.nan

    # Build result DataFrame
    result = pd.DataFrame()
    result['title'] = df.get('property_type', 'Terreno').values
    result['price_mxn'] = df['price_mxn'].values
    result['area_m2'] = df['area_m2'].values
    result['price_m2'] = df['price_m2'].values
    result['address'] = df.get('title', '').values
    result['city'] = df['_city'].values
    result['state'] = df['_state'].values
    result['lat'] = df['lat'].values
    result['lon'] = df['lon'].values
    result['rooms'] = df.get('rooms', np.nan).values
    result['property_type'] = df.get('property_type', 'unknown').values
    result['collection_date'] = df.get('created_on', datetime.now().strftime('%Y-%m-%d')).values
    result['source'] = 'properati'
    result['source_url'] = 'https://properati.com.mx'

    output_path = DATA_DIR / f"properati_processed_{datetime.now().strftime('%Y%m%d')}.csv"
    result.to_csv(output_path, index=False)

    logger.info(f"Processed {len(result)} records → {output_path}")
    logger.info(f"Cities: {result['city'].nunique()}")
    logger.info(f"States: {result['state'].nunique()}")
    logger.info(f"Price range: ${result['price_m2'].min():.0f} - ${result['price_m2'].max():.0f}/m²")

    return output_path


if __name__ == "__main__":
    raw_path = download_properati()
    if raw_path:
        process_for_model(raw_path)
    else:
        logger.info("Manual download required. Visit: https://datamx.io/dataset/propiedades-venta-renta-properati")
