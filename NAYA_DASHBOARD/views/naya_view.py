"""NAYA V19 - Naya View - Vue principale du dashboard."""
import time, logging
from typing import Dict, List

log = logging.getLogger("NAYA.VIEW.MAIN")

class NayaView:
    """Vue principale du dashboard TORI - resume complet du systeme."""

    def render(self) -> Dict:
        view = {"view": "naya_main", "ts": time.time(), "sections": []}

        # Pipeline
        try:
            from NAYA_CORE.hunt.cash_rapide_classifier import get_classifier
            clf = get_classifier()
            stats = clf.get_stats()
            view["sections"].append({
                "name": "Pipeline",
                "data": stats,
                "highlights": {
                    "active": stats.get("active", 0),
                    "incubation": stats.get("incubation", 0),
                    "pipeline_value": stats.get("pipeline_value_eur", 0)
                }
            })
        except Exception:
            pass

        # Revenue
        try:
            from NAYA_REVENUE_ENGINE.payment_tracker import get_payment_tracker
            view["sections"].append({"name": "Revenue", "data": get_payment_tracker().get_stats()})
        except Exception:
            pass

        # Learning
        try:
            from NAYA_CORE.learning_feedback_engine import get_learning_engine
            view["sections"].append({"name": "Learning", "data": get_learning_engine().get_stats()})
        except Exception:
            pass

        # Antifragility
        try:
            from NAYA_CORE.antifragility_engine import get_antifragility
            view["sections"].append({"name": "Antifragility", "data": get_antifragility().get_stats()})
        except Exception:
            pass

        # Memory narrative
        try:
            from naya_memory_narrative.narrative_memory import get_narrative_memory
            view["sections"].append({"name": "Memory", "data": get_narrative_memory().get_stats()})
        except Exception:
            pass

        # Guardian
        try:
            from naya_guardian.guardian import get_guardian
            view["sections"].append({"name": "Guardian", "data": get_guardian().status})
        except Exception:
            pass

        return view

    def get_stats(self) -> Dict:
        return {"sections_available": 6}
