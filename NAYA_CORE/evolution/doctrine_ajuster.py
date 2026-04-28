"""NAYA V19 - Doctrine Adjuster - Ajuste la doctrine selon les resultats."""
import logging, time
from typing import Dict, List

log = logging.getLogger("NAYA.EVOLUTION.DOCTRINE")

class DoctrineAdjuster:
    """Ajuste les parametres doctrinaux selon la performance reelle."""

    ADJUSTABLE_PARAMS = {
        "hunt_interval_s": {"min": 600, "max": 7200, "default": 3600},
        "premium_floor_eur": {"min": 1000, "max": 1000, "default": 1000},  # plancher inviolable, jamais en dessous
        "max_parallel_ops": {"min": 4, "max": 4, "default": 4},  # toujours 4 projets en parallèle
        "outreach_batch_size": {"min": 5, "max": 50, "default": 10},
        "pricing_aggressiveness": {"min": 0.5, "max": 1.5, "default": 1.0},
    }

    def __init__(self):
        self._current = {k: v["default"] for k, v in self.ADJUSTABLE_PARAMS.items()}
        self._adjustments: List[Dict] = []

    def adjust(self, param: str, direction: str = "up", factor: float = 0.1) -> Dict:
        if param not in self.ADJUSTABLE_PARAMS:
            return {"error": f"Parametre {param} non ajustable"}
        cfg = self.ADJUSTABLE_PARAMS[param]
        old = self._current[param]
        if direction == "up":
            new = min(cfg["max"], old * (1 + factor))
        else:
            new = max(cfg["min"], old * (1 - factor))
        self._current[param] = new
        adj = {"param": param, "old": old, "new": new, "direction": direction, "ts": time.time()}
        self._adjustments.append(adj)
        log.info(f"[DOCTRINE] {param}: {old} -> {new} ({direction})")
        return adj

    def auto_adjust(self, performance: Dict) -> List[Dict]:
        """Ajuste automatiquement selon les metriques de performance."""
        adjustments = []
        revenue_rate = performance.get("weekly_revenue", 0) / max(1, performance.get("weekly_target", 60000))
        if revenue_rate < 0.5:
            adjustments.append(self.adjust("hunt_interval_s", "down", 0.2))
            adjustments.append(self.adjust("outreach_batch_size", "up", 0.3))
        elif revenue_rate > 1.2:
            adjustments.append(self.adjust("pricing_aggressiveness", "up", 0.1))
        conversion = performance.get("conversion_rate", 0)
        if conversion < 0.1:
            adjustments.append(self.adjust("outreach_batch_size", "up", 0.2))
        return [a for a in adjustments if "error" not in a]

    def get_current(self) -> Dict:
        return self._current.copy()

    def reset_to_defaults(self) -> None:
        self._current = {k: v["default"] for k, v in self.ADJUSTABLE_PARAMS.items()}

    def get_stats(self) -> Dict:
        return {
            "params": self._current,
            "total_adjustments": len(self._adjustments),
            "last_adjustment": self._adjustments[-1] if self._adjustments else None
        }
