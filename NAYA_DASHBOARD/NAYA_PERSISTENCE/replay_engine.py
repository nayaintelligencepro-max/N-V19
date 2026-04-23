"""NAYA V19 - Replay Engine - Replay des evenements pour debug."""
import time, logging, json
from typing import Dict, List, Optional
from pathlib import Path
log = logging.getLogger("NAYA.REPLAY")

class ReplayEngine:
    """Enregistre et replay les evenements systeme pour debug et analyse."""

    REPLAY_FILE = Path("data/cache/event_replay.json")

    def __init__(self):
        self._events: List[Dict] = []
        self._recording = False
        self._replay_position = 0

    def start_recording(self) -> None:
        self._recording = True
        log.info("[REPLAY] Recording started")

    def stop_recording(self) -> None:
        self._recording = False
        self._save()
        log.info(f"[REPLAY] Recording stopped: {len(self._events)} events")

    def record_event(self, event_type: str, module: str, data: Dict = None) -> None:
        if not self._recording:
            return
        self._events.append({
            "type": event_type, "module": module,
            "data": data or {}, "ts": time.time()
        })
        if len(self._events) > 5000:
            self._events = self._events[-2500:]

    def replay(self, start_idx: int = 0, end_idx: int = None) -> List[Dict]:
        end = end_idx or len(self._events)
        return self._events[start_idx:end]

    def replay_by_module(self, module: str) -> List[Dict]:
        return [e for e in self._events if e["module"] == module]

    def replay_by_type(self, event_type: str) -> List[Dict]:
        return [e for e in self._events if e["type"] == event_type]

    def _save(self) -> None:
        try:
            self.REPLAY_FILE.parent.mkdir(parents=True, exist_ok=True)
            self.REPLAY_FILE.write_text(json.dumps(self._events[-1000:], default=str))
        except Exception as e:
            log.debug(f"[REPLAY] Save: {e}")

    def get_stats(self) -> Dict:
        return {
            "recording": self._recording,
            "total_events": len(self._events),
            "event_types": list(set(e["type"] for e in self._events[-100:]))
        }
