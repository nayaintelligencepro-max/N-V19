"""NAYA V19 - Detecteur de contournements internes - Detecte les workarounds qui masquent les douleurs"""
import logging, time
from typing import Dict, List
log = logging.getLogger("NAYA.PAIN.INTERNAL_WORKAROUNDS_DETECTOR")

class InternalWorkaroundsDetector:
    """Detecte les workarounds qui masquent les douleurs."""

    def __init__(self):
        self._log: List[Dict] = []

    WORKAROUND_SIGNALS = [
        "excel_comme_base_de_donnees", "copier_coller_manuel", "email_comme_workflow",
        "post_it_comme_kanban", "telephone_comme_crm", "papier_comme_archive",
        "whatsapp_comme_communication_interne"
    ]

    def detect(self, description: str) -> Dict:
        desc_lower = description.lower()
        detected = [w for w in self.WORKAROUND_SIGNALS if any(k in desc_lower for k in w.split("_"))]
        return {"workarounds_detected": len(detected), "signals": detected,
                "pain_hidden": len(detected) > 0, "severity": "high" if len(detected) >= 3 else "medium" if detected else "low"}

    def get_stats(self) -> Dict:
        return {"module": "internal_workarounds_detector"}
