"""NAYA V19 - Registre de douleurs latentes - Stocke les douleurs detectees mais non encore actionnables"""
import logging, time
from typing import Dict, List
log = logging.getLogger("NAYA.PAIN.LATENT_PAIN_REGISTRY")

class LatentPainRegistry:
    """Stocke les douleurs detectees mais non encore actionnables."""

    def __init__(self):
        self._log: List[Dict] = []

    def __init__(self):
        self._log = []
        self._registry = []

    def register(self, sector: str, pain: str, estimated_value: float, readiness: float = 0.3) -> Dict:
        entry = {"sector": sector, "pain": pain, "value": estimated_value, "readiness": readiness, "ts": time.time()}
        self._registry.append(entry)
        return entry

    def get_ready(self, min_readiness: float = 0.6) -> list:
        return [p for p in self._registry if p["readiness"] >= min_readiness]

    def update_readiness(self, idx: int, new_readiness: float) -> None:
        if 0 <= idx < len(self._registry):
            self._registry[idx]["readiness"] = new_readiness

    def get_by_sector(self, sector: str) -> list:
        return [p for p in self._registry if p["sector"] == sector]

    def get_stats(self) -> Dict:
        return {"module": "latent_pain_registry"}
