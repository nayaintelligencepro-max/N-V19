"""NAYA V19 - Domain Initializer - Initialise les domaines metier."""
import logging
from typing import Dict, List
log = logging.getLogger("NAYA.DOMAIN")

class DomainInitializer:
    DOMAINS = [
        {"name": "hunt", "module": "NAYA_CORE.hunt", "critical": True},
        {"name": "revenue", "module": "NAYA_REVENUE_ENGINE", "critical": True},
        {"name": "projects", "module": "NAYA_PROJECT_ENGINE", "critical": True},
        {"name": "security", "module": "REAPERS", "critical": True},
        {"name": "channel", "module": "CHANNEL_INTELLIGENCE", "critical": False},
        {"name": "orchestration", "module": "NAYA_ORCHESTRATION", "critical": False},
    ]

    def __init__(self):
        self._initialized: Dict[str, bool] = {}

    def initialize_all(self) -> Dict:
        results = {}
        for domain in self.DOMAINS:
            try:
                __import__(domain["module"])
                self._initialized[domain["name"]] = True
                results[domain["name"]] = "ok"
            except Exception as e:
                self._initialized[domain["name"]] = False
                results[domain["name"]] = str(e)[:50]
        return results

    def get_stats(self) -> Dict:
        return {"domains": len(self.DOMAINS), "initialized": self._initialized}
