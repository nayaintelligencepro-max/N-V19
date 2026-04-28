"""
NAYA V20 — Neuromorphic Scorer
══════════════════════════════════════════════════════════════════════════════
Temporal spike-based scoring for sales cycle momentum.
Inspired by Spiking Neural Networks (SNN): recent activity contributes more
than old activity via exponential time decay.

DOCTRINE:
  A lead that opened 3 emails last week is 10x hotter than one that opened
  10 emails last month.  Recency-weighted scoring surfaces the RIGHT leads
  at the RIGHT moment — not just the historically most active ones.

DECAY MODEL:
  score = Σ (event_weight × value × 0.5^(age_days / HALF_LIFE_DAYS))
  HALF_LIFE_DAYS = 7  → score halves every week

EVENT WEIGHTS:
  email_open: 5 | link_click: 10 | reply: 25 | meeting_request: 40
  document_download: 15
══════════════════════════════════════════════════════════════════════════════
"""
import hashlib
import json
import logging
import math
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

log = logging.getLogger("NAYA.NEUROMORPHIC_SCORER")

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_FILE = ROOT / "data" / "cache" / "neuromorphic_scorer.json"

EVENT_WEIGHTS: Dict[str, float] = {
    "email_open":          5.0,
    "link_click":         10.0,
    "reply":              25.0,
    "meeting_request":    40.0,
    "document_download":  15.0,
}

HALF_LIFE_DAYS = 7


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


class NeuromorphicScorer:
    """
    Assigns a temporally-decayed engagement score to each lead based on
    the recency and type of their interactions.

    Thread-safe singleton.  Persists spike records to DATA_FILE.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._data_file = DATA_FILE
        # spikes: {lead_id: [{"event_type": str, "timestamp": str, "value": float}]}
        self._spikes: Dict[str, List[Dict]] = {}
        self._load()

    # ──────────────────────────────────────────────────────────────────────
    # Persistence
    # ──────────────────────────────────────────────────────────────────────

    def _load(self) -> None:
        if self._data_file.exists():
            try:
                with open(self._data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._spikes = data.get("spikes", {})
            except Exception:
                pass

    def _save(self) -> None:
        self._data_file.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            with open(self._data_file, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "spikes": self._spikes,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    },
                    f,
                    indent=2,
                    ensure_ascii=False,
                )

    # ──────────────────────────────────────────────────────────────────────
    # Business methods
    # ──────────────────────────────────────────────────────────────────────

    def record_event(
        self,
        lead_id: str,
        event_type: str,
        timestamp: str,
        value: float = 1.0,
    ) -> None:
        """
        Record an engagement event (spike) for a lead.

        Args:
            lead_id: Unique lead identifier.
            event_type: Engagement type (see EVENT_WEIGHTS).
            timestamp: ISO-8601 timestamp of the event.
            value: Multiplier for the event weight (default 1.0).
        """
        spike = {"event_type": event_type, "timestamp": timestamp, "value": value}
        with self._lock:
            self._spikes.setdefault(lead_id, []).append(spike)
        self._save()

    def compute_temporal_score(self, lead_id: str) -> float:
        """
        Compute the current decayed engagement score for a lead.

        Each spike contributes: EVENT_WEIGHT × value × 0.5^(age_days / HALF_LIFE_DAYS)

        Args:
            lead_id: Target lead identifier.

        Returns:
            Score clamped to [0, 100]. Returns 0.0 if no spikes exist.
        """
        with self._lock:
            spikes = list(self._spikes.get(lead_id, []))

        if not spikes:
            return 0.0

        now = datetime.now(timezone.utc)
        total = 0.0

        for spike in spikes:
            weight = EVENT_WEIGHTS.get(spike["event_type"], 5.0) * spike.get("value", 1.0)
            try:
                event_dt = datetime.fromisoformat(spike["timestamp"])
                # Ensure tz-aware comparison
                if event_dt.tzinfo is None:
                    event_dt = event_dt.replace(tzinfo=timezone.utc)
                age_days = (now - event_dt).total_seconds() / 86_400
            except (ValueError, TypeError):
                age_days = 0.0

            decay = 0.5 ** (age_days / HALF_LIFE_DAYS)
            total += weight * decay

        return min(100.0, round(total, 2))

    def get_spike_pattern(self, lead_id: str) -> Dict:
        """
        Return a breakdown of spike activity for a lead.

        Args:
            lead_id: Target lead identifier.

        Returns:
            Dict with lead_id, total_spikes, score, event_breakdown.
        """
        with self._lock:
            spikes = list(self._spikes.get(lead_id, []))

        breakdown: Dict[str, int] = {}
        for spike in spikes:
            et = spike["event_type"]
            breakdown[et] = breakdown.get(et, 0) + 1

        return {
            "lead_id": lead_id,
            "total_spikes": len(spikes),
            "score": self.compute_temporal_score(lead_id),
            "event_breakdown": breakdown,
        }

    def get_top_leads(self, top_n: int = 10) -> List[Dict]:
        """
        Return the top-N leads by current temporal score.

        Args:
            top_n: Number of leads to return.

        Returns:
            List of dicts with lead_id, score, spike_count, sorted by score desc.
        """
        with self._lock:
            lead_ids = list(self._spikes.keys())

        results = [
            {
                "lead_id": lid,
                "score": self.compute_temporal_score(lid),
                "spike_count": len(self._spikes.get(lid, [])),
            }
            for lid in lead_ids
        ]
        results.sort(key=lambda r: r["score"], reverse=True)
        return results[:top_n]

    def get_stats(self) -> Dict:
        """
        Return aggregate statistics for the dashboard.

        Returns:
            Dict with total_leads, total_spikes, avg_score.
        """
        with self._lock:
            lead_ids = list(self._spikes.keys())
            total_spikes = sum(len(v) for v in self._spikes.values())

        total_leads = len(lead_ids)
        avg_score = (
            sum(self.compute_temporal_score(lid) for lid in lead_ids) / total_leads
            if total_leads > 0
            else 0.0
        )
        return {
            "total_leads": total_leads,
            "total_spikes": total_spikes,
            "avg_score": round(avg_score, 2),
        }


# ──────────────────────────────────────────────────────────────────────────────
# Singleton
# ──────────────────────────────────────────────────────────────────────────────

_neuro: Optional[NeuromorphicScorer] = None


def get_neuromorphic_scorer() -> NeuromorphicScorer:
    """Return the process-wide singleton NeuromorphicScorer instance."""
    global _neuro
    if _neuro is None:
        _neuro = NeuromorphicScorer()
    return _neuro
