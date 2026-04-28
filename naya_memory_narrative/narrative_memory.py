"""NAYA — Narrative Memory persistée sur disque."""
import json, time, threading, logging
from collections import deque
from pathlib import Path
from typing import Dict, List, Optional
log = logging.getLogger("NAYA.MEMORY")
MEM_FILE = Path("data/cache/naya_narrative.json")

class NarrativeMemory:
    def __init__(self, max_entries=500):
        self.memory = deque(maxlen=max_entries)
        self._lock = threading.RLock()  # RLock to allow re-entrant acquisition (get_stats → get_best_sectors)
        self._sector_wins: Dict[str, int] = {}
        self._total_pipeline = 0.0
        self._total_pains = 0
        self._load()

    def add(self, text):
        self._add({"type": "narrative", "text": text, "ts": time.time()})

    def get_all(self):
        with self._lock: return list(self.memory)

    def record_pain(self, sector, category, annual_cost, offer_price):
        entry = {"type": "pain", "sector": sector, "category": category, "annual_cost": annual_cost, "offer_price": offer_price, "ts": time.time()}
        self._add(entry)
        with self._lock:
            self._sector_wins[sector] = self._sector_wins.get(sector, 0) + 1
            self._total_pipeline += offer_price
            self._total_pains += 1

    def record_cycle(self, cycle_dict):
        self._add({"type": "cycle", "ts": time.time(), **{k: v for k, v in cycle_dict.items() if k != "type"}})

    def record_event(self, event_type, data):
        self._add({"type": event_type, "ts": time.time(), **data})

    def get_best_sectors(self, n=5):
        with self._lock:
            return sorted([{"sector": k, "wins": v} for k, v in self._sector_wins.items()], key=lambda x: x["wins"], reverse=True)[:n]

    def get_recent(self, n=20, type_filter=None):
        with self._lock: entries = list(self.memory)
        if type_filter: entries = [e for e in entries if e.get("type") == type_filter]
        return entries[-n:]

    def get_stats(self):
        with self._lock:
            return {"total_entries": len(self.memory), "total_pains": self._total_pains, "total_pipeline_eur": self._total_pipeline, "best_sectors": self.get_best_sectors(3), "recent": list(self.memory)[-10:]}

    def _add(self, entry):
        with self._lock: self.memory.append(entry)
        self._save()

    def _save(self):
        try:
            MEM_FILE.parent.mkdir(parents=True, exist_ok=True)
            with self._lock: data = list(self.memory)[-500:]
            MEM_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        except Exception as e: log.debug(f"[MEMORY] Save: {e}")

    def _load(self):
        try:
            if MEM_FILE.exists():
                data = json.loads(MEM_FILE.read_text())
                for d in data:
                    self.memory.append(d)
                    if d.get("type") == "pain":
                        s = d.get("sector", "")
                        self._sector_wins[s] = self._sector_wins.get(s, 0) + 1
                        self._total_pipeline += d.get("offer_price", 0)
                        self._total_pains += 1
                log.info(f"[MEMORY] {len(self.memory)} entrées chargées")
        except Exception as e: log.debug(f"[MEMORY] Load: {e}")

_M = None
_M_lock = __import__('threading').Lock()
def get_narrative_memory():
    global _M
    if _M is None:
        with _M_lock:
            if _M is None: _M = NarrativeMemory()
    return _M
