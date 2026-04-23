"""
NAYA SUPREME V19 — Prospect Memory
Chaque interaction prospect est mémorisée pour apprentissage continu.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from .vector_store import get_vector_store

log = logging.getLogger("NAYA.ProspectMemory")


class ProspectMemory:
    """Mémoire dédiée aux prospects — historique, scores, préférences."""

    def __init__(self) -> None:
        self._store = get_vector_store()

    async def remember(self, prospect_id: str, event_type: str, data: dict[str, Any]) -> str:
        """Enregistre un événement lié à un prospect."""
        interaction = {
            "prospect_id": prospect_id,
            "type": event_type,
            "data": data,
            "timestamp": time.time(),
        }
        doc_id = await self._store.save_interaction(interaction)
        log.debug("Prospect %s — %s mémorisé (%s)", prospect_id, event_type, doc_id)
        return doc_id

    async def recall(self, prospect_id: str) -> list[dict[str, Any]]:
        """Récupère tout l'historique d'un prospect."""
        return await self._store.get_prospect_history(prospect_id)

    async def last_touch(self, prospect_id: str) -> dict[str, Any] | None:
        """Retourne le dernier point de contact avec un prospect."""
        history = await self.recall(prospect_id)
        if not history:
            return None
        return max(history, key=lambda h: h.get("timestamp", 0))

    async def days_since_last_touch(self, prospect_id: str) -> float:
        """Nombre de jours depuis le dernier contact."""
        last = await self.last_touch(prospect_id)
        if not last:
            return float("inf")
        elapsed = time.time() - last.get("timestamp", 0)
        return elapsed / 86_400

    async def save_pains(self, pains: list[dict[str, Any]]) -> None:
        """Sauvegarde une liste de douleurs détectées."""
        for pain in pains:
            await self._store.save_market_signal({"type": "pain", **pain})
        log.info("%d douleurs mémorisées", len(pains))

    async def get_scored_pains(self, min_score: int = 70) -> list[dict[str, Any]]:
        """Retourne les douleurs avec score >= min_score."""
        signals = await self._store.get_market_patterns(sector="", days=30)
        return [
            s for s in signals
            if s.get("type") == "pain" and s.get("score", 0) >= min_score
        ]


# Singleton
_prospect_memory: ProspectMemory | None = None


def get_prospect_memory() -> ProspectMemory:
    global _prospect_memory
    if _prospect_memory is None:
        _prospect_memory = ProspectMemory()
    return _prospect_memory
