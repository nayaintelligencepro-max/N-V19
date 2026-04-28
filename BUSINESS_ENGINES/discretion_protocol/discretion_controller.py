"""
NAYA — Discretion Protocol
Opère en mode furtif : efficace sans exposition inutile.
"""
import hashlib, time
from enum import Enum
from typing import Dict, List, Optional

class DiscretionLevel(Enum):
    VISIBLE = "visible"         # Communication normale
    SILENT = "silent"           # Minimal exposure, résultats seulement
    STEALTH = "stealth"         # Opérations invisibles
    PHANTOM = "phantom"         # Zéro trace externe

class DiscretionProtocol:
    """Contrôle le niveau d'exposition opérationnelle de NAYA."""

    def __init__(self):
        self.level = DiscretionLevel.SILENT
        self._operation_log = []
        self._masked_fields = {"client_name", "revenue", "strategy", "contacts"}

    def activate_silent_mode(self): self.level = DiscretionLevel.SILENT
    def activate_stealth(self): self.level = DiscretionLevel.STEALTH
    def activate_phantom(self): self.level = DiscretionLevel.PHANTOM
    def deactivate_silent_mode(self): self.level = DiscretionLevel.VISIBLE
    def get_mode(self): return self.level.value

    def mask(self, data: Dict) -> Dict:
        """Masque les données sensibles selon le niveau."""
        if self.level == DiscretionLevel.VISIBLE:
            return data
        masked = {}
        for key, val in data.items():
            if key in self._masked_fields:
                masked[key] = self._hash(str(val))[:8] + "***"
            else:
                masked[key] = val
        return masked

    def should_log(self, operation: str) -> bool:
        if self.level == DiscretionLevel.PHANTOM: return False
        if self.level == DiscretionLevel.STEALTH:
            return operation in ("BOOT", "CRITICAL_ERROR", "REVENUE_CONFIRMED")
        return True

    def _hash(self, val: str) -> str:
        return hashlib.sha256(val.encode()).hexdigest()

    def log_operation(self, op: str, context: Dict = None):
        if self.should_log(op):
            self._operation_log.append({"op": op, "ts": time.time(), 
                                        "ctx": self.mask(context or {})})
