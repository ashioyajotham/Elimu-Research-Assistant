import json
from pathlib import Path
from typing import Any, Optional

from config.config_manager import ConfigManager as BaseConfigManager

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = Path.home() / ".elimu_research_assistant"
CONFIG_FILE = CONFIG_DIR / "config.json"
ENV_FILE = PROJECT_ROOT / ".env"

class ElimuConfigManager(BaseConfigManager):
    """Configuration manager with Elimu defaults and persistence."""

    DEFAULT_CONFIG = {
        **BaseConfigManager.DEFAULT_CONFIG,
        "timeout": 30,
        "max_search_results": 8,
        "output_format": "markdown",
        "educational_focus": True,
        "prioritize_kenyan_sources": True,
        "default_education_level": "secondary",
        "supported_subjects": [
            "business_studies",
            "geography",
            "history",
            "mathematics",
            "science",
            "literature",
        ],
        "language_support": ["english", "swahili"],
        "model_name": "gemini-2.0-flash-exp",
        "model_fallback": "gemini-1.5-flash-latest",
    }

    ENV_MAPPING = {
        **BaseConfigManager.ENV_MAPPING,
        "ELIMU_MODEL_NAME": "model_name",
        "ELIMU_MODEL_FALLBACK": "model_fallback",
    }

    def __init__(self):
        CONFIG_DIR.mkdir(exist_ok=True, parents=True)
        config_path = str(CONFIG_FILE) if CONFIG_FILE.exists() else None
        env_path = str(ENV_FILE)
        super().__init__(config_path=config_path, env_file=env_path)
        self.config_file = CONFIG_FILE
        self._apply_default_values()

    def _apply_default_values(self) -> None:
        for key, value in self.DEFAULT_CONFIG.items():
            if self.get(key) is None:
                self.config[key] = value

    def update(self, key: str, value: Any, store_in_keyring: bool = True) -> bool:
        result = super().update(key, value, store_in_keyring)
        self._persist()
        return result

    def _persist(self) -> None:
        serializable = dict(self.config)
        for secure_key in getattr(self, "SECURE_KEYS", []):
            serializable.pop(secure_key, None)
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(serializable, f, indent=2)

_config: Optional["ElimuConfigManager"] = None

def init_config() -> ElimuConfigManager:
    """Initialize and return the Elimu configuration manager."""
    global _config
    if _config is None:
        _config = ElimuConfigManager()
    return _config

def get_config() -> ElimuConfigManager:
    """Get the current configuration instance."""
    return init_config()

def update_config(key: str, value: Any) -> ElimuConfigManager:
    """Update configuration and persist to disk."""
    config = get_config()
    config.update(key, value)
    return config

ConfigManager = ElimuConfigManager

__all__ = ["get_config", "init_config", "update_config", "ElimuConfigManager", "ConfigManager"]