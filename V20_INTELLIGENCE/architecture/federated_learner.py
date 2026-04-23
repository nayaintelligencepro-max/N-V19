"""
NAYA V20 — Federated Learner
══════════════════════════════════════════════════════════════════════════════
Local-only federated learning: feature importance from outcome patterns.
All data stays on-device. No external transfer.

DOCTRINE:
  Classical ML requires large datasets and GPU nodes.  This module applies
  a lightweight frequentist approximation: track which feature values
  co-occur with "success" outcomes and weight future predictions accordingly.
  Over time NAYA builds a private proprietary success model specific to
  its exact deal flow — impossible for competitors to replicate.

ALGORITHM:
  For each (outcome_type, feature_key=feature_value) pair:
    weight = P(result=="success" | feature_key=feature_val)
           = success_count / total_count

  Prediction: average weight across all known features in a new observation.
  Returns 0.5 (neutral prior) when no historical data exists.
══════════════════════════════════════════════════════════════════════════════
"""
import hashlib
import json
import logging
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

log = logging.getLogger("NAYA.FEDERATED_LEARNER")

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_FILE = ROOT / "data" / "cache" / "federated_learner.json"


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


class FederatedLearner:
    """
    Lightweight on-device federated learner that accumulates feature-outcome
    statistics to predict deal success probability.

    Thread-safe singleton.  Persists to DATA_FILE.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._data_file = DATA_FILE
        self._outcomes: List[Dict] = []
        self._weights: Dict[str, Dict[str, float]] = {}
        self._version: int = 0
        self._load()

    # ──────────────────────────────────────────────────────────────────────
    # Persistence
    # ──────────────────────────────────────────────────────────────────────

    def _load(self) -> None:
        if self._data_file.exists():
            try:
                with open(self._data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._outcomes = data.get("outcomes", [])
                    self._weights = data.get("weights", {})
                    self._version = data.get("version", 0)
            except Exception:
                pass

    def _save(self) -> None:
        self._data_file.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            with open(self._data_file, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "outcomes": self._outcomes,
                        "weights": self._weights,
                        "version": self._version,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    },
                    f,
                    indent=2,
                    ensure_ascii=False,
                )

    # ──────────────────────────────────────────────────────────────────────
    # Learning
    # ──────────────────────────────────────────────────────────────────────

    def _update_weights(self, outcome_type: str) -> None:
        """
        Recompute feature weights for a given outcome_type from scratch.

        For each (feature_key, feature_value) pair seen in outcomes of this
        type, weight = fraction of times result == "success".
        """
        relevant = [
            o for o in self._outcomes if o["outcome_type"] == outcome_type
        ]
        if not relevant:
            return

        # Accumulate counts: {feature_key=feature_val: [total, success_count]}
        counts: Dict[str, List[int]] = {}
        for record in relevant:
            for fk, fv in record.get("features", {}).items():
                key = f"{fk}={fv}"
                if key not in counts:
                    counts[key] = [0, 0]
                counts[key][0] += 1
                if record.get("result") == "success":
                    counts[key][1] += 1

        self._weights.setdefault(outcome_type, {})
        for pair_key, (total, successes) in counts.items():
            self._weights[outcome_type][pair_key] = successes / total

    # ──────────────────────────────────────────────────────────────────────
    # Business methods
    # ──────────────────────────────────────────────────────────────────────

    def record_outcome(
        self,
        outcome_type: str,
        features: Dict,
        result: str,
        revenue_eur: float,
    ) -> str:
        """
        Record a labeled outcome and immediately update the feature weights.

        Args:
            outcome_type: Category label (e.g. "outreach_email", "audit_deal").
            features: Dict of feature key-value pairs describing the context.
            result: Outcome label — "success" or "failure" (or other).
            revenue_eur: Monetary value associated with this outcome.

        Returns:
            outcome_id — unique identifier for this record.
        """
        outcome_id = _sha256(outcome_type + str(features) + str(time.time()))[:12]
        record = {
            "outcome_id": outcome_id,
            "outcome_type": outcome_type,
            "features": features,
            "result": result,
            "revenue_eur": revenue_eur,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }
        with self._lock:
            self._outcomes.append(record)
            self._version += 1
        self._update_weights(outcome_type)
        self._save()
        return outcome_id

    def get_pattern_weights(self, outcome_type: str) -> Dict:
        """
        Return the current feature weight dict for an outcome type.

        Args:
            outcome_type: The category whose weights to retrieve.

        Returns:
            Dict mapping "feature_key=feature_val" → P(success) weight.
        """
        with self._lock:
            return dict(self._weights.get(outcome_type, {}))

    def predict_success_probability(
        self, outcome_type: str, features: Dict
    ) -> float:
        """
        Estimate success probability for a new observation.

        Args:
            outcome_type: Outcome category to use for look-up.
            features: Feature dict describing the new observation.

        Returns:
            Float in [0, 1].  Returns 0.5 when no historical weights exist.
        """
        with self._lock:
            type_weights = self._weights.get(outcome_type, {})

        relevant_weights = []
        for fk, fv in features.items():
            pair_key = f"{fk}={fv}"
            if pair_key in type_weights:
                relevant_weights.append(type_weights[pair_key])

        if not relevant_weights:
            return 0.5
        return sum(relevant_weights) / len(relevant_weights)

    def get_model_version(self) -> str:
        """
        Return a human-readable model version string.

        Returns:
            String like "v3.47" (version.num_outcomes).
        """
        with self._lock:
            return f"v{self._version}.{len(self._outcomes)}"

    def get_stats(self) -> Dict:
        """
        Return aggregate stats for the dashboard.

        Returns:
            Dict with total_outcomes, outcome_types list, model_version string.
        """
        with self._lock:
            total = len(self._outcomes)
            types = list({o["outcome_type"] for o in self._outcomes})
        return {
            "total_outcomes": total,
            "outcome_types": sorted(types),
            "model_version": self.get_model_version(),
        }


# ──────────────────────────────────────────────────────────────────────────────
# Singleton
# ──────────────────────────────────────────────────────────────────────────────

_learner: Optional[FederatedLearner] = None


def get_federated_learner() -> FederatedLearner:
    """Return the process-wide singleton FederatedLearner instance."""
    global _learner
    if _learner is None:
        _learner = FederatedLearner()
    return _learner
