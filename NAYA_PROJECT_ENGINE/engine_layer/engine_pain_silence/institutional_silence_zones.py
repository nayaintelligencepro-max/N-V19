"""NAYA V19 - Zones de silence institutionnel - Ou les institutions ne parlent pas de leurs douleurs"""
import logging, time
from typing import Dict, List
log = logging.getLogger("NAYA.PAIN.INSTITUTIONAL_SILENCE_ZONES")

class InstitutionalSilenceZones:
    """Ou les institutions ne parlent pas de leurs douleurs."""

    def __init__(self):
        self._log: List[Dict] = []

    SILENCE_ZONES = {
        "budget_overruns": {"sectors": ["gouvernement", "sante", "education"], "shame_level": 0.85},
        "tech_debt": {"sectors": ["finance", "industrie", "assurance"], "shame_level": 0.7},
        "staff_inefficiency": {"sectors": ["gouvernement", "administration"], "shame_level": 0.9},
        "security_breaches": {"sectors": ["finance", "tech", "sante"], "shame_level": 0.95},
        "compliance_gaps": {"sectors": ["pharma", "finance", "energie"], "shame_level": 0.8},
    }

    def identify_zones(self, sector: str) -> list:
        zones = []
        for zone, cfg in self.SILENCE_ZONES.items():
            if sector in cfg["sectors"]:
                zones.append({"zone": zone, "shame_level": cfg["shame_level"]})
        return sorted(zones, key=lambda z: z["shame_level"], reverse=True)

    def get_stats(self) -> Dict:
        return {"module": "institutional_silence_zones"}
