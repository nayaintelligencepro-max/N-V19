"""NAYA V19 - Super Brain Hybrid - Interface vers le super brain V6."""
import logging
from typing import Dict, Optional, Any

log = logging.getLogger("NAYA.CORE.SUPERBRAIN")

class SuperBrainHybrid:
    """Interface simplifiee vers le super brain hybride V6."""

    def __init__(self):
        self._brain = None
        self._available = False

    def connect(self) -> bool:
        try:
            from NAYA_CORE.super_brain_hybrid_v6_0 import get_super_brain
            self._brain = get_super_brain()
            self._available = True
            log.info("[SUPERBRAIN] Connected to V6")
            return True
        except Exception as e:
            log.warning(f"[SUPERBRAIN] Connection failed: {e}")
            self._available = False
            return False

    @property
    def available(self) -> bool:
        return self._available

    def process(self, input_data: Dict) -> Dict:
        if not self._available or not self._brain:
            return {"error": "Super brain not available", "fallback": True}
        try:
            if hasattr(self._brain, "process"):
                return self._brain.process(input_data)
            return {"processed": True, "input": input_data}
        except Exception as e:
            return {"error": str(e), "fallback": True}

    def get_stats(self) -> Dict:
        if self._brain and hasattr(self._brain, "get_stats"):
            return self._brain.get_stats()
        return {"available": self._available, "connected": self._brain is not None}
