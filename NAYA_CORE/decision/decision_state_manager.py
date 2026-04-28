"""NAYA V19 — Decision State Manager"""
import time, logging, threading, json
from typing import Dict, Optional, Any
from pathlib import Path
log = logging.getLogger("NAYA.DECISION.STATE")

STATE_FILE = Path("data/cache/decision_state.json")

class DecisionStateManager:
    """Gère l'état persistant des décisions en cours."""
    
    def __init__(self):
        self._state: Dict[str, Any] = {}
        self._lock = threading.RLock()
        self._dirty = False
        self._load()
    
    def set(self, key: str, value: Any):
        with self._lock:
            self._state[key] = {"value": value, "updated_at": time.time()}
            self._dirty = True
    
    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            entry = self._state.get(key)
            return entry["value"] if entry else default
    
    def delete(self, key: str):
        with self._lock:
            self._state.pop(key, None)
            self._dirty = True
    
    def get_all(self) -> Dict:
        with self._lock:
            return {k: v["value"] for k, v in self._state.items()}
    
    def track_pipeline(self, opportunity_id: str, stage: str, value: float = 0):
        """Track une opportunité dans le pipeline."""
        self.set(f"pipeline:{opportunity_id}", {
            "stage": stage, "value": value, "ts": time.time(),
        })
    
    def get_pipeline(self) -> Dict:
        with self._lock:
            return {
                k.replace("pipeline:", ""): v["value"]
                for k, v in self._state.items() if k.startswith("pipeline:")
            }
    
    def save(self):
        if not self._dirty: return
        try:
            STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            with self._lock:
                STATE_FILE.write_text(json.dumps(self._state, default=str, indent=2))
                self._dirty = False
        except Exception as e:
            log.debug(f"[STATE] Save error: {e}")
    
    def _load(self):
        try:
            if STATE_FILE.exists():
                self._state = json.loads(STATE_FILE.read_text())
                log.info(f"[STATE] {len(self._state)} entries loaded")
        except Exception as e:
            log.debug(f"[STATE] Load error: {e}")
    
    def get_stats(self) -> Dict:
        with self._lock:
            pipeline = self.get_pipeline()
            return {
                "total_entries": len(self._state),
                "pipeline_size": len(pipeline),
                "pipeline_value": sum(p.get("value", 0) for p in pipeline.values()),
            }
