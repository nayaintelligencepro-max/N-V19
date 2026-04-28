"""NAYA — Intention Loop"""
import os, time, threading, logging
from typing import Dict, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass, field
log = logging.getLogger("NAYA.INTENTION")

class Intent(Enum):
    HUNT = "hunt"; EVOLVE = "evolve"; STABILIZE = "stabilize"; REST = "rest"

@dataclass
class IntentDecision:
    intent: Intent; reason: str; urgency: float = 0.5; ts: float = field(default_factory=time.time)

class IntentionLoop:
    EVAL_INTERVAL = 60
    def __init__(self):
        self.state = "IDLE"; self._running = False
        self._thread = None; self._last_hunt = 0.0; self._last_evolve = 0.0
        self._decisions: List[IntentDecision] = []
        self._callbacks: Dict = {i: [] for i in Intent}
        self.hunt_interval = int(os.environ.get("NAYA_AUTO_HUNT_INTERVAL_SECONDS", 3600))

    def on(self, intent, fn):
        self._callbacks[intent].append(fn); return self

    def start(self):
        if self._running: return
        self._running = True
        self._thread = threading.Thread(target=self._loop, name="NAYA-INTENTION", daemon=True)
        self._thread.start()
        log.info("[INTENTION] Loop démarrée")

    def stop(self): self._running = False

    def _loop(self):
        time.sleep(20)
        while self._running:
            try:
                d = self.evaluate({"seconds_since_hunt": time.time()-self._last_hunt, "seconds_since_evolve": time.time()-self._last_evolve, "hunt_interval": self.hunt_interval})
                self.state = d.intent.value.upper()
                self._fire(d)
                self._decisions.append(d)
                if len(self._decisions) > 300: self._decisions = self._decisions[-300:]
            except Exception as e: log.error(f"[INTENTION] {e}")
            time.sleep(self.EVAL_INTERVAL)

    def evaluate(self, system_status):
        since_hunt = system_status.get("seconds_since_hunt", 9999)
        since_evolve = system_status.get("seconds_since_evolve", 9999)
        hunt_iv = system_status.get("hunt_interval", 3600)
        errors = system_status.get("errors", [])
        if len(errors) > 3: return IntentDecision(Intent.STABILIZE, "Erreurs détectées", 1.0)
        if since_hunt >= hunt_iv: return IntentDecision(Intent.HUNT, f"Intervalle {hunt_iv}s atteint", 0.9)
        if since_evolve >= 21600: return IntentDecision(Intent.EVOLVE, "Évolution 6h", 0.5)
        rem = int(hunt_iv - since_hunt); m, s = rem//60, rem%60
        return IntentDecision(Intent.REST, f"Prochain dans {m}min {s}s", 0.0)

    def _fire(self, d):
        now = time.time()
        for cb in self._callbacks.get(d.intent, []):
            try: cb(d)
            except Exception as e: log.warning(f"[INTENTION] Callback: {e}")
        if d.intent == Intent.HUNT: self._last_hunt = now
        if d.intent == Intent.EVOLVE: self._last_evolve = now

    def run(self, system_status): return self.evaluate(system_status).intent.value

    def get_stats(self):
        intents = [d.intent.value for d in self._decisions]
        last = self._decisions[-1] if self._decisions else None
        return {"running": self._running, "state": self.state, "total_decisions": len(self._decisions), "last": {"intent": last.intent.value, "reason": last.reason} if last else None, "hunt_count": intents.count("hunt")}

_L = None
_L_lock = __import__('threading').Lock()
def get_intention_loop():
    global _L
    if _L is None:
        with _L_lock:
            if _L is None: _L = IntentionLoop()
    return _L
