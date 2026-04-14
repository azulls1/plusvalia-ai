"""
Scraper del Índice SHF de Precios de la Vivienda
(Sociedad Hipotecaria Federal)

Descarga y procesa los índices de precios de vivienda publicados por SHF,
así como datos complementarios del SIE de Banxico.

Fuentes:
- SHF: https://www.gob.mx/shf (Índice SHF de Precios de la Vivienda)
- Banxico SIE API: https://www.banxico.org.mx/SieAPIRest/service/v1/

Features derivados:
  - price_trend_1yr: cambio anualizado de precios
  - price_trend_3yr: crecimiento compuesto a 3 años
  - price_momentum: aceleración/desaceleración del cambio de precios
  - relative_to_national: índice relativo al promedio nacional

Tabla destino: iainmobiliaria_shf_price_index
"""

import asyncio
import os
import sys
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx
import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)

try:
    from tenacity import retry, stop_after_attempt, wait_exponential
except ImportError:
    def retry(**kwargs):
        def decorator(func):
            return func
        return decorator
    stop_after_attempt = lambda n: None
    wait_exponential = lambda **kw: None

from config import (
    DATA_DIR,
    SUPABASE_URL,
    SUPABASE_SERVICE_ROLE_KEY,
    SCRAPER_DELAY,
    SCRAPER_MAX_RETRIES,
    SCRAPER_USER_AGENT,
)

# ── Constantes ──────────────────────────────────────────────────────────────

# URL de descarga del índice SHF
# SHF publica datos trimestrales en formato Excel/CSV
SHF_INDEX_URL = (
    "https://www.gob.mx/cms/uploads/attachment/file/904523/"
    "indice_shf_precios_vivienda_2024.csv"
)

SHF_ALT_URLS = [
    "https://www.gob.mx/cms/uploads/attachment/file/880234/indice_shf_precios_vivienda.xlsx",
    "https://www.gob.mx/cms/uploads/attachment/file/850123/indice_shf_precios_vivienda_2023.csv",
]

# API de Banxico SIE (Series de Indicadores Económicos)
# Series relevantes de precios de vivienda
BANXICO_SIE_BASE = "https://www.banxico.org.mx/SieAPIRest/service/v1/series"
BANXICO_TOKEN = os.getenv("BANXICO_API_TOKEN", "")

# Series de Banxico para índice de precios de vivienda
BANXICO_SERIES: Dict[str, str] = {
    "indice_precios_vivienda_nacional": "SP74660",   # Índice SHF Nacional
    "indice_precios_vivienda_nuevas": "SP74661",     # Viviendas nuevas
    "indice_precios_vivienda_usadas": "SP74662",     # Viviendas usadas
}

# Mapeo de entidades federativas a zonas metropolitanas principales
ZONAS_METROPOLITANAS: Dict[str, List[str]] = {
    "Aguascalientes": ["ZM Aguascalientes"],
    "Baja California": ["ZM Tijuana", "ZM Mexicali"],
    "Baja California Sur": ["ZM La Paz"],
    "Chihuahua": ["ZM Chihuahua", "ZM Ciudad Juárez"],
    "Ciudad de México": ["ZM Valle de México"],
    "Coahuila": ["ZM Saltillo", "ZM La Laguna"],
    "Colima": ["ZM Colima-Villa de Álvarez"],
    "Guanajuato": ["ZM León", "ZM Celaya"],
    "Guerrero": ["ZM Acapulco"],
    "Jalisco": ["ZM Guadalajara"],
    "México": ["ZM Valle de México", "ZM Toluca"],
    "Michoacán": ["ZM Morelia"],
    "Morelos": ["ZM Cuernavaca"],
    "Nuevo León": ["ZM Monterrey"],
    "Oaxaca": ["ZM Oaxaca"],
    "Puebla": ["ZM Puebla-Tlaxcala"],
    "Querétaro": ["ZM Querétaro"],
    "Quintana Roo": ["ZM Cancún"],
    "San Luis Potosí": ["ZM San Luis Potosí"],
    "Sinaloa": ["ZM Culiacán", "ZM Mazatlán"],
    "Sonora": ["ZM Hermosillo"],
    "Tabasco": ["ZM Villahermosa"],
    "Tamaulipas": ["ZM Reynosa-Río Bravo", "ZM Tampico"],
    "Veracruz": ["ZM Veracruz", "ZM Xalapa"],
    "Yucatán": ["ZM Mérida"],
    "Zacatecas": ["ZM Zacatecas-Guadalupe"],
}

# Tabla en Supabase
TABLE_SHF = "iainmobiliaria_shf_price_index"


class SHFPriceIndexScraper:
    """
    Descarga y procesa los índices de precios de vivienda del SHF
    y datos complementarios de Banxico.
    Calcula tendencias, momentum y relativos al nacional.
    """

    def __init__(self, delay: float = SCRAPER_DELAY):
        self.delay = delay
        self.supabase = None
        self._init_supabase()

    def _init_supabase(self):
        """Inicializa el cliente de Supabase."""
        try:
            from supabase import create_client
            if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
                self.supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
                logger.info("Cliente Supabase inicializado correctamente")
            else:
                logger.warning("Credenciales Supabase no configuradas; solo se guardarán CSVs")
        except ImportError:
            logger.warning("Biblioteca supabase no instalada; solo se guardarán CSVs")

    # ── Descarga de datos SHF ───────────────────────────────────────────

    async def _descargar_shf(
        self, client: httpx.AsyncClient
    ) -> Optional[bytes]:
        """Descarga el archivo de índice SHF."""
        todas_urls = [SHF_INDEX_URL] + SHF_ALT_URLS

        for idx, url in enumerate(todas_urls):
            try:
                logger.info(f"Descargando índice SHF desde: {url}")
                resp = await client.get(url, timeout=120, follow_redirects=True)
                if resp.status_code == 200 and len(resp.content) > 500:
                    logger.info(f"Descarga exitosa: {len(resp.content) / 1024:.1f} KB")
                    return resp.content
                else:
                    logger.warning(f"HTTP {resp.status_code}, {len(resp.content)} bytes")
            except (httpx.TimeoutException, httpx.ConnectError, OSError) as exc:
                logger.warning(f"Error ({idx + 1}/{len(todas_urls)}): {exc}")
                await asyncio.sleep(2)

        logger.warning("No se pudo descargar archivo SHF de ninguna URL")
        return None

    # ── Descarga de datos Banxico ───────────────────────────────────────

    async def _descargar_banxico(
        self, client: httpx.AsyncClient, serie: str
    ) -> Optional[List[Dict]]:
        """
        Consulta la API SIE de Banxico para una serie específica.
        Retorna lista de observaciones {fecha, valor}.
        """
        if not BANXICO_TOKEN:
            logger.debug("Token de Banxico no configurado; omitiendo consulta API")
            return None

        url = f"{BANXICO_SIE_BASE}/{serie}/datos/2018-01-01/2026-12-31"
        headers = {
            "Bmx-Token": BANXICO_TOKEN,
            "Accept": "application/json",
        }

        try:
            resp = await client.get(url, headers=headers, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                series = data.get("bmx", {}).get("series", [])
                if series:
                    observaciones = series[0].get("datos", [])
                    logger.info(f"Banxico serie {serie}: {len(observaciones)} observaciones")
                    return observaciones
            else:
                logger.debug(f"Banxico API HTTP {resp.status_code} para serie {serie}")
        except Exception as exc:
            logger.debug(f"Error consultando Banxico: {exc}")

        return None

    # ── Procesamiento ───────────────────────────────────────────────────

    def _cargar_datos_shf(self, raw_bytes: bytes) -> pd.DataFrame:
        """Carga y procesa el archivo CSV/Excel del SHF."""
        df = None

        # Intentar como CSV
        for encoding in ["utf-8", "latin-1", "cp1252"]:
            try:
                df = pd.read_csv(BytesIO(raw_bytes), encoding=encoding)
                if len(df) > 5:
                    break
            except Exception:
                continue

        # Intentar como Excel
        if df is None or df.empty:
            try:
                df = pd.read_excel(BytesIO(raw_bytes))
            except Exception as exc:
                logger.error(f"No se pudo leer archivo SHF: {exc}")
                return pd.DataFrame()

        if df is None or df.empty:
            logger.error("Archivo SHF vacío o no legible")
            return pd.DataFrame()

        logger.info(f"Datos SHF cargados: {len(df)} registros, columnas: {list(df.columns)}")

        # Normalizar nombres de columnas
        rename_map = {}
        for c in df.columns:
            cl = c.strip().lower()
            if "entidad" in cl or "estado" in cl or "state" in cl:
                rename_map[c] = "estado"
            elif "metro" in cl or "zona" in cl or "area" in cl:
                rename_map[c] = "zona_metropolitana"
            elif "trimestre" in cl or "quarter" in cl:
                rename_map[c] = "trimestre"
            elif "año" in cl or "anio" in cl or "year" in cl:
                rename_map[c] = "anio"
            elif "indice" in cl or "index" in cl or "precio" in cl:
                rename_map[c] = "indice_precio"
            elif "variacion" in cl or "cambio" in cl or "change" in cl:
                rename_map[c] = "variacion"

        df = df.rename(columns=rename_map)

        return df

    def _procesar_datos_banxico(
        self, observaciones: List[Dict], nombre_serie: str
    ) -> pd.DataFrame:
        """Convierte observaciones de Banxico a DataFrame."""
        if not observaciones:
            return pd.DataFrame()

        registros = []
        for obs in observaciones:
            fecha_str = obs.get("fecha", "")
            valor_str = obs.get("dato", "N/E")

            if valor_str == "N/E" or not valor_str:
                continue

            try:
                valor = float(valor_str.replace(",", ""))
            except (ValueError, AttributeError):
                continue

            # Parsear fecha (formato dd/mm/yyyy de Banxico)
            try:
                fecha = datetime.strptime(fecha_str, "%d/%m/%Y")
            except ValueError:
                continue

            registros.append({
                "fecha": fecha,
                "anio": fecha.year,
                "trimestre": (fecha.month - 1) // 3 + 1,
                "indice_precio": valor,
                "serie": nombre_serie,
            })

        return pd.DataFrame(registros)

    # ── Cálculo de features derivados ───────────────────────────────────

    def calcular_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula features derivados del índice de precios:
          - price_change_qoq: cambio trimestral
          - price_change_yoy: cambio interanual
          - price_trend_1yr: tendencia anualizada
          - price_trend_3yr: crecimiento compuesto a 3 años
          - price_momentum: aceleración del cambio
          - relative_to_national: relativo al promedio nacional
        """
        if df.empty:
            return pd.DataFrame()

        # Asegurar tipos correctos
        if "indice_precio" in df.columns:
            df["indice_precio"] = pd.to_numeric(df["indice_precio"], errors="coerce")

        if "anio" in df.columns:
            df["anio"] = pd.to_numeric(df["anio"], errors="coerce")

        if "trimestre" in df.columns:
            df["trimestre"] = pd.to_numeric(df["trimestre"], errors="coerce")

        # Ordenar por estado/zona y tiempo
        cols_sort = [c for c in ["estado", "zona_metropolitana", "anio", "trimestre"]
                     if c in df.columns]
        if cols_sort:
            df = df.sort_values(cols_sort)

        # Agrupar por entidad geográfica
        cols_grupo = [c for c in ["estado", "zona_metropolitana"] if c in df.columns]
        if not cols_grupo:
            cols_grupo = ["estado"] if "estado" in df.columns else []

        if not cols_grupo or "indice_precio" not in df.columns:
            logger.warning("No se pueden calcular features sin columnas de grupo e índice")
            return df

        # Calcular cambios dentro de cada grupo
        def calcular_cambios(grupo):
            grupo = grupo.sort_values(
                [c for c in ["anio", "trimestre"] if c in grupo.columns]
            )

            # Cambio trimestral (quarter-over-quarter)
            grupo["price_change_qoq"] = (
                grupo["indice_precio"].pct_change() * 100
            ).round(2)

            # Cambio interanual (year-over-year) — comparar con 4 trimestres atrás
            grupo["price_change_yoy"] = (
                grupo["indice_precio"].pct_change(periods=4) * 100
            ).round(2)

            # Tendencia a 1 año (últimos 4 trimestres)
            if len(grupo) >= 4:
                idx_actual = grupo["indice_precio"].iloc[-1]
                idx_1yr_ago = grupo["indice_precio"].iloc[-4]
                if idx_1yr_ago > 0:
                    grupo["price_trend_1yr"] = round(
                        (idx_actual / idx_1yr_ago - 1) * 100, 2
                    )
                else:
                    grupo["price_trend_1yr"] = 0.0
            else:
                grupo["price_trend_1yr"] = np.nan

            # Tendencia a 3 años (últimos 12 trimestres)
            if len(grupo) >= 12:
                idx_actual = grupo["indice_precio"].iloc[-1]
                idx_3yr_ago = grupo["indice_precio"].iloc[-12]
                if idx_3yr_ago > 0:
                    # Crecimiento compuesto anual: ((Vf/Vi)^(1/3) - 1) * 100
                    cagr = ((idx_actual / idx_3yr_ago) ** (1 / 3) - 1) * 100
                    grupo["price_trend_3yr"] = round(cagr, 2)
                else:
                    grupo["price_trend_3yr"] = 0.0
            else:
                grupo["price_trend_3yr"] = np.nan

            # Price momentum: diferencia entre cambio YoY actual y anterior
            if len(grupo) >= 5:
                yoy_actual = grupo["price_change_yoy"].iloc[-1]
                yoy_anterior = grupo["price_change_yoy"].iloc[-2]
                if pd.notna(yoy_actual) and pd.notna(yoy_anterior):
                    momentum = yoy_actual - yoy_anterior
                    grupo["price_momentum"] = round(momentum, 2)
                else:
                    grupo["price_momentum"] = 0.0
            else:
                grupo["price_momentum"] = np.nan

            return grupo

        df = df.groupby(cols_grupo, group_keys=False).apply(calcular_cambios)

        # Relative to national: índice relativo al promedio nacional del mismo trimestre
        if "anio" in df.columns and "trimestre" in df.columns:
            promedios = (
                df.groupby(["anio", "trimestre"])["indice_precio"]
                .mean()
                .reset_index()
                .rename(columns={"indice_precio": "indice_nacional_avg"})
            )
            df = df.merge(promedios, on=["anio", "trimestre"], how="left")
            df["relative_to_national"] = (
                (df["indice_precio"] / df["indice_nacional_avg"] - 1) * 100
            ).round(2)
        else:
            df["relative_to_national"] = 0.0

        logger.info(f"Features calculados para {len(df)} registros")
        return df

    # ── Guardado ────────────────────────────────────────────────────────

    def guardar_csv(self, df: pd.DataFrame, filename: str = "shf_indice_precios.csv") -> Optional[Path]:
        """Guarda el DataFrame como CSV."""
        if df.empty:
            logger.warning("DataFrame vacío, no se guarda CSV")
            return None

        filepath = DATA_DIR / filename
        df.to_csv(filepath, index=False, encoding="utf-8-sig")
        logger.info(f"CSV guardado: {filepath} ({len(df)} registros)")
        return filepath

    def upsert_supabase(self, df: pd.DataFrame):
        """Hace upsert de los datos del índice SHF a Supabase."""
        if self.supabase is None:
            logger.warning("Supabase no disponible; omitiendo upsert")
            return

        if df.empty:
            return

        records = []
        for _, row in df.iterrows():
            record = {
                "estado": str(row.get("estado", "")).strip(),
                "zona_metropolitana": str(row.get("zona_metropolitana", "")).strip()
                    if pd.notna(row.get("zona_metropolitana")) else None,
                "anio": int(row["anio"]) if pd.notna(row.get("anio")) else None,
                "trimestre": int(row["trimestre"]) if pd.notna(row.get("trimestre")) else None,
                "indice_precio": float(row["indice_precio"])
                    if pd.notna(row.get("indice_precio")) else None,
                "price_change_qoq": float(row.get("price_change_qoq", 0))
                    if pd.notna(row.get("price_change_qoq")) else None,
                "price_change_yoy": float(row.get("price_change_yoy", 0))
                    if pd.notna(row.get("price_change_yoy")) else None,
                "price_trend_1yr": float(row.get("price_trend_1yr", 0))
                    if pd.notna(row.get("price_trend_1yr")) else None,
                "price_trend_3yr": float(row.get("price_trend_3yr", 0))
                    if pd.notna(row.get("price_trend_3yr")) else None,
                "price_momentum": float(row.get("price_momentum", 0))
                    if pd.notna(row.get("price_momentum")) else None,
                "relative_to_national": float(row.get("relative_to_national", 0))
                    if pd.notna(row.get("relative_to_national")) else None,
                "fecha_actualizacion": datetime.now().strftime("%Y-%m-%d"),
                "fuente": "SHF / Banxico",
            }
            records.append(record)

        logger.info(f"Insertando {len(records)} registros en {TABLE_SHF}...")

        batch_size = 100
        insertados = 0
        errores = 0

        for i in range(0, len(records), batch_size):
            batch = records[i : i + batch_size]
            try:
                self.supabase.table(TABLE_SHF).upsert(batch).execute()
                insertados += len(batch)
                if insertados % 500 == 0 or insertados == len(records):
                    logger.info(f"  Progreso: {insertados}/{len(records)}")
            except Exception as exc:
                errores += 1
                logger.error(f"  Error en lote {i // batch_size + 1}: {exc}")

        logger.info(f"Upsert completado: {insertados} insertados, {errores} lotes con error")

    # ── Ejecución principal ─────────────────────────────────────────────

    async def scrape(self) -> pd.DataFrame:
        """Ejecuta el proceso completo."""
        logger.info("=" * 70)
        logger.info("SHF - SCRAPER DE ÍNDICE DE PRECIOS DE VIVIENDA")
        logger.info(f"  Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        logger.info("=" * 70)

        df_final = pd.DataFrame()

        async with httpx.AsyncClient(
            headers={
                "User-Agent": SCRAPER_USER_AGENT,
                "Accept": "*/*",
            },
            follow_redirects=True,
        ) as client:

            # 1. Intentar descargar datos del sitio SHF
            logger.info("\n--- Datos del sitio SHF ---")
            raw_shf = await self._descargar_shf(client)

            if raw_shf:
                df_shf = self._cargar_datos_shf(raw_shf)
                if not df_shf.empty:
                    df_final = df_shf

            await asyncio.sleep(self.delay)

            # 2. Complementar con datos de Banxico SIE
            logger.info("\n--- Datos de Banxico SIE ---")
            dfs_banxico = []
            for nombre, serie in BANXICO_SERIES.items():
                obs = await self._descargar_banxico(client, serie)
                if obs:
                    df_serie = self._procesar_datos_banxico(obs, nombre)
                    if not df_serie.empty:
                        dfs_banxico.append(df_serie)
                await asyncio.sleep(self.delay)

            if dfs_banxico:
                df_banxico = pd.concat(dfs_banxico, ignore_index=True)
                logger.info(f"Total datos Banxico: {len(df_banxico)} registros")

                # Si no hay datos SHF directos, usar Banxico como fuente principal
                if df_final.empty:
                    df_final = df_banxico
                    df_final["estado"] = "Nacional"

        # 3. Si no se obtuvieron datos de ninguna fuente, generar estructura vacía
        if df_final.empty:
            logger.warning(
                "No se obtuvieron datos de SHF ni Banxico. "
                "Verifique URLs y tokens de API."
            )
            return pd.DataFrame()

        # 4. Calcular features
        df_features = self.calcular_features(df_final)

        # 5. Guardar
        self.guardar_csv(df_features, "shf_indice_precios.csv")
        self.upsert_supabase(df_features)

        # Resumen
        logger.info("\n" + "=" * 70)
        logger.info("RESUMEN - SHF Índice de Precios")
        logger.info("=" * 70)
        logger.info(f"  Registros totales: {len(df_features)}")

        if "estado" in df_features.columns:
            estados = df_features["estado"].nunique()
            logger.info(f"  Estados/Zonas: {estados}")

        if "price_trend_1yr" in df_features.columns:
            trend_avg = df_features["price_trend_1yr"].dropna().mean()
            logger.info(f"  Tendencia 1 año promedio: {trend_avg:.2f}%")

        if "price_momentum" in df_features.columns:
            mom_avg = df_features["price_momentum"].dropna().mean()
            logger.info(f"  Momentum promedio: {mom_avg:.2f}")

        if "relative_to_national" in df_features.columns:
            rel_max = df_features["relative_to_national"].dropna().max()
            rel_min = df_features["relative_to_national"].dropna().min()
            logger.info(
                f"  Relativo al nacional: min={rel_min:.1f}%, max={rel_max:.1f}%"
            )

        logger.info("=" * 70)

        return df_features


# ── Punto de entrada ────────────────────────────────────────────────────────

def main():
    """Ejecuta el scraper de SHF Price Index."""
    scraper = SHFPriceIndexScraper()
    asyncio.run(scraper.scrape())


if __name__ == "__main__":
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level:<8}</level> | <level>{message}</level>",
        level="INFO",
    )
    main()
