"""
Scraper de Incidencia Delictiva del SESNSP
(Secretariado Ejecutivo del Sistema Nacional de Seguridad Pública)

Descarga y procesa las cifras de incidencia delictiva municipal publicadas
por el SESNSP con datos mensuales desde 2015 al presente.

Fuente:
- https://www.gob.mx/sesnsp/acciones-y-programas/datos-abiertos-de-incidencia-delictiva
- Archivo: "Cifras de Incidencia Delictiva Municipal"

Features derivados:
  - homicide_rate_per_100k: tasa de homicidios por cada 100,000 habitantes
  - robbery_rate_per_100k: tasa de robos por cada 100,000 habitantes
  - total_crime_rate: tasa total de delitos
  - crime_trend_12m: tendencia 'improving' / 'stable' / 'worsening'
  - safety_score: 0-100 normalizado (100 = más seguro)

Tabla destino: iainmobiliaria_crime_stats
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

# URL de descarga del CSV de incidencia delictiva municipal del SESNSP
# El SESNSP publica archivos CSV actualizados periódicamente
SESNSP_MUNICIPAL_URL = (
    "https://www.gob.mx/cms/uploads/attachment/file/941312/"
    "Municipal-Delitos-2015-2024_oct2024.csv"
)

# URLs alternativas (el SESNSP actualiza la URL con cada publicación)
SESNSP_ALT_URLS = [
    "https://www.gob.mx/cms/uploads/attachment/file/885496/Municipal-Delitos-2015-2024_jun2024.csv",
    "https://www.gob.mx/cms/uploads/attachment/file/868192/Municipal-Delitos-2015-2024_mar2024.csv",
]

# Meses del año en español (como aparecen en las columnas del CSV del SESNSP)
MESES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]

# Mapeo de tipos de delito a categorías agregadas
CATEGORIAS_DELITO: Dict[str, List[str]] = {
    "homicidio": [
        "Homicidio doloso",
        "Homicidio culposo",
        "Feminicidio",
    ],
    "robo": [
        "Robo a casa habitación",
        "Robo a negocio",
        "Robo a transeúnte",
        "Robo de vehículo automotor",
        "Robo a transporte público",
        "Robo en transporte público",
    ],
    "violencia_familiar": [
        "Violencia familiar",
        "Violencia de género en todas sus modalidades distinta a la violencia familiar",
    ],
    "extorsion": [
        "Extorsión",
    ],
    "secuestro": [
        "Secuestro",
    ],
    "fraude": [
        "Fraude",
    ],
    "narcomenudeo": [
        "Narcomenudeo",
    ],
}

# Poblaciones estimadas por municipio (CONAPO 2024, aprox.)
# Se usa para calcular tasas per cápita
# En producción, estos datos se cruzarían con la tabla de CONAPO
POBLACION_MUNICIPIOS_APROX: Dict[str, int] = {
    # Formato: "CVE_ENT-CVE_MUN": población
    # Principales municipios
    "09-015": 1_815_000,  # CDMX - Cuauhtémoc (aprox delegación)
    "14-039": 1_385_000,  # Guadalajara
    "14-120": 1_476_000,  # Zapopan
    "19-039": 1_142_000,  # Monterrey
    "21-114": 1_692_000,  # Puebla
    "22-014": 1_049_000,  # Querétaro
    "23-005": 888_000,    # Benito Juárez (Cancún)
    "31-050": 995_000,    # Mérida
    "02-004": 1_922_000,  # Tijuana
    "11-020": 1_500_000,  # León
}

# Tabla en Supabase
TABLE_CRIME = "iainmobiliaria_crime_stats"


class SESNSPCrimeScraper:
    """
    Descarga y procesa datos de incidencia delictiva del SESNSP.
    Calcula tasas, tendencias y un safety_score por municipio.
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

    # ── Descarga ────────────────────────────────────────────────────────

    async def _descargar_csv(
        self,
        client: httpx.AsyncClient,
    ) -> Optional[bytes]:
        """
        Descarga el CSV de incidencia delictiva municipal del SESNSP.
        Intenta la URL principal y luego las alternativas.
        """
        todas_urls = [SESNSP_MUNICIPAL_URL] + SESNSP_ALT_URLS

        for idx, url in enumerate(todas_urls):
            try:
                logger.info(f"Descargando datos SESNSP desde: {url}")
                resp = await client.get(url, timeout=180, follow_redirects=True)
                if resp.status_code == 200 and len(resp.content) > 10000:
                    logger.info(
                        f"Descarga exitosa: {len(resp.content) / (1024 * 1024):.1f} MB"
                    )
                    return resp.content
                else:
                    logger.warning(
                        f"Respuesta inesperada (HTTP {resp.status_code}, "
                        f"{len(resp.content)} bytes)"
                    )
            except (httpx.TimeoutException, httpx.ConnectError, OSError) as exc:
                logger.warning(f"Error de conexión ({idx + 1}/{len(todas_urls)}): {exc}")
                await asyncio.sleep(3)

        logger.error("No se pudo descargar el CSV del SESNSP de ninguna URL")
        return None

    # ── Procesamiento ───────────────────────────────────────────────────

    def _cargar_csv(self, raw_bytes: bytes) -> pd.DataFrame:
        """Carga el CSV del SESNSP manejando diferentes encodings."""
        for encoding in ["utf-8", "latin-1", "cp1252"]:
            try:
                df = pd.read_csv(BytesIO(raw_bytes), encoding=encoding, low_memory=False)
                if len(df) > 100:
                    logger.info(f"CSV cargado: {len(df)} registros, {len(df.columns)} columnas")
                    logger.info(f"Columnas: {list(df.columns[:15])}...")
                    return df
            except Exception:
                continue

        logger.error("No se pudo leer el CSV con ningún encoding")
        return pd.DataFrame()

    def _extraer_conteos_mensuales(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        El CSV del SESNSP tiene una columna por cada mes.
        Esta función transforma los datos a formato largo (tidy).
        Columnas esperadas: Año, Clave_Ent, Entidad, Cve. Municipio,
        Municipio, Bien jurídico afectado, Tipo de delito, Subtipo de delito,
        Modalidad, Enero, Febrero, ..., Diciembre
        """
        # Identificar columnas de meses
        cols_meses = [c for c in df.columns if c.strip() in MESES]
        if not cols_meses:
            # Intentar con nombres en minúsculas
            cols_meses = [c for c in df.columns if c.strip().capitalize() in MESES]

        if not cols_meses:
            logger.error(f"No se encontraron columnas de meses. Columnas: {list(df.columns)}")
            return pd.DataFrame()

        # Columnas de identificación (no son meses)
        cols_id = [c for c in df.columns if c not in cols_meses]

        # Normalizar nombres de columnas de identificación
        rename_map = {}
        for c in cols_id:
            cl = c.strip().lower()
            if "clave_ent" in cl or "cve_ent" in cl:
                rename_map[c] = "cve_ent"
            elif "entidad" in cl:
                rename_map[c] = "entidad"
            elif "cve" in cl and "mun" in cl:
                rename_map[c] = "cve_mun"
            elif "municipio" in cl:
                rename_map[c] = "municipio"
            elif cl == "año" or cl == "anio" or cl == "year":
                rename_map[c] = "anio"
            elif "tipo de delito" in cl:
                rename_map[c] = "tipo_delito"
            elif "subtipo" in cl:
                rename_map[c] = "subtipo_delito"
            elif "bien" in cl and "jurídico" in cl.replace("juridico", "jurídico"):
                rename_map[c] = "bien_juridico"
            elif "modalidad" in cl:
                rename_map[c] = "modalidad"

        df = df.rename(columns=rename_map)

        # Convertir conteos de meses a numérico
        for col in cols_meses:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

        # Melt: de ancho a largo
        cols_id_final = [c for c in df.columns if c not in cols_meses]
        df_long = df.melt(
            id_vars=cols_id_final,
            value_vars=cols_meses,
            var_name="mes_nombre",
            value_name="conteo",
        )

        # Agregar número de mes
        mes_a_num = {m: i + 1 for i, m in enumerate(MESES)}
        df_long["mes"] = df_long["mes_nombre"].str.strip().str.capitalize().map(mes_a_num)

        logger.info(f"Datos en formato largo: {len(df_long)} registros")
        return df_long

    def _agregar_por_municipio(self, df_long: pd.DataFrame) -> pd.DataFrame:
        """
        Agrega los conteos por municipio, año y tipo de delito.
        Calcula totales anuales y tasas.
        """
        if df_long.empty:
            return pd.DataFrame()

        # Clasificar delitos en categorías
        def clasificar_delito(tipo: str) -> str:
            tipo_str = str(tipo).strip()
            for categoria, patrones in CATEGORIAS_DELITO.items():
                for patron in patrones:
                    if patron.lower() in tipo_str.lower():
                        return categoria
            return "otros"

        col_tipo = "tipo_delito" if "tipo_delito" in df_long.columns else "subtipo_delito"
        if col_tipo not in df_long.columns:
            # Usar la primera columna que parezca contener tipos de delito
            for c in df_long.columns:
                if "delito" in c.lower() or "tipo" in c.lower():
                    col_tipo = c
                    break

        if col_tipo in df_long.columns:
            df_long["categoria_delito"] = df_long[col_tipo].apply(clasificar_delito)
        else:
            df_long["categoria_delito"] = "otros"

        # Agregar por entidad + municipio + año + categoría
        cols_grupo = ["cve_ent", "entidad", "cve_mun", "municipio", "anio", "categoria_delito"]
        cols_grupo = [c for c in cols_grupo if c in df_long.columns]

        if not cols_grupo:
            logger.error("No se encontraron columnas de agrupación")
            return pd.DataFrame()

        df_agg = (
            df_long.groupby(cols_grupo, as_index=False)["conteo"]
            .sum()
            .rename(columns={"conteo": "total_anual"})
        )

        logger.info(f"Datos agregados: {len(df_agg)} registros")
        return df_agg

    # ── Cálculo de features derivados ───────────────────────────────────

    def calcular_features(self, df_agg: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula features derivados por municipio:
          - homicide_rate_per_100k
          - robbery_rate_per_100k
          - total_crime_rate
          - crime_trend_12m
          - safety_score (0-100)
        """
        if df_agg.empty:
            return pd.DataFrame()

        # Pivotar categorías a columnas
        cols_pivot = ["cve_ent", "entidad", "cve_mun", "municipio", "anio"]
        cols_pivot = [c for c in cols_pivot if c in df_agg.columns]

        if "categoria_delito" not in df_agg.columns:
            logger.error("Columna 'categoria_delito' no encontrada")
            return pd.DataFrame()

        df_pivot = df_agg.pivot_table(
            index=cols_pivot,
            columns="categoria_delito",
            values="total_anual",
            aggfunc="sum",
            fill_value=0,
        ).reset_index()

        # Aplanar nombres de columnas
        df_pivot.columns = [
            c if isinstance(c, str) else "_".join(str(x) for x in c).strip("_")
            for c in df_pivot.columns
        ]

        # Calcular total de delitos
        categorias_cols = [c for c in df_pivot.columns if c in CATEGORIAS_DELITO or c == "otros"]
        df_pivot["total_delitos"] = df_pivot[categorias_cols].sum(axis=1)

        # Estimar población (usar lookup o default)
        def obtener_poblacion(row):
            cve = f"{str(row.get('cve_ent', '')).zfill(2)}-{str(row.get('cve_mun', '')).zfill(3)}"
            return POBLACION_MUNICIPIOS_APROX.get(cve, 500_000)

        df_pivot["poblacion_est"] = df_pivot.apply(obtener_poblacion, axis=1)

        # Tasas por 100k habitantes
        factor = 100_000
        if "homicidio" in df_pivot.columns:
            df_pivot["homicide_rate_per_100k"] = (
                df_pivot["homicidio"] / df_pivot["poblacion_est"] * factor
            ).round(2)
        else:
            df_pivot["homicide_rate_per_100k"] = 0.0

        if "robo" in df_pivot.columns:
            df_pivot["robbery_rate_per_100k"] = (
                df_pivot["robo"] / df_pivot["poblacion_est"] * factor
            ).round(2)
        else:
            df_pivot["robbery_rate_per_100k"] = 0.0

        df_pivot["total_crime_rate"] = (
            df_pivot["total_delitos"] / df_pivot["poblacion_est"] * factor
        ).round(2)

        # Tendencia de 12 meses: comparar último año vs año anterior
        # Agrupamos por municipio y calculamos cambio porcentual
        df_pivot = df_pivot.sort_values(cols_pivot)

        def calcular_tendencia(grupo):
            """Compara los últimos 2 años disponibles para determinar tendencia."""
            if len(grupo) < 2:
                return "stable"
            ultimos_2 = grupo.sort_values("anio").tail(2)
            if len(ultimos_2) < 2:
                return "stable"
            anterior = ultimos_2.iloc[0]["total_delitos"]
            actual = ultimos_2.iloc[1]["total_delitos"]
            if anterior == 0:
                return "stable"
            cambio_pct = (actual - anterior) / anterior * 100
            if cambio_pct < -5:
                return "improving"
            elif cambio_pct > 5:
                return "worsening"
            else:
                return "stable"

        cols_mun = [c for c in ["cve_ent", "cve_mun", "municipio"] if c in df_pivot.columns]
        if cols_mun:
            tendencias = (
                df_pivot.groupby(cols_mun)
                .apply(calcular_tendencia, include_groups=False)
                .reset_index()
                .rename(columns={0: "crime_trend_12m"})
            )
            df_pivot = df_pivot.merge(tendencias, on=cols_mun, how="left")
        else:
            df_pivot["crime_trend_12m"] = "stable"

        # Safety score (0-100, donde 100 = más seguro)
        # Basado en el total_crime_rate: menor tasa = mayor score
        if "total_crime_rate" in df_pivot.columns and not df_pivot["total_crime_rate"].empty:
            max_rate = df_pivot["total_crime_rate"].quantile(0.95)  # Usar percentil 95 como máximo
            if max_rate > 0:
                df_pivot["safety_score"] = (
                    100 * (1 - df_pivot["total_crime_rate"].clip(0, max_rate) / max_rate)
                ).round(1)
            else:
                df_pivot["safety_score"] = 50.0
        else:
            df_pivot["safety_score"] = 50.0

        # Filtrar solo el año más reciente para el output final
        if "anio" in df_pivot.columns:
            anio_max = df_pivot["anio"].max()
            df_reciente = df_pivot[df_pivot["anio"] == anio_max].copy()
            logger.info(f"Datos filtrados al año más reciente: {anio_max}")
        else:
            df_reciente = df_pivot.copy()

        logger.info(f"Features calculados para {len(df_reciente)} municipios")
        return df_reciente

    # ── Guardado ────────────────────────────────────────────────────────

    def guardar_csv(self, df: pd.DataFrame, filename: str = "sesnsp_incidencia_municipal.csv") -> Optional[Path]:
        """Guarda el DataFrame como CSV."""
        if df.empty:
            logger.warning("DataFrame vacío, no se guarda CSV")
            return None

        filepath = DATA_DIR / filename
        df.to_csv(filepath, index=False, encoding="utf-8-sig")
        logger.info(f"CSV guardado: {filepath} ({len(df)} registros)")
        return filepath

    def upsert_supabase(self, df: pd.DataFrame):
        """Hace upsert de los datos de criminalidad a Supabase."""
        if self.supabase is None:
            logger.warning("Supabase no disponible; omitiendo upsert")
            return

        if df.empty:
            return

        records = []
        for _, row in df.iterrows():
            record = {
                "cve_ent": str(row.get("cve_ent", "")).strip(),
                "entidad": str(row.get("entidad", "")).strip(),
                "cve_mun": str(row.get("cve_mun", "")).strip(),
                "municipio": str(row.get("municipio", "")).strip(),
                "anio": int(row["anio"]) if pd.notna(row.get("anio")) else None,
                "total_delitos": int(row["total_delitos"]) if pd.notna(row.get("total_delitos")) else 0,
                "homicide_rate_per_100k": float(row.get("homicide_rate_per_100k", 0)),
                "robbery_rate_per_100k": float(row.get("robbery_rate_per_100k", 0)),
                "total_crime_rate": float(row.get("total_crime_rate", 0)),
                "crime_trend_12m": str(row.get("crime_trend_12m", "stable")),
                "safety_score": float(row.get("safety_score", 50)),
                "fecha_actualizacion": datetime.now().strftime("%Y-%m-%d"),
                "fuente": "SESNSP",
            }
            records.append(record)

        logger.info(f"Insertando {len(records)} registros en {TABLE_CRIME}...")

        batch_size = 100
        insertados = 0
        errores = 0

        for i in range(0, len(records), batch_size):
            batch = records[i : i + batch_size]
            try:
                self.supabase.table(TABLE_CRIME).upsert(batch).execute()
                insertados += len(batch)
                if insertados % 500 == 0 or insertados == len(records):
                    logger.info(f"  Progreso: {insertados}/{len(records)}")
            except Exception as exc:
                errores += 1
                logger.error(f"  Error en lote {i // batch_size + 1}: {exc}")

        logger.info(f"Upsert completado: {insertados} insertados, {errores} lotes con error")

    # ── Ejecución principal ─────────────────────────────────────────────

    async def scrape(self) -> pd.DataFrame:
        """Ejecuta el proceso completo de descarga, procesamiento y guardado."""
        logger.info("=" * 70)
        logger.info("SESNSP - SCRAPER DE INCIDENCIA DELICTIVA")
        logger.info(f"  Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        logger.info("=" * 70)

        async with httpx.AsyncClient(
            headers={
                "User-Agent": SCRAPER_USER_AGENT,
                "Accept": "*/*",
            },
            follow_redirects=True,
        ) as client:
            raw_bytes = await self._descargar_csv(client)

        if raw_bytes is None:
            logger.error("No se pudo obtener datos del SESNSP")
            return pd.DataFrame()

        # 1. Cargar CSV
        df_raw = self._cargar_csv(raw_bytes)
        if df_raw.empty:
            return pd.DataFrame()

        # 2. Extraer conteos mensuales (formato largo)
        df_long = self._extraer_conteos_mensuales(df_raw)
        if df_long.empty:
            return pd.DataFrame()

        # 3. Agregar por municipio
        df_agg = self._agregar_por_municipio(df_long)

        # 4. Calcular features
        df_features = self.calcular_features(df_agg)

        # 5. Guardar
        self.guardar_csv(df_features, "sesnsp_incidencia_municipal.csv")
        self.upsert_supabase(df_features)

        # Resumen
        logger.info("\n" + "=" * 70)
        logger.info("RESUMEN - SESNSP Incidencia Delictiva")
        logger.info("=" * 70)
        logger.info(f"  Municipios procesados: {len(df_features)}")

        if "safety_score" in df_features.columns:
            logger.info(f"  Safety score promedio: {df_features['safety_score'].mean():.1f}")
            logger.info(f"  Safety score mínimo: {df_features['safety_score'].min():.1f}")
            logger.info(f"  Safety score máximo: {df_features['safety_score'].max():.1f}")

        if "crime_trend_12m" in df_features.columns:
            tendencias = df_features["crime_trend_12m"].value_counts()
            logger.info("  Tendencias:")
            for tendencia, count in tendencias.items():
                logger.info(f"    {tendencia}: {count} municipios")

        logger.info("=" * 70)

        return df_features


# ── Punto de entrada ────────────────────────────────────────────────────────

def main():
    """Ejecuta el scraper de SESNSP."""
    scraper = SESNSPCrimeScraper()
    asyncio.run(scraper.scrape())


if __name__ == "__main__":
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level:<8}</level> | <level>{message}</level>",
        level="INFO",
    )
    main()
