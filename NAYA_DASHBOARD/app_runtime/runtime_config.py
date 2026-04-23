"""NAYA Dashboard — Runtime Config"""
import os
from typing import Dict, Any

class RuntimeConfig:
    """Configuration runtime du dashboard NAYA."""
    DEFAULTS = {
        "debug": False,
        "ws_port": 8765,
        "api_port": 8080,
        "voice_enabled": True,
        "mobile_enabled": True,
        "auto_refresh_seconds": 5,
        "max_messages_history": 100,
        "theme": "dark",
        "language": "fr",
    }

    def __init__(self, overrides: Dict[str, Any] = None):
        self._config = {**self.DEFAULTS}
        if overrides:
            self._config.update(overrides)
        # Load from environment
        for key in self._config:
            env_key = f"NAYA_DASH_{key.upper()}"
            if env_val := os.environ.get(env_key):
                self._config[key] = self._cast(env_val, type(self._config[key]))

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._config[key] = value

    def _cast(self, value: str, target_type: type) -> Any:
        if target_type == bool: return value.lower() in ("true","1","yes")
        if target_type == int: return int(value)
        if target_type == float: return float(value)
        return value

    def to_dict(self) -> Dict:
        return dict(self._config)
