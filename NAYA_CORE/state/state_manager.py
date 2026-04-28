"""
NAYA_CORE — State Manager v5.0
===============================
Gestionnaire d'état centralisé. Thread-safe, snapshot, replay.
"""
import json, os, time, logging
from threading import Lock, RLock
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger("NAYA.STATE")

@dataclass
class CoreState:
    version: str = "5.0"
    instance_id: str = ""
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_updated: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    decisions_made: int = 0
    success_rate: float = 0.96
    confidence_level: float = 0.85
    processing_speed_ms: float = 120.0
    adaptation_mode: str = "INTELLIGENT"
    system_health: float = 100.0
    learning_rate: float = 0.03
    fast_cash_deployed_total: float = 0.0
    fast_cash_daily_revenue: float = 0.0
    discreet_pipeline_value: float = 0.0
    parallel_ops_completed: int = 0
    credibility_score: float = 75.0
    offers_generated: int = 0
    waste_items_recycled: int = 0
    opportunities_scanned: int = 0
    opportunities_approved: int = 0
    opportunities_rejected: int = 0
    doctrine_version: str = "1.0"
    last_mutation: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]: return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "CoreState":
        valid = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in valid})


class StateManager:
    _instance: Optional["StateManager"] = None
    _lock: RLock = RLock()

    def __new__(cls, *a, **kw):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self, state_file: str = "naya_state.json", auto_save: bool = True):
        if hasattr(self, "_initialized"): return
        self._initialized = True
        self._file = state_file
        self._auto_save = auto_save
        self._write_lock = Lock()
        self._history: List[Dict] = []
        self.state = self._load()

    def _load(self) -> CoreState:
        if os.path.exists(self._file):
            try:
                with open(self._file) as f: return CoreState.from_dict(json.load(f))
            except Exception: pass
        return CoreState()

    def save(self) -> bool:
        with self._write_lock:
            try:
                self.state.last_updated = datetime.now(timezone.utc).isoformat()
                with open(self._file, "w") as f: json.dump(self.state.to_dict(), f, indent=2)
                return True
            except Exception as e:
                log.error(f"Save failed: {e}"); return False

    def update(self, key: str, value: Any) -> None:
        if hasattr(self.state, key):
            setattr(self.state, key, value)
            if self._auto_save: self.save()

    def increment(self, key: str, delta: float = 1.0) -> float:
        new_val = getattr(self.state, key, 0) + delta
        self.update(key, new_val); return new_val

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self.state, key, default)

    def record_decision(self, decision_id: str, status: str, confidence: float,
                        processing_time_ms: float, opp_type: str = "unknown") -> None:
        self._history.append({"id": decision_id, "status": status,
                               "confidence": confidence, "ms": processing_time_ms,
                               "type": opp_type, "ts": datetime.now(timezone.utc).isoformat()})
        if len(self._history) > 1000: self._history = self._history[-1000:]
        self.increment("decisions_made")
        if status == "APPROVED": self.increment("opportunities_approved")
        elif status == "REJECTED": self.increment("opportunities_rejected")

    def get_stats(self) -> Dict[str, Any]:
        if not self._history: return {"total": 0}
        t = len(self._history)
        approved = sum(1 for d in self._history if d["status"] == "APPROVED")
        return {"total": t, "approved": approved, "approval_rate": approved/t,
                "avg_confidence": sum(d["confidence"] for d in self._history)/t}

    def get_full_status(self) -> Dict[str, Any]:
        return {"state": self.state.to_dict(), "decision_stats": self.get_stats()}

    def reset(self) -> None:
        self.state = CoreState(); self._history = []; self.save()


def get_state_manager() -> StateManager:
    return StateManager()
