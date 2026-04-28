"""Base abstraite des agents NAYA V19.

Centralise le cycle de vie, les métriques et la gestion d'erreurs des agents.
"""

from __future__ import annotations

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict


log = logging.getLogger(__name__)


@dataclass
class AgentStats:
    """Métriques d'exécution d'un agent."""

    runs: int = 0
    errors: int = 0
    last_duration_s: float = 0.0
    last_error: str = ""
    updated_at: float = field(default_factory=time.time)


class NayaBaseAgent(ABC):
    """Classe mère pour tous les agents métiers NAYA."""

    agent_name: str = "base_agent"

    def __init__(self) -> None:
        self.stats = AgentStats()

    @abstractmethod
    async def run(self, *args: Any, **kwargs: Any) -> Any:
        """Exécute la logique principale de l'agent."""

    async def run_safe(self, *args: Any, **kwargs: Any) -> Any:
        """Exécute ``run`` avec instrumentation et gestion d'erreurs."""
        start = time.perf_counter()
        self.stats.runs += 1
        self.stats.updated_at = time.time()
        try:
            return await self.run(*args, **kwargs)
        except Exception as exc:
            self.stats.errors += 1
            self.stats.last_error = f"{type(exc).__name__}: {exc}"
            log.exception("[%s] run_safe failure", self.agent_name)
            raise
        finally:
            self.stats.last_duration_s = round(time.perf_counter() - start, 4)
            self.stats.updated_at = time.time()

    async def heartbeat(self) -> Dict[str, Any]:
        """Retourne un heartbeat standardisé."""
        await asyncio.sleep(0)
        return {
            "agent": self.agent_name,
            "runs": self.stats.runs,
            "errors": self.stats.errors,
            "last_duration_s": self.stats.last_duration_s,
            "last_error": self.stats.last_error,
            "updated_at": self.stats.updated_at,
        }
