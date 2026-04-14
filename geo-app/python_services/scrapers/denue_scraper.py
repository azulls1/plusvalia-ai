"""
Scraper de DENUE (Directorio Estadístico Nacional de Unidades Económicas)
Fuente: INEGI - https://www.inegi.org.mx/app/descarga/?ti=6

Descarga y procesa los datos del DENUE para extraer unidades económicas
por categoría SCIAN (NAICS mexicano), filtrar las relevantes para el
análisis inmobiliario, y calcular features de densidad de amenidades.

Categorías clave (códigos SCIAN):
  46xxxx  Comercio al por menor (supermercados, tiendas)
  52xxxx  Servicios financieros (bancos, cajeros)
  61xxxx  Servicios educativos (escuelas, universidades)
  62xxxx  Servicios de salud (hospitales, clínicas)
  72xxxx  Alojamiento y alimentos (restaurantes, hoteles)
  93xxxx  Actividades gubernamentales

Tabla destino (Supabase): No se hace upsert directo; el CSV resultante
se integra vía el pipeline de features del modelo ML.
"""

import asyncio
import math
import os
import sys
from datetime import datetime
from io import BytesIO
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
    def retry(**kwargs):
        def decorator(func):
            return func
        return decorator
    stop_after_attempt = lambda n: None
    wait_exponential = lambda **kw: None

from config import (
    DATA_DIR,
    INEGI_API_TOKEN,
    SCRAPER_DELAY,
    SCRAPER_MAX_RETRIES,
    SCRAPER_USER_AGENT,
)

# ── Constantes ──────────────────────────────────────────────────────────────

# URL base de la API DENUE de INEGI
DENUE_API_BASE = "https://www.inegi.org.mx/app/api/denue/v1/consulta"

# URL de descarga masiva (CSVs por estado)
DENUE_DESCARGA_URL = "https://www.inegi.org.mx/app/descarga/?ti=6"

# Códigos SCIAN relevantes para análisis inmobiliario
CATEGORIAS_SCIAN: Dict[str, Dict[str, Any]] = {
    "comercio_menudeo": {
        "codigos": ["46"],
        "descripcion": "Comercio al por menor (supermercados, tiendas)",
        "peso_densidad": 1.0,
        "subcategorias": {
            "supermercados": ["4611", "4621"],
            "tiendas_conveniencia": ["4611"],
            "farmacias": ["4641"],
        },
    },
    "servicios_financieros": {
        "codigos": ["52"],
        "descripcion": "Servicios financieros (bancos, cajeros)",
        "peso_densidad": 1.5,
        "subcategorias": {
            "bancos": ["5221"],
            "cajeros": ["5221"],
        },
    },
    "educacion": {
        "codigos": ["61"],
        "descripcion": "Servicios educativos (escuelas, universidades)",
        "peso_densidad": 1.2,
        "subcategorias": {
            "preescolar": ["6111"],
            "primaria": ["6111"],
            "secundaria": ["6111"],
            "preparatoria": ["6112"],
            "universidad": ["6113"],
        },
    },
    "salud": {
        "codigos": ["62"],
        "descripcion": "Servicios de salud (hospitales, clínicas)",
        "peso_densidad": 1.8,
        "subcategorias": {
            "hospitales": ["6221", "6222", "6223"],
            "consultorios": ["6211", "6212"],
            "clinicas": ["6214", "6215"],
        },
    },
    "alojamiento_alimentos": {
        "codigos": ["72"],
        "descripcion": "Alojamiento temporal y restaurantes",
        "peso_densidad": 0.8,
        "subcategorias": {
            "restaurantes": ["7221", "7222", "7223", "7224", "7225"],
            "hoteles": ["7211"],
            "cafeterias": ["7225"],
        },
    },
    "gobierno": {
        "codigos": ["93"],
        "descripcion": "Actividades gubernamentales",
        "peso_densidad": 0.5,
        "subcategorias": {
            "oficinas_gobierno": ["9311", "9312", "9313"],
        },
    },
}

# Pesos para el cálculo de commercial_density_score
PESOS_DENSIDAD: Dict[str, float] = {
    cat: info["peso_densidad"] for cat, info in CATEGORIAS_SCIAN.items()
}

# Radio de la Tierra en km (para cálculo de distancias Haversine)
RADIO_TIERRA_KM = 6371.0


class DENUEScraper:
    """
    Scraper del DENUE que usa la API de INEGI para obtener unidades
    económicas cerca de puntos de interés, filtra por categorías SCIAN
    relevantes, y calcula features de densidad.
    """

    def __init__(
        self,
        token: Optional[str] = None,
        radio_m: int = 2000,
        delay: float = SCRAPER_DELAY,
    ):
        self.token = token or INEGI_API_TOKEN or os.getenv("INEGI_API_TOKEN", "")
        self.radio_m = radio_m
        self.delay = delay

        if not self.token:
            logger.warning(
                "INEGI_API_TOKEN no configurado. Las llamadas a la API DENUE fallarán.\n"
                "Registra un token gratuito en: https://www.inegi.org.mx/app/api/denue/v1/"
            )

    # ── Distancia Haversine ─────────────────────────────────────────────

    @staticmethod
    def distancia_haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calcula la distancia en metros entre dos coordenadas usando Haversine.
        """
        lat1_r, lon1_r = math.radians(lat1), math.radians(lon1)
        lat2_r, lon2_r = math.radians(lat2), math.radians(lon2)

        dlat = lat2_r - lat1_r
        dlon = lon2_r - lon1_r

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return RADIO_TIERRA_KM * c * 1000  # metros

    # ── Consulta a la API DENUE ─────────────────────────────────────────

    async def _consultar_denue_api(
        self,
        client: httpx.AsyncClient,
        lat: float,
        lon: float,
        actividad: str,
        max_reintentos: int = SCRAPER_MAX_RETRIES,
    ) -> List[Dict]:
        """
        Consulta la API DENUE para establecimientos cerca de un punto.
        URL: /BuscarAreaActEstr/{lat}/{lon}/{metros}/{actividad}/0/{token}
        """
        url = (
            f"{DENUE_API_BASE}/BuscarAreaActEstr/"
            f"{lat}/{lon}/{self.radio_m}/{actividad}/0/{self.token}"
        )

        for intento in range(max_reintentos):
            try:
                resp = await client.get(url, timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    if isinstance(data, list):
                        return data
                    return []
                elif resp.status_code == 429:
                    espera = 2 ** (intento + 1)
                    logger.warning(f"Rate limited, esperando {espera}s")
                    await asyncio.sleep(espera)
                else:
                    logger.debug(f"HTTP {resp.status_code} para actividad={actividad}")
                    return []
            except (httpx.TimeoutException, httpx.ConnectError, OSError) as exc:
                logger.debug(f"Error de conexión: {exc} (intento {intento + 1})")
                await asyncio.sleep(2 ** intento)

        return []

    # ── Clasificación SCIAN ─────────────────────────────────────────────

    @staticmethod
    def clasificar_scian(codigo_scian: str) -> Optional[str]:
        """
        Clasifica un código SCIAN en una de las categorías relevantes.
        Retorna el nombre de la categoría o None si no es relevante.
        """
        codigo = str(codigo_scian).strip()
        for categoria, info in CATEGORIAS_SCIAN.items():
            for prefijo in info["codigos"]:
                if codigo.startswith(prefijo):
                    return categoria
        return None

    # ── Scraping por puntos de interés ──────────────────────────────────

    async def scrape_por_puntos(
        self, puntos: List[Dict[str, Any]]
    ) -> pd.DataFrame:
        """
        Para cada punto (lat, lon), consulta la API DENUE por todas las
        categorías SCIAN relevantes y recopila los establecimientos.

        Args:
            puntos: Lista de dicts con al menos {lat, lon, nombre}

        Returns:
            DataFrame con todos los establecimientos encontrados.
        """
        if not self.token:
            logger.error("Token INEGI no disponible. Abortando.")
            return pd.DataFrame()

        logger.info("=" * 70)
        logger.info("DENUE SCRAPER - Unidades Económicas")
        logger.info(f"  Puntos a consultar: {len(puntos)}")
        logger.info(f"  Radio de búsqueda: {self.radio_m}m")
        logger.info(f"  Categorías: {list(CATEGORIAS_SCIAN.keys())}")
        logger.info("=" * 70)

        registros: List[Dict] = []

        # Códigos de actividad a consultar (todos los prefijos)
        codigos_actividad = []
        for info in CATEGORIAS_SCIAN.values():
            codigos_actividad.extend(info["codigos"])

        async with httpx.AsyncClient(
            headers={
                "Accept": "application/json",
                "User-Agent": SCRAPER_USER_AGENT,
            },
            follow_redirects=True,
        ) as client:

            for idx, punto in enumerate(puntos, 1):
                lat = punto["lat"]
                lon = punto["lon"]
                nombre = punto.get("nombre", f"Punto {idx}")

                logger.info(f"\n[{idx}/{len(puntos)}] {nombre} ({lat}, {lon})")

                for codigo in codigos_actividad:
                    establecimientos = await self._consultar_denue_api(
                        client, lat, lon, codigo
                    )

                    for est in establecimientos:
                        est_lat = est.get("Latitud") or est.get("latitud")
                        est_lon = est.get("Longitud") or est.get("longitud")
                        codigo_act = (
                            est.get("Codigo_actividad")
                            or est.get("codigo_actividad")
                            or ""
                        )
                        categoria = self.clasificar_scian(str(codigo_act))

                        try:
                            est_lat_f = float(est_lat) if est_lat else None
                            est_lon_f = float(est_lon) if est_lon else None
                        except (ValueError, TypeError):
                            est_lat_f = None
                            est_lon_f = None

                        # Calcular distancia al punto de referencia
                        distancia_m = None
                        if est_lat_f and est_lon_f:
                            distancia_m = self.distancia_haversine(
                                lat, lon, est_lat_f, est_lon_f
                            )

                        registros.append({
                            "punto_referencia": nombre,
                            "punto_lat": lat,
                            "punto_lon": lon,
                            "nombre_negocio": str(
                                est.get("Nombre") or est.get("nombre")
                                or est.get("Razon_social") or ""
                            )[:200],
                            "codigo_scian": str(codigo_act),
                            "actividad_economica": str(
                                est.get("Clase_actividad")
                                or est.get("clase_actividad") or ""
                            )[:300],
                            "categoria": categoria,
                            "negocio_lat": est_lat_f,
                            "negocio_lon": est_lon_f,
                            "estado": str(
                                est.get("Entidad") or est.get("entidad") or ""
                            ),
                            "municipio": str(
                                est.get("Municipio") or est.get("municipio") or ""
                            ),
                            "distancia_m": round(distancia_m, 1) if distancia_m else None,
                            "fecha_recoleccion": datetime.now().strftime("%Y-%m-%d"),
                        })

                    logger.info(
                        f"  SCIAN {codigo}: {len(establecimientos)} establecimientos"
                    )
                    await asyncio.sleep(self.delay)

        df = pd.DataFrame(registros)
        logger.info(f"\nTotal registros recopilados: {len(df)}")

        return df

    # ── Cálculo de features de densidad ─────────────────────────────────

    @staticmethod
    def calcular_densidad_amenidades(
        df: pd.DataFrame,
        punto_lat: float,
        punto_lon: float,
    ) -> Dict[str, Any]:
        """
        Calcula features de densidad de amenidades para un punto dado.

        Features generados:
          - count_restaurants_500m: restaurantes a menos de 500m
          - count_banks_1km: bancos a menos de 1km
          - count_schools_1km: escuelas a menos de 1km
          - count_supermarkets_1km: supermercados a menos de 1km
          - count_hospitals_1km: hospitales/clínicas a menos de 1km
          - commercial_density_score: puntaje ponderado de densidad comercial
        """
        if df.empty:
            return {
                "count_restaurants_500m": 0,
                "count_banks_1km": 0,
                "count_schools_1km": 0,
                "count_supermarkets_1km": 0,
                "count_hospitals_1km": 0,
                "commercial_density_score": 0.0,
            }

        # Filtrar registros con coordenadas válidas
        df_valid = df.dropna(subset=["negocio_lat", "negocio_lon"]).copy()
        if df_valid.empty:
            return {
                "count_restaurants_500m": 0,
                "count_banks_1km": 0,
                "count_schools_1km": 0,
                "count_supermarkets_1km": 0,
                "count_hospitals_1km": 0,
                "commercial_density_score": 0.0,
            }

        # Calcular distancias si no existen
        if "distancia_m" not in df_valid.columns or df_valid["distancia_m"].isna().all():
            df_valid["distancia_m"] = df_valid.apply(
                lambda row: DENUEScraper.distancia_haversine(
                    punto_lat, punto_lon,
                    row["negocio_lat"], row["negocio_lon"],
                ),
                axis=1,
            )

        # Conteos por categoría y radio
        features = {}

        # Restaurantes a 500m
        mask_rest = (
            (df_valid["categoria"] == "alojamiento_alimentos")
            & (df_valid["distancia_m"] <= 500)
        )
        features["count_restaurants_500m"] = int(mask_rest.sum())

        # Bancos a 1km
        mask_bancos = (
            (df_valid["categoria"] == "servicios_financieros")
            & (df_valid["distancia_m"] <= 1000)
        )
        features["count_banks_1km"] = int(mask_bancos.sum())

        # Escuelas a 1km
        mask_escuelas = (
            (df_valid["categoria"] == "educacion")
            & (df_valid["distancia_m"] <= 1000)
        )
        features["count_schools_1km"] = int(mask_escuelas.sum())

        # Supermercados a 1km
        mask_super = (
            (df_valid["categoria"] == "comercio_menudeo")
            & (df_valid["distancia_m"] <= 1000)
        )
        features["count_supermarkets_1km"] = int(mask_super.sum())

        # Hospitales/clínicas a 1km
        mask_salud = (
            (df_valid["categoria"] == "salud")
            & (df_valid["distancia_m"] <= 1000)
        )
        features["count_hospitals_1km"] = int(mask_salud.sum())

        # Commercial density score (ponderado)
        # Cada categoría contribuye con su peso * conteo normalizado
        density_score = 0.0
        for categoria, peso in PESOS_DENSIDAD.items():
            mask_cat = (
                (df_valid["categoria"] == categoria)
                & (df_valid["distancia_m"] <= 1000)
            )
            conteo = mask_cat.sum()
            # Normalizar: 0 negocios = 0, 50+ negocios = 1
            normalizado = min(conteo / 50.0, 1.0)
            density_score += peso * normalizado

        # Escalar a 0-100
        max_score = sum(PESOS_DENSIDAD.values())
        features["commercial_density_score"] = round(
            (density_score / max_score) * 100.0, 2
        ) if max_score > 0 else 0.0

        return features

    def calcular_features_todos_puntos(
        self, df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Para cada punto de referencia único en el DataFrame, calcula
        los features de densidad de amenidades.

        Retorna un DataFrame con un registro por punto y todas las features.
        """
        if df.empty:
            return pd.DataFrame()

        puntos_unicos = df.groupby(["punto_referencia", "punto_lat", "punto_lon"]).size().reset_index()
        features_rows = []

        for _, punto in puntos_unicos.iterrows():
            p_lat = punto["punto_lat"]
            p_lon = punto["punto_lon"]
            p_nombre = punto["punto_referencia"]

            # Filtrar negocios cercanos a este punto
            df_punto = df[
                (df["punto_lat"] == p_lat) & (df["punto_lon"] == p_lon)
            ]

            features = self.calcular_densidad_amenidades(df_punto, p_lat, p_lon)
            features["punto_referencia"] = p_nombre
            features["lat"] = p_lat
            features["lon"] = p_lon
            features_rows.append(features)

        return pd.DataFrame(features_rows)

    # ── Guardado ────────────────────────────────────────────────────────

    def guardar_csv(self, df: pd.DataFrame, filename: str = "denue_negocios.csv") -> Optional[Path]:
        """Guarda el DataFrame como CSV."""
        if df.empty:
            logger.warning("DataFrame vacío, no se guarda CSV")
            return None

        filepath = DATA_DIR / filename
        df.to_csv(filepath, index=False, encoding="utf-8-sig")
        logger.info(f"CSV guardado: {filepath} ({len(df)} registros)")
        return filepath

    # ── Ejecución principal ─────────────────────────────────────────────

    async def scrape(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Ejecuta el scraper completo:
        1. Consulta DENUE para ciudades principales
        2. Guarda negocios en CSV
        3. Calcula features de densidad por punto
        """
        # Ciudades principales para consulta
        ciudades_principales = [
            {"nombre": "Ciudad de México - Centro", "lat": 19.4326, "lon": -99.1332},
            {"nombre": "Ciudad de México - Polanco", "lat": 19.4338, "lon": -99.1907},
            {"nombre": "Ciudad de México - Santa Fe", "lat": 19.3592, "lon": -99.2739},
            {"nombre": "Guadalajara - Centro", "lat": 20.6597, "lon": -103.3496},
            {"nombre": "Guadalajara - Providencia", "lat": 20.6902, "lon": -103.3851},
            {"nombre": "Zapopan - Andares", "lat": 20.6892, "lon": -103.4198},
            {"nombre": "Monterrey - Centro", "lat": 25.6866, "lon": -100.3161},
            {"nombre": "Monterrey - San Pedro", "lat": 25.6597, "lon": -100.3623},
            {"nombre": "Puebla - Centro", "lat": 19.0414, "lon": -98.2063},
            {"nombre": "Querétaro - Centro", "lat": 20.5888, "lon": -100.3899},
            {"nombre": "Cancún - Zona Hotelera", "lat": 21.1619, "lon": -86.8515},
            {"nombre": "Mérida - Centro", "lat": 20.9674, "lon": -89.5926},
            {"nombre": "Tijuana - Zona Río", "lat": 32.5149, "lon": -117.0382},
            {"nombre": "León - Centro", "lat": 21.1250, "lon": -101.6860},
            {"nombre": "Hermosillo - Centro", "lat": 29.0729, "lon": -110.9559},
            {"nombre": "Aguascalientes - Centro", "lat": 21.8818, "lon": -102.2916},
            {"nombre": "San Luis Potosí - Centro", "lat": 22.1565, "lon": -100.9855},
            {"nombre": "Morelia - Centro", "lat": 19.7060, "lon": -101.1950},
            {"nombre": "Toluca - Centro", "lat": 19.2826, "lon": -99.6557},
            {"nombre": "Veracruz - Centro", "lat": 19.2026, "lon": -96.1533},
        ]

        # 1. Scraping de negocios
        df_negocios = await self.scrape_por_puntos(ciudades_principales)

        if df_negocios.empty:
            logger.warning("No se obtuvieron resultados del DENUE")
            return pd.DataFrame(), pd.DataFrame()

        # 2. Guardar CSV de negocios
        self.guardar_csv(df_negocios, "denue_negocios.csv")

        # 3. Calcular features de densidad
        df_features = self.calcular_features_todos_puntos(df_negocios)
        if not df_features.empty:
            self.guardar_csv(df_features, "denue_density_features.csv")

        # Reporte
        logger.info("\n" + "=" * 70)
        logger.info("RESUMEN - DENUE Scraper")
        logger.info("=" * 70)
        logger.info(f"  Total negocios recopilados: {len(df_negocios)}")

        if "categoria" in df_negocios.columns:
            by_cat = df_negocios["categoria"].value_counts()
            logger.info("  Por categoría:")
            for cat, count in by_cat.items():
                logger.info(f"    {cat}: {count}")

        if not df_features.empty:
            logger.info(f"\n  Features de densidad calculados para {len(df_features)} puntos")
            logger.info(
                f"  Promedio commercial_density_score: "
                f"{df_features['commercial_density_score'].mean():.1f}"
            )

        logger.info("=" * 70)

        return df_negocios, df_features


# ── Punto de entrada ────────────────────────────────────────────────────────

def main():
    """Ejecuta el scraper DENUE."""
    scraper = DENUEScraper()
    asyncio.run(scraper.scrape())


if __name__ == "__main__":
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level:<8}</level> | <level>{message}</level>",
        level="INFO",
    )
    main()
