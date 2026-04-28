"""NAYA Bootstrap — VM Initializer"""
import os
import logging
from typing import Dict, Any

log = logging.getLogger("NAYA.BOOTSTRAP.VM")

class VMInitializer:
    """Initialisation de l'environnement VM/GCE pour NAYA."""

    REQUIRED_ENV_VARS = ["ANTHROPIC_API_KEY"]
    OPTIONAL_ENV_VARS = ["OPENAI_API_KEY", "REDIS_URL", "DATABASE_URL"]

    @staticmethod
    def prepare() -> bool:
        """Prepare VM environment. Returns True if ready."""
        log.info("[VM_INIT] Preparing VM environment...")
        VMInitializer._setup_directories()
        VMInitializer._check_environment()
        VMInitializer._configure_logging()
        log.info("[VM_INIT] VM Environment ready")
        return True

    @staticmethod
    def _setup_directories() -> None:
        dirs = ["logs", "data/db", "data/cache", "snapshots", "logs/execution_reports"]
        for d in dirs:
            os.makedirs(d, exist_ok=True)

    @staticmethod
    def _check_environment() -> Dict[str, str]:
        status = {}
        for var in VMInitializer.REQUIRED_ENV_VARS:
            status[var] = "SET" if os.environ.get(var) else "MISSING"
            if status[var] == "MISSING":
                log.warning(f"[VM_INIT] Required env var missing: {var}")
        for var in VMInitializer.OPTIONAL_ENV_VARS:
            status[var] = "SET" if os.environ.get(var) else "NOT_SET"
        return status

    @staticmethod
    def _configure_logging() -> None:
        log_level = os.environ.get("LOG_LEVEL", "INFO")
        logging.basicConfig(level=getattr(logging, log_level, logging.INFO),
                           format="%(asctime)s [%(levelname)s] %(name)s — %(message)s")

    @staticmethod
    def get_vm_metadata() -> Dict[str, Any]:
        """Get GCE VM metadata if available."""
        try:
            import urllib.request
            req = urllib.request.Request(
                "http://metadata.google.internal/computeMetadata/v1/instance/?recursive=true",
                headers={"Metadata-Flavor": "Google"}
            )
            with urllib.request.urlopen(req, timeout=1) as r:
                import json
                return json.loads(r.read())
        except Exception:
            return {"environment": "local_or_non_gce"}
