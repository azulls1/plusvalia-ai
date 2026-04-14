"""
LightGBM Model para geo-app.
Alternativa mas rapida a XGBoost con mejor manejo de features categoricos y dispersos.
Soporta el mismo pipeline jerarquico (Global + Cluster + Estado).
"""

import math
import numpy as np
import pandas as pd
import joblib
import json
import yaml
import warnings
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from loguru import logger
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error

try:
    import lightgbm as lgb
    _HAS_LIGHTGBM = True
except ImportError:
    _HAS_LIGHTGBM = False
    logger.warning("LightGBM no instalado; LightGBMPredictor no funcionara")

try:
    from xgboost import XGBRegressor
    _HAS_XGBOOST = True
except ImportError:
    _HAS_XGBOOST = False

warnings.filterwarnings("ignore")

# ================================================================
# Constantes
# ================================================================

_CONFIG_PATH = Path(__file__).parent / "model_config.yaml"
_MODELS_DIR = Path(__file__).parent / "models"


def _load_config() -> dict:
    """Carga configuracion desde YAML."""
    if _CONFIG_PATH.exists():
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


# Importar utilidades compartidas del predictor existente
from ml_model.predictor import CITY_CENTERS


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula distancia haversine entre dos puntos en km."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(min(1.0, math.sqrt(a)))


def _distance_to_center(lat: float, lon: float, city: str) -> float:
    """Distancia al centro de la ciudad mas cercana."""
    center = CITY_CENTERS.get(city)
    if not center:
        for c, coords in CITY_CENTERS.items():
            if city and city.lower() in c.lower():
                center = coords
                break
    if not center:
        return 5.0
    return _haversine_km(lat, lon, center[0], center[1])


# ================================================================
# LightGBMPredictor
# ================================================================

class LightGBMPredictor:
    """Predictor basado en LightGBM con soporte nativo para categoricos.

    Ventajas sobre XGBoost:
        - Entrenamiento mas rapido (especialmente con datos grandes)
        - Manejo nativo de features categoricos (sin necesidad de target encoding)
        - Mejor manejo de features dispersos (sparse)
        - Menor uso de memoria

    Interfaz compatible con HierarchicalPredictor para intercambio directo.
    """

    # Atributo sentinel para duck-typing con PlusvaliaPredictorModel
    price_model = None

    # Hiperparametros por defecto
    DEFAULT_PARAMS: Dict[str, Any] = {
        'objective': 'regression',
        'metric': 'mae',
        'boosting_type': 'gbdt',
        'num_leaves': 63,
        'learning_rate': 0.05,
        'feature_fraction': 0.8,
        'bagging_fraction': 0.8,
        'bagging_freq': 5,
        'verbose': -1,
        'n_estimators': 500,
        'early_stopping_rounds': 50,
    }

    def __init__(
        self,
        model_version: str = "4.0-lgbm",
        params: Optional[Dict[str, Any]] = None,
    ):
        self.model_version = model_version

        # Configuracion desde YAML
        config = _load_config()
        self._cluster_config = config.get("clusters", {})

        # Parametros del modelo (merge usuario + defaults)
        self.params = {**self.DEFAULT_PARAMS}
        if params:
            self.params.update(params)

        # Mapeo estado -> cluster
        self._state_to_cluster: Dict[str, str] = {}
        for cluster_name, cdata in self._cluster_config.items():
            for state in cdata.get("states", []):
                self._state_to_cluster[state] = cluster_name

        # Modelo entrenado
        self.model: Optional[lgb.LGBMRegressor] = None
        self.scaler = StandardScaler()
        self.label_encoders: Dict[str, LabelEncoder] = {}
        self.feature_names: List[str] = []
        self.categorical_features: List[str] = []

        # Cache de demograficos
        self._demographics_cache: Dict[str, dict] = {}

        # Ruta de modelos
        self.model_path = _MODELS_DIR
        self.model_path.mkdir(parents=True, exist_ok=True)

        # Metricas de entrenamiento
        self._training_metrics: Dict = {}

        # Log transform habilitado
        self._use_log_transform: bool = True
        self._y_mean: float = 0.0

    # ------------------------------------------------------------------
    # Demograficos (reutiliza logica del predictor existente)
    # ------------------------------------------------------------------

    def _preload_all_demographics(self) -> None:
        """Carga todos los demograficos de BD en una sola query."""
        if self._demographics_cache:
            return
        try:
            import sys
            sys.path.append("..")
            from config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
            from supabase import create_client
            sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
            result = sb.table("iainmobiliaria_demographics").select("*").execute()
            if result.data:
                for d in result.data:
                    key = f"{d['city']}|{d['state']}"
                    self._demographics_cache[key] = {
                        "population_density": d.get("population_density", 1500),
                        "economic_level_score": self._compute_economic_score(d),
                        "unemployment_rate": d.get("unemployment_rate", 4.0),
                        "avg_income": d.get("avg_income_mxn", 8000),
                        "education_index": d.get("pct_education_superior", 15) / 100,
                        "security_score": d.get("security_perception_score", 50),
                        "infrastructure_score": (
                            d.get("pct_water_access", 95)
                            + d.get("pct_electricity", 99)
                            + d.get("pct_drainage", 95)
                            + d.get("pct_internet", 60)
                        ) / 4,
                        "pct_vacant_housing": d.get("pct_vacant_housing", 8),
                        "population_growth": d.get("population_growth_5yr_pct", 1.0),
                        "median_age": d.get("median_age", 30),
                        "homicide_rate_per_100k": d.get("homicide_rate_per_100k", 15.0),
                        "pct_internet": d.get("pct_internet", 60),
                        "pea_pct": d.get("pea_pct", 55.0),
                    }
                logger.info(f"Demograficos precargados para {len(result.data)} ciudades")
        except Exception as e:
            logger.warning(f"No se pudieron precargar demograficos: {e}")

    @staticmethod
    def _compute_economic_score(demographics: dict) -> float:
        """Calcula score economico compuesto."""
        income = demographics.get("avg_income_mxn", 8000)
        education = demographics.get("pct_education_superior", 15)
        marginacion = demographics.get("grado_marginacion", "bajo")
        margin_map = {"muy_bajo": 9, "bajo": 7, "medio": 5, "alto": 3, "muy_alto": 1}
        margin_score = margin_map.get(marginacion, 5)
        income_score = min(10, income / 1500)
        edu_score = min(10, education / 3.5)
        return round(margin_score * 0.4 + income_score * 0.35 + edu_score * 0.25, 1)

    def _get_demographics(self, city: str, state: str) -> dict:
        """Obtiene demograficos para una ciudad/estado."""
        if not self._demographics_cache:
            self._preload_all_demographics()
        cache_key = f"{city}|{state}"
        if cache_key in self._demographics_cache:
            return self._demographics_cache[cache_key]
        # Busqueda parcial
        for key, demo in self._demographics_cache.items():
            if city and city.lower() in key.lower():
                self._demographics_cache[cache_key] = demo
                return demo
        # Fallback con valores por defecto
        fallback = {
            "population_density": 1500, "economic_level_score": 5,
            "unemployment_rate": 4.0, "avg_income": 8000,
            "education_index": 0.15, "security_score": 50,
            "infrastructure_score": 85, "pct_vacant_housing": 8,
            "population_growth": 1.0, "median_age": 30,
            "homicide_rate_per_100k": 15.0, "pct_internet": 60,
            "pea_pct": 55.0,
        }
        self._demographics_cache[cache_key] = fallback
        return fallback

    # ------------------------------------------------------------------
    # Preparacion de features
    # ------------------------------------------------------------------

    def prepare_features(
        self, df: pd.DataFrame, fit_encoders: bool = False,
    ) -> pd.DataFrame:
        """Prepara la matriz de features completa.

        Usa soporte nativo de LightGBM para categoricos cuando es posible.
        """
        df_f = df.copy()

        # Calcular price_m2 si no existe
        if "price_mxn" in df_f.columns and "area_m2" in df_f.columns:
            df_f["price_m2"] = df_f["price_mxn"] / df_f["area_m2"].replace(0, np.nan)

        # Features core
        df_f["log_area"] = np.log1p(df_f["area_m2"])
        df_f["is_large_lot"] = (df_f["area_m2"] > df_f["area_m2"].median()).astype(int)

        # Distancia al centro
        if {"lat", "lon", "city"}.issubset(df_f.columns):
            df_f["distance_to_center"] = df_f.apply(
                lambda r: _distance_to_center(r["lat"], r["lon"], r.get("city", "")),
                axis=1,
            )
        else:
            df_f["distance_to_center"] = 0.0

        # Lat/lon normalizados (rango Mexico)
        if "lat" in df_f.columns and "lon" in df_f.columns:
            df_f["lat_normalized"] = (df_f["lat"] - 14) / (33 - 14)
            df_f["lon_normalized"] = (df_f["lon"] - (-118)) / ((-86) - (-118))
        else:
            df_f["lat_normalized"] = 0.5
            df_f["lon_normalized"] = 0.5

        # Demograficos
        if "city" in df_f.columns:
            demos = df_f.apply(
                lambda r: self._get_demographics(r.get("city", ""), r.get("state", "")),
                axis=1,
            )
            demo_keys = [
                "population_density", "economic_level_score", "unemployment_rate",
                "avg_income", "education_index", "security_score",
                "infrastructure_score", "pct_vacant_housing", "population_growth",
                "median_age", "homicide_rate_per_100k", "pct_internet", "pea_pct",
            ]
            for k in demo_keys:
                df_f[k] = demos.apply(lambda d: d.get(k, 0))
        else:
            fallback = self._get_demographics("", "")
            for k, v in fallback.items():
                df_f[k] = v

        # Features temporales
        if "collection_date" in df_f.columns:
            dates = pd.to_datetime(df_f["collection_date"], errors="coerce")
            df_f["month"] = dates.dt.month.fillna(6).astype(int)
            df_f["quarter"] = dates.dt.quarter.fillna(2).astype(int)
        else:
            df_f["month"] = 6
            df_f["quarter"] = 2

        # Features de interaccion
        if "area_m2" in df_f.columns and "avg_income" in df_f.columns:
            df_f["area_x_income"] = df_f["area_m2"] * df_f["avg_income"]
        if "distance_to_center" in df_f.columns and "population_density" in df_f.columns:
            df_f["distance_x_density"] = df_f["distance_to_center"] * df_f["population_density"]

        # Categoricos: LightGBM los maneja nativamente con label encoding
        for col in ["city", "state"]:
            if col in df_f.columns:
                if fit_encoders or col not in self.label_encoders:
                    self.label_encoders[col] = LabelEncoder()
                    df_f[f"{col}_encoded"] = self.label_encoders[col].fit_transform(
                        df_f[col].astype(str)
                    )
                else:
                    known = set(self.label_encoders[col].classes_)
                    safe = df_f[col].astype(str).apply(
                        lambda v: v if v in known else self.label_encoders[col].classes_[0]
                    )
                    df_f[f"{col}_encoded"] = self.label_encoders[col].transform(safe)

        return df_f

    # ------------------------------------------------------------------
    # Columnas de features
    # ------------------------------------------------------------------

    def _get_feature_columns(self, df: pd.DataFrame) -> List[str]:
        """Retorna las columnas de features disponibles en el DataFrame."""
        candidate_cols = [
            # Core
            "area_m2", "log_area", "is_large_lot",
            # Ubicacion
            "distance_to_center", "lat_normalized", "lon_normalized",
            # Demograficos
            "population_density", "economic_level_score",
            "unemployment_rate", "avg_income", "education_index",
            "security_score", "infrastructure_score",
            "pct_vacant_housing", "population_growth",
            "median_age", "homicide_rate_per_100k", "pct_internet", "pea_pct",
            # Temporales
            "month", "quarter",
            # Interaccion
            "area_x_income", "distance_x_density",
            # Categoricos encoded
            "city_encoded", "state_encoded",
        ]
        return [c for c in candidate_cols if c in df.columns]

    # ------------------------------------------------------------------
    # Entrenamiento
    # ------------------------------------------------------------------

    def train(
        self,
        df: pd.DataFrame,
        target_col: str = "price_m2",
        test_size: float = 0.2,
    ) -> Dict:
        """Entrena el modelo LightGBM con log-transform del target.

        Args:
            df: DataFrame con datos de propiedades
            target_col: Columna objetivo (precio por m2)
            test_size: Fraccion para test set

        Returns:
            dict con metricas de entrenamiento
        """
        if not _HAS_LIGHTGBM:
            raise ImportError("LightGBM es requerido. Instalar: pip install lightgbm")

        logger.info(f"=== LightGBMPredictor entrenamiento con {len(df)} muestras ===")

        if len(df) < 20:
            raise ValueError(f"Se necesitan al menos 20 muestras (recibidas: {len(df)})")

        # Limpiar cache
        self._demographics_cache.clear()

        # Preparar datos
        df_work = df.copy()
        if "price_m2" not in df_work.columns and "price_mxn" in df_work.columns:
            df_work["price_m2"] = df_work["price_mxn"] / df_work["area_m2"].replace(0, np.nan)
            df_work = df_work.dropna(subset=["price_m2"])

        # Preparar features
        logger.info("Preparando features...")
        df_features = self.prepare_features(df_work, fit_encoders=True)

        # Seleccionar columnas
        feature_cols = self._get_feature_columns(df_features)
        self.feature_names = feature_cols
        logger.info(f"Usando {len(feature_cols)} features: {feature_cols}")

        X = df_features[feature_cols].fillna(0)
        y = df_features[target_col].copy()

        # Filtrar valores invalidos
        valid_mask = (y > 0) & y.notna()
        X = X[valid_mask]
        y = y[valid_mask]

        # Log-transform del target para mejor distribucion
        if self._use_log_transform:
            self._y_mean = float(y.mean())
            y_transformed = np.log1p(y)
        else:
            y_transformed = y

        # Escalar features
        X_scaled = pd.DataFrame(
            self.scaler.fit_transform(X), columns=feature_cols, index=X.index,
        )

        # Split train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y_transformed, test_size=test_size, random_state=42,
        )

        # Identificar features categoricos para LightGBM
        cat_feature_indices = [
            i for i, col in enumerate(feature_cols)
            if col in ["city_encoded", "state_encoded"]
        ]
        self.categorical_features = [
            feature_cols[i] for i in cat_feature_indices
        ]

        # Crear y entrenar modelo
        train_params = {k: v for k, v in self.params.items()
                        if k != 'early_stopping_rounds'}
        self.model = lgb.LGBMRegressor(**train_params)

        # Entrenar con early stopping
        self.model.fit(
            X_train, y_train,
            eval_set=[(X_test, y_test)],
            categorical_feature=cat_feature_indices if cat_feature_indices else "auto",
            callbacks=[
                lgb.early_stopping(self.params.get('early_stopping_rounds', 50)),
                lgb.log_evaluation(period=0),  # Silenciar logs
            ],
        )

        # Marcar modelo como entrenado
        self.price_model = True

        # Predicciones en test
        y_pred_transformed = self.model.predict(X_test)

        # Invertir log-transform para metricas en escala original
        if self._use_log_transform:
            y_pred_original = np.expm1(y_pred_transformed)
            y_test_original = np.expm1(y_test)
        else:
            y_pred_original = y_pred_transformed
            y_test_original = y_test

        # Calcular metricas
        self._training_metrics = {
            "model_type": "LightGBM",
            "version": self.model_version,
            "n_samples": len(df),
            "n_features": len(feature_cols),
            "n_train": len(X_train),
            "n_test": len(X_test),
            "best_iteration": self.model.best_iteration_,
            "r2": float(r2_score(y_test_original, y_pred_original)),
            "mae": float(mean_absolute_error(y_test_original, y_pred_original)),
            "rmse": float(np.sqrt(mean_squared_error(y_test_original, y_pred_original))),
            "mape": float(np.mean(np.abs(
                (y_test_original - y_pred_original) / y_test_original.clip(lower=1)
            )) * 100),
            "trained_at": datetime.now().isoformat(),
            "feature_names": feature_cols,
        }

        logger.info(
            f"  LightGBM R2={self._training_metrics['r2']:.4f}  "
            f"MAE=${self._training_metrics['mae']:,.0f}  "
            f"RMSE=${self._training_metrics['rmse']:,.0f}  "
            f"MAPE={self._training_metrics['mape']:.1f}%  "
            f"Best iter={self._training_metrics['best_iteration']}"
        )

        return self._training_metrics

    # ------------------------------------------------------------------
    # Prediccion
    # ------------------------------------------------------------------

    def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Predice precio por m2 para un conjunto de features.

        Args:
            features: dict con features de la propiedad

        Returns:
            dict con prediccion, confianza e intervalo
        """
        if self.model is None:
            raise RuntimeError("Modelo no entrenado. Ejecutar train() primero.")

        # Crear DataFrame con una fila
        df_input = pd.DataFrame([features])
        df_prepared = self.prepare_features(df_input, fit_encoders=False)

        # Seleccionar features del modelo
        feature_cols = self.feature_names
        X = df_prepared[feature_cols].fillna(0)
        X_scaled = pd.DataFrame(
            self.scaler.transform(X), columns=feature_cols,
        )

        # Predecir
        y_pred_transformed = self.model.predict(X_scaled)[0]

        # Invertir log-transform
        if self._use_log_transform:
            price_m2 = float(np.expm1(y_pred_transformed))
        else:
            price_m2 = float(y_pred_transformed)

        # Asegurar precio positivo
        price_m2 = max(100.0, price_m2)

        # Calcular intervalo de confianza (basado en RMSE del entrenamiento)
        rmse = self._training_metrics.get("rmse", price_m2 * 0.15)
        ci_lower = max(100.0, price_m2 - 1.96 * rmse)
        ci_upper = price_m2 + 1.96 * rmse

        # Calcular confianza basada en la distancia al rango de entrenamiento
        confidence = min(0.95, max(0.3, 1.0 - (rmse / max(price_m2, 1.0))))

        return {
            "price_m2": round(price_m2, 2),
            "confidence": round(confidence, 3),
            "ci_lower": round(ci_lower, 2),
            "ci_upper": round(ci_upper, 2),
            "model_type": "LightGBM",
            "model_version": self.model_version,
        }

    # ------------------------------------------------------------------
    # Importancia de features
    # ------------------------------------------------------------------

    def get_feature_importance(self) -> Dict[str, float]:
        """Retorna importancia de cada feature ordenada de mayor a menor.

        Returns:
            dict {nombre_feature: importancia_normalizada}
        """
        if self.model is None:
            raise RuntimeError("Modelo no entrenado. Ejecutar train() primero.")

        # LightGBM provee importancia por ganancia (gain)
        importances = self.model.feature_importances_
        total = importances.sum()
        if total == 0:
            total = 1.0

        importance_dict = {
            name: round(float(imp / total), 4)
            for name, imp in zip(self.feature_names, importances)
        }

        # Ordenar por importancia descendente
        return dict(sorted(importance_dict.items(), key=lambda x: x[1], reverse=True))

    # ------------------------------------------------------------------
    # Comparacion con XGBoost
    # ------------------------------------------------------------------

    def compare_with_xgboost(
        self, df: pd.DataFrame, target_col: str = "price_m2",
    ) -> Dict[str, Any]:
        """Entrena ambos modelos y compara metricas lado a lado.

        Args:
            df: DataFrame con datos de propiedades
            target_col: Columna objetivo

        Returns:
            dict con metricas de LightGBM, XGBoost y diferencia porcentual
        """
        if not _HAS_XGBOOST:
            raise ImportError("XGBoost requerido para comparacion")
        if not _HAS_LIGHTGBM:
            raise ImportError("LightGBM requerido para comparacion")

        import time

        logger.info("=== Comparacion LightGBM vs XGBoost ===")

        # Preparar datos compartidos
        df_work = df.copy()
        if "price_m2" not in df_work.columns and "price_mxn" in df_work.columns:
            df_work["price_m2"] = df_work["price_mxn"] / df_work["area_m2"].replace(0, np.nan)
            df_work = df_work.dropna(subset=["price_m2"])

        # -- Entrenar LightGBM --
        logger.info("Entrenando LightGBM...")
        t0 = time.time()
        lgbm_metrics = self.train(df_work, target_col=target_col)
        lgbm_time = time.time() - t0

        # -- Entrenar XGBoost con los mismos datos --
        logger.info("Entrenando XGBoost para comparacion...")
        df_features = self.prepare_features(df_work, fit_encoders=False)
        feature_cols = self.feature_names
        X = df_features[feature_cols].fillna(0)
        y = df_features[target_col].copy()

        valid_mask = (y > 0) & y.notna()
        X = X[valid_mask]
        y = y[valid_mask]

        # Log-transform
        y_log = np.log1p(y)

        X_scaled = pd.DataFrame(
            self.scaler.transform(X), columns=feature_cols, index=X.index,
        )

        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y_log, test_size=0.2, random_state=42,
        )

        t0 = time.time()
        xgb_model = XGBRegressor(
            n_estimators=500, max_depth=8, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8,
            reg_alpha=0.1, reg_lambda=1.0,
            random_state=42, n_jobs=-1, verbosity=0,
            early_stopping_rounds=50,
        )
        xgb_model.fit(
            X_train, y_train,
            eval_set=[(X_test, y_test)],
            verbose=False,
        )
        xgb_time = time.time() - t0

        # Predicciones XGBoost
        xgb_pred = np.expm1(xgb_model.predict(X_test))
        y_test_original = np.expm1(y_test)

        xgb_metrics = {
            "r2": float(r2_score(y_test_original, xgb_pred)),
            "mae": float(mean_absolute_error(y_test_original, xgb_pred)),
            "rmse": float(np.sqrt(mean_squared_error(y_test_original, xgb_pred))),
        }

        # Comparativa
        comparison = {
            "lightgbm": {
                "r2": lgbm_metrics["r2"],
                "mae": lgbm_metrics["mae"],
                "rmse": lgbm_metrics["rmse"],
                "training_time_seconds": round(lgbm_time, 2),
                "best_iteration": lgbm_metrics.get("best_iteration"),
            },
            "xgboost": {
                "r2": xgb_metrics["r2"],
                "mae": xgb_metrics["mae"],
                "rmse": xgb_metrics["rmse"],
                "training_time_seconds": round(xgb_time, 2),
                "best_iteration": xgb_model.best_iteration,
            },
            "diferencia_porcentual": {
                "r2": round((lgbm_metrics["r2"] - xgb_metrics["r2"]) / max(abs(xgb_metrics["r2"]), 0.001) * 100, 2),
                "mae": round((xgb_metrics["mae"] - lgbm_metrics["mae"]) / max(xgb_metrics["mae"], 1) * 100, 2),
                "rmse": round((xgb_metrics["rmse"] - lgbm_metrics["rmse"]) / max(xgb_metrics["rmse"], 1) * 100, 2),
                "velocidad": round((xgb_time - lgbm_time) / max(xgb_time, 0.001) * 100, 2),
            },
            "ganador": "lightgbm" if lgbm_metrics["r2"] >= xgb_metrics["r2"] else "xgboost",
            "n_samples": len(df_work),
            "timestamp": datetime.now().isoformat(),
        }

        logger.info(
            f"Comparacion completada:\n"
            f"  LightGBM: R2={comparison['lightgbm']['r2']:.4f}, "
            f"MAE=${comparison['lightgbm']['mae']:,.0f}, "
            f"Tiempo={comparison['lightgbm']['training_time_seconds']}s\n"
            f"  XGBoost:  R2={comparison['xgboost']['r2']:.4f}, "
            f"MAE=${comparison['xgboost']['mae']:,.0f}, "
            f"Tiempo={comparison['xgboost']['training_time_seconds']}s\n"
            f"  Ganador: {comparison['ganador']}"
        )

        return comparison

    # ------------------------------------------------------------------
    # Persistencia
    # ------------------------------------------------------------------

    def save_model(self, path: Optional[Path] = None) -> Path:
        """Guarda el modelo entrenado a disco."""
        save_dir = path or self.model_path
        save_dir.mkdir(parents=True, exist_ok=True)

        model_file = save_dir / "lightgbm_model.joblib"
        metadata = {
            "model": self.model,
            "scaler": self.scaler,
            "label_encoders": self.label_encoders,
            "feature_names": self.feature_names,
            "categorical_features": self.categorical_features,
            "params": self.params,
            "training_metrics": self._training_metrics,
            "model_version": self.model_version,
            "use_log_transform": self._use_log_transform,
            "y_mean": self._y_mean,
        }
        joblib.dump(metadata, model_file)
        logger.info(f"Modelo LightGBM guardado en: {model_file}")
        return model_file

    def load_model(self, path: Optional[Path] = None) -> bool:
        """Carga un modelo previamente guardado."""
        load_dir = path or self.model_path
        model_file = load_dir / "lightgbm_model.joblib"

        if not model_file.exists():
            logger.warning(f"No se encontro modelo en: {model_file}")
            return False

        try:
            metadata = joblib.load(model_file)
            self.model = metadata["model"]
            self.scaler = metadata["scaler"]
            self.label_encoders = metadata["label_encoders"]
            self.feature_names = metadata["feature_names"]
            self.categorical_features = metadata.get("categorical_features", [])
            self.params = metadata.get("params", self.DEFAULT_PARAMS)
            self._training_metrics = metadata.get("training_metrics", {})
            self.model_version = metadata.get("model_version", "4.0-lgbm")
            self._use_log_transform = metadata.get("use_log_transform", True)
            self._y_mean = metadata.get("y_mean", 0.0)
            self.price_model = True
            logger.info(f"Modelo LightGBM cargado desde: {model_file}")
            return True
        except Exception as e:
            logger.error(f"Error cargando modelo LightGBM: {e}")
            return False
