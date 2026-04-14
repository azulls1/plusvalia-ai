"""
Scraper de datos CONAVI/RUV (Registro Único de Vivienda).

Fuente: datos.gob.mx datasets de CONAVI, portal SNIIV
         https://sniiv.conavi.gob.mx/
         https://datos.gob.mx/busca/organization/conavi

Datos: registros de vivienda nueva con precios, ubicación, tipo, desarrollador.
El RUV contiene información de todas las viviendas registradas ante CONAVI
para obtener subsidios o créditos de organismos nacionales (INFONAVIT, FOVISSSTE).

El scraper:
  1. Descarga datos de vivienda registrada desde datos.gob.mx
  2. Busca datasets CONAVI en el portal CKAN de datos.gob.mx
  3. Procesa y normaliza los registros
  4. Calcula features de mercado (precio promedio obra nueva, densidad)
  5. Guarda en CSV y opcionalmente en Supabase
"""

import asyncio
import io
import json
import math
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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

from config import DATA_DIR, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

try:
    from supabase import create_client
    HAS_SUPABASE = True
except ImportError:
    HAS_SUPABASE = False
    logger.warning("supabase-py no instalado, se omite upsert a Supabase")

try:
    from tenacity import retry, stop_after_attempt, wait_exponential
    HAS_TENACITY = True
except ImportError:
    HAS_TENACITY = False

# ── Paths ────────────────────────────────────────────────────────────────────

OUTPUT_FILE = DATA_DIR / "conavi_ruv_vivienda.csv"
CITIES_FILE = DATA_DIR / "cities_mexico_32_states.json"
SUPABASE_TABLE = "iainmobiliaria_conavi_ruv"

# ── URLs de datos abiertos CONAVI ────────────────────────────────────────────

DATOS_GOB_CKAN = "https://datos.gob.mx/busca/api/3/action"

# URLs conocidas de datasets CONAVI en datos.gob.mx
KNOWN_CONAVI_URLS = [
    # Subsidios federales para vivienda
    "https://datos.gob.mx/busca/dataset/subsidios-federales-para-vivienda",
    # Registro de vivienda
    "https://datos.gob.mx/busca/dataset/registro-unico-de-vivienda",
]

# Datasets SNIIV con datos de registro de vivienda
SNIIV_BASE = "https://sniiv.conavi.gob.mx"
SNIIV_API_URLS = [
    # Registro — viviendas registradas por estado y municipio
    f"{SNIIV_BASE}/Reports/Excel/Registro",
    f"{SNIIV_BASE}/Reports/Excel/Financiamiento",
]

# ── Normalización de estados ────────────────────────────────────────────────

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

# Coordenadas de municipios para geocodificación
MUNICIPALITY_COORDS: Dict[str, Tuple[float, float]] = {
    "Guadalajara": (20.6597, -103.3496),
    "Zapopan": (20.7167, -103.4000),
    "Tlaquepaque": (20.6400, -103.3100),
    "Tonalá": (20.6250, -103.2333),
    "Tlajomulco de Zúñiga": (20.4740, -103.4410),
    "El Salto": (20.5196, -103.2218),
    "Monterrey": (25.6866, -100.3161),
    "Ciudad de México": (19.4326, -99.1332),
    "Puebla": (19.0414, -98.2063),
    "Querétaro": (20.5888, -100.3899),
    "León": (21.1250, -101.6860),
    "Tijuana": (32.5149, -117.0382),
    "Cancún": (21.1619, -86.8515),
    "Mérida": (20.9674, -89.5926),
    "Toluca": (19.2826, -99.6557),
    "Aguascalientes": (21.8818, -102.2916),
    "Hermosillo": (29.0729, -110.9559),
    "San Luis Potosí": (22.1565, -100.9855),
    "Morelia": (19.7060, -101.1950),
    "Chihuahua": (28.6353, -106.0889),
    "Saltillo": (25.4232, -100.9925),
    "Culiacán": (24.8049, -107.3940),
    "Villahermosa": (17.9892, -92.9475),
    "Veracruz": (19.2026, -96.1533),
    "Acapulco": (16.8531, -99.8237),
    "Oaxaca de Juárez": (17.0732, -96.7266),
    "Tuxtla Gutiérrez": (16.7528, -93.1152),
    "Durango": (24.0277, -104.6532),
    "Cuernavaca": (18.9186, -99.2342),
    "Pachuca": (20.1011, -98.7591),
}


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula distancia haversine en km."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class CONAVIRUVScraper:
    """
    Descarga y procesa datos del Registro Único de Vivienda (RUV)
    desde CONAVI/datos.gob.mx/SNIIV.
    """

    def __init__(self):
        self.city_coords: Dict[str, Tuple[float, float]] = {}
        self._load_cities_lookup()

    def _load_cities_lookup(self):
        """Carga coordenadas de ciudades desde el archivo JSON."""
        # Primero cargar coordenadas hardcoded
        self.city_coords.update(MUNICIPALITY_COORDS)

        if not CITIES_FILE.exists():
            logger.warning(f"Archivo de ciudades no encontrado: {CITIES_FILE}")
            return

        try:
            with open(CITIES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            for estado in data.get("estados", []):
                for ciudad in estado.get("ciudades", []):
                    city_name = ciudad["city"]
                    if "lat" in ciudad and "lon" in ciudad:
                        self.city_coords[city_name] = (ciudad["lat"], ciudad["lon"])
                        self.city_coords[city_name.upper()] = (ciudad["lat"], ciudad["lon"])

            logger.info(f"Cargadas {len(self.city_coords)} coordenadas de ciudades")
        except Exception as exc:
            logger.warning(f"Error cargando ciudades: {exc}")

    def _geocode(self, municipality: str) -> Tuple[Optional[float], Optional[float]]:
        """Busca coordenadas para un municipio."""
        coords = self.city_coords.get(municipality)
        if coords:
            return coords
        coords = self.city_coords.get(municipality.upper())
        if coords:
            return coords
        # Búsqueda parcial
        muni_upper = municipality.upper()
        for key, val in self.city_coords.items():
            if isinstance(key, str) and muni_upper in key.upper():
                return val
        return (None, None)

    def _normalize_state(self, raw: str) -> str:
        """Normaliza nombre de estado."""
        if not raw or not isinstance(raw, str):
            return ""
        cleaned = raw.strip().upper()
        return STATE_ALIASES.get(cleaned, raw.strip().title())

    # ── Descarga de datos ────────────────────────────────────────────────

    async def _download_file(
        self, client: httpx.AsyncClient, url: str
    ) -> Optional[bytes]:
        """Descarga un archivo con manejo de errores."""
        try:
            logger.info(f"  Descargando: {url}")
            resp = await client.get(url, timeout=120, follow_redirects=True)
            if resp.status_code == 200:
                size = len(resp.content)
                logger.info(f"  Descargados {size:,} bytes")
                return resp.content
            else:
                logger.warning(f"  HTTP {resp.status_code} para {url}")
        except (httpx.TimeoutException, httpx.ConnectError, OSError) as exc:
            logger.warning(f"  Error de descarga: {exc}")
        return None

    async def _discover_conavi_datasets(
        self, client: httpx.AsyncClient
    ) -> List[str]:
        """Descubre datasets CONAVI en el portal datos.gob.mx vía CKAN API."""
        urls = []
        try:
            # Buscar datasets de CONAVI
            for query in ["conavi vivienda", "registro vivienda", "ruv vivienda"]:
                resp = await client.get(
                    f"{DATOS_GOB_CKAN}/package_search",
                    params={"q": query, "rows": 10},
                    timeout=30,
                )
                if resp.status_code != 200:
                    continue

                data = resp.json()
                results = data.get("result", {}).get("results", [])

                for dataset in results:
                    for resource in dataset.get("resources", []):
                        fmt = (resource.get("format") or "").lower()
                        if fmt in ("csv", "xlsx", "xls"):
                            download_url = resource.get("url", "")
                            if download_url and download_url not in urls:
                                urls.append(download_url)
                                logger.info(
                                    f"  Descubierto: {resource.get('name', 'sin nombre')} "
                                    f"({fmt}) -> {download_url}"
                                )

                await asyncio.sleep(1)

        except Exception as exc:
            logger.warning(f"Error en descubrimiento CKAN: {exc}")

        return urls

    # ── Procesamiento de datos ───────────────────────────────────────────

    def _parse_content(self, content: bytes, url: str) -> pd.DataFrame:
        """Intenta parsear contenido como CSV o XLSX."""
        # Intentar como CSV
        for encoding in ["utf-8", "latin-1", "cp1252", "utf-8-sig"]:
            try:
                df = pd.read_csv(
                    io.BytesIO(content),
                    encoding=encoding,
                    low_memory=False,
                    on_bad_lines="skip",
                )
                if len(df) > 0 and len(df.columns) > 2:
                    logger.info(f"  Parseado CSV: {len(df)} filas, {len(df.columns)} columnas")
                    return df
            except Exception:
                continue

        # Intentar como XLSX
        try:
            df = pd.read_excel(io.BytesIO(content), engine="openpyxl")
            if len(df) > 0:
                logger.info(f"  Parseado XLSX: {len(df)} filas, {len(df.columns)} columnas")
                return df
        except Exception:
            pass

        return pd.DataFrame()

    def _identify_columns(self, df: pd.DataFrame) -> Dict[str, str]:
        """Identifica columnas relevantes en el dataset."""
        col_lower = {c: c.lower().strip() for c in df.columns}
        mapping = {}

        # Estado
        for col, low in col_lower.items():
            if any(kw in low for kw in ["entidad", "estado", "nom_ent"]):
                mapping["state"] = col
                break

        # Municipio
        for col, low in col_lower.items():
            if any(kw in low for kw in ["municipio", "nom_mun", "delegacion", "alcaldia"]):
                mapping["municipality"] = col
                break

        # Precio / valor
        for col, low in col_lower.items():
            if any(kw in low for kw in [
                "valor", "precio", "monto", "costo", "valor_vivienda",
                "valor_de_la_vivienda", "subsidio",
            ]):
                mapping["price"] = col
                break

        # Área
        for col, low in col_lower.items():
            if any(kw in low for kw in ["superficie", "area", "m2", "metros"]):
                mapping["area_m2"] = col
                break

        # Tipo de vivienda
        for col, low in col_lower.items():
            if any(kw in low for kw in [
                "tipo_vivienda", "tipo_de_vivienda", "modalidad", "segmento",
            ]):
                mapping["housing_type"] = col
                break

        # Desarrollador
        for col, low in col_lower.items():
            if any(kw in low for kw in ["desarrollador", "empresa", "constructor", "oferente"]):
                mapping["developer"] = col
                break

        # Fecha
        for col, low in col_lower.items():
            if any(kw in low for kw in [
                "fecha_registro", "fecha", "anio", "año", "year", "periodo",
            ]):
                mapping["date"] = col
                break

        # Número de viviendas (para datos agregados)
        for col, low in col_lower.items():
            if any(kw in low for kw in ["viviendas", "acciones", "numero", "cantidad"]):
                mapping["units"] = col
                break

        logger.info(f"  Mapeo de columnas: {mapping}")
        return mapping

    def _normalize_dataset(self, df: pd.DataFrame, source_url: str) -> pd.DataFrame:
        """Normaliza un dataset CONAVI al formato estándar."""
        if df.empty:
            return pd.DataFrame()

        col_map = self._identify_columns(df)

        if not col_map:
            logger.warning("  No se identificaron columnas relevantes")
            return pd.DataFrame()

        rows: List[Dict] = []

        for _, row in df.iterrows():
            try:
                # Estado
                state = self._normalize_state(
                    str(row.get(col_map.get("state", ""), ""))
                )

                # Municipio
                municipality = str(
                    row.get(col_map.get("municipality", ""), "")
                ).strip().title()

                # Precio
                price_raw = row.get(col_map.get("price", ""), 0)
                try:
                    price = float(
                        str(price_raw).replace(",", "").replace("$", "").replace(" ", "")
                    )
                except (ValueError, TypeError):
                    price = 0

                # Área
                area_m2 = 0
                if "area_m2" in col_map:
                    try:
                        area_m2 = float(
                            str(row.get(col_map["area_m2"], 0))
                            .replace(",", "").replace(" ", "")
                        )
                    except (ValueError, TypeError):
                        area_m2 = 0

                # Tipo de vivienda
                housing_type = str(
                    row.get(col_map.get("housing_type", ""), "")
                ).strip()

                # Desarrollador
                developer = str(
                    row.get(col_map.get("developer", ""), "")
                ).strip()

                # Fecha
                date_raw = str(row.get(col_map.get("date", ""), ""))
                try:
                    year = int(float(re.sub(r"[^\d.]", "", date_raw)[:4]))
                    if year < 2000 or year > 2030:
                        year = datetime.now().year
                except (ValueError, TypeError):
                    year = datetime.now().year

                # Número de viviendas
                units = 1
                if "units" in col_map:
                    try:
                        units = int(float(str(row.get(col_map["units"], 1))))
                    except (ValueError, TypeError):
                        units = 1

                # Geocodificar
                lat, lon = self._geocode(municipality)

                # Calcular precio por m2
                price_m2 = round(price / area_m2, 2) if area_m2 > 0 and price > 0 else 0

                rows.append({
                    "state": state,
                    "municipality": municipality,
                    "price_mxn": round(price, 2) if price > 0 else None,
                    "area_m2": area_m2 if area_m2 > 0 else None,
                    "price_m2": price_m2 if price_m2 > 0 else None,
                    "housing_type": housing_type if housing_type else None,
                    "developer": developer[:200] if developer else None,
                    "registration_year": year,
                    "units": units,
                    "lat": lat,
                    "lon": lon,
                    "source": "conavi_ruv",
                    "source_url": source_url,
                    "collection_date": datetime.now().strftime("%Y-%m-%d"),
                })

            except Exception as exc:
                logger.debug(f"Error procesando fila: {exc}")
                continue

        result = pd.DataFrame(rows)
        logger.info(f"  Normalizados: {len(result)} registros de {len(df)} filas")
        return result

    # ── Descarga principal ───────────────────────────────────────────────

    async def download_ruv_data(self) -> pd.DataFrame:
        """
        Descarga y procesa datos del RUV desde múltiples fuentes.

        Returns:
            DataFrame con registros de vivienda normalizada
        """
        logger.info("=" * 70)
        logger.info("CONAVI/RUV - REGISTRO UNICO DE VIVIENDA")
        logger.info(f"  Fuente: datos.gob.mx / SNIIV")
        logger.info(f"  Salida: {OUTPUT_FILE}")
        logger.info("=" * 70)

        all_frames: List[pd.DataFrame] = []

        async with httpx.AsyncClient(
            headers={
                "User-Agent": "IAInmobiliaria-GeoApp/1.0 (investigacion)",
                "Accept": "*/*",
            },
            follow_redirects=True,
        ) as client:

            # 1. Descubrir datasets en datos.gob.mx
            logger.info("\n[1/3] Descubriendo datasets CONAVI en datos.gob.mx...")
            discovered_urls = await self._discover_conavi_datasets(client)

            for url in discovered_urls:
                content = await self._download_file(client, url)
                if content is None:
                    continue

                df_raw = self._parse_content(content, url)
                if not df_raw.empty:
                    df_norm = self._normalize_dataset(df_raw, url)
                    if not df_norm.empty:
                        all_frames.append(df_norm)

                await asyncio.sleep(2)

            # 2. Intentar SNIIV
            logger.info("\n[2/3] Intentando descargar de SNIIV...")
            for url in SNIIV_API_URLS:
                content = await self._download_file(client, url)
                if content is None:
                    continue

                df_raw = self._parse_content(content, url)
                if not df_raw.empty:
                    df_norm = self._normalize_dataset(df_raw, url)
                    if not df_norm.empty:
                        all_frames.append(df_norm)

                await asyncio.sleep(2)

            # 3. Usar datos locales existentes de SNIIV/CONAVI si los hay
            logger.info("\n[3/3] Buscando datos locales existentes...")
            local_files = list(DATA_DIR.glob("conavi_subsidios_*.csv")) + \
                          list(DATA_DIR.glob("sniiv_registro_*.csv"))

            for local_file in local_files:
                try:
                    df_local = pd.read_csv(local_file, encoding="utf-8-sig")
                    if df_local.empty:
                        df_local = pd.read_csv(local_file, encoding="latin-1")
                    if not df_local.empty:
                        logger.info(f"  Archivo local: {local_file.name} ({len(df_local)} filas)")
                        df_norm = self._normalize_dataset(df_local, f"local:{local_file.name}")
                        if not df_norm.empty:
                            all_frames.append(df_norm)
                except Exception as exc:
                    logger.warning(f"  Error leyendo {local_file.name}: {exc}")

        # Combinar resultados
        if not all_frames:
            logger.warning("No se obtuvieron datos de CONAVI/RUV")
            return pd.DataFrame()

        df_all = pd.concat(all_frames, ignore_index=True)

        # Deduplicar
        before = len(df_all)
        dedup_cols = ["state", "municipality", "price_mxn", "registration_year"]
        existing = [c for c in dedup_cols if c in df_all.columns]
        if existing:
            df_all = df_all.drop_duplicates(subset=existing, keep="first")
        logger.info(f"Deduplicación: {before} -> {len(df_all)}")

        return df_all

    # ── Features de mercado ──────────────────────────────────────────────

    def compute_market_features(
        self, df: pd.DataFrame, lat: float, lon: float, radius_km: float = 5.0
    ) -> Dict[str, Any]:
        """
        Calcula features de mercado de obra nueva para un punto dado.

        Args:
            df: DataFrame con datos RUV
            lat: Latitud del punto de interés
            lon: Longitud del punto de interés
            radius_km: Radio de búsqueda en km

        Returns:
            Diccionario con features:
            - new_construction_avg_price_m2
            - new_construction_count_5km
            - new_vs_existing_price_ratio (estimado)
        """
        if df.empty or "lat" not in df.columns or "lon" not in df.columns:
            return {
                "new_construction_avg_price_m2": None,
                "new_construction_count_5km": 0,
                "new_vs_existing_price_ratio": None,
            }

        # Filtrar registros con coordenadas válidas
        df_valid = df.dropna(subset=["lat", "lon", "price_m2"])
        if df_valid.empty:
            return {
                "new_construction_avg_price_m2": None,
                "new_construction_count_5km": 0,
                "new_vs_existing_price_ratio": None,
            }

        # Calcular distancias
        distances = df_valid.apply(
            lambda row: _haversine_km(lat, lon, row["lat"], row["lon"]),
            axis=1,
        )

        # Filtrar por radio
        nearby = df_valid[distances <= radius_km]

        if nearby.empty:
            return {
                "new_construction_avg_price_m2": None,
                "new_construction_count_5km": 0,
                "new_vs_existing_price_ratio": None,
            }

        avg_price_m2 = nearby["price_m2"].mean()
        count = len(nearby)

        # Ratio obra nueva vs existente (la obra nueva suele ser 15-25% más cara)
        # Este es un estimado; el ratio real requiere datos de mercado secundario
        ratio = 1.20  # Valor default

        return {
            "new_construction_avg_price_m2": round(avg_price_m2, 2),
            "new_construction_count_5km": count,
            "new_vs_existing_price_ratio": ratio,
        }

    def add_conavi_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Agrega features de CONAVI/RUV al DataFrame.

        Requiere columnas 'lat' y 'lon'. Calcula features de mercado de obra nueva
        para cada punto en el DataFrame.

        Args:
            df: DataFrame con columnas lat y lon

        Returns:
            DataFrame con columnas de CONAVI agregadas
        """
        if df.empty:
            logger.warning("DataFrame vacío, no se agregan features CONAVI")
            return df

        df = df.copy()

        if "lat" not in df.columns or "lon" not in df.columns:
            logger.error("DataFrame no tiene columnas 'lat' y 'lon'")
            return df

        # Cargar datos RUV
        if OUTPUT_FILE.exists():
            try:
                df_ruv = pd.read_csv(OUTPUT_FILE, encoding="utf-8-sig")
                logger.info(f"Cargados {len(df_ruv)} registros RUV desde {OUTPUT_FILE}")
            except Exception:
                df_ruv = pd.DataFrame()
        else:
            logger.warning(f"Archivo RUV no encontrado: {OUTPUT_FILE}")
            df_ruv = pd.DataFrame()

        logger.info(f"Calculando features CONAVI/RUV para {len(df)} registros...")

        new_price_m2 = []
        new_count = []
        new_ratio = []

        for _, row in df.iterrows():
            lat = row.get("lat")
            lon = row.get("lon")

            if pd.isna(lat) or pd.isna(lon):
                new_price_m2.append(None)
                new_count.append(0)
                new_ratio.append(None)
                continue

            features = self.compute_market_features(df_ruv, lat, lon)
            new_price_m2.append(features["new_construction_avg_price_m2"])
            new_count.append(features["new_construction_count_5km"])
            new_ratio.append(features["new_vs_existing_price_ratio"])

        df["new_construction_avg_price_m2"] = new_price_m2
        df["new_construction_count_5km"] = new_count
        df["new_vs_existing_price_ratio"] = new_ratio

        logger.info(
            f"Features CONAVI agregados. Promedio precio obra nueva: "
            f"{df['new_construction_avg_price_m2'].mean():.0f} MXN/m2"
        )

        return df

    # ── Persistencia ─────────────────────────────────────────────────────

    def save_csv(self, df: pd.DataFrame) -> Path:
        """Guarda datos procesados en CSV."""
        df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
        logger.info(f"Guardado: {OUTPUT_FILE} ({len(df)} registros)")
        return OUTPUT_FILE

    def upsert_to_supabase(self, df: pd.DataFrame) -> int:
        """Inserta datos en Supabase tabla iainmobiliaria_conavi_ruv."""
        if not HAS_SUPABASE:
            logger.warning("supabase-py no disponible, omitiendo upsert")
            return 0

        if df.empty:
            return 0

        try:
            supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        except Exception as exc:
            logger.error(f"Error conectando a Supabase: {exc}")
            return 0

        # Preparar registros para inserción
        records = df.head(5000).to_dict("records")  # Limitar a 5000 registros

        # Limpiar NaN/None para Supabase
        for record in records:
            for key, val in record.items():
                if pd.isna(val) if isinstance(val, (float, np.floating)) else val is None:
                    record[key] = None

        batch_size = 100
        saved = 0

        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            try:
                supabase.table(SUPABASE_TABLE).upsert(batch).execute()
                saved += len(batch)
                if saved % 500 == 0 or saved == len(records):
                    logger.info(f"  Supabase: {saved}/{len(records)} registros")
            except Exception as exc:
                logger.warning(f"  Error en lote Supabase: {exc}")
            time.sleep(0.3)

        logger.info(f"Supabase upsert completado: {saved} registros en {SUPABASE_TABLE}")
        return saved


# ── Funciones de conveniencia ────────────────────────────────────────────────

def download_ruv_data() -> pd.DataFrame:
    """Función de conveniencia para descargar datos RUV."""
    scraper = CONAVIRUVScraper()
    return asyncio.run(scraper.download_ruv_data())


def compute_market_features(
    df: pd.DataFrame, lat: float, lon: float, radius_km: float = 5.0
) -> Dict[str, Any]:
    """Función de conveniencia para calcular features de mercado."""
    scraper = CONAVIRUVScraper()
    return scraper.compute_market_features(df, lat, lon, radius_km)


def add_conavi_features(df: pd.DataFrame) -> pd.DataFrame:
    """Función de conveniencia para agregar features CONAVI a un DataFrame."""
    scraper = CONAVIRUVScraper()
    return scraper.add_conavi_features(df)


# ── CLI ──────────────────────────────────────────────────────────────────────

async def main():
    """Descarga y procesa todos los datos CONAVI/RUV disponibles."""
    scraper = CONAVIRUVScraper()
    df = await scraper.download_ruv_data()

    if df.empty:
        logger.warning("No se obtuvieron resultados de CONAVI/RUV.")
        return

    # Guardar CSV
    scraper.save_csv(df)

    # Upsert a Supabase
    scraper.upsert_to_supabase(df)

    # Reporte
    logger.info("\n" + "=" * 60)
    logger.info("REPORTE CONAVI/RUV")
    logger.info("=" * 60)

    if "state" in df.columns:
        state_counts = df.groupby("state").size().sort_values(ascending=False)
        logger.info("\nRegistros por estado:")
        for state, count in state_counts.head(15).items():
            logger.info(f"  {state:<30s} {count:>8,}")

    logger.info(f"\n  TOTAL: {len(df):,} registros")

    if "price_m2" in df.columns:
        valid_prices = df["price_m2"].dropna()
        if len(valid_prices) > 0:
            logger.info(f"  Precio promedio m2: ${valid_prices.mean():,.0f} MXN")
            logger.info(f"  Precio mediano m2: ${valid_prices.median():,.0f} MXN")

    with_coords = df[df["lat"].notna() & df["lon"].notna()]
    logger.info(f"  Con coordenadas: {len(with_coords):,} / {len(df):,}")


if __name__ == "__main__":
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level:<8}</level> | <level>{message}</level>",
        level="INFO",
    )
    asyncio.run(main())
