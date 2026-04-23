"""NAYA V19 - Signature Panel - Panel d identite et signature NAYA."""
import time
from typing import Dict

class SignaturePanel:
    """Affiche l identite et la signature du systeme."""

    IDENTITY = {
        "name": "NAYA SUPREME",
        "version": "12.2.0",
        "type": "Autonomous Business Revenue System",
        "owner": "Fondatrice",
        "status": "Operationnel",
        "mode": "Furtif",
        "vendable": False,
        "transmissible": True,
    }

    def get_panel_data(self) -> Dict:
        return {
            "panel": "signature",
            "identity": self.IDENTITY,
            "uptime": self._get_uptime(),
            "ts": time.time()
        }

    def _get_uptime(self) -> str:
        try:
            import os
            boot = os.environ.get("NAYA_BOOT_TIME", "")
            if boot:
                elapsed = time.time() - float(boot)
                hours = int(elapsed / 3600)
                return f"{hours}h"
        except Exception:
            pass
        return "N/A"
