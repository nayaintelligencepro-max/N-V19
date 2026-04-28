"""NAYA V19 - Core Signal Fusion - Fusionne les signaux de multiples sources."""
import logging, time
from typing import Dict, List, Optional

log = logging.getLogger("NAYA.EVOLUTION.FUSION")

class CoreSignalFusion:
    """Fusionne les signaux de differentes sources pour decision unifiee."""

    SIGNAL_WEIGHTS = {
        "market": 0.25, "internal": 0.20, "customer": 0.25,
        "financial": 0.15, "competitive": 0.15
    }

    def __init__(self):
        self._signals: List[Dict] = []
        self._fusions: List[Dict] = []

    def add_signal(self, source: str, signal_type: str, value: float,
                   context: str = "") -> None:
        self._signals.append({
            "source": source, "type": signal_type,
            "value": value, "context": context, "ts": time.time()
        })
        if len(self._signals) > 1000:
            self._signals = self._signals[-500:]

    def fuse(self, window_seconds: int = 3600) -> Dict:
        """Fusionne les signaux recents en un signal unique."""
        cutoff = time.time() - window_seconds
        recent = [s for s in self._signals if s["ts"] > cutoff]
        if not recent:
            return {"fused_value": 0.5, "confidence": 0, "signals_count": 0}

        by_source = {}
        for s in recent:
            src = s["source"]
            if src not in by_source:
                by_source[src] = []
            by_source[src].append(s["value"])

        weighted_sum = 0
        total_weight = 0
        for src, values in by_source.items():
            avg = sum(values) / len(values)
            weight = self.SIGNAL_WEIGHTS.get(src, 0.1)
            weighted_sum += avg * weight
            total_weight += weight

        fused = weighted_sum / total_weight if total_weight > 0 else 0.5
        confidence = min(1.0, len(recent) / 10)

        result = {
            "fused_value": round(fused, 3),
            "confidence": round(confidence, 2),
            "signals_count": len(recent),
            "sources": list(by_source.keys())
        }
        self._fusions.append(result)
        return result

    def get_stats(self) -> Dict:
        return {
            "total_signals": len(self._signals),
            "total_fusions": len(self._fusions),
            "last_fusion": self._fusions[-1] if self._fusions else None
        }
