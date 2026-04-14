"""
Scraper del Índice de Marginación de CONAPO
(Consejo Nacional de Población)

Descarga y procesa los índices de marginación a nivel municipal y AGEB
publicados por CONAPO con datos del Censo 2020.

Fuentes:
- https://www.gob.mx/conapo/documentos/indices-de-marginacion-2020-284372
- Archivos Excel/CSV con índices a nivel municipal y AGEB

Tabla destino: iainmobiliaria_conapo_marginacion
"""

import asyncio
import os
import sys
import tempfile
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

try:
    from tenacity import retry, stop_after_attempt, wait_exponential
except ImportError:
    # Fallback si tenacity no está disponible
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

# URLs de descarga de CONAPO (índices de marginación 2020)
# Los archivos se publican en formato Excel en la página de CONAPO
CONAPO_MUNICIPAL_URL = (
    "https://www.gob.mx/cms/uploads/attachment/file/685354/"
    "IMM_2020.csv"
)
CONAPO_AGEB_URL = (
    "https://www.gob.mx/cms/uploads/attachment/file/685360/"
    "IMA_2020.csv"
)

# URLs alternativas (a veces CONAPO cambia la ubicación)
CONAPO_MUNICIPAL_ALT_URLS = [
    "https://raw.githubusercontent.com/conapo-datos/marginacion/main/datos/IMM_2020.csv",
    "https://www.gob.mx/cms/uploads/attachment/file/835461/IMM_2020.csv",
]
CONAPO_AGEB_ALT_URLS = [
    "https://raw.githubusercontent.com/conapo-datos/marginacion/main/datos/IMA_2020.csv",
    "https://www.gob.mx/cms/uploads/attachment/file/835462/IMA_2020.csv",
]

# Mapeo de grado de marginación a valor numérico (0-100, donde 100 = menor marginación)
GRADO_A_SCORE: Dict[str, float] = {
    "Muy alto": 10.0,
    "Alto": 30.0,
    "Medio": 50.0,
    "Bajo": 70.0,
    "Muy bajo": 90.0,
}

# Nombres esperados de columnas del CSV municipal de CONAPO
# (pueden variar entre publicaciones, se normalizan al cargar)
COLS_MUNICIPAL = {
    "CVE_ENT": "cve_ent",
    "NOM_ENT": "nom_ent",
    "CVE_MUN": "cve_mun",
    "NOM_MUN": "nom_mun",
    "POB_TOT": "pob_tot",
    "IM_2020": "indice_marginacion",
    "GM_2020": "grado_marginacion",
    "IMN_2020": "indice_marginacion_normalizado",
}

COLS_AGEB = {
    "CVE_ENT": "cve_ent",
    "NOM_ENT": "nom_ent",
    "CVE_MUN": "cve_mun",
    "NOM_MUN": "nom_mun",
    "CVE_LOC": "cve_loc",
    "CVE_AGEB": "cve_ageb",
    "POB_TOT": "pob_tot",
    "IM_2020": "indice_marginacion",
    "GM_2020": "grado_marginacion",
}

# Tabla en Supabase
TABLE_CONAPO = "iainmobiliaria_conapo_marginacion"


class CONAPOMarginacionScraper:
    """
    Descarga y procesa los índices de marginación publicados por CONAPO.
    Genera archivos CSV y hace upsert a Supabase.
    """

    def __init__(self, delay: float = SCRAPER_DELAY):
        self.delay = delay
        self.supabase = None
        self._init_supabase()

    def _init_supabase(self):
        """Inicializa el cliente de Supabase si las credenciales existen."""
        try:
            from supabase import create_client
            if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
                self.supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
                logger.info("Cliente Supabase inicializado correctamente")
            else:
                logger.warning("Credenciales de Supabase no configuradas; solo se guardarán CSVs")
        except ImportError:
            logger.warning("Biblioteca supabase no instalada; solo se guardarán CSVs")

    # ── Descarga de archivos ────────────────────────────────────────────

    async def _descargar_archivo(
        self,
        client: httpx.AsyncClient,
        url: str,
        alt_urls: Optional[List[str]] = None,
        descripcion: str = "archivo",
    ) -> Optional[bytes]:
        """
        Descarga un archivo desde la URL principal; si falla, prueba las alternativas.
        Retorna los bytes del archivo o None si todas fallan.
        """
        todas_urls = [url] + (alt_urls or [])

        for idx, u in enumerate(todas_urls):
            try:
                logger.info(f"Descargando {descripcion} desde: {u}")
                resp = await client.get(u, timeout=120, follow_redirects=True)
                if resp.status_code == 200 and len(resp.content) > 1000:
                    logger.info(
                        f"Descarga exitosa: {len(resp.content) / 1024:.1f} KB"
                    )
                    return resp.content
                else:
                    logger.warning(
                        f"Respuesta inesperada (HTTP {resp.status_code}, "
                        f"{len(resp.content)} bytes) — intentando siguiente URL"
                    )
            except (httpx.TimeoutException, httpx.ConnectError, OSError) as exc:
                logger.warning(f"Error de conexión ({idx + 1}/{len(todas_urls)}): {exc}")
                await asyncio.sleep(2)

        logger.error(f"No se pudo descargar {descripcion} de ninguna URL")
        return None

    # ── Procesamiento de datos ──────────────────────────────────────────

    @staticmethod
    def calcular_score_marginacion(indice: float, grado: str) -> float:
        """
        Calcula un puntaje numérico de 0-100 a partir del índice de marginación.
        100 = menor marginación (mejor condición socioeconómica).
        0 = mayor marginación.

        Combina el grado textual con el índice numérico para mayor precisión.
        """
        # Si tenemos grado textual, usarlo como base
        base_score = GRADO_A_SCORE.get(str(grado).strip(), 50.0)

        # Ajustar con el índice numérico (típicamente entre -2 y +4)
        # Normalizar a rango 0-100: menor índice = menor marginación = mayor score
        try:
            idx_float = float(indice)
            # El índice de marginación de CONAPO va aprox de -1.8 a +4.5
            # Normalizamos: -1.8 -> 100, +4.5 -> 0
            idx_min, idx_max = -1.8, 4.5
            idx_clamped = max(idx_min, min(idx_max, idx_float))
            idx_score = 100.0 * (1.0 - (idx_clamped - idx_min) / (idx_max - idx_min))
            # Promediar con score basado en grado
            return round((base_score + idx_score) / 2.0, 2)
        except (ValueError, TypeError):
            return base_score

    def _normalizar_columnas(self, df: pd.DataFrame, mapeo: Dict[str, str]) -> pd.DataFrame:
        """Normaliza nombres de columnas del DataFrame según el mapeo."""
        # Primero intentar mapeo directo
        rename_map = {}
        cols_upper = {c.upper().strip(): c for c in df.columns}

        for orig, nuevo in mapeo.items():
            # Buscar coincidencia exacta o case-insensitive
            if orig in df.columns:
                rename_map[orig] = nuevo
            elif orig.upper() in cols_upper:
                rename_map[cols_upper[orig.upper()]] = nuevo

        if rename_map:
            df = df.rename(columns=rename_map)

        return df

    def _procesar_municipal(self, raw_bytes: bytes) -> pd.DataFrame:
        """Procesa el archivo CSV/Excel de marginación municipal."""
        # Intentar leer como CSV primero, luego como Excel
        df = None
        for encoding in ["utf-8", "latin-1", "cp1252"]:
            try:
                from io import BytesIO
                df = pd.read_csv(BytesIO(raw_bytes), encoding=encoding)
                if len(df) > 10:
                    break
            except Exception:
                continue

        if df is None or df.empty:
            try:
                from io import BytesIO
                df = pd.read_excel(BytesIO(raw_bytes))
            except Exception as exc:
                logger.error(f"No se pudo leer archivo municipal: {exc}")
                return pd.DataFrame()

        logger.info(f"Archivo municipal cargado: {len(df)} registros, columnas: {list(df.columns)}")

        # Normalizar columnas
        df = self._normalizar_columnas(df, COLS_MUNICIPAL)

        # Calcular score numérico
        if "indice_marginacion" in df.columns and "grado_marginacion" in df.columns:
            df["marginacion_score"] = df.apply(
                lambda row: self.calcular_score_marginacion(
                    row.get("indice_marginacion", 0),
                    row.get("grado_marginacion", "Medio"),
                ),
                axis=1,
            )
        else:
            logger.warning(
                "Columnas de índice/grado no encontradas. "
                f"Columnas disponibles: {list(df.columns)}"
            )

        # Agregar metadatos
        df["nivel"] = "municipal"
        df["fecha_actualizacion"] = datetime.now().strftime("%Y-%m-%d")
        df["fuente"] = "CONAPO Índice de Marginación 2020"

        return df

    def _procesar_ageb(self, raw_bytes: bytes) -> pd.DataFrame:
        """Procesa el archivo CSV/Excel de marginación a nivel AGEB."""
        df = None
        for encoding in ["utf-8", "latin-1", "cp1252"]:
            try:
                from io import BytesIO
                df = pd.read_csv(BytesIO(raw_bytes), encoding=encoding)
                if len(df) > 10:
                    break
            except Exception:
                continue

        if df is None or df.empty:
            try:
                from io import BytesIO
                df = pd.read_excel(BytesIO(raw_bytes))
            except Exception as exc:
                logger.error(f"No se pudo leer archivo AGEB: {exc}")
                return pd.DataFrame()

        logger.info(f"Archivo AGEB cargado: {len(df)} registros, columnas: {list(df.columns)}")

        df = self._normalizar_columnas(df, COLS_AGEB)

        if "indice_marginacion" in df.columns and "grado_marginacion" in df.columns:
            df["marginacion_score"] = df.apply(
                lambda row: self.calcular_score_marginacion(
                    row.get("indice_marginacion", 0),
                    row.get("grado_marginacion", "Medio"),
                ),
                axis=1,
            )

        df["nivel"] = "ageb"
        df["fecha_actualizacion"] = datetime.now().strftime("%Y-%m-%d")
        df["fuente"] = "CONAPO Índice de Marginación 2020"

        return df

    # ── Guardado ────────────────────────────────────────────────────────

    def guardar_csv(
        self, df: pd.DataFrame, filename: str
    ) -> Optional[Path]:
        """Guarda DataFrame como CSV en DATA_DIR."""
        if df.empty:
            logger.warning(f"DataFrame vacío, no se guarda {filename}")
            return None

        filepath = DATA_DIR / filename
        df.to_csv(filepath, index=False, encoding="utf-8-sig")
        logger.info(f"CSV guardado: {filepath} ({len(df)} registros)")
        return filepath

    def upsert_supabase(self, df: pd.DataFrame, nivel: str = "municipal"):
        """
        Hace upsert de los datos a la tabla iainmobiliaria_conapo_marginacion.
        Usa cve_mun (o cve_ageb) como clave para evitar duplicados.
        """
        if self.supabase is None:
            logger.warning("Supabase no disponible; omitiendo upsert")
            return

        if df.empty:
            logger.warning("DataFrame vacío; omitiendo upsert")
            return

        # Preparar registros para Supabase
        records = []
        for _, row in df.iterrows():
            record = {
                "cve_ent": str(row.get("cve_ent", "")).strip(),
                "nom_ent": str(row.get("nom_ent", "")).strip(),
                "cve_mun": str(row.get("cve_mun", "")).strip(),
                "nom_mun": str(row.get("nom_mun", "")).strip(),
                "nivel": nivel,
                "indice_marginacion": float(row["indice_marginacion"])
                    if pd.notna(row.get("indice_marginacion")) else None,
                "grado_marginacion": str(row.get("grado_marginacion", "")).strip(),
                "marginacion_score": float(row["marginacion_score"])
                    if pd.notna(row.get("marginacion_score")) else None,
                "poblacion_total": int(row["pob_tot"])
                    if pd.notna(row.get("pob_tot")) else None,
                "fecha_actualizacion": datetime.now().strftime("%Y-%m-%d"),
                "fuente": "CONAPO 2020",
            }

            # Agregar clave AGEB si aplica
            if nivel == "ageb":
                record["cve_ageb"] = str(row.get("cve_ageb", "")).strip()
                record["cve_loc"] = str(row.get("cve_loc", "")).strip()

            records.append(record)

        logger.info(f"Insertando {len(records)} registros ({nivel}) en {TABLE_CONAPO}...")

        batch_size = 100
        insertados = 0
        errores = 0

        for i in range(0, len(records), batch_size):
            batch = records[i : i + batch_size]
            try:
                self.supabase.table(TABLE_CONAPO).upsert(batch).execute()
                insertados += len(batch)
                if insertados % 500 == 0 or insertados == len(records):
                    logger.info(f"  Progreso: {insertados}/{len(records)}")
            except Exception as exc:
                errores += 1
                logger.error(f"  Error en lote {i // batch_size + 1}: {exc}")

        logger.info(
            f"Upsert completado: {insertados} insertados, {errores} lotes con error"
        )

    # ── Ejecución principal ─────────────────────────────────────────────

    async def scrape(self):
        """Ejecuta el proceso completo de descarga y procesamiento."""
        logger.info("=" * 70)
        logger.info("CONAPO - SCRAPER DE ÍNDICES DE MARGINACIÓN")
        logger.info(f"  Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        logger.info("=" * 70)

        async with httpx.AsyncClient(
            headers={
                "User-Agent": SCRAPER_USER_AGENT,
                "Accept": "*/*",
            },
            follow_redirects=True,
        ) as client:

            # 1. Descargar datos municipales
            logger.info("\n--- Datos a nivel MUNICIPAL ---")
            raw_municipal = await self._descargar_archivo(
                client,
                CONAPO_MUNICIPAL_URL,
                alt_urls=CONAPO_MUNICIPAL_ALT_URLS,
                descripcion="índice municipal",
            )

            df_municipal = pd.DataFrame()
            if raw_municipal:
                df_municipal = self._procesar_municipal(raw_municipal)
                self.guardar_csv(df_municipal, "conapo_marginacion_municipio.csv")
                self.upsert_supabase(df_municipal, nivel="municipal")
            else:
                logger.error("No se pudieron obtener datos municipales de CONAPO")

            await asyncio.sleep(self.delay)

            # 2. Descargar datos a nivel AGEB
            logger.info("\n--- Datos a nivel AGEB ---")
            raw_ageb = await self._descargar_archivo(
                client,
                CONAPO_AGEB_URL,
                alt_urls=CONAPO_AGEB_ALT_URLS,
                descripcion="índice AGEB",
            )

            df_ageb = pd.DataFrame()
            if raw_ageb:
                df_ageb = self._procesar_ageb(raw_ageb)
                self.guardar_csv(df_ageb, "conapo_marginacion_ageb.csv")
                self.upsert_supabase(df_ageb, nivel="ageb")
            else:
                logger.error("No se pudieron obtener datos AGEB de CONAPO")

        # Resumen
        logger.info("\n" + "=" * 70)
        logger.info("RESUMEN - CONAPO Marginación")
        logger.info("=" * 70)
        logger.info(f"  Registros municipales: {len(df_municipal)}")
        logger.info(f"  Registros AGEB: {len(df_ageb)}")

        if not df_municipal.empty and "grado_marginacion" in df_municipal.columns:
            dist = df_municipal["grado_marginacion"].value_counts()
            logger.info("  Distribución por grado (municipal):")
            for grado, count in dist.items():
                logger.info(f"    {grado}: {count}")

        logger.info("=" * 70)

        return df_municipal, df_ageb


# ── Punto de entrada ────────────────────────────────────────────────────────

def main():
    """Ejecuta el scraper de CONAPO Marginación."""
    scraper = CONAPOMarginacionScraper()
    asyncio.run(scraper.scrape())


if __name__ == "__main__":
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level:<8}</level> | <level>{message}</level>",
        level="INFO",
    )
    main()
