"""NAYA V19 — Decision Monitor"""
import time, logging, threading
from typing import Dict, List, Optional
from collections import deque
log = logging.getLogger("NAYA.DECISION.MONITOR")

class DecisionMonitor:
    """Surveille toutes les décisions prises par le système en temps réel."""
    
    def __init__(self, max_history: int = 1000):
        self._decisions = deque(maxlen=max_history)
        self._lock = threading.RLock()
        self._counters: Dict[str, int] = {}
        self._total_value = 0.0
        self._alerts: List[Dict] = []
    
    def record(self, decision_type: str, target: str, value: float = 0,
               outcome: str = "pending", metadata: Dict = None):
        """Enregistre une décision."""
        entry = {
            "type": decision_type, "target": target, "value": value,
            "outcome": outcome, "ts": time.time(),
            "metadata": metadata or {},
        }
        with self._lock:
            self._decisions.append(entry)
            self._counters[decision_type] = self._counters.get(decision_type, 0) + 1
            if value > 0: self._total_value += value
        
        # Alertes automatiques
        if value > 50000:
            self._alerts.append({
                "level": "high_value", "value": value,
                "type": decision_type, "ts": time.time(),
            })
        log.debug(f"[MONITOR] {decision_type} → {target} ({value}€)")
    
    def update_outcome(self, index: int, outcome: str):
        with self._lock:
            if 0 <= index < len(self._decisions):
                self._decisions[index]["outcome"] = outcome
    
    def get_recent(self, n: int = 20, type_filter: str = None) -> List[Dict]:
        with self._lock:
            items = list(self._decisions)
        if type_filter:
            items = [d for d in items if d["type"] == type_filter]
        return items[-n:]
    
    def get_stats(self) -> Dict:
        with self._lock:
            outcomes = [d.get("outcome") for d in self._decisions]
            return {
                "total_decisions": len(self._decisions),
                "by_type": dict(self._counters),
                "total_value_eur": round(self._total_value, 2),
                "outcomes": {
                    "pending": outcomes.count("pending"),
                    "success": outcomes.count("success"),
                    "failed": outcomes.count("failed"),
                },
                "alerts": self._alerts[-5:],
            }
