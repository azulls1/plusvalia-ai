"""
Scraper de datos de avalúos y valuaciones INFONAVIT.

Fuente: INFONAVIT datos abiertos en datos.gob.mx
        https://portaldatosabiertos.infonavit.org.mx/
        https://datos.gob.mx/busca/organization/infonavit

Datos: precios medianos de vivienda por municipio derivados de avalúos
respaldados por créditos hipotecarios INFONAVIT. Estos representan
transacciones reales del mercado, lo que los hace una fuente confiable
para modelos de valuación.

Extrae:
  - Precio mediano y promedio por municipio
  - Densidad de créditos (créditos per cápita)
  - Tendencia de precios a 1 año
  - Tipo de vivienda dominante por zona

El scraper:
  1. Descarga datos de créditos originados desde INFONAVIT
  2. Agrega estadísticas por estado/municipio
  3. Calcula tendencias y densidades
  4. Guarda en CSV y opcionalmente en Supabase
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

OUTPUT_FILE = DATA_DIR / "infonavit_avaluos.csv"
CITIES_FILE = DATA_DIR / "cities_mexico_32_states.json"
SUPABASE_TABLE = "iainmobiliaria_infonavit_data"

# ── URLs de datos abiertos INFONAVIT ─────────────────────────────────────────

INFONAVIT_PORTAL = "https://portaldatosabiertos.infonavit.org.mx"
DATOS_GOB_CKAN = "https://datos.gob.mx/busca/api/3/action"

KNOWN_URLS = [
    # Créditos originados (contienen valor de vivienda = avalúo)
    f"{INFONAVIT_PORTAL}/downloads/creditos_originados.csv",
    f"{INFONAVIT_PORTAL}/downloads/creditos_colocados.csv",
    # CKAN de INFONAVIT
    f"{INFONAVIT_PORTAL}/api/3/action",
]

# ── Población por estado (INEGI 2020, miles) para cálculo de densidad ───────

STATE_POPULATION_THOUSANDS: Dict[str, int] = {
    "Aguascalientes": 1426,
    "Baja California": 3769,
    "Baja California Sur": 798,
    "Campeche": 928,
    "Chiapas": 5543,
    "Chihuahua": 3741,
    "Ciudad de México": 9209,
    "Coahuila": 3146,
    "Colima": 731,
    "Durango": 1832,
    "Guanajuato": 6166,
    "Guerrero": 3540,
    "Hidalgo": 3082,
    "Jalisco": 8348,
    "México": 16992,
    "Michoacán": 4748,
    "Morelos": 1971,
    "Nayarit": 1235,
    "Nuevo León": 5784,
    "Oaxaca": 4132,
    "Puebla": 6583,
    "Querétaro": 2368,
    "Quintana Roo": 1857,
    "San Luis Potosí": 2822,
    "Sinaloa": 3026,
    "Sonora": 2944,
    "Tabasco": 2402,
    "Tamaulipas": 3527,
    "Tlaxcala": 1342,
    "Veracruz": 8063,
    "Yucatán": 2320,
    "Zacatecas": 1622,
}

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

# Tipo de vivienda → área estimada en m2
HOUSING_TYPE_AREA: Dict[str, float] = {
    "economica": 42,
    "popular": 55,
    "tradicional": 80,
    "media": 120,
    "residencial": 180,
    "residencial plus": 250,
    "vivienda usada": 80,
    "vivienda nueva": 75,
}


class InfonavitDataScraper:
    """
    Descarga datos de avalúos INFONAVIT, calcula estadísticas por
    municipio y genera features para el modelo de valuación.
    """

    def __init__(self):
        self.city_coords: Dict[str, Tuple[float, float]] = {}
        self._load_cities()

    def _load_cities(self):
        """Carga coordenadas de ciudades."""
        # Coordenadas conocidas
        known = {
            "Guadalajara": (20.6597, -103.3496),
            "Zapopan": (20.7167, -103.4000),
            "Monterrey": (25.6866, -100.3161),
            "Ciudad de México": (19.4326, -99.1332),
            "Puebla": (19.0414, -98.2063),
            "Tijuana": (32.5149, -117.0382),
            "León": (21.1250, -101.6860),
            "Querétaro": (20.5888, -100.3899),
            "Cancún": (21.1619, -86.8515),
            "Mérida": (20.9674, -89.5926),
            "Toluca": (19.2826, -99.6557),
            "Aguascalientes": (21.8818, -102.2916),
            "San Luis Potosí": (22.1565, -100.9855),
            "Hermosillo": (29.0729, -110.9559),
            "Morelia": (19.7060, -101.1950),
            "Chihuahua": (28.6353, -106.0889),
            "Saltillo": (25.4232, -100.9925),
            "Culiacán": (24.8049, -107.3940),
            "Veracruz": (19.2026, -96.1533),
            "Oaxaca": (17.0732, -96.7266),
            "Villahermosa": (17.9892, -92.9475),
            "Acapulco": (16.8531, -99.8237),
            "Cuernavaca": (18.9186, -99.2342),
            "Durango": (24.0277, -104.6532),
            "Pachuca": (20.1011, -98.7591),
        }
        self.city_coords.update(known)

        if CITIES_FILE.exists():
            try:
                with open(CITIES_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for estado in data.get("estados", []):
                    for ciudad in estado.get("ciudades", []):
                        name = ciudad["city"]
                        if "lat" in ciudad and "lon" in ciudad:
                            self.city_coords[name] = (ciudad["lat"], ciudad["lon"])
                            self.city_coords[name.upper()] = (ciudad["lat"], ciudad["lon"])
            except Exception as exc:
                logger.warning(f"Error cargando ciudades: {exc}")

        logger.info(f"Cargadas {len(self.city_coords)} coordenadas de ciudades")

    def _normalize_state(self, raw: str) -> str:
        """Normaliza nombre de estado."""
        if not raw or not isinstance(raw, str):
            return ""
        return STATE_ALIASES.get(raw.strip().upper(), raw.strip().title())

    def _geocode(self, city: str) -> Tuple[Optional[float], Optional[float]]:
        """Busca coordenadas para una ciudad."""
        coords = self.city_coords.get(city)
        if coords:
            return coords
        coords = self.city_coords.get(city.upper())
        if coords:
            return coords
        city_upper = city.upper()
        for key, val in self.city_coords.items():
            if isinstance(key, str) and city_upper in key.upper():
                return val
        return (None, None)

    # ── Descarga ─────────────────────────────────────────────────────────

    async def _download(
        self, client: httpx.AsyncClient, url: str
    ) -> Optional[bytes]:
        """Descarga un archivo con reintentos."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info(f"  Descargando (intento {attempt + 1}): {url}")
                resp = await client.get(url, timeout=120, follow_redirects=True)
                if resp.status_code == 200:
                    logger.info(f"  OK: {len(resp.content):,} bytes")
                    return resp.content
                else:
                    logger.warning(f"  HTTP {resp.status_code}")
            except (httpx.TimeoutException, httpx.ConnectError, OSError) as exc:
                logger.warning(f"  Error: {exc}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
        return None

    async def _discover_infonavit_datasets(
        self, client: httpx.AsyncClient
    ) -> List[str]:
        """Descubre datasets INFONAVIT en datos.gob.mx."""
        urls = []
        try:
            for query in ["infonavit creditos", "infonavit avaluos", "infonavit vivienda"]:
                resp = await client.get(
                    f"{DATOS_GOB_CKAN}/package_search",
                    params={"q": query, "rows": 10},
                    timeout=30,
                )
                if resp.status_code != 200:
                    continue

                data = resp.json()
                for dataset in data.get("result", {}).get("results", []):
                    for resource in dataset.get("resources", []):
                        fmt = (resource.get("format") or "").lower()
                        if fmt in ("csv", "xlsx", "xls"):
                            url = resource.get("url", "")
                            if url and url not in urls:
                                urls.append(url)
                                logger.info(
                                    f"  Descubierto: {resource.get('name', 'N/A')} -> {url}"
                                )
                await asyncio.sleep(1)

            # También probar el CKAN de INFONAVIT
            try:
                resp = await client.get(
                    f"{INFONAVIT_PORTAL}/api/3/action/package_search",
                    params={"q": "creditos", "rows": 20},
                    timeout=30,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    for dataset in data.get("result", {}).get("results", []):
                        for resource in dataset.get("resources", []):
                            url = resource.get("url", "")
                            fmt = (resource.get("format") or "").lower()
                            if url and fmt in ("csv", "xlsx") and url not in urls:
                                urls.append(url)
            except Exception:
                pass

        except Exception as exc:
            logger.warning(f"Error en descubrimiento: {exc}")

        return urls

    # ── Procesamiento ────────────────────────────────────────────────────

    def _parse_content(self, content: bytes, url: str) -> pd.DataFrame:
        """Parsea contenido descargado."""
        for encoding in ["utf-8", "latin-1", "cp1252", "utf-8-sig"]:
            try:
                df = pd.read_csv(
                    io.BytesIO(content),
                    encoding=encoding,
                    low_memory=False,
                    on_bad_lines="skip",
                )
                if len(df) > 0 and len(df.columns) > 2:
                    logger.info(f"  CSV: {len(df)} filas, {len(df.columns)} columnas")
                    return df
            except Exception:
                continue

        try:
            df = pd.read_excel(io.BytesIO(content), engine="openpyxl")
            if len(df) > 0:
                logger.info(f"  XLSX: {len(df)} filas")
                return df
        except Exception:
            pass

        return pd.DataFrame()

    def _extract_credit_data(self, df: pd.DataFrame, source: str) -> pd.DataFrame:
        """
        Extrae datos de créditos/avalúos de un DataFrame descargado.
        Identifica columnas automáticamente y normaliza.
        """
        if df.empty:
            return pd.DataFrame()

        col_lower = {c: c.lower().strip() for c in df.columns}
        mapping = {}

        # Identificar columnas
        for col, low in col_lower.items():
            if any(kw in low for kw in ["entidad", "estado", "nom_ent"]):
                mapping["state"] = col
            elif any(kw in low for kw in ["municipio", "nom_mun", "delegacion"]):
                mapping["municipality"] = col
            elif any(kw in low for kw in [
                "valor_vivienda", "valor_avaluo", "monto_credito",
                "valor_de_la_vivienda", "precio", "valor",
            ]):
                mapping["price"] = col
            elif any(kw in low for kw in ["tipo_vivienda", "segmento", "tipo_de_vivienda"]):
                mapping["housing_type"] = col
            elif any(kw in low for kw in ["anio", "año", "year", "ejercicio", "periodo"]):
                mapping["year"] = col
            elif any(kw in low for kw in ["trimestre", "quarter", "trim"]):
                mapping["quarter"] = col
            elif any(kw in low for kw in ["superficie", "area", "m2"]):
                mapping["area_m2"] = col

        if not mapping:
            logger.warning(f"  No se identificaron columnas en dataset {source}")
            return pd.DataFrame()

        logger.info(f"  Mapeo: {mapping}")

        rows = []
        for _, row in df.iterrows():
            try:
                state = self._normalize_state(
                    str(row.get(mapping.get("state", ""), ""))
                )
                municipality = str(
                    row.get(mapping.get("municipality", ""), "")
                ).strip().title()

                # Precio
                price_raw = row.get(mapping.get("price", ""), 0)
                try:
                    price = float(
                        str(price_raw).replace(",", "").replace("$", "").replace(" ", "")
                    )
                except (ValueError, TypeError):
                    price = 0

                if price <= 10_000:
                    continue

                # Tipo de vivienda
                housing_type = str(
                    row.get(mapping.get("housing_type", ""), "")
                ).strip().lower()

                # Área
                area_m2 = 0
                if "area_m2" in mapping:
                    try:
                        area_m2 = float(str(row.get(mapping["area_m2"], 0)).replace(",", ""))
                    except (ValueError, TypeError):
                        area_m2 = 0
                if area_m2 <= 0:
                    area_m2 = HOUSING_TYPE_AREA.get(housing_type, 75)

                # Año y trimestre
                year = datetime.now().year
                if "year" in mapping:
                    try:
                        year = int(float(str(row.get(mapping["year"], year))))
                    except (ValueError, TypeError):
                        pass

                quarter = 0
                if "quarter" in mapping:
                    try:
                        quarter = int(float(str(row.get(mapping["quarter"], 0))))
                    except (ValueError, TypeError):
                        pass

                price_m2 = round(price / area_m2, 2) if area_m2 > 0 else 0

                rows.append({
                    "state": state,
                    "municipality": municipality,
                    "price_mxn": round(price, 2),
                    "area_m2": area_m2,
                    "price_m2": price_m2,
                    "housing_type": housing_type,
                    "year": year,
                    "quarter": quarter if quarter > 0 else None,
                    "source": source,
                })

            except Exception:
                continue

        result = pd.DataFrame(rows)
        logger.info(f"  Extraídos {len(result)} registros de créditos")
        return result

    # ── Cálculo de features por municipio ────────────────────────────────

    def _aggregate_by_municipality(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Agrega datos de créditos individuales a estadísticas por municipio.
        Calcula mediana, promedio, conteo y tendencia.
        """
        if df.empty:
            return pd.DataFrame()

        # Filtrar precios válidos
        df_valid = df[df["price_m2"] > 0].copy()

        if df_valid.empty:
            return pd.DataFrame()

        # Agrupar por estado + municipio
        groups = df_valid.groupby(["state", "municipality"])

        rows = []
        for (state, muni), group in groups:
            # Estadísticas de precio
            median_price = group["price_mxn"].median()
            avg_price = group["price_mxn"].mean()
            median_price_m2 = group["price_m2"].median()
            avg_price_m2 = group["price_m2"].mean()
            credit_count = len(group)

            # Tipo de vivienda dominante
            if "housing_type" in group.columns:
                housing_mode = group["housing_type"].mode()
                dominant_type = housing_mode.iloc[0] if len(housing_mode) > 0 else ""
            else:
                dominant_type = ""

            # Tendencia de precios (último año vs anterior)
            price_trend = 0.0
            if "year" in group.columns:
                years = group["year"].dropna().unique()
                if len(years) >= 2:
                    max_year = int(max(years))
                    prev_year = max_year - 1
                    current = group[group["year"] == max_year]["price_m2"].median()
                    previous = group[group["year"] == prev_year]["price_m2"].median()
                    if previous and previous > 0 and not pd.isna(current):
                        price_trend = round(
                            ((current - previous) / previous) * 100, 2
                        )

            # Densidad de créditos (créditos por cada 1000 habitantes)
            pop = STATE_POPULATION_THOUSANDS.get(state, 0)
            credit_density = round(
                (credit_count / (pop * 1000)) * 100_000, 2
            ) if pop > 0 else 0

            # Geocodificar
            lat, lon = self._geocode(muni)

            # Años cubiertos
            years_list = sorted(group["year"].dropna().unique().tolist())
            year_min = int(min(years_list)) if years_list else None
            year_max = int(max(years_list)) if years_list else None

            rows.append({
                "state": state,
                "municipality": muni,
                "median_price_mxn": round(median_price, 2),
                "avg_price_mxn": round(avg_price, 2),
                "infonavit_median_price_m2": round(median_price_m2, 2),
                "infonavit_avg_price_m2": round(avg_price_m2, 2),
                "credit_count": credit_count,
                "infonavit_credit_density": credit_density,
                "dominant_housing_type": dominant_type,
                "infonavit_price_trend_1yr": price_trend,
                "year_min": year_min,
                "year_max": year_max,
                "lat": lat,
                "lon": lon,
                "generated_at": datetime.now().isoformat(),
            })

        result = pd.DataFrame(rows)
        result = result.sort_values("credit_count", ascending=False)
        logger.info(f"Agregados: {len(result)} municipios con datos INFONAVIT")
        return result

    # ── Descarga principal ───────────────────────────────────────────────

    async def download_infonavit_data(self) -> pd.DataFrame:
        """
        Descarga y procesa datos de avalúos/créditos INFONAVIT.

        Returns:
            DataFrame con estadísticas por municipio
        """
        logger.info("=" * 70)
        logger.info("INFONAVIT - DATOS DE AVALUOS Y CREDITOS")
        logger.info(f"  Portal: {INFONAVIT_PORTAL}")
        logger.info(f"  Salida: {OUTPUT_FILE}")
        logger.info("=" * 70)

        all_credits: List[pd.DataFrame] = []

        async with httpx.AsyncClient(
            headers={
                "User-Agent": "IAInmobiliaria-GeoApp/1.0 (investigacion)",
                "Accept": "*/*",
            },
            follow_redirects=True,
        ) as client:

            # 1. URLs conocidas
            logger.info("\n[1/3] Intentando URLs conocidas de INFONAVIT...")
            for url in KNOWN_URLS:
                if "/api/" in url:
                    continue  # APIs se usan en el paso 2
                content = await self._download(client, url)
                if content:
                    df_raw = self._parse_content(content, url)
                    if not df_raw.empty:
                        df_credits = self._extract_credit_data(df_raw, url)
                        if not df_credits.empty:
                            all_credits.append(df_credits)
                await asyncio.sleep(2)

            # 2. Descubrimiento automático
            logger.info("\n[2/3] Descubriendo datasets en datos.gob.mx...")
            discovered = await self._discover_infonavit_datasets(client)
            for url in discovered:
                content = await self._download(client, url)
                if content:
                    df_raw = self._parse_content(content, url)
                    if not df_raw.empty:
                        df_credits = self._extract_credit_data(df_raw, url)
                        if not df_credits.empty:
                            all_credits.append(df_credits)
                await asyncio.sleep(2)

            # 3. Datos locales existentes
            logger.info("\n[3/3] Buscando datos locales INFONAVIT/SNIIV...")
            local_patterns = [
                "infonavit_*.csv",
                "sniiv_infonavit_*.csv",
            ]
            for pattern in local_patterns:
                for local_file in DATA_DIR.glob(pattern):
                    try:
                        df_local = pd.read_csv(local_file, encoding="utf-8-sig")
                        if df_local.empty:
                            df_local = pd.read_csv(local_file, encoding="latin-1")
                        if not df_local.empty:
                            logger.info(f"  Local: {local_file.name} ({len(df_local)} filas)")
                            df_credits = self._extract_credit_data(
                                df_local, f"local:{local_file.name}"
                            )
                            if not df_credits.empty:
                                all_credits.append(df_credits)
                    except Exception as exc:
                        logger.debug(f"  Error: {exc}")

        if not all_credits:
            logger.warning("No se obtuvieron datos de créditos INFONAVIT")
            return pd.DataFrame()

        # Combinar todos los créditos
        df_all = pd.concat(all_credits, ignore_index=True)
        logger.info(f"Total de créditos individuales: {len(df_all):,}")

        # Deduplicar
        before = len(df_all)
        df_all = df_all.drop_duplicates(
            subset=["state", "municipality", "price_mxn", "year"],
            keep="first",
        )
        logger.info(f"Deduplicación: {before:,} -> {len(df_all):,}")

        # Filtrar precios razonables
        df_all = df_all[df_all["price_mxn"] > 50_000]
        df_all = df_all[df_all["price_mxn"] < 50_000_000]

        # Agregar por municipio
        df_aggregated = self._aggregate_by_municipality(df_all)

        return df_aggregated

    # ── Features para el modelo ──────────────────────────────────────────

    def compute_valuation_features(
        self, state: str, municipality: str
    ) -> Dict[str, Any]:
        """
        Calcula features de valuación INFONAVIT para un estado/municipio.

        Args:
            state: Nombre del estado
            municipality: Nombre del municipio

        Returns:
            Diccionario con features:
            - infonavit_median_price_m2
            - infonavit_credit_density
            - infonavit_price_trend_1yr
        """
        defaults = {
            "infonavit_median_price_m2": None,
            "infonavit_credit_density": None,
            "infonavit_price_trend_1yr": None,
        }

        if not OUTPUT_FILE.exists():
            logger.warning(f"Archivo no encontrado: {OUTPUT_FILE}")
            return defaults

        try:
            df = pd.read_csv(OUTPUT_FILE, encoding="utf-8-sig")
        except Exception:
            return defaults

        # Buscar el municipio
        mask = (
            (df["state"].str.upper() == state.upper())
            & (df["municipality"].str.upper() == municipality.upper())
        )
        match = df[mask]

        if match.empty:
            # Intentar búsqueda parcial
            mask = df["municipality"].str.upper().str.contains(
                municipality.upper(), na=False
            )
            match = df[mask]

        if match.empty:
            return defaults

        row = match.iloc[0]
        return {
            "infonavit_median_price_m2": row.get("infonavit_median_price_m2"),
            "infonavit_credit_density": row.get("infonavit_credit_density"),
            "infonavit_price_trend_1yr": row.get("infonavit_price_trend_1yr"),
        }

    def add_infonavit_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Agrega features INFONAVIT al DataFrame.

        Requiere columnas 'state' y 'city' (o 'municipality') en el DataFrame.

        Args:
            df: DataFrame con columnas state y city/municipality

        Returns:
            DataFrame con columnas INFONAVIT agregadas
        """
        if df.empty:
            logger.warning("DataFrame vacío, no se agregan features INFONAVIT")
            return df

        df = df.copy()

        # Determinar columna de municipio
        muni_col = None
        for col in ["municipality", "city", "municipio"]:
            if col in df.columns:
                muni_col = col
                break

        state_col = None
        for col in ["state", "estado"]:
            if col in df.columns:
                state_col = col
                break

        if not muni_col or not state_col:
            logger.error("DataFrame no tiene columnas de estado/municipio requeridas")
            return df

        logger.info(f"Calculando features INFONAVIT para {len(df)} registros...")

        median_prices = []
        credit_densities = []
        price_trends = []

        for _, row in df.iterrows():
            state = str(row.get(state_col, ""))
            muni = str(row.get(muni_col, ""))

            features = self.compute_valuation_features(state, muni)
            median_prices.append(features["infonavit_median_price_m2"])
            credit_densities.append(features["infonavit_credit_density"])
            price_trends.append(features["infonavit_price_trend_1yr"])

        df["infonavit_median_price_m2"] = median_prices
        df["infonavit_credit_density"] = credit_densities
        df["infonavit_price_trend_1yr"] = price_trends

        filled = df["infonavit_median_price_m2"].notna().sum()
        logger.info(f"Features INFONAVIT: {filled}/{len(df)} registros con datos")

        return df

    # ── Persistencia ─────────────────────────────────────────────────────

    def save_csv(self, df: pd.DataFrame) -> Path:
        """Guarda datos en CSV."""
        df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
        logger.info(f"Guardado: {OUTPUT_FILE} ({len(df)} registros)")
        return OUTPUT_FILE

    def upsert_to_supabase(self, df: pd.DataFrame) -> int:
        """Inserta datos en Supabase."""
        if not HAS_SUPABASE:
            logger.warning("supabase-py no disponible")
            return 0

        if df.empty:
            return 0

        try:
            supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        except Exception as exc:
            logger.error(f"Error conectando a Supabase: {exc}")
            return 0

        records = df.to_dict("records")

        # Limpiar NaN
        for record in records:
            for key, val in record.items():
                if isinstance(val, (float, np.floating)) and pd.isna(val):
                    record[key] = None

        batch_size = 100
        saved = 0

        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            try:
                supabase.table(SUPABASE_TABLE).upsert(batch).execute()
                saved += len(batch)
                if saved % 200 == 0 or saved == len(records):
                    logger.info(f"  Supabase: {saved}/{len(records)}")
            except Exception as exc:
                logger.warning(f"  Error lote: {exc}")
            time.sleep(0.3)

        logger.info(f"Upsert completado: {saved} registros en {SUPABASE_TABLE}")
        return saved


# ── Funciones de conveniencia ────────────────────────────────────────────────

def download_infonavit_data() -> pd.DataFrame:
    """Descarga datos de avalúos INFONAVIT."""
    scraper = InfonavitDataScraper()
    return asyncio.run(scraper.download_infonavit_data())


def compute_valuation_features(state: str, municipality: str) -> Dict[str, Any]:
    """Calcula features de valuación para un municipio."""
    scraper = InfonavitDataScraper()
    return scraper.compute_valuation_features(state, municipality)


def add_infonavit_features(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega features INFONAVIT a un DataFrame."""
    scraper = InfonavitDataScraper()
    return scraper.add_infonavit_features(df)


# ── CLI ──────────────────────────────────────────────────────────────────────

async def main():
    """Descarga y procesa datos de avalúos INFONAVIT."""
    scraper = InfonavitDataScraper()
    df = await scraper.download_infonavit_data()

    if df.empty:
        logger.warning("No se obtuvieron resultados.")
        return

    # Guardar
    scraper.save_csv(df)
    scraper.upsert_to_supabase(df)

    # Reporte
    logger.info("\n" + "=" * 60)
    logger.info("REPORTE INFONAVIT - AVALUOS POR MUNICIPIO")
    logger.info("=" * 60)

    if "state" in df.columns:
        state_counts = df.groupby("state").size().sort_values(ascending=False)
        logger.info("\nMunicipios con datos por estado:")
        for state, count in state_counts.head(15).items():
            logger.info(f"  {state:<30s} {count:>5}")

    logger.info(f"\n  TOTAL: {len(df):,} municipios con datos")

    if "infonavit_median_price_m2" in df.columns:
        valid = df["infonavit_median_price_m2"].dropna()
        if len(valid) > 0:
            logger.info(f"  Precio mediano m2 nacional: ${valid.median():,.0f} MXN")

    if "credit_count" in df.columns:
        logger.info(f"  Total créditos procesados: {df['credit_count'].sum():,.0f}")

    if "infonavit_price_trend_1yr" in df.columns:
        trends = df["infonavit_price_trend_1yr"].dropna()
        if len(trends) > 0:
            logger.info(f"  Tendencia promedio 1yr: {trends.mean():+.1f}%")

    # Top 10 municipios más caros
    if "infonavit_median_price_m2" in df.columns:
        top = df.nlargest(10, "infonavit_median_price_m2")
        logger.info("\nTop 10 municipios más caros (precio/m2):")
        for _, row in top.iterrows():
            logger.info(
                f"  {row['municipality']:<25s} {row['state']:<20s} "
                f"${row['infonavit_median_price_m2']:>10,.0f}/m2  "
                f"({row['credit_count']:,} créditos)"
            )


if __name__ == "__main__":
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level:<8}</level> | <level>{message}</level>",
        level="INFO",
    )
    asyncio.run(main())
