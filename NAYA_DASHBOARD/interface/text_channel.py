"""
NAYA Dashboard — Text Channel
Canal de transmission des intentions humaines en texte.
Aucune logique métier, aucun traitement — pont pur vers le système.
"""
import logging
from typing import Optional, Dict, Any

log = logging.getLogger("NAYA.DASHBOARD.text")

__all__ = ["TextChannel"]


class TextChannel:
    """
    Canal texte unidirectionnel Dashboard → Système NAYA.
    Reçoit les intentions humaines et les transmet sans transformation.
    """

    def __init__(self, system=None) -> None:
        self._system = system
        self._message_count = 0
        self._last_message: Optional[str] = None

    def send(self, text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Transmet un message texte au système NAYA.
        Retourne la réponse ou un accusé de réception.
        """
        self._message_count += 1
        self._last_message = text
        context = context or {}

        if not text or not text.strip():
            return {"status": "error", "message": "Texte vide"}

        log.debug(f"[TEXT_CHANNEL] Message #{self._message_count}: {text[:60]}...")

        # Transmettre au système si disponible
        if self._system:
            try:
                # Tenter via le sovereign engine
                if hasattr(self._system, "sovereign_engine") and self._system.sovereign_engine:
                    self._system.sovereign_engine.register_human_activity()
                # Tenter via le brain
                if hasattr(self._system, "_brain") and self._system._brain and self._system._brain.available:
                    from NAYA_CORE.execution.naya_brain import TaskType
                    result = self._system._brain.think(text, TaskType.FAST)
                    return {
                        "status": "ok",
                        "response": result.text,
                        "provider": result.provider,
                        "message_id": self._message_count,
                    }
            except Exception as e:
                log.warning(f"[TEXT_CHANNEL] Erreur transmission: {e}")

        return {
            "status": "received",
            "message_id": self._message_count,
            "text_preview": text[:100],
            "system_available": self._system is not None,
        }

    def get_stats(self) -> Dict[str, Any]:
        return {
            "messages_sent": self._message_count,
            "last_message_preview": (self._last_message or "")[:80],
            "system_connected": self._system is not None,
        }
