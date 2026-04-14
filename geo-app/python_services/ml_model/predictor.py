# ================================================================
# MODELO ML - Prediccion de Plusvalia y Precio de Terrenos
# V3: Target encoding, amenity features, interaction features,
#     percentile-based plusvalia, no redundant log_area
# ================================================================

import math
import pandas as pd
import numpy as np
from functools import lru_cache
import hashlib
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
import joblib
from datetime import datetime
from pathlib import Path
from loguru import logger
from typing import Dict, Tuple, Optional
import yaml
import json
import warnings

# Suppress only non-actionable convergence/future warnings from sklearn internals
warnings.filterwarnings('ignore', category=FutureWarning, module='sklearn')
warnings.filterwarnings('ignore', category=UserWarning, message='.*n_jobs.*')


def _load_model_config() -> dict:
    """Load model configuration from YAML file."""
    config_path = Path(__file__).parent / "model_config.yaml"
    if config_path.exists():
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    return {}


MODEL_CONFIG = _load_model_config()

import sys
sys.path.append('..')
from config import MODEL_PATH, MIN_TRAINING_SAMPLES
from integrations.inegi_client import INEGIClient


# ================================================================
# City center coordinates for Haversine distance calculation
# ================================================================
CITY_CENTERS = {
    "Ciudad de Mexico": (19.4326, -99.1332),
    "Ciudad de México": (19.4326, -99.1332),
    "Guadalajara": (20.6597, -103.3496),
    "Monterrey": (25.6866, -100.3161),
    "Puebla": (19.0414, -98.2063),
    "Querétaro": (20.5888, -100.3899),
    "Mérida": (20.9674, -89.5926),
    "Cancún": (21.1619, -86.8515),
    "Tijuana": (32.5149, -117.0382),
    "León": (21.1221, -101.6839),
    "Aguascalientes": (21.8818, -102.2916),
    "San Luis Potosí": (22.1565, -100.9855),
    "Chihuahua": (28.6353, -106.0889),
    "Morelia": (19.7060, -101.1950),
    "Hermosillo": (29.0729, -110.9559),
    "Saltillo": (25.4232, -100.9924),
    "Villahermosa": (17.9894, -92.9475),
    "Tuxtla Gutiérrez": (16.7516, -93.1152),
    "Oaxaca": (17.0732, -96.7266),
    "Veracruz": (19.1738, -96.1342),
    "Toluca": (19.2826, -99.6557),
    "Cuernavaca": (18.9242, -99.2216),
    "Pachuca": (20.1011, -98.7591),
    "Playa del Carmen": (20.6296, -87.0739),
    "Tulum": (20.2114, -87.4654),
    "Los Cabos": (22.8905, -109.9167),
    "Puerto Vallarta": (20.6534, -105.2253),
    "Mazatlán": (23.2494, -106.4111),
    "Acapulco": (16.8531, -99.8237),
    "Zapopan": (20.7230, -103.3843),
    "Naucalpan": (19.4784, -99.2397),
    "Tlalnepantla": (19.5370, -99.1949),
    "Ecatepec": (19.6015, -99.0520),
    # Distrito Federal boroughs
    "Benito Juárez": (19.3718, -99.1590),
    "Miguel Hidalgo": (19.4148, -99.1925),
    "Cuauhtémoc": (19.4285, -99.1428),
    "Coyoacán": (19.3467, -99.1617),
    "Alvaro Obregón": (19.3579, -99.2067),
    "Tlalpan": (19.2847, -99.1683),
    "Iztapalapa": (19.3558, -99.0592),
    "Gustavo A. Madero": (19.4748, -99.1139),
    "Azcapotzalco": (19.4869, -99.1843),
    "Iztacalco": (19.3954, -99.0974),
    "Venustiano Carranza": (19.4409, -99.1069),
    "Tláhuac": (19.2867, -99.0046),
    "Xochimilco": (19.2620, -99.1036),
    "Milpa Alta": (19.1925, -99.0230),
    "La Magdalena Contreras": (19.3227, -99.2437),
    "Cuajimalpa de Morelos": (19.3557, -99.2988),
    "San Pedro Garza García": (25.6581, -100.4023),
    # --- Aguascalientes ---
    "Jesús María": (21.96, -102.34),
    "Calvillo": (21.85, -102.72),
    # --- Baja California ---
    "Mexicali": (32.63, -115.45),
    "Ensenada": (31.87, -116.60),
    "Rosarito": (32.36, -117.06),
    "Tecate": (32.57, -116.63),
    "San Quintín": (30.53, -115.93),
    # --- Baja California Sur ---
    "La Paz": (24.14, -110.31),
    "Cabo San Lucas": (22.89, -109.91),
    "San José del Cabo": (23.06, -109.70),
    "Loreto": (26.01, -111.35),
    "Ciudad Constitución": (25.03, -111.67),
    # --- Campeche ---
    "Campeche": (19.84, -90.53),
    "Ciudad del Carmen": (18.65, -91.83),
    "Champotón": (19.35, -90.72),
    "Escárcega": (18.61, -90.74),
    # --- Chiapas ---
    "San Cristóbal de las Casas": (16.74, -92.64),
    "Tapachula": (14.90, -92.26),
    "Comitán": (16.25, -92.13),
    "Palenque": (17.51, -91.98),
    "Ocosingo": (16.91, -92.09),
    # --- Chihuahua ---
    "Ciudad Juárez": (31.69, -106.42),
    "Delicias": (28.19, -105.47),
    "Cuauhtémoc Ciudad": (28.41, -106.87),
    "Parral": (26.93, -105.66),
    "Nuevo Casas Grandes": (30.42, -107.91),
    # --- Coahuila ---
    "Torreón": (25.54, -103.41),
    "Monclova": (26.91, -101.42),
    "Piedras Negras": (28.70, -100.52),
    "Acuña": (29.32, -100.93),
    "Sabinas": (27.85, -101.12),
    # --- Colima ---
    "Colima": (19.24, -103.72),
    "Manzanillo": (19.05, -104.32),
    "Tecomán": (18.91, -103.87),
    "Villa de Álvarez": (19.27, -103.74),
    # --- Durango ---
    "Durango": (24.02, -104.67),
    "Gómez Palacio": (25.56, -103.50),
    "Lerdo": (25.54, -103.52),
    "Santiago Papasquiaro": (24.69, -105.42),
    # --- Estado de México ---
    "Nezahualcóyotl": (19.40, -99.01),
    "Atizapán": (19.56, -99.27),
    "Huixquilucan": (19.36, -99.35),
    "Metepec": (19.26, -99.60),
    "Cuautitlán Izcalli": (19.65, -99.21),
    "Texcoco": (19.52, -98.88),
    "Ixtapaluca": (19.32, -98.88),
    "Chalco": (19.26, -98.90),
    "Coacalco": (19.63, -99.10),
    "Tultitlán": (19.65, -99.17),
    # --- Guanajuato ---
    "Irapuato": (20.68, -101.35),
    "Celaya": (20.52, -100.81),
    "Salamanca": (20.57, -101.19),
    "Guanajuato": (21.02, -101.26),
    "San Miguel de Allende": (20.91, -100.74),
    "Silao": (20.94, -101.43),
    "Dolores Hidalgo": (21.16, -100.93),
    # --- Guerrero ---
    "Chilpancingo": (17.55, -99.50),
    "Iguala": (18.35, -99.54),
    "Zihuatanejo": (17.64, -101.55),
    "Taxco": (18.56, -99.60),
    # --- Hidalgo ---
    "Tulancingo": (20.08, -98.36),
    "Tula": (20.05, -99.34),
    "Actopan": (20.27, -98.94),
    "Huejutla": (21.14, -98.42),
    "Tizayuca": (19.84, -98.98),
    # --- Jalisco ---
    "Tlaquepaque": (20.64, -103.31),
    "Tonalá": (20.62, -103.23),
    "Tlajomulco": (20.47, -103.44),
    "Lagos de Moreno": (21.36, -101.93),
    "Tepatitlán": (20.82, -102.73),
    "Ocotlán": (20.35, -102.77),
    "Chapala": (20.30, -103.19),
    # --- Michoacán ---
    "Uruapan": (19.42, -102.07),
    "Zamora": (19.98, -102.28),
    "Lázaro Cárdenas": (17.96, -102.20),
    "Pátzcuaro": (19.52, -101.61),
    "Apatzingán": (19.09, -102.35),
    "Zitácuaro": (19.44, -100.36),
    "La Piedad": (20.35, -102.03),
    # --- Morelos ---
    "Cuautla": (18.81, -98.95),
    "Jiutepec": (18.88, -99.18),
    "Temixco": (18.85, -99.23),
    "Yautepec": (18.88, -99.07),
    "Tepoztlán": (18.98, -99.10),
    # --- Nayarit ---
    "Tepic": (21.51, -104.89),
    "Bahía de Banderas": (20.75, -105.36),
    "Compostela": (21.24, -104.90),
    "Santiago Ixcuintla": (21.81, -105.21),
    "Sayulita": (20.87, -105.44),
    # --- Nuevo León ---
    "Apodaca": (25.78, -100.19),
    "Guadalupe NL": (25.68, -100.26),
    "San Nicolás": (25.74, -100.30),
    "Santa Catarina": (25.67, -100.46),
    "Escobedo": (25.80, -100.32),
    "García": (25.81, -100.59),
    "Cadereyta": (25.59, -100.00),
    "Santiago NL": (25.42, -100.15),
    # --- Oaxaca ---
    "Salina Cruz": (16.17, -95.20),
    "Juchitán": (16.43, -95.02),
    "Huatulco": (15.77, -96.13),
    "Tuxtepec": (18.09, -96.12),
    "Puerto Escondido": (15.86, -97.07),
    # --- Puebla ---
    "Tehuacán": (18.46, -97.39),
    "San Martín Texmelucan": (19.28, -98.44),
    "Atlixco": (18.91, -98.44),
    "Cholula": (19.06, -98.31),
    "Izúcar de Matamoros": (18.60, -98.47),
    "San Andrés Cholula": (19.05, -98.31),
    # --- Querétaro ---
    "San Juan del Río": (20.39, -99.99),
    "El Marqués": (20.62, -100.28),
    "Corregidora": (20.53, -100.45),
    "Tequisquiapan": (20.52, -99.89),
    # --- Quintana Roo ---
    "Chetumal": (18.50, -88.30),
    "Cozumel": (20.51, -86.95),
    "Bacalar": (18.68, -88.39),
    "Isla Mujeres": (21.23, -86.73),
    # --- San Luis Potosí ---
    "Soledad de Graciano Sánchez": (22.18, -100.93),
    "Ciudad Valles": (21.99, -99.01),
    "Matehuala": (23.65, -100.64),
    "Rioverde": (21.93, -99.99),
    "Tamazunchale": (21.26, -98.79),
    # --- Sinaloa ---
    "Culiacán": (24.81, -107.39),
    "Los Mochis": (25.79, -108.99),
    "Guasave": (25.57, -108.47),
    "Navolato": (24.76, -107.70),
    # --- Sonora ---
    "Ciudad Obregón": (27.49, -109.94),
    "Nogales": (31.31, -110.94),
    "Guaymas": (27.92, -110.90),
    "San Luis Río Colorado": (32.46, -114.77),
    "Navojoa": (27.07, -109.44),
    "Puerto Peñasco": (31.31, -113.54),
    # --- Tabasco ---
    "Comalcalco": (18.28, -93.20),
    "Cárdenas Tab": (18.00, -93.38),
    "Paraíso": (18.40, -93.21),
    "Macuspana": (17.76, -92.60),
    "Tenosique": (17.47, -91.42),
    # --- Tamaulipas ---
    "Reynosa": (26.09, -98.28),
    "Matamoros": (25.87, -97.50),
    "Nuevo Laredo": (27.48, -99.52),
    "Tampico": (22.23, -97.86),
    "Ciudad Victoria": (23.74, -99.15),
    "Ciudad Madero": (22.28, -97.83),
    "Altamira": (22.39, -97.94),
    # --- Tlaxcala ---
    "Tlaxcala": (19.32, -98.24),
    "Apizaco": (19.42, -98.14),
    "Huamantla": (19.31, -97.92),
    "Chiautempan": (19.32, -98.19),
    "Calpulalpan": (19.59, -98.56),
    # --- Veracruz ---
    "Xalapa": (19.54, -96.91),
    "Coatzacoalcos": (18.15, -94.43),
    "Poza Rica": (20.53, -97.46),
    "Córdoba": (18.88, -96.93),
    "Orizaba": (18.85, -97.10),
    "Minatitlán": (17.99, -94.55),
    "Boca del Río": (19.10, -96.11),
    "Tuxpan": (20.96, -97.40),
    "Papantla": (20.45, -97.32),
    # --- Yucatán ---
    "Valladolid": (20.69, -88.20),
    "Tizimín": (21.14, -88.15),
    "Progreso": (21.28, -89.66),
    "Umán": (20.88, -89.75),
    "Kanasín": (20.93, -89.56),
    "Izamal": (20.93, -89.02),
    # --- Zacatecas ---
    "Zacatecas": (22.77, -102.57),
    "Fresnillo": (23.17, -102.87),
    "Guadalupe Zac": (22.75, -102.52),
    "Jerez": (22.65, -102.99),
    "Río Grande": (23.83, -103.03),
    "Loreto Zac": (22.28, -101.98),
}


class TargetEncoder:
    """Target encoder with smoothing for categorical features.

    Encodes each category as a weighted average between the category's
    mean target value and the global mean.  The smoothing parameter
    controls the trade-off: higher smoothing biases towards the global
    mean (safer for rare categories).
    """

    def __init__(self, smoothing: float = 10.0):
        self.smoothing = smoothing
        self.global_mean: float = 0.0
        self.encoding_map: Dict[str, float] = {}

    def fit(self, values: pd.Series, target: pd.Series) -> "TargetEncoder":
        self.global_mean = float(target.mean())
        df_tmp = pd.DataFrame({"val": values.astype(str), "target": target})
        agg = df_tmp.groupby("val")["target"].agg(["mean", "count"])
        for val, row in agg.iterrows():
            weight = row["count"] / (row["count"] + self.smoothing)
            self.encoding_map[val] = weight * row["mean"] + (1 - weight) * self.global_mean
        return self

    def transform(self, values: pd.Series) -> pd.Series:
        return values.astype(str).map(self.encoding_map).fillna(self.global_mean)

    def fit_transform(self, values: pd.Series, target: pd.Series) -> pd.Series:
        self.fit(values, target)
        return self.transform(values)


class PlusvaliaPredictorModel:
    """
    Modelo de Machine Learning para predecir plusvalia y precios de terrenos.
    V3: Target encoding, amenity features, interaction features,
        percentile-based plusvalia score.
    """

    def __init__(self, model_version: str = "3.0"):
        self.model_version = model_version
        self.price_model = None
        self.growth_model = None
        self.scaler = StandardScaler()
        # V3: replaced LabelEncoder with TargetEncoder
        self.target_encoders: Dict[str, TargetEncoder] = {}
        # Keep label_encoders attribute for backward compat with saved V2 models
        self.label_encoders: dict = {}
        self.feature_names = []
        self.model_path = MODEL_PATH
        self.inegi_client = INEGIClient()
        self._demographics_cache: Dict[str, dict] = {}
        self._amenity_cache: Dict[str, dict] = {}
        # State-level price distributions for percentile plusvalia
        self._state_price_distributions: Dict[str, np.ndarray] = {}

        # Crear directorio de modelos si no existe
        self.model_path.mkdir(parents=True, exist_ok=True)

    # ================================================================
    # Demographics helpers
    # ================================================================

    def _preload_all_demographics(self):
        """Load ALL demographics from DB in a single query and cache them."""
        if self._demographics_cache:
            return  # Already loaded
        try:
            from config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
            from supabase import create_client
            sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
            result = sb.table('iainmobiliaria_demographics').select('*').execute()
            if result.data:
                for d in result.data:
                    key = f"{d['city']}|{d['state']}"
                    self._demographics_cache[key] = {
                        'population_density': d.get('population_density', 1500),
                        'economic_level_score': self._compute_economic_score(d),
                        'unemployment_rate': d.get('unemployment_rate', 4.0),
                        'avg_income': d.get('avg_income_mxn', 8000),
                        'education_index': d.get('pct_education_superior', 15) / 100,
                        'security_score': d.get('security_perception_score', 50),
                        'infrastructure_score': (
                            d.get('pct_water_access', 95) +
                            d.get('pct_electricity', 99) +
                            d.get('pct_drainage', 95) +
                            d.get('pct_internet', 60)
                        ) / 4,
                        'pct_vacant_housing': d.get('pct_vacant_housing', 8),
                        'population_growth': d.get('population_growth_5yr_pct', 1.0),
                        # V3: additional demographics previously unused
                        'median_age': d.get('median_age', 30),
                        'homicide_rate_per_100k': d.get('homicide_rate_per_100k', 15.0),
                        'pct_internet': d.get('pct_internet', 60),
                        'pea_pct': d.get('pea_pct', 55.0),
                    }
                logger.info(f"Preloaded demographics for {len(result.data)} cities")
        except Exception as e:
            logger.warning(f"Could not preload demographics: {e}")

    def _get_demographics(self, city: str, state: str) -> dict:
        """Get demographic data from pre-loaded cache. Falls back to defaults."""
        # Preload on first call
        if not self._demographics_cache:
            self._preload_all_demographics()

        cache_key = f"{city}|{state}"
        if cache_key in self._demographics_cache:
            return self._demographics_cache[cache_key]

        # Try partial match (city name without state)
        for key, demo in self._demographics_cache.items():
            if city and city.lower() in key.lower():
                self._demographics_cache[cache_key] = demo
                return demo

        # Fallback defaults
        fallback = {
            'population_density': 1500, 'economic_level_score': 5,
            'unemployment_rate': 4.0, 'avg_income': 8000,
            'education_index': 0.15, 'security_score': 50,
            'infrastructure_score': 85, 'pct_vacant_housing': 8,
            'population_growth': 1.0,
            # V3 additions
            'median_age': 30, 'homicide_rate_per_100k': 15.0,
            'pct_internet': 60, 'pea_pct': 55.0,
        }
        self._demographics_cache[cache_key] = fallback
        return fallback

    def _compute_economic_score(self, demographics: dict) -> float:
        """Compute economic score 1-10 from demographic data."""
        income = demographics.get('avg_income_mxn', 8000)
        education = demographics.get('pct_education_superior', 15)
        marginacion = demographics.get('grado_marginacion', 'bajo')

        margin_map = {'muy_bajo': 9, 'bajo': 7, 'medio': 5, 'alto': 3, 'muy_alto': 1}
        margin_score = margin_map.get(marginacion, 5)

        income_score = min(10, income / 1500)   # 15000+ = 10
        edu_score = min(10, education / 3.5)    # 35%+ = 10

        return round((margin_score * 0.4 + income_score * 0.35 + edu_score * 0.25), 1)

    # ================================================================
    # Amenity feature helpers (V3)
    # ================================================================

    def _preload_all_amenities(self):
        """Load amenity counts from iainmobiliaria_amenity_counts in a single query."""
        if self._amenity_cache:
            return
        try:
            from config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
            from supabase import create_client
            sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
            result = sb.table('iainmobiliaria_amenity_counts').select('*').execute()
            if result.data:
                for row in result.data:
                    comp_id = str(row.get('comparable_id', ''))
                    self._amenity_cache[comp_id] = {
                        'nearest_school_km': (row.get('nearest_school_m') or 99999) / 1000.0,
                        'nearest_hospital_km': (row.get('nearest_hospital_m') or 99999) / 1000.0,
                        'nearest_supermarket_km': (row.get('nearest_supermarket_m') or 99999) / 1000.0,
                        'amenity_count_1km': row.get('total_1km', 0),
                        'walkability_score': row.get('walkability_score', 0),
                    }
                logger.info(f"Preloaded amenity features for {len(result.data)} comparables")
        except Exception as e:
            logger.warning(f"Could not preload amenity features: {e}")

    def _get_amenity_features(self, comparable_id: str) -> dict:
        """Get amenity features for a comparable, with fallback defaults."""
        if not self._amenity_cache:
            self._preload_all_amenities()

        if comparable_id and comparable_id in self._amenity_cache:
            return self._amenity_cache[comparable_id]

        return {
            'nearest_school_km': 2.0,
            'nearest_hospital_km': 3.0,
            'nearest_supermarket_km': 1.5,
            'amenity_count_1km': 5,
            'walkability_score': 30.0,
        }

    def _join_amenity_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Join amenity features from the cache onto a DataFrame.

        For training data that has an 'id' column (comparable_id),
        we look up the precomputed amenity features.
        For prediction requests (no id), we use fallback defaults.
        """
        defaults = self._get_amenity_features('')
        amenity_cols = list(defaults.keys())

        if 'id' in df.columns:
            amenity_rows = df['id'].apply(
                lambda cid: self._get_amenity_features(str(cid)) if pd.notna(cid) else defaults
            )
            for col in amenity_cols:
                df[col] = amenity_rows.apply(lambda d: d[col])
        else:
            for col in amenity_cols:
                df[col] = defaults[col]

        return df

    # ================================================================
    # Distance helpers
    # ================================================================

    def _calculate_distance_to_center(self, lat: float, lon: float, city: str) -> float:
        """Calculate real distance to city center using Haversine formula.

        Returns distance in kilometers.
        """
        center = CITY_CENTERS.get(city)
        if not center:
            # Try partial match
            for c, coords in CITY_CENTERS.items():
                if city and city.lower() in c.lower():
                    center = coords
                    break
        if not center:
            return 5.0  # Default 5km if city not found

        R = 6371  # Earth radius in km
        dlat = math.radians(center[0] - lat)
        dlon = math.radians(center[1] - lon)
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat)) * math.cos(math.radians(center[0])) *
             math.sin(dlon / 2) ** 2)
        return R * 2 * math.asin(math.sqrt(a))

    # ================================================================
    # Feature preparation
    # ================================================================

    def prepare_features(self, df: pd.DataFrame, target_series: pd.Series = None) -> pd.DataFrame:
        """
        Prepare feature matrix from dataframe.
        V3: target encoding, amenity features, interaction features,
            no redundant log_area.

        Args:
            df: DataFrame with raw data (must contain price_mxn, area_m2,
                and ideally lat, lon, city, state, collection_date).
            target_series: Target variable (price_m2) for fitting target encoders
                during training. None during prediction (uses pre-fitted encoders).

        Returns:
            DataFrame with all features plus original columns.
        """
        logger.info("Preparando features (V3 enrichment)...")

        df_features = df.copy()

        # === CORE FEATURES ===
        if 'price_m2' not in df_features.columns:
            df_features['price_m2'] = df_features['price_mxn'] / df_features['area_m2']
        # V3: removed log_area (redundant with area_m2 — was inflating area importance to 62.8%)
        df_features['is_large_lot'] = (
            df_features['area_m2'] > df_features['area_m2'].median()
        ).astype(int)

        # === LOCATION FEATURES (Haversine, not placeholder) ===
        if 'lat' in df.columns and 'lon' in df.columns and 'city' in df.columns:
            df_features['distance_to_center'] = df_features.apply(
                lambda row: self._calculate_distance_to_center(
                    row['lat'], row['lon'], row.get('city', '')
                ),
                axis=1
            )
        else:
            df_features['distance_to_center'] = 0.0

        # Normalize lat/lon to Mexico geographic bounds
        if 'lat' in df.columns and 'lon' in df.columns:
            df_features['lat_normalized'] = (df['lat'] - 14) / (33 - 14)
            df_features['lon_normalized'] = (df['lon'] - (-118)) / ((-86) - (-118))
        else:
            df_features['lat_normalized'] = 0.5
            df_features['lon_normalized'] = 0.5

        # === DEMOGRAPHIC FEATURES (from real DB data) ===
        def _get_demo_cached(city, state):
            return self._get_demographics(city, state)

        if 'city' in df.columns:
            demos = df.apply(
                lambda r: _get_demo_cached(
                    r.get('city', ''), r.get('state', '')
                ),
                axis=1
            )
            df_features['population_density'] = demos.apply(lambda d: d['population_density'])
            df_features['economic_level_score'] = demos.apply(lambda d: d['economic_level_score'])
            df_features['unemployment_rate'] = demos.apply(lambda d: d['unemployment_rate'])
            df_features['avg_income'] = demos.apply(lambda d: d['avg_income'])
            df_features['education_index'] = demos.apply(lambda d: d['education_index'])
            df_features['security_score'] = demos.apply(lambda d: d['security_score'])
            df_features['infrastructure_score'] = demos.apply(lambda d: d['infrastructure_score'])
            df_features['pct_vacant_housing'] = demos.apply(lambda d: d['pct_vacant_housing'])
            df_features['population_growth'] = demos.apply(lambda d: d['population_growth'])
            # V3: new demographic features
            df_features['median_age'] = demos.apply(lambda d: d['median_age'])
            df_features['homicide_rate_per_100k'] = demos.apply(lambda d: d['homicide_rate_per_100k'])
            df_features['pct_internet'] = demos.apply(lambda d: d['pct_internet'])
            df_features['pea_pct'] = demos.apply(lambda d: d['pea_pct'])
        else:
            fallback = self._get_demographics('', '')
            for key in fallback:
                df_features[key] = fallback[key]

        # === AMENITY FEATURES (V3: from iainmobiliaria_amenity_counts) ===
        df_features = self._join_amenity_features(df_features)

        # === INTERACTION FEATURES (V3) ===
        df_features['area_x_income'] = df_features['area_m2'] * df_features['avg_income']
        df_features['distance_x_density'] = (
            df_features['distance_to_center'] * df_features['population_density']
        )

        # === TEMPORAL FEATURES ===
        if 'collection_date' in df.columns:
            dates = pd.to_datetime(df_features['collection_date'], errors='coerce')
            df_features['month'] = dates.dt.month.fillna(6).astype(int)
            df_features['quarter'] = dates.dt.quarter.fillna(2).astype(int)
            df_features['year'] = dates.dt.year.fillna(2024).astype(int)
        else:
            df_features['month'] = 6
            df_features['quarter'] = 2
            df_features['year'] = 2024

        # If 'year' was already provided as a column (e.g. from clean pipeline),
        # prefer the pre-existing value over the one extracted above.
        if 'year' in df.columns and df['year'].notna().any():
            df_features['year'] = df['year'].fillna(2024).astype(int)

        # === ENCODED CATEGORICALS (V3: Target Encoding) ===
        for col in ['city', 'state', 'property_type']:
            if col in df_features.columns:
                if target_series is not None:
                    # Training mode: fit and transform
                    encoder = TargetEncoder(smoothing=10.0)
                    df_features[f'{col}_encoded'] = encoder.fit_transform(
                        df_features[col], target_series
                    )
                    self.target_encoders[col] = encoder
                elif col in self.target_encoders:
                    # Prediction mode: use pre-fitted encoder
                    df_features[f'{col}_encoded'] = self.target_encoders[col].transform(
                        df_features[col]
                    )
                else:
                    # Fallback: no encoder available, use 0
                    logger.warning(f"No target encoder for '{col}', using 0")
                    df_features[f'{col}_encoded'] = 0.0

        logger.success(f"Features preparadas: {len(df_features.columns)} columnas")

        return df_features

    def train(
        self,
        df: pd.DataFrame,
        target_col: str = 'price_m2',
        test_size: float = 0.2
    ) -> Dict:
        """
        Entrena el modelo de prediccion de precios.

        Args:
            df: DataFrame con datos de entrenamiento
            target_col: Columna objetivo
            test_size: Proporcion de datos para testing

        Returns:
            Diccionario con metricas de evaluacion
        """
        logger.info(f"Iniciando entrenamiento con {len(df)} muestras")

        if len(df) < 20:
            raise ValueError(f"Se requieren al menos 20 muestras para entrenar (actual: {len(df)})")
        elif len(df) < MIN_TRAINING_SAMPLES:
            logger.warning(f"Se tienen {len(df)} muestras. Se recomienda al menos {MIN_TRAINING_SAMPLES} para mejores resultados.")

        # Clear caches for fresh training
        self._demographics_cache.clear()
        self._amenity_cache.clear()
        self.target_encoders.clear()

        # Compute target before prepare_features so we can pass it for target encoding
        df_tmp = df.copy()
        if 'price_m2' not in df_tmp.columns:
            df_tmp['price_m2'] = df_tmp['price_mxn'] / df_tmp['area_m2']
        target_for_encoding = df_tmp['price_m2']

        # Preparar features (pass target for target encoding fitting)
        df_features = self.prepare_features(df, target_series=target_for_encoding)

        # Build state-level price distributions for percentile-based plusvalia
        self._build_state_price_distributions(df_features)

        # V3 expanded feature list
        feature_cols = [
            # Core
            'area_m2', 'is_large_lot',
            # Location
            'distance_to_center', 'lat_normalized', 'lon_normalized',
            # Demographics (from real DB)
            'population_density', 'economic_level_score',
            'unemployment_rate', 'avg_income', 'education_index',
            'security_score', 'infrastructure_score',
            'pct_vacant_housing', 'population_growth',
            # V3: new demographics
            'median_age', 'homicide_rate_per_100k', 'pct_internet', 'pea_pct',
            # V3: amenity features
            'nearest_school_km', 'nearest_hospital_km', 'nearest_supermarket_km',
            'amenity_count_1km', 'walkability_score',
            # V3: interaction features
            'area_x_income', 'distance_x_density',
            # Temporal
            'month', 'quarter', 'year',
            # Categoricals (target-encoded)
            'city_encoded', 'state_encoded', 'property_type_encoded',
        ]

        # Filtrar features que existen
        feature_cols = [col for col in feature_cols if col in df_features.columns]
        self.feature_names = feature_cols

        X = df_features[feature_cols].fillna(0)
        y = df_features[target_col]

        # Split train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )

        # Log-transformar variable objetivo para reducir sesgo por outliers
        y_train_log = np.log1p(y_train)
        y_test_log = np.log1p(y_test)

        # Escalar features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Entrenar modelo (Random Forest) con target log-transformado
        logger.info("Entrenando Random Forest (log-transformed target)...")
        self.price_model = RandomForestRegressor(
            n_estimators=100,
            max_depth=15,
            min_samples_split=10,
            min_samples_leaf=5,
            random_state=42,
            n_jobs=-1
        )

        self.price_model.fit(X_train_scaled, y_train_log)

        # Predicciones en escala log y revertir a escala original
        y_pred_train_log = self.price_model.predict(X_train_scaled)
        y_pred_test_log = self.price_model.predict(X_test_scaled)
        y_pred_train = np.expm1(y_pred_train_log)
        y_pred_test = np.expm1(y_pred_test_log)

        # Metricas en escala original (no log) para interpretabilidad
        metrics = {
            'train_mae': mean_absolute_error(y_train, y_pred_train),
            'test_mae': mean_absolute_error(y_test, y_pred_test),
            'train_r2': r2_score(y_train, y_pred_train),
            'test_r2': r2_score(y_test, y_pred_test),
            'train_rmse': np.sqrt(mean_squared_error(y_train, y_pred_train)),
            'test_rmse': np.sqrt(mean_squared_error(y_test, y_pred_test)),
            'n_samples': len(df),
            'n_features': len(feature_cols),
            'trained_at': datetime.now().isoformat()
        }

        # Feature importance - log sorted
        feature_importance = dict(zip(feature_cols, self.price_model.feature_importances_))
        sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)

        logger.success("Entrenamiento completado")
        logger.info(f"  R2 Test: {metrics['test_r2']:.4f}")
        logger.info(f"  MAE Test: ${metrics['test_mae']:,.0f} MXN/m2")
        logger.info(f"  RMSE Test: ${metrics['test_rmse']:,.0f} MXN/m2")

        logger.info("Feature importance:")
        for name, imp in sorted_features[:15]:
            logger.info(f"  {name}: {imp:.4f}")

        # Cross-validation con target log-transformado (consistente con entrenamiento)
        cv_scores = cross_val_score(self.price_model, X_train_scaled, y_train_log, cv=5, scoring='r2')

        # Guardar modelo
        model_file_path = self.save_model()

        # Save metrics to JSON alongside the model
        model_path = Path(model_file_path)
        saved_metrics = {
            "version": self.model_version,
            "trained_at": datetime.now().isoformat(),
            "r2_score": float(metrics['test_r2']),
            "mae": float(metrics['test_mae']),
            "mse": float(metrics['test_rmse'] ** 2),
            "cross_val_mean": float(cv_scores.mean()),
            "cross_val_std": float(cv_scores.std()),
            "n_samples": len(X_train) + len(X_test),
            "n_features": X_train.shape[1],
            "feature_names": list(self.feature_names) if hasattr(self.feature_names, '__iter__') else [],
            "feature_importance": {name: float(imp) for name, imp in sorted_features},
        }
        metrics_path = model_path.with_suffix('.metrics.json')
        with open(metrics_path, 'w') as f:
            json.dump(saved_metrics, f, indent=2)
        logger.info(f"Model metrics saved: R2={metrics['test_r2']:.4f}, MAE={metrics['test_mae']:.2f}, MSE={saved_metrics['mse']:.2f}")

        return metrics

    # ================================================================
    # State price distribution for percentile-based plusvalia
    # ================================================================

    def _build_state_price_distributions(self, df_features: pd.DataFrame):
        """Build per-state price_m2 distributions from training data."""
        self._state_price_distributions.clear()
        if 'state' in df_features.columns and 'price_m2' in df_features.columns:
            for state, group in df_features.groupby('state'):
                prices = group['price_m2'].dropna().values
                if len(prices) >= 5:
                    self._state_price_distributions[str(state)] = np.sort(prices)
            logger.info(
                f"Built price distributions for {len(self._state_price_distributions)} states"
            )

    def _compute_plusvalia_score(self, predicted_price_m2: float, state: str) -> float:
        """Compute plusvalia score as percentile rank within the state.

        Returns a score 0-100 representing how this property's predicted
        price_m2 compares to the distribution of prices in the same state.
        """
        dist = self._state_price_distributions.get(state)
        if dist is not None and len(dist) > 0:
            # Percentile rank: fraction of state prices that are <= predicted
            rank = np.searchsorted(dist, predicted_price_m2, side='right')
            percentile = (rank / len(dist)) * 100.0
            return min(100.0, max(0.0, percentile))

        # Fallback: use national-level heuristic if no state data
        # Approximate national median ~5000 MXN/m2, P90 ~15000
        # Map predicted price to a 0-100 scale using a log transform
        if predicted_price_m2 <= 0:
            return 0.0
        log_price = math.log(predicted_price_m2)
        # log(1000)=6.9, log(5000)=8.5, log(15000)=9.6, log(50000)=10.8
        score = ((log_price - 6.9) / (10.8 - 6.9)) * 100.0
        return min(100.0, max(0.0, score))

    def predict_price(
        self,
        lat: float,
        lon: float,
        area_m2: float,
        city: str,
        state: str,
        **kwargs
    ) -> Dict:
        """
        Predice el precio de un terreno.

        Uses the same prepare_features() pipeline as train() to guarantee
        feature consistency.

        Args:
            lat: Latitud
            lon: Longitud
            area_m2: Superficie en m2
            city: Ciudad
            state: Estado
            **kwargs: Features adicionales

        Returns:
            Diccionario con prediccion y metadatos
        """
        if self.price_model is None:
            raise ValueError("Modelo no entrenado. Ejecutar train() primero.")

        # Crear DataFrame con los datos de entrada
        # Provide sensible defaults for new features if not in kwargs
        defaults = {
            'property_type': 'terreno',
            'year': datetime.now().year,
            'collection_date': datetime.now().strftime('%Y-%m-%d'),
        }
        merged = {**defaults, **kwargs}
        input_data = pd.DataFrame([{
            'lat': lat,
            'lon': lon,
            'area_m2': area_m2,
            'price_mxn': area_m2 * 1000,  # Placeholder for price_m2 calc
            'city': city,
            'state': state,
            **merged
        }])

        # Preparar features (same pipeline as training, no target_series for prediction)
        df_features = self.prepare_features(input_data)

        # Extraer features usadas en entrenamiento
        X = df_features[self.feature_names].fillna(0)
        X_scaled = self.scaler.transform(X)

        # Prediccion: el modelo predice en escala log, revertir a escala original
        predicted_log = self.price_model.predict(X_scaled)[0]
        predicted_price_m2 = float(np.expm1(predicted_log))
        predicted_total_price = predicted_price_m2 * area_m2

        # V3: Percentile-based plusvalia score
        plusvalia_score = self._compute_plusvalia_score(predicted_price_m2, state)

        # Categorize growth potential using config thresholds
        thresholds = MODEL_CONFIG.get("thresholds", {}).get("plusvalia_score", {})
        muy_alto_threshold = thresholds.get("muy_alto", 75)
        alto_threshold = thresholds.get("alto", 60)
        medio_threshold = thresholds.get("medio", 40)

        if plusvalia_score >= muy_alto_threshold:
            growth_potential = 'muy_alto'
        elif plusvalia_score >= alto_threshold:
            growth_potential = 'alto'
        elif plusvalia_score >= medio_threshold:
            growth_potential = 'medio'
        else:
            growth_potential = 'bajo'

        # Calcular confianza desde predicciones de arboles individuales (escala original)
        if hasattr(self.price_model, 'estimators_'):
            tree_predictions = [float(np.expm1(tree.predict(X_scaled)[0])) for tree in self.price_model.estimators_]
            std_dev = float(np.std(tree_predictions))
            mean_pred = float(np.mean(tree_predictions))
            cv = std_dev / max(mean_pred, 1.0)  # coefficient of variation
            confidence = max(50.0, min(99.0, 100.0 - (cv * 100.0)))
        else:
            confidence = 75.0

        # Build demographics info for response
        demo = self._get_demographics(city, state)

        result = {
            'predicted_price_m2': round(predicted_price_m2, 2),
            'predicted_total_price': round(predicted_total_price, 2),
            'plusvalia_score': round(plusvalia_score, 2),
            'growth_potential': growth_potential,
            'confidence': confidence,
            'model_version': self.model_version,
            'features_used': {
                'area_m2': area_m2,
                'distance_to_center': float(df_features['distance_to_center'].iloc[0]),
                'city': city,
                'state': state,
                'population_density': demo['population_density'],
                'economic_level_score': demo['economic_level_score'],
                'security_score': demo['security_score'],
                'infrastructure_score': demo['infrastructure_score'],
            }
        }

        return result

    def save_model(self, filename: str = None):
        """Guarda el modelo entrenado"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"plusvalia_model_v{self.model_version}_{timestamp}.pkl"

        filepath = Path(filename)
        model_file = filepath if filepath.is_absolute() else self.model_path / filepath.name

        model_data = {
            'price_model': self.price_model,
            'scaler': self.scaler,
            'target_encoders': self.target_encoders,
            # Keep label_encoders key for backward compat when loading V2 models
            'label_encoders': self.label_encoders,
            'feature_names': self.feature_names,
            'model_version': self.model_version,
            'state_price_distributions': self._state_price_distributions,
            'saved_at': datetime.now().isoformat()
        }

        joblib.dump(model_data, model_file)
        logger.success(f"Modelo guardado en: {model_file}")

        return str(model_file)

    def explain_prediction(
        self,
        lat: float,
        lon: float,
        area_m2: float,
        city: str,
        state: str,
        **kwargs
    ) -> Dict:
        """
        Genera explicacion SHAP para una prediccion individual.

        Args:
            lat: Latitud
            lon: Longitud
            area_m2: Superficie en m2
            city: Ciudad
            state: Estado

        Returns:
            Diccionario con valores SHAP, prediccion y metadatos
        """
        if self.price_model is None:
            raise ValueError("Modelo no entrenado. Ejecutar train() primero.")

        try:
            import shap
        except ImportError:
            raise ImportError("shap no esta instalado. Ejecutar: pip install shap")

        # Preparar input
        input_data = pd.DataFrame([{
            'lat': lat, 'lon': lon, 'area_m2': area_m2,
            'price_mxn': area_m2 * 1000,
            'city': city, 'state': state, **kwargs
        }])

        df_features = self.prepare_features(input_data)
        X = df_features[self.feature_names].fillna(0)
        X_scaled = self.scaler.transform(X)

        # Calcular SHAP values con TreeExplainer (rapido para RandomForest)
        explainer = shap.TreeExplainer(self.price_model)
        shap_values = explainer.shap_values(X_scaled)

        # Construir explicacion por feature
        feature_explanations = []
        for i, feature_name in enumerate(self.feature_names):
            shap_val = float(shap_values[0][i])
            raw_val = float(X.iloc[0][feature_name])
            feature_explanations.append({
                'feature': feature_name,
                'value': round(raw_val, 4),
                'shap_value': round(shap_val, 2),
                'impact': 'positive' if shap_val > 0 else 'negative',
                'abs_importance': round(abs(shap_val), 2)
            })

        # Ordenar por importancia absoluta
        feature_explanations.sort(key=lambda x: x['abs_importance'], reverse=True)

        # Prediccion base (expected value)
        base_value = float(explainer.expected_value)
        predicted_price_m2 = float(self.price_model.predict(X_scaled)[0])

        return {
            'predicted_price_m2': round(predicted_price_m2, 2),
            'base_value': round(base_value, 2),
            'feature_explanations': feature_explanations,
            'top_positive_factors': [
                f for f in feature_explanations if f['impact'] == 'positive'
            ][:3],
            'top_negative_factors': [
                f for f in feature_explanations if f['impact'] == 'negative'
            ][:3],
            'model_version': self.model_version,
            'explanation_method': 'SHAP (TreeExplainer)'
        }

    def load_model(self, filename: str):
        """Carga un modelo previamente entrenado"""
        model_file = self.model_path / filename

        if not model_file.exists():
            raise FileNotFoundError(f"Modelo no encontrado: {model_file}")

        logger.info(f"Cargando modelo desde: {model_file}")

        model_data = joblib.load(model_file)

        self.price_model = model_data['price_model']
        self.scaler = model_data['scaler']
        # V3: load target encoders; fall back to label_encoders for V2 compat
        self.target_encoders = model_data.get('target_encoders', {})
        self.label_encoders = model_data.get('label_encoders', {})
        self.feature_names = model_data['feature_names']
        self.model_version = model_data['model_version']
        self._state_price_distributions = model_data.get('state_price_distributions', {})

        logger.success(f"Modelo cargado (version {self.model_version})")


# ================================================================
# SCRIPT DE ENTRENAMIENTO
# ================================================================

def main():
    """
    Script principal para entrenar el modelo
    """
    from supabase import create_client
    from config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

    logger.info("Iniciando entrenamiento del modelo ML V3")

    # 1. Conectar a Supabase
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

    # 2. Obtener datos de entrenamiento
    logger.info("Obteniendo datos de entrenamiento desde Supabase...")
    response = supabase.table('iainmobiliaria_comparables').select('*').execute()

    if not response.data:
        logger.error("No hay datos para entrenar")
        return

    df = pd.DataFrame(response.data)
    logger.info(f"Datos obtenidos: {len(df)} registros")

    # 3. Entrenar modelo
    model = PlusvaliaPredictorModel(model_version="3.0")
    metrics = model.train(df)

    # 4. Prueba de prediccion
    logger.info("\nPrueba de prediccion:")
    test_prediction = model.predict_price(
        lat=20.5888,
        lon=-100.3899,
        area_m2=500,
        city="Querétaro",
        state="Querétaro"
    )

    logger.info(f"  Precio/m2: ${test_prediction['predicted_price_m2']:,.0f} MXN")
    logger.info(f"  Precio total: ${test_prediction['predicted_total_price']:,.0f} MXN")
    logger.info(f"  Score plusvalia: {test_prediction['plusvalia_score']:.1f}/100")
    logger.info(f"  Potencial: {test_prediction['growth_potential']}")
    logger.info(f"  Confianza: {test_prediction['confidence']:.1f}%")

    logger.success("\nEntrenamiento completado exitosamente")


if __name__ == "__main__":
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )

    main()
