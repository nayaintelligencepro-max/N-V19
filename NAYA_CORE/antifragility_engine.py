"""
NAYA V19 - Antifragility Engine
Au-dela de la resilience: chaque echec renforce le systeme.
Prospect qui refuse -> ameliore l offre. Module qui crashe -> renforce le module.
"""
import time, logging, json, threading
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path

log = logging.getLogger("NAYA.ANTIFRAGILE")

@dataclass
class StressEvent:
    event_type: str  # rejection, crash, timeout, error, attack
    source: str
    description: str
    severity: float  # 0-1
    timestamp: float = field(default_factory=time.time)
    lesson_learned: str = ""
    improvement_applied: str = ""
    resolved: bool = False

class AntifragilityEngine:
    """Le systeme devient plus fort sous le stress."""

    def __init__(self):
        self._events: List[StressEvent] = []
        self._improvements: Dict[str, int] = {}  # improvement_type -> count
        self._lock = threading.RLock()
        self._resilience_score = 0.5
        self._total_stress = 0
        self._total_improvements = 0

    def record_stress(self, event_type: str, source: str, description: str,
                      severity: float = 0.5) -> StressEvent:
        """Enregistre un evenement de stress et determine l amelioration."""
        event = StressEvent(
            event_type=event_type, source=source,
            description=description, severity=severity
        )

        # Determiner la lecon et l amelioration
        lesson, improvement = self._analyze_stress(event)
        event.lesson_learned = lesson
        event.improvement_applied = improvement

        with self._lock:
            self._events.append(event)
            self._total_stress += 1
            if improvement:
                self._improvements[improvement] = self._improvements.get(improvement, 0) + 1
                self._total_improvements += 1
            self._update_resilience()
            if len(self._events) > 2000:
                self._events = self._events[-1000:]

        log.info(f"[ANTIFRAGILE] Stress: {event_type}/{source} -> Amelioration: {improvement}")
        return event

    def _analyze_stress(self, event: StressEvent) -> tuple:
        """Analyse le stress et determine l amelioration appropriee."""
        STRESS_RESPONSES = {
            "rejection": {
                "lesson": "Prospect a refuse - analyser pourquoi et ajuster",
                "improvements": {
                    "prix trop eleve": "adjust_pricing_model",
                    "pas le bon timing": "improve_timing_intelligence",
                    "offre pas adaptee": "improve_offer_matching",
                    "default": "refine_outreach_strategy"
                }
            },
            "crash": {
                "lesson": "Module crashe - renforcer la resilience",
                "improvements": {
                    "memory": "add_memory_limits",
                    "timeout": "increase_timeout_buffers",
                    "default": "add_error_handling"
                }
            },
            "timeout": {
                "lesson": "Timeout detecte - optimiser les performances",
                "improvements": {"default": "optimize_response_time"}
            },
            "error": {
                "lesson": "Erreur systeme - corriger et prevenir",
                "improvements": {"default": "improve_error_recovery"}
            },
            "attack": {
                "lesson": "Tentative d attaque - renforcer la securite",
                "improvements": {"default": "strengthen_security"}
            }
        }

        response = STRESS_RESPONSES.get(event.event_type, {
            "lesson": f"Stress inconnu: {event.event_type}",
            "improvements": {"default": "general_hardening"}
        })

        lesson = response["lesson"]
        desc_lower = event.description.lower()
        improvement = response["improvements"].get("default", "general_hardening")
        for keyword, imp in response["improvements"].items():
            if keyword != "default" and keyword in desc_lower:
                improvement = imp
                break

        return lesson, improvement

    def _update_resilience(self) -> None:
        """Met a jour le score de resilience base sur le ratio stress/improvements."""
        if self._total_stress > 0:
            ratio = self._total_improvements / self._total_stress
            self._resilience_score = min(1.0, 0.5 + ratio * 0.5)

    def get_resilience_score(self) -> float:
        return round(self._resilience_score, 3)

    def get_improvement_summary(self) -> Dict:
        with self._lock:
            return {
                "resilience_score": self.get_resilience_score(),
                "total_stress_events": self._total_stress,
                "total_improvements": self._total_improvements,
                "improvements_by_type": dict(self._improvements),
                "recent_events": [
                    {"type": e.event_type, "source": e.source, "improvement": e.improvement_applied}
                    for e in self._events[-10:]
                ]
            }

    def get_stats(self) -> Dict:
        return self.get_improvement_summary()

_engine = None
_lock = threading.Lock()
def get_antifragility() -> AntifragilityEngine:
    global _engine
    if _engine is None:
        with _lock:
            if _engine is None:
                _engine = AntifragilityEngine()
    return _engine
