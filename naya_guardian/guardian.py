"""NAYA — Guardian Mode"""
import os, time, logging
from typing import Dict, Optional
log = logging.getLogger("NAYA.GUARDIAN")
THRESHOLD_H = float(os.environ.get("NAYA_GUARDIAN_THRESHOLD_H", 72))

class GuardianMode:
    def __init__(self):
        self.active = False
        self._last_human_ts = time.time()
        self._guardian_since: Optional[float] = None
        self._auto_decisions = 0

    def register_human_activity(self):
        was = self.active
        self._last_human_ts = time.time()
        self.active = False
        self._guardian_since = None
        if was: log.info("[GUARDIAN] Désactivé — activité humaine")

    def check(self, last_human_interaction_hours=None):
        h = last_human_interaction_hours if last_human_interaction_hours is not None else (time.time() - self._last_human_ts) / 3600
        if h >= THRESHOLD_H and not self.active:
            self.active = True
            self._guardian_since = time.time()
            log.info(f"[GUARDIAN] ⚡ Activé — {h:.1f}h sans interaction")
        return self.active

    def enforce(self):
        if self.active:
            h = (time.time() - (self._guardian_since or time.time())) / 3600
            return {"mode": "GUARDIAN_ACTIVE", "hunt_interval_s": 1800, "auto_propose": True, "guardian_since_h": round(h, 1), "auto_decisions": self._auto_decisions}
        return {"mode": "NORMAL", "hunt_interval_s": int(os.environ.get("NAYA_AUTO_HUNT_INTERVAL_SECONDS", 3600)), "auto_propose": False}

    def record_auto_decision(self): self._auto_decisions += 1

    @property
    def status(self):
        h = (time.time() - self._last_human_ts) / 3600
        return {"active": self.active, "hours_since_human": round(h, 1), "threshold_h": THRESHOLD_H, "auto_decisions": self._auto_decisions}

_G = None
_G_lock = __import__('threading').Lock()
def get_guardian():
    global _G
    if _G is None:
        with _G_lock:
            if _G is None: _G = GuardianMode()
    return _G
