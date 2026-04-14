# ================================================================
# HIERARCHICAL MODEL ARCHITECTURE
# Global + Cluster + State models with alpha-blending
# Drop-in replacement for PlusvaliaPredictorModel
# ================================================================

import math
import numpy as np
import pandas as pd
import joblib
import json
import yaml
import warnings
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from loguru import logger
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error

try:
    from xgboost import XGBRegressor
    _HAS_XGBOOST = True
except ImportError:
    _HAS_XGBOOST = False
    logger.warning("XGBoost not installed; HierarchicalPredictor will not work")

from ml_model.spatial_features import SpatialFeatureEngine

warnings.filterwarnings("ignore")

# ================================================================
# Constants
# ================================================================

_CONFIG_PATH = Path(__file__).parent / "model_config.yaml"
_MODELS_DIR = Path(__file__).parent / "models"


def _load_config() -> dict:
    if _CONFIG_PATH.exists():
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


# ================================================================
# City centers (imported from predictor for Haversine)
# ================================================================
from ml_model.predictor import CITY_CENTERS


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(min(1.0, math.sqrt(a)))


def _distance_to_center(lat: float, lon: float, city: str) -> float:
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
# HierarchicalPredictor
# ================================================================

class HierarchicalPredictor:
    """Hierarchical XGBoost prediction system.

    Levels:
        1. Global model  (all data)
        2. Cluster models (7 economic clusters)
        3. State models   (states with 500+ samples)

    Blending:
        If state model exists:
            final = alpha * state_pred + (1 - alpha) * cluster_pred
        Else:
            final = cluster_pred

        alpha = min(1.0, n_state_samples / 2000) * min(1.0, state_r2 / max(cluster_r2, 0.01))

    The class exposes the same public interface as PlusvaliaPredictorModel
    (predict_price, explain_prediction, save_model, load_model, train)
    so the API layer can use it as a drop-in replacement.
    """

    # Attributes that mirror PlusvaliaPredictorModel for duck-typing
    price_model = None  # Set to a truthy sentinel after training

    def __init__(self, model_version: str = "3.0"):
        self.model_version = model_version

        # Config
        config = _load_config()
        self._cluster_config = config.get("clusters", {})
        self._model_params = config.get("model", {})

        # Build state -> cluster mapping
        self._state_to_cluster: Dict[str, str] = {}
        for cluster_name, cdata in self._cluster_config.items():
            for state in cdata.get("states", []):
                self._state_to_cluster[state] = cluster_name

        # Models
        self.global_model: Optional[XGBRegressor] = None
        self.cluster_models: Dict[str, XGBRegressor] = {}
        self.state_models: Dict[str, XGBRegressor] = {}
        self.state_alpha: Dict[str, float] = {}

        # Shared preprocessing
        self.scaler = StandardScaler()
        self.label_encoders: Dict[str, LabelEncoder] = {}
        self.feature_names: List[str] = []

        # Spatial engine
        self.spatial_engine = SpatialFeatureEngine()

        # Demographics cache (same as predictor.py)
        self._demographics_cache: Dict[str, dict] = {}

        # Model path
        self.model_path = _MODELS_DIR
        self.model_path.mkdir(parents=True, exist_ok=True)

        # Metrics
        self._training_metrics: Dict = {}

    # ------------------------------------------------------------------
    # Cluster lookup
    # ------------------------------------------------------------------

    def _get_cluster(self, state: str) -> str:
        """Return the economic cluster for a state, or 'unknown'."""
        return self._state_to_cluster.get(state, "unknown")

    # ------------------------------------------------------------------
    # Demographics (reuse logic from predictor.py)
    # ------------------------------------------------------------------

    def _preload_all_demographics(self):
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
                    }
                logger.info(f"Demographics preloaded for {len(result.data)} cities")
        except Exception as e:
            logger.warning(f"Could not preload demographics: {e}")

    @staticmethod
    def _compute_economic_score(demographics: dict) -> float:
        income = demographics.get("avg_income_mxn", 8000)
        education = demographics.get("pct_education_superior", 15)
        marginacion = demographics.get("grado_marginacion", "bajo")
        margin_map = {"muy_bajo": 9, "bajo": 7, "medio": 5, "alto": 3, "muy_alto": 1}
        margin_score = margin_map.get(marginacion, 5)
        income_score = min(10, income / 1500)
        edu_score = min(10, education / 3.5)
        return round(margin_score * 0.4 + income_score * 0.35 + edu_score * 0.25, 1)

    def _get_demographics(self, city: str, state: str) -> dict:
        if not self._demographics_cache:
            self._preload_all_demographics()
        cache_key = f"{city}|{state}"
        if cache_key in self._demographics_cache:
            return self._demographics_cache[cache_key]
        for key, demo in self._demographics_cache.items():
            if city and city.lower() in key.lower():
                self._demographics_cache[cache_key] = demo
                return demo
        fallback = {
            "population_density": 1500, "economic_level_score": 5,
            "unemployment_rate": 4.0, "avg_income": 8000,
            "education_index": 0.15, "security_score": 50,
            "infrastructure_score": 85, "pct_vacant_housing": 8,
            "population_growth": 1.0,
        }
        self._demographics_cache[cache_key] = fallback
        return fallback

    # ------------------------------------------------------------------
    # Feature preparation (mirrors PlusvaliaPredictorModel.prepare_features)
    # ------------------------------------------------------------------

    def prepare_features(self, df: pd.DataFrame, fit_encoders: bool = False) -> pd.DataFrame:
        """Prepare the full feature matrix.

        Includes all features from predictor.py V2 **plus** spatial KNN
        features from SpatialFeatureEngine.
        """
        df_f = df.copy()

        # Core
        if "price_mxn" in df_f.columns and "area_m2" in df_f.columns:
            df_f["price_m2"] = df_f["price_mxn"] / df_f["area_m2"].replace(0, np.nan)
        df_f["log_area"] = np.log1p(df_f["area_m2"])
        df_f["is_large_lot"] = (df_f["area_m2"] > df_f["area_m2"].median()).astype(int)

        # Distance to center
        if {"lat", "lon", "city"}.issubset(df_f.columns):
            df_f["distance_to_center"] = df_f.apply(
                lambda r: _distance_to_center(r["lat"], r["lon"], r.get("city", "")),
                axis=1,
            )
        else:
            df_f["distance_to_center"] = 0.0

        # Normalised lat/lon
        if "lat" in df_f.columns and "lon" in df_f.columns:
            df_f["lat_normalized"] = (df_f["lat"] - 14) / (33 - 14)
            df_f["lon_normalized"] = (df_f["lon"] - (-118)) / ((-86) - (-118))
        else:
            df_f["lat_normalized"] = 0.5
            df_f["lon_normalized"] = 0.5

        # Demographics
        if "city" in df_f.columns:
            demos = df_f.apply(
                lambda r: self._get_demographics(r.get("city", ""), r.get("state", "")),
                axis=1,
            )
            for k in [
                "population_density", "economic_level_score", "unemployment_rate",
                "avg_income", "education_index", "security_score",
                "infrastructure_score", "pct_vacant_housing", "population_growth",
            ]:
                df_f[k] = demos.apply(lambda d: d[k])
        else:
            fallback = self._get_demographics("", "")
            for k, v in fallback.items():
                df_f[k] = v

        # Temporal
        if "collection_date" in df_f.columns:
            dates = pd.to_datetime(df_f["collection_date"], errors="coerce")
            df_f["month"] = dates.dt.month.fillna(6).astype(int)
            df_f["quarter"] = dates.dt.quarter.fillna(2).astype(int)
        else:
            df_f["month"] = 6
            df_f["quarter"] = 2

        # Encoded categoricals
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

        # Spatial KNN features (added by the spatial engine)
        if self.spatial_engine._is_fitted:
            df_f = self.spatial_engine.transform(df_f)

        return df_f

    # ------------------------------------------------------------------
    # XGBoost factory
    # ------------------------------------------------------------------

    def _make_xgb(self, level: str = "global") -> "XGBRegressor":
        """Create an XGBRegressor with config-driven hyperparameters."""
        params = self._model_params.get(level, {})
        return XGBRegressor(
            n_estimators=params.get("n_estimators", 500),
            max_depth=params.get("max_depth", 8),
            learning_rate=params.get("learning_rate", 0.05),
            subsample=0.8,
            colsample_bytree=0.8,
            reg_alpha=0.1,
            reg_lambda=1.0,
            random_state=42,
            n_jobs=-1,
            verbosity=0,
        )

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def train(
        self,
        df: pd.DataFrame,
        target_col: str = "price_m2",
        test_size: float = 0.2,
    ) -> Dict:
        """Train the full hierarchical model stack.

        1. Fit spatial engine on all data
        2. Prepare features
        3. Train global model
        4. Train cluster models
        5. Train state models (500+ samples)
        6. Compute alpha per state
        """
        if not _HAS_XGBOOST:
            raise ImportError("XGBoost is required for HierarchicalPredictor")

        logger.info(f"=== HierarchicalPredictor training with {len(df)} samples ===")

        if len(df) < 20:
            raise ValueError(f"Need at least 20 samples (got {len(df)})")

        # Clear caches
        self._demographics_cache.clear()

        # 0. Ensure price_m2 exists for spatial engine
        df_work = df.copy()
        if "price_m2" not in df_work.columns and "price_mxn" in df_work.columns:
            df_work["price_m2"] = df_work["price_mxn"] / df_work["area_m2"].replace(0, np.nan)
            df_work = df_work.dropna(subset=["price_m2"])

        # 1. Fit spatial engine on ALL data
        logger.info("Step 1: Fitting spatial feature engine...")
        self.spatial_engine.fit(df_work)

        # 2. Prepare features
        logger.info("Step 2: Preparing features...")
        df_features = self.prepare_features(df_work, fit_encoders=True)
        del df_work  # Free memory — no longer needed after feature preparation

        # Feature columns (V2 + spatial)
        feature_cols = [
            # Core
            "area_m2", "log_area", "is_large_lot",
            # Location
            "distance_to_center", "lat_normalized", "lon_normalized",
            # Demographics
            "population_density", "economic_level_score",
            "unemployment_rate", "avg_income", "education_index",
            "security_score", "infrastructure_score",
            "pct_vacant_housing", "population_growth",
            # Temporal
            "month", "quarter",
            # Categoricals
            "city_encoded", "state_encoded",
            # Spatial KNN
            "avg_price_m2_1km", "avg_price_m2_5km", "median_price_m2_5km",
            "comparable_count_1km", "comparable_count_5km", "price_trend_5km",
            "nearest_price_m2", "nearest_distance_km",
        ]
        feature_cols = [c for c in feature_cols if c in df_features.columns]
        self.feature_names = feature_cols
        logger.info(f"Using {len(feature_cols)} features: {feature_cols}")

        X = df_features[feature_cols].fillna(0)
        y = df_features[target_col]

        # Keep state series before deleting df_features
        if "state" in df_features.columns:
            _states_series = df_features["state"].copy()
        else:
            _states_series = pd.Series(["unknown"] * len(df_features))
        del df_features  # Free memory — no longer needed after extracting X, y, and states

        # Scale
        X_scaled = pd.DataFrame(
            self.scaler.fit_transform(X), columns=feature_cols, index=X.index,
        )

        # Train/test split (stratified isn't applicable to regression, just random)
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=test_size, random_state=42,
        )

        # Keep track of state for each row (for cluster/state splits)
        states_series = _states_series

        states_train = states_series.loc[X_train.index]
        states_test = states_series.loc[X_test.index]

        # ---- 3. Global model ----
        logger.info("Step 3: Training GLOBAL model...")
        self.global_model = self._make_xgb("global")
        self.global_model.fit(X_train, y_train)
        global_pred_test = self.global_model.predict(X_test)

        global_metrics = {
            "r2": float(r2_score(y_test, global_pred_test)),
            "mae": float(mean_absolute_error(y_test, global_pred_test)),
            "rmse": float(np.sqrt(mean_squared_error(y_test, global_pred_test))),
        }
        logger.info(
            f"  Global R2={global_metrics['r2']:.4f}  "
            f"MAE=${global_metrics['mae']:,.0f}  "
            f"RMSE=${global_metrics['rmse']:,.0f}"
        )

        # ---- 4. Cluster models ----
        logger.info("Step 4: Training CLUSTER models...")
        cluster_metrics = {}
        for cluster_name, cdata in self._cluster_config.items():
            cluster_states = cdata.get("states", [])
            min_samples = cdata.get("min_samples", 300)

            mask_train = states_train.isin(cluster_states)
            if mask_train.sum() < min_samples:
                logger.warning(
                    f"  Cluster '{cluster_name}': {mask_train.sum()} samples "
                    f"(< {min_samples}); using global model as fallback"
                )
                continue

            X_c_train = X_train[mask_train]
            y_c_train = y_train[mask_train]

            model_c = self._make_xgb("cluster")
            model_c.fit(X_c_train, y_c_train)
            self.cluster_models[cluster_name] = model_c

            # Evaluate on cluster test data
            mask_test = states_test.isin(cluster_states)
            if mask_test.sum() > 0:
                y_c_test = y_test[mask_test]
                pred_c_test = model_c.predict(X_test[mask_test])
                cm = {
                    "r2": float(r2_score(y_c_test, pred_c_test)),
                    "mae": float(mean_absolute_error(y_c_test, pred_c_test)),
                    "n_train": int(mask_train.sum()),
                    "n_test": int(mask_test.sum()),
                }
            else:
                cm = {"r2": None, "mae": None, "n_train": int(mask_train.sum()), "n_test": 0}

            cluster_metrics[cluster_name] = cm
            logger.info(
                f"  Cluster '{cluster_name}': n={cm['n_train']}, "
                f"R2={cm['r2']:.4f}" if cm['r2'] is not None else "R2=N/A"
            )

        # ---- 5. State models ----
        logger.info("Step 5: Training STATE models...")
        state_metrics = {}
        state_counts = states_train.value_counts()
        for state_name, count in state_counts.items():
            if count < 500:
                continue

            mask_train = states_train == state_name
            X_s_train = X_train[mask_train]
            y_s_train = y_train[mask_train]

            model_s = self._make_xgb("state")
            model_s.fit(X_s_train, y_s_train)
            self.state_models[state_name] = model_s

            # Evaluar modelo estatal en test para obtener R2
            mask_test = states_test == state_name
            state_r2 = 0.0
            if mask_test.sum() > 0:
                pred_s = model_s.predict(X_test[mask_test])
                state_r2 = max(0.0, float(r2_score(y_test[mask_test], pred_s)))

            # Obtener R2 del cluster correspondiente para ponderar calidad
            cluster_name = self._get_cluster(state_name)
            cluster_r2 = 0.0
            if cluster_name in cluster_metrics and cluster_metrics[cluster_name].get("r2") is not None:
                cluster_r2 = max(0.0, cluster_metrics[cluster_name]["r2"])

            # Alpha ponderado por calidad: penalizar estados cuyo modelo local
            # es peor que el modelo de cluster, incluso si tienen muchas muestras
            alpha = min(1.0, count / 2000.0) * min(1.0, state_r2 / max(cluster_r2, 0.01))
            self.state_alpha[state_name] = alpha

            # Metricas del modelo estatal
            if mask_test.sum() > 0:
                sm = {
                    "r2": state_r2,
                    "mae": float(mean_absolute_error(y_test[mask_test], pred_s)),
                    "n_train": int(count),
                    "alpha": float(alpha),
                }
            else:
                sm = {"r2": None, "mae": None, "n_train": int(count), "alpha": float(alpha)}

            state_metrics[state_name] = sm
            logger.info(
                f"  State '{state_name}': n={count}, alpha={alpha:.2f}, "
                f"R2={sm['r2']:.4f}" if sm['r2'] is not None else "R2=N/A"
            )

        # ---- Overall blended evaluation on test set ----
        logger.info("Step 6: Evaluating blended predictions on test set...")
        blended_preds = self._predict_batch_internal(X_test, states_test)
        blended_metrics = {
            "r2": float(r2_score(y_test, blended_preds)),
            "mae": float(mean_absolute_error(y_test, blended_preds)),
            "rmse": float(np.sqrt(mean_squared_error(y_test, blended_preds))),
        }
        logger.info(
            f"  BLENDED R2={blended_metrics['r2']:.4f}  "
            f"MAE=${blended_metrics['mae']:,.0f}  "
            f"RMSE=${blended_metrics['rmse']:,.0f}"
        )

        # Set sentinel so API knows model is ready
        self.price_model = self.global_model

        # Compile metrics
        self._training_metrics = {
            "global": global_metrics,
            "blended": blended_metrics,
            "clusters": cluster_metrics,
            "states": state_metrics,
            "n_samples": len(df),
            "n_features": len(feature_cols),
            "n_cluster_models": len(self.cluster_models),
            "n_state_models": len(self.state_models),
            "trained_at": datetime.now().isoformat(),
            "model_version": self.model_version,
        }

        # Feature importance from global model
        importance = dict(zip(feature_cols, self.global_model.feature_importances_))
        sorted_imp = sorted(importance.items(), key=lambda x: x[1], reverse=True)
        logger.info("Global feature importance (top 10):")
        for name, imp in sorted_imp[:10]:
            logger.info(f"  {name}: {imp:.4f}")

        # Save
        model_path = self.save_model()

        # Save metrics JSON
        p = Path(model_path)
        metrics_path = p.with_suffix(".metrics.json")
        with open(metrics_path, "w") as f:
            json.dump(self._training_metrics, f, indent=2, default=str)
        logger.info(f"Metrics saved to {metrics_path}")

        logger.success(
            f"=== Training complete: Global R2={global_metrics['r2']:.4f}, "
            f"Blended R2={blended_metrics['r2']:.4f} ==="
        )

        # Return flat metrics dict compatible with existing callers
        return {
            "train_r2": global_metrics["r2"],
            "test_r2": blended_metrics["r2"],
            "test_mae": blended_metrics["mae"],
            "test_rmse": blended_metrics["rmse"],
            "train_mae": global_metrics["mae"],
            "train_rmse": global_metrics["rmse"],
            "n_samples": len(df),
            "n_features": len(feature_cols),
            "trained_at": datetime.now().isoformat(),
        }

    # ------------------------------------------------------------------
    # Internal batch prediction (for evaluation)
    # ------------------------------------------------------------------

    def _predict_batch_internal(
        self, X_scaled: pd.DataFrame, states: pd.Series
    ) -> np.ndarray:
        """Vectorized blended predictions for a batch (already scaled)."""
        global_preds = self.global_model.predict(X_scaled)
        result = np.copy(global_preds)

        # Vectorized: group by cluster, predict entire group at once
        states_arr = states.values
        X_arr = X_scaled.values
        positions = np.arange(len(states_arr))

        # Map each row to its cluster
        cluster_for_row = np.array([self._get_cluster(s) for s in states_arr])

        # Cluster-level batch predictions
        cluster_preds = np.copy(global_preds)
        for cluster_name, model in self.cluster_models.items():
            mask = cluster_for_row == cluster_name
            if mask.any():
                cluster_preds[mask] = model.predict(X_scaled.iloc[mask])

        # State-level batch predictions + alpha blending
        for state_name, model in self.state_models.items():
            mask = states_arr == state_name
            if mask.any():
                state_preds = model.predict(X_scaled.iloc[mask])
                alpha = self.state_alpha.get(state_name, 0.5)
                result[mask] = alpha * state_preds + (1 - alpha) * cluster_preds[mask]
                continue

        # For rows without state model, use cluster prediction
        states_with_models = set(self.state_models.keys())
        no_state_model = np.array([s not in states_with_models for s in states_arr])
        if no_state_model.any():
            result[no_state_model] = cluster_preds[no_state_model]

        return result

    # ------------------------------------------------------------------
    # Single prediction (API-facing)
    # ------------------------------------------------------------------

    def predict_price(
        self,
        lat: float,
        lon: float,
        area_m2: float,
        city: str,
        state: str,
        **kwargs,
    ) -> Dict:
        """Predict price for a single property. Drop-in replacement for
        PlusvaliaPredictorModel.predict_price.
        """
        if self.global_model is None:
            raise ValueError("Modelo no entrenado. Ejecutar train() primero.")

        # Build input DataFrame
        input_data = pd.DataFrame([{
            "lat": lat, "lon": lon, "area_m2": area_m2,
            "price_mxn": area_m2 * 1000,  # placeholder for feature pipeline
            "city": city, "state": state,
            **kwargs,
        }])

        # Prepare features (spatial features computed inside)
        df_features = self.prepare_features(input_data)

        X = df_features[self.feature_names].fillna(0)
        X_scaled = pd.DataFrame(
            self.scaler.transform(X), columns=self.feature_names, index=X.index,
        )

        # ---------- Hierarchical prediction ----------
        cluster = self._get_cluster(state)
        global_pred = float(self.global_model.predict(X_scaled)[0])

        # Cluster
        if cluster in self.cluster_models:
            cluster_pred = float(self.cluster_models[cluster].predict(X_scaled)[0])
        else:
            cluster_pred = global_pred

        # State
        state_pred = None
        alpha = 0.0
        if state in self.state_models:
            state_pred = float(self.state_models[state].predict(X_scaled)[0])
            alpha = self.state_alpha.get(state, 0.5)
            final_pred = alpha * state_pred + (1 - alpha) * cluster_pred
        else:
            final_pred = cluster_pred

        # Ensure non-negative
        final_pred = max(0.0, final_pred)
        predicted_price_m2 = final_pred
        predicted_total_price = predicted_price_m2 * area_m2

        # ---------- Confidence interval ----------
        lower, upper, conf_level = self.get_prediction_interval(X_scaled)

        # ---------- Plusvalia score ----------
        config = _load_config()
        thresholds = config.get("thresholds", {}).get("plusvalia_score", {})
        avg_price_m2 = 5000
        plusvalia_score = min(100, max(0, (predicted_price_m2 / avg_price_m2) * 50))

        if plusvalia_score >= thresholds.get("muy_alto", 75):
            growth_potential = "muy_alto"
        elif plusvalia_score >= thresholds.get("alto", 60):
            growth_potential = "alto"
        elif plusvalia_score >= thresholds.get("medio", 40):
            growth_potential = "medio"
        else:
            growth_potential = "bajo"

        # ---------- Confidence percentage ----------
        # Use tree variance across the global ensemble
        confidence = self._compute_confidence(X_scaled)

        # Demographics for response
        demo = self._get_demographics(city, state)

        # Spatial features for response
        spatial_feats = self.spatial_engine.compute_features(lat, lon, city, state)

        return {
            "predicted_price_m2": round(predicted_price_m2, 2),
            "predicted_total_price": round(predicted_total_price, 2),
            "plusvalia_score": round(plusvalia_score, 2),
            "growth_potential": growth_potential,
            "confidence": round(confidence, 1),
            "model_version": self.model_version,
            "prediction_interval": {
                "lower": round(lower * area_m2, 2),
                "upper": round(upper * area_m2, 2),
                "confidence_level": conf_level,
            },
            "prediction_breakdown": {
                "global_prediction": round(global_pred, 2),
                "cluster_prediction": round(cluster_pred, 2),
                "state_prediction": round(state_pred, 2) if state_pred is not None else None,
                "cluster": cluster,
                "alpha": round(alpha, 3),
                "blending_method": "alpha" if state_pred is not None else "cluster_only",
            },
            "comparable_sales": {
                "avg_price_m2_1km": round(spatial_feats.get("avg_price_m2_1km", 0), 2),
                "avg_price_m2_5km": round(spatial_feats.get("avg_price_m2_5km", 0), 2),
                "comparable_count_5km": int(spatial_feats.get("comparable_count_5km", 0)),
                "nearest_distance_km": round(spatial_feats.get("nearest_distance_km", 0), 2),
            },
            "features_used": {
                "area_m2": area_m2,
                "distance_to_center": float(df_features["distance_to_center"].iloc[0]),
                "city": city,
                "state": state,
                "population_density": demo["population_density"],
                "economic_level_score": demo["economic_level_score"],
                "security_score": demo["security_score"],
                "infrastructure_score": demo["infrastructure_score"],
            },
        }

    # ------------------------------------------------------------------
    # Prediction interval
    # ------------------------------------------------------------------

    def get_prediction_interval(
        self,
        X_scaled: pd.DataFrame,
        confidence: float = 0.9,
    ) -> Tuple[float, float, float]:
        """Compute prediction interval using tree variance.

        For XGBoost we use the global model's individual tree predictions
        to estimate uncertainty.

        Returns (lower_bound_price_m2, upper_bound_price_m2, confidence_level).
        """
        if self.global_model is None:
            return (0.0, 0.0, confidence)

        # Get individual tree predictions via the booster
        try:
            booster = self.global_model.get_booster()
            import xgboost as xgb
            dmat = xgb.DMatrix(X_scaled, feature_names=self.feature_names)

            # Get predictions from each iteration
            n_trees = booster.num_boosted_rounds()
            preds_per_iter = []
            # Accumulate predictions tree by tree
            for i in range(max(1, n_trees // 10), n_trees + 1, max(1, n_trees // 10)):
                pred = booster.predict(dmat, iteration_range=(0, i))
                preds_per_iter.append(float(pred[0]))

            if len(preds_per_iter) >= 3:
                std = np.std(preds_per_iter[-5:])  # variance of last few iterations
                mean_pred = float(preds_per_iter[-1])
            else:
                mean_pred = float(self.global_model.predict(X_scaled)[0])
                std = mean_pred * 0.15  # 15% default uncertainty
        except Exception:
            mean_pred = float(self.global_model.predict(X_scaled)[0])
            std = mean_pred * 0.15

        # Use a simple normal approximation
        from scipy.stats import norm
        z = norm.ppf(0.5 + confidence / 2)
        # Add a floor of 5% to avoid overconfidence
        std = max(std, mean_pred * 0.05)

        lower = max(0.0, mean_pred - z * std)
        upper = mean_pred + z * std

        return (lower, upper, confidence)

    def _compute_confidence(self, X_scaled: pd.DataFrame) -> float:
        """Compute confidence percentage (50-99) from prediction variance."""
        try:
            booster = self.global_model.get_booster()
            import xgboost as xgb
            dmat = xgb.DMatrix(X_scaled, feature_names=self.feature_names)

            n_trees = booster.num_boosted_rounds()
            step = max(1, n_trees // 10)
            preds = []
            for i in range(step, n_trees + 1, step):
                pred = booster.predict(dmat, iteration_range=(0, i))
                preds.append(float(pred[0]))

            if len(preds) >= 3:
                final = preds[-1]
                cv = np.std(preds[-5:]) / max(abs(final), 1.0)
                return max(50.0, min(99.0, 100.0 - cv * 200.0))
        except Exception:
            pass
        return 75.0

    # ------------------------------------------------------------------
    # SHAP explanation (same interface as predictor.py)
    # ------------------------------------------------------------------

    def explain_prediction(
        self,
        lat: float, lon: float, area_m2: float,
        city: str, state: str, **kwargs,
    ) -> Dict:
        """Generate SHAP explanation. Uses global model for explanations."""
        if self.global_model is None:
            raise ValueError("Modelo no entrenado.")

        try:
            import shap
        except ImportError:
            raise ImportError("shap not installed: pip install shap")

        input_data = pd.DataFrame([{
            "lat": lat, "lon": lon, "area_m2": area_m2,
            "price_mxn": area_m2 * 1000,
            "city": city, "state": state, **kwargs,
        }])

        df_features = self.prepare_features(input_data)
        X = df_features[self.feature_names].fillna(0)
        X_scaled = self.scaler.transform(X)

        explainer = shap.TreeExplainer(self.global_model)
        shap_values = explainer.shap_values(X_scaled)

        feature_explanations = []
        for i, fname in enumerate(self.feature_names):
            sv = float(shap_values[0][i])
            rv = float(X.iloc[0][fname])
            feature_explanations.append({
                "feature": fname,
                "value": round(rv, 4),
                "shap_value": round(sv, 2),
                "impact": "positive" if sv > 0 else "negative",
                "abs_importance": round(abs(sv), 2),
            })

        feature_explanations.sort(key=lambda x: x["abs_importance"], reverse=True)

        base_value = float(explainer.expected_value)
        predicted = float(self.global_model.predict(X_scaled)[0])

        return {
            "predicted_price_m2": round(predicted, 2),
            "base_value": round(base_value, 2),
            "feature_explanations": feature_explanations,
            "top_positive_factors": [f for f in feature_explanations if f["impact"] == "positive"][:3],
            "top_negative_factors": [f for f in feature_explanations if f["impact"] == "negative"][:3],
            "model_version": self.model_version,
            "explanation_method": "SHAP (TreeExplainer on global XGBoost)",
        }

    # ------------------------------------------------------------------
    # Save / Load
    # ------------------------------------------------------------------

    def save_model(self, filename: str = None) -> str:
        """Save the entire hierarchical model stack."""
        if filename is None:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"hierarchical_v{self.model_version}_{ts}.pkl"

        _fp = Path(filename)
        model_file = _fp if _fp.is_absolute() else self.model_path / _fp.name

        model_data = {
            "type": "hierarchical",
            "model_version": self.model_version,
            "global_model": self.global_model,
            "cluster_models": self.cluster_models,
            "state_models": self.state_models,
            "state_alpha": self.state_alpha,
            "scaler": self.scaler,
            "label_encoders": self.label_encoders,
            "feature_names": self.feature_names,
            "state_to_cluster": self._state_to_cluster,
            "cluster_config": self._cluster_config,
            "spatial_state": self.spatial_engine.get_state(),
            "saved_at": datetime.now().isoformat(),
        }

        joblib.dump(model_data, model_file)
        logger.success(f"Hierarchical model saved: {model_file}")
        return str(model_file)

    def load_model(self, filename: str):
        """Load a previously saved hierarchical model."""
        _fp = Path(filename)
        model_file = _fp if _fp.is_absolute() else self.model_path / _fp.name

        if not model_file.exists():
            raise FileNotFoundError(f"Model not found: {model_file}")

        logger.info(f"Loading hierarchical model from: {model_file}")
        data = joblib.load(model_file)

        if data.get("type") != "hierarchical":
            raise ValueError(
                f"Expected hierarchical model, got '{data.get('type', 'unknown')}'"
            )

        self.model_version = data["model_version"]
        self.global_model = data["global_model"]
        self.cluster_models = data.get("cluster_models", {})
        self.state_models = data.get("state_models", {})
        self.state_alpha = data.get("state_alpha", {})
        self.scaler = data["scaler"]
        self.label_encoders = data["label_encoders"]
        self.feature_names = data["feature_names"]
        self._state_to_cluster = data.get("state_to_cluster", {})
        self._cluster_config = data.get("cluster_config", {})

        # Restore spatial engine
        spatial_state = data.get("spatial_state", {})
        if spatial_state:
            self.spatial_engine.load_state(spatial_state)

        # Set sentinel
        self.price_model = self.global_model

        logger.success(
            f"Hierarchical model loaded (v{self.model_version}): "
            f"global + {len(self.cluster_models)} clusters + "
            f"{len(self.state_models)} state models"
        )


# ================================================================
# Standalone training script
# ================================================================

def main():
    """Train the hierarchical model from Supabase data."""
    import sys
    sys.path.append("..")
    from supabase import create_client
    from config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

    logger.info("=== Hierarchical Model Training ===")

    sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    response = sb.table("iainmobiliaria_comparables").select("*").execute()

    if not response.data:
        logger.error("No training data found")
        return

    df = pd.DataFrame(response.data)
    logger.info(f"Loaded {len(df)} records")

    model = HierarchicalPredictor(model_version="3.0")
    metrics = model.train(df)

    # Test prediction
    logger.info("\n--- Test prediction ---")
    pred = model.predict_price(
        lat=20.5888, lon=-100.3899, area_m2=500,
        city="Queretaro", state="Queretaro",
    )
    logger.info(f"Price/m2: ${pred['predicted_price_m2']:,.0f}")
    logger.info(f"Total: ${pred['predicted_total_price']:,.0f}")
    logger.info(f"Confidence: {pred['confidence']:.1f}%")
    logger.info(f"Breakdown: {pred['prediction_breakdown']}")
    logger.info(f"Comparables: {pred['comparable_sales']}")

    logger.success("=== Training complete ===")


if __name__ == "__main__":
    logger.remove()
    logger.add(
        __import__("sys").stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO",
    )
    main()
