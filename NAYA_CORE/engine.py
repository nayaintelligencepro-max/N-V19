"""Moteur central NAYA V19.

Orchestre un cycle complet via le multi-agent orchestrator.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from NAYA_CORE.multi_agent_orchestrator import multi_agent_orchestrator


log = logging.getLogger(__name__)


class NayaEngine:
    """Façade d'exécution du moteur NAYA."""

    async def run_cycle(self) -> Dict[str, Any]:
        """Exécute un cycle complet et retourne le résultat brut."""
        result = await multi_agent_orchestrator.run_full_cycle()
        log.info("Engine cycle completed: #%s", result.get("cycle"))
        return result

    async def run_daemon(self, interval_seconds: int = 3600) -> None:
        """Démarre le mode daemon orchestration."""
        await multi_agent_orchestrator.start_daemon(interval_seconds=interval_seconds)


engine = NayaEngine()
