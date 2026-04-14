"""
Prompt versioning for the Favier AI chatbot.
Tracks system prompts and their versions for reproducibility.
"""
import json
from pathlib import Path
from datetime import datetime

PROMPTS_DIR = Path(__file__).parent / "prompts"
PROMPTS_DIR.mkdir(exist_ok=True)

PROMPT_VERSIONS = {
    "v1.0": {
        "name": "Favier AI - Real Estate Assistant",
        "version": "1.0",
        "created_at": "2024-10-25",
        "system_prompt": (
            "Eres Favier, un asistente experto en mercado inmobiliario mexicano. "
            "Ayudas a analizar plusvalia, precios por m2, tendencias de mercado, "
            "y oportunidades de inversion en terrenos. "
            "Respondes en espanol, de manera profesional pero accesible. "
            "Usas datos de predicciones ML cuando estan disponibles."
        ),
        "temperature": 0.7,
        "max_tokens": 500,
        "active": True,
    },
}


def get_active_prompt() -> dict:
    """Get the currently active prompt configuration."""
    for version, config in PROMPT_VERSIONS.items():
        if config.get("active"):
            return config
    return list(PROMPT_VERSIONS.values())[-1]


def get_all_versions() -> dict:
    """Get all prompt versions."""
    return PROMPT_VERSIONS


def log_prompt_usage(version: str, user_input: str, response: str):
    """Log prompt usage for evaluation (anonymized)."""
    log_path = PROMPTS_DIR / f"usage_{datetime.now().strftime('%Y%m')}.jsonl"
    entry = {
        "timestamp": datetime.now().isoformat(),
        "version": version,
        "input_length": len(user_input),
        "output_length": len(response),
    }
    with open(log_path, "a") as f:
        f.write(json.dumps(entry) + "\n")
