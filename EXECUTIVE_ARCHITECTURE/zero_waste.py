"""NAYA V19 - Zero Waste Engine - Rien n est jete, tout est recycle."""
import logging, time
from typing import Dict, List

log = logging.getLogger("NAYA.EXEC.ZEROWASTE")

class ZeroWasteEngine:
    """Garantit que chaque creation, chaque echec, chaque donnee est reutilisee."""

    RECYCLABLE_TYPES = [
        "service_template", "offer_document", "outreach_message",
        "audit_report", "chatbot_config", "landing_page",
        "pricing_model", "negotiation_script", "client_insight"
    ]

    def __init__(self):
        self._waste_log: List[Dict] = []
        self._recycled: List[Dict] = []
        self._total_saved_value = 0.0

    def check_waste(self, item: Dict) -> Dict:
        """Verifie si un item peut etre recycle au lieu d etre jete."""
        item_type = item.get("type", "unknown")
        if item_type in self.RECYCLABLE_TYPES:
            return {
                "recyclable": True,
                "recycle_to": self._suggest_recycle_target(item),
                "estimated_value_saved": item.get("creation_cost", 0) * 0.7
            }
        return {"recyclable": False, "reason": "Type non recyclable", "suggestion": "Archiver pour reference"}

    def recycle(self, item: Dict, target_project: str) -> Dict:
        """Recycle un item vers un nouveau projet."""
        recycled_item = {
            "original": item, "target": target_project,
            "recycled_at": time.time(), "status": "recycled"
        }
        self._recycled.append(recycled_item)
        value = item.get("creation_cost", 0) * 0.7
        self._total_saved_value += value
        log.info(f"[ZERO-WASTE] Recycle: {item.get('type')} -> {target_project} | {value}EUR economises")
        return recycled_item

    def from_failure(self, failure: Dict) -> Dict:
        """Transforme un echec en lecon reutilisable."""
        lesson = {
            "type": "failure_lesson",
            "original_failure": failure.get("description", ""),
            "sector": failure.get("sector", ""),
            "lesson": f"Eviter: {failure.get('reason', 'inconnu')}",
            "created_at": time.time()
        }
        self._recycled.append(lesson)
        return lesson

    def _suggest_recycle_target(self, item: Dict) -> str:
        sector = item.get("sector", "general")
        item_type = item.get("type", "")
        if item_type in ("chatbot_config", "landing_page"):
            return "Adapter pour un autre secteur similaire"
        if item_type == "audit_report":
            return "Transformer en template de diagnostic"
        return "Integrer dans la bibliotheque de templates"

    def get_stats(self) -> Dict:
        return {
            "total_recycled": len(self._recycled),
            "value_saved_eur": self._total_saved_value,
            "recyclable_types": len(self.RECYCLABLE_TYPES)
        }
