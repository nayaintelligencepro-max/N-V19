"""NAYA V19 - System Panel - Panneau systeme pour le dashboard TORI."""
import logging, time
from typing import Dict

log = logging.getLogger("NAYA.PANEL.SYSTEM")

class SystemPanel:
    """Panneau d etat systeme complet pour TORI."""

    def __init__(self):
        self._last_refresh = 0.0

    def get_panel_data(self) -> Dict:
        self._last_refresh = time.time()
        data = {"panel": "system", "ts": time.time(), "sections": {}}

        # Diagnostic
        try:
            from naya_self_diagnostic.diagnostic import get_diagnostic
            data["sections"]["diagnostic"] = get_diagnostic().get_report()
        except Exception as e:
            data["sections"]["diagnostic"] = {"status": "unavailable", "error": str(e)[:50]}

        # Intention Loop
        try:
            from naya_intention_loop.intention_loop import get_intention_loop
            data["sections"]["intention"] = get_intention_loop().get_stats()
        except Exception:
            data["sections"]["intention"] = {"status": "unavailable"}

        # Guardian
        try:
            from naya_guardian.guardian import get_guardian
            data["sections"]["guardian"] = get_guardian().status
        except Exception:
            data["sections"]["guardian"] = {"status": "unavailable"}

        # Memory
        try:
            from naya_memory_narrative.narrative_memory import get_narrative_memory
            data["sections"]["memory"] = get_narrative_memory().get_stats()
        except Exception:
            data["sections"]["memory"] = {"status": "unavailable"}

        # Revenue
        try:
            from NAYA_REVENUE_ENGINE.payment_tracker import get_payment_tracker
            data["sections"]["payments"] = get_payment_tracker().get_stats()
        except Exception:
            data["sections"]["payments"] = {"status": "unavailable"}

        return data

    def get_stats(self) -> Dict:
        return {"last_refresh": self._last_refresh}
