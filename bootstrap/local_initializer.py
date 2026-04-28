"""NAYA V19 - Local Initializer - Initialisation pour le mode local."""
import os, logging
from pathlib import Path
from typing import Dict

log = logging.getLogger("NAYA.BOOT.LOCAL")

class LocalInitializer:
    """Prepare l environnement local: dossiers, fichiers, DB."""

    REQUIRED_DIRS = [
        "data/db", "data/cache", "data/exports",
        "logs", "SECRETS/keys", "SECRETS/service_accounts"
    ]

    def initialize(self) -> Dict:
        created = []
        for d in self.REQUIRED_DIRS:
            path = Path(d)
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
                created.append(d)

        # Create .env if missing
        env_file = Path(".env")
        if not env_file.exists():
            env_example = Path(".env.example")
            if env_example.exists():
                import shutil
                shutil.copy(env_example, env_file)
                created.append(".env (from .env.example)")

        log.info(f"[LOCAL] Initialized: {len(created)} items created")
        return {"initialized": True, "created": created, "dirs_checked": len(self.REQUIRED_DIRS)}

    def verify(self) -> Dict:
        missing = [d for d in self.REQUIRED_DIRS if not Path(d).exists()]
        return {"ok": len(missing) == 0, "missing": missing}

    def get_stats(self) -> Dict:
        return self.verify()
