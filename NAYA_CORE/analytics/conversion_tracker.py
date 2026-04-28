"""
NAYA V19 — Conversion Tracker
Suit le taux de conversion RÉEL de chaque source, secteur, et canal.
Permet d'optimiser les efforts sur les sources qui convertissent vraiment.
"""
import json, time, threading, logging
from typing import Dict, List, Optional
from pathlib import Path
from collections import defaultdict

log = logging.getLogger("NAYA.CONVERSION")


class ConversionTracker:
    """
    Tracks real conversion metrics across the entire funnel:
    prospect_found → enriched → outreach_sent → opened → replied → meeting → won → paid
    """

    STAGES = [
        "prospect_found", "enriched", "outreach_sent",
        "opened", "replied", "meeting", "won", "paid"
    ]
    PERSIST_FILE = Path("data/cache/conversion_metrics.json")

    def __init__(self):
        self._lock = threading.Lock()
        # Metrics par source × secteur
        self._by_source: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._by_sector: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._by_channel: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._total: Dict[str, int] = defaultdict(int)
        self._revenue_by_source: Dict[str, float] = defaultdict(float)
        self._load()

    def record(self, stage: str, source: str = "", sector: str = "",
               channel: str = "", amount: float = 0.0) -> None:
        """Enregistre une conversion à un stage donné."""
        if stage not in self.STAGES:
            return
        with self._lock:
            self._total[stage] += 1
            if source:
                self._by_source[source][stage] += 1
            if sector:
                self._by_sector[sector][stage] += 1
            if channel:
                self._by_channel[channel][stage] += 1
            if stage == "paid" and amount > 0:
                self._revenue_by_source[source or "unknown"] += amount
        self._persist()

    def get_funnel(self, source: str = "") -> Dict:
        """Retourne le funnel complet pour une source ou global."""
        with self._lock:
            data = self._by_source.get(source, {}) if source else self._total
            funnel = {}
            prev = 0
            for stage in self.STAGES:
                count = data.get(stage, 0)
                rate = round(count / max(prev, 1) * 100, 1) if prev > 0 else 100.0
                funnel[stage] = {"count": count, "conversion_rate": rate}
                prev = count if count > 0 else prev
            return funnel

    def get_best_sources(self, top_n: int = 5) -> List[Dict]:
        """Retourne les sources triées par taux de conversion vers paid."""
        with self._lock:
            sources = []
            for source, stages in self._by_source.items():
                found = stages.get("prospect_found", 0)
                paid = stages.get("paid", 0)
                revenue = self._revenue_by_source.get(source, 0)
                rate = round(paid / max(found, 1) * 100, 2)
                sources.append({
                    "source": source,
                    "prospects": found,
                    "paid": paid,
                    "conversion_rate": rate,
                    "revenue": revenue,
                })
            sources.sort(key=lambda x: x["conversion_rate"], reverse=True)
            return sources[:top_n]

    def get_stats(self) -> Dict:
        with self._lock:
            return {
                "total_funnel": dict(self._total),
                "sources_count": len(self._by_source),
                "sectors_count": len(self._by_sector),
                "total_revenue": sum(self._revenue_by_source.values()),
                "best_source": self.get_best_sources(1)[0] if self._by_source else None,
            }

    def _persist(self) -> None:
        try:
            self.PERSIST_FILE.parent.mkdir(parents=True, exist_ok=True)
            with self._lock:
                data = {
                    "total": dict(self._total),
                    "by_source": {k: dict(v) for k, v in self._by_source.items()},
                    "by_sector": {k: dict(v) for k, v in self._by_sector.items()},
                    "by_channel": {k: dict(v) for k, v in self._by_channel.items()},
                    "revenue_by_source": dict(self._revenue_by_source),
                    "updated_at": time.time(),
                }
            self.PERSIST_FILE.write_text(json.dumps(data, indent=2))
        except Exception:
            pass

    def _load(self) -> None:
        if not self.PERSIST_FILE.exists():
            return
        try:
            data = json.loads(self.PERSIST_FILE.read_text())
            self._total = defaultdict(int, data.get("total", {}))
            for k, v in data.get("by_source", {}).items():
                self._by_source[k] = defaultdict(int, v)
            for k, v in data.get("by_sector", {}).items():
                self._by_sector[k] = defaultdict(int, v)
            for k, v in data.get("by_channel", {}).items():
                self._by_channel[k] = defaultdict(int, v)
            self._revenue_by_source = defaultdict(float, data.get("revenue_by_source", {}))
        except Exception:
            pass


_tracker = None
_tracker_lock = threading.Lock()

def get_conversion_tracker() -> ConversionTracker:
    global _tracker
    if _tracker is None:
        with _tracker_lock:
            if _tracker is None:
                _tracker = ConversionTracker()
    return _tracker
