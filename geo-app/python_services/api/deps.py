"""Shared dependencies for API routers.

Uses lazy initialization so tests can mock before first access.
Supports both legacy PlusvaliaPredictorModel and the new
HierarchicalPredictor — loads hierarchical if a saved model exists,
otherwise falls back to the legacy predictor.
"""

import sys
sys.path.append("..")

from pathlib import Path
from loguru import logger

from ml_model.predictor import PlusvaliaPredictorModel
from config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, MODEL_PATH
from supabase import create_client as _create_client

_model = None
_supabase = None


def _find_latest_hierarchical_model() -> str | None:
    """Return filename of the most recent hierarchical .pkl, or None."""
    models_dir = MODEL_PATH
    if not models_dir.exists():
        return None
    candidates = sorted(
        models_dir.glob("hierarchical_*.pkl"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return candidates[0].name if candidates else None


def get_model():
    """Lazy-initialize the ML model singleton.

    Tries to load a HierarchicalPredictor first; falls back to legacy
    PlusvaliaPredictorModel if no hierarchical model is found or if
    XGBoost is not available.
    """
    global _model
    if _model is not None:
        return _model

    # Attempt hierarchical model first
    hierarchical_file = _find_latest_hierarchical_model()
    if hierarchical_file:
        try:
            from ml_model.hierarchical_model import HierarchicalPredictor
            # Extract version from filename (e.g. "hierarchical_v5.0_20260401.pkl" -> "5.0")
            import re
            version_match = re.search(r"_v([\d.]+)", hierarchical_file)
            model_version = version_match.group(1) if version_match else "1.0"
            hp = HierarchicalPredictor(model_version=model_version)
            hp.load_model(hierarchical_file)
            _model = hp
            logger.info(f"Loaded HierarchicalPredictor v{model_version} from {hierarchical_file}")
            return _model
        except Exception as e:
            logger.warning(
                f"Failed to load hierarchical model '{hierarchical_file}': {e}. "
                "Falling back to legacy predictor."
            )

    # Fallback: legacy predictor
    _model = PlusvaliaPredictorModel(model_version="1.0")
    logger.info("Using legacy PlusvaliaPredictorModel")
    return _model


def get_supabase():
    """Lazy-initialize the Supabase client singleton."""
    global _supabase
    if _supabase is None:
        _supabase = _create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    return _supabase


# Module-level aliases for backward compat (routers import these)
# These are properties that resolve lazily
class _LazyProxy:
    """Proxy that defers initialization until first attribute access."""
    def __init__(self, factory):
        object.__setattr__(self, '_factory', factory)
        object.__setattr__(self, '_obj', None)

    def _resolve(self):
        obj = object.__getattribute__(self, '_obj')
        if obj is None:
            factory = object.__getattribute__(self, '_factory')
            obj = factory()
            object.__setattr__(self, '_obj', obj)
        return obj

    def __getattr__(self, name):
        return getattr(self._resolve(), name)

    def __setattr__(self, name, value):
        setattr(self._resolve(), name, value)

    def __repr__(self):
        return repr(self._resolve())


model = _LazyProxy(get_model)
supabase = _LazyProxy(get_supabase)
