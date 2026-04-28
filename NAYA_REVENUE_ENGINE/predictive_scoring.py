"""NAYA V19 — Predictive Scoring — score de probabilité de closing pour chaque opportunité"""
import time, logging, threading, json, hashlib, copy
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
log = logging.getLogger("NAYA")

class PredictiveScoring:
    """Predictive Scoring — score de probabilité de closing pour chaque opportunité"""
    
    def __init__(self):
        self._lock = threading.RLock()
        self._started_at = time.time()
        self._history: List[Dict] = []
        self._ops_count = 0
        self._assignments: Dict = {}
        self._erased: List = []
        self._offers: List = []
        self._feedbacks: List = []
        self._strategies: Dict = {}
        self._sources: Dict = {}
        self._clones: List = []
        self._failures: List = []
        self._lessons: List = []
        self._reinforcements: Dict = {}
        self._snapshots: List = []
        self._current_capabilities: Dict = {}
        self._sector_rates: Dict = {}
        self._publish_count = 0

    def score(self, opportunity: Dict) -> Dict:
        """Score une opportunité sur sa probabilité de closing."""
        factors = {
            "pain_severity": min(opportunity.get("pain_severity", 5) / 10, 1.0),
            "budget_match": min(opportunity.get("budget", 0) / max(opportunity.get("price", 1), 1), 1.0),
            "decision_maker": 0.9 if opportunity.get("has_decision_maker") else 0.4,
            "urgency": opportunity.get("urgency", 0.5),
            "sector_history": self._sector_success_rate(opportunity.get("sector", "")),
            "response_speed": 0.8 if opportunity.get("responded_within_24h") else 0.4,
        }
        weights = {"pain_severity": 0.25, "budget_match": 0.2, "decision_maker": 0.2,
                   "urgency": 0.15, "sector_history": 0.1, "response_speed": 0.1}
        score = sum(factors[k] * weights[k] for k in factors)
        tier = "HOT" if score > 0.7 else "WARM" if score > 0.4 else "COLD"
        return {"score": round(score, 3), "tier": tier, "factors": factors, "recommendation": "PRIORITIZE" if score > 0.7 else "NURTURE"}
    
    def _sector_success_rate(self, sector: str) -> float:
        rates = self._sector_rates.get(sector.lower(), 0.5)
        return rates
    
    def record_outcome(self, sector: str, success: bool):
        rate = self._sector_rates.get(sector.lower(), 0.5)
        self._sector_rates[sector.lower()] = rate * 0.9 + (1.0 if success else 0.0) * 0.1

    
    def get_stats(self) -> Dict:
        return {"class": "PredictiveScoring", "ops": self._ops_count, "uptime": int(time.time() - self._started_at)}
