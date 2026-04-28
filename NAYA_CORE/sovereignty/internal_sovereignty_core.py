"""NAYA V19 - Internal Sovereignty Core - Souverainete interne du systeme."""
import logging, os, time
from typing import Dict, List

log = logging.getLogger("NAYA.SOVEREIGNTY")

class InternalSovereigntyCore:
    """Garantit que le systeme reste souverain et independant."""

    CRITICAL_DEPENDENCIES = {
        "llm": {"required": False, "fallback": "internal_templates", "degraded_ok": True},
        "database": {"required": True, "fallback": "sqlite_local", "degraded_ok": True},
        "network": {"required": False, "fallback": "offline_mode", "degraded_ok": True},
        "redis": {"required": False, "fallback": "in_memory_cache", "degraded_ok": True},
    }

    def __init__(self):
        self._dependency_status: Dict[str, bool] = {}
        self._sovereignty_score = 1.0

    def check_sovereignty(self) -> Dict:
        """Verifie que le systeme n est pas dependant d un service externe critique."""
        issues = []
        for dep, cfg in self.CRITICAL_DEPENDENCIES.items():
            available = self._check_dependency(dep)
            self._dependency_status[dep] = available
            if not available and cfg["required"]:
                issues.append(f"{dep}: indisponible et requis")
            elif not available and not cfg["degraded_ok"]:
                issues.append(f"{dep}: indisponible, mode degrade non supporte")

        self._sovereignty_score = 1.0 - (len(issues) * 0.2)
        return {
            "sovereign": len(issues) == 0,
            "score": round(max(0, self._sovereignty_score), 2),
            "issues": issues,
            "dependencies": self._dependency_status
        }

    def _check_dependency(self, dep: str) -> bool:
        if dep == "llm":
            return bool(os.getenv("GROQ_API_KEY") or os.getenv("ANTHROPIC_API_KEY") or
                       os.getenv("OLLAMA_HOST"))
        if dep == "database":
            return True  # SQLite toujours disponible
        if dep == "network":
            return True  # Assume available
        if dep == "redis":
            return bool(os.getenv("REDIS_URL"))
        return True

    def get_fallback(self, dependency: str) -> str:
        cfg = self.CRITICAL_DEPENDENCIES.get(dependency, {})
        return cfg.get("fallback", "none")

    def get_stats(self) -> Dict:
        return {
            "sovereignty_score": self._sovereignty_score,
            "dependencies": self._dependency_status,
            "critical_deps": len(self.CRITICAL_DEPENDENCIES)
        }
