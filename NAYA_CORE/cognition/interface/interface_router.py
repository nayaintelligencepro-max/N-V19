"""
NAYA_CORE — Cognition Interface Router
========================================
Route les entrées externes vers les couches cognitives appropriées.
"""
from typing import Dict, Any, Optional, List
from enum import Enum
import logging

log = logging.getLogger("NAYA.COG_INTERFACE")

class InputChannel(Enum):
    TEXT = "text"
    VOICE = "voice"
    API = "api"
    WEBSOCKET = "websocket"
    INTERNAL = "internal"

class CognitionInterfaceRouter:
    """
    Router d'interface cognitif.
    Normalise et route les entrées vers les bonnes couches.
    """

    def __init__(self):
        self._handlers: Dict[InputChannel, List] = {ch: [] for ch in InputChannel}
        self._preprocessors: List = []

    def register_handler(self, channel: InputChannel, handler) -> None:
        self._handlers[channel].append(handler)

    def add_preprocessor(self, preprocessor) -> None:
        self._preprocessors.append(preprocessor)

    def route(self, raw_input: Any, channel: InputChannel = InputChannel.API) -> Dict[str, Any]:
        # Normalize input
        normalized = self._normalize(raw_input, channel)

        # Apply preprocessors
        for preprocessor in self._preprocessors:
            try: normalized = preprocessor(normalized)
            except Exception as e: log.warning(f"Preprocessor error: {e}")

        # Route to handlers
        results = []
        for handler in self._handlers.get(channel, []):
            try: results.append(handler(normalized))
            except Exception as e: log.error(f"Handler error: {e}")

        return {
            "normalized_input": normalized,
            "channel": channel.value,
            "handler_results": results,
            "routed": len(results) > 0
        }

    def _normalize(self, raw_input: Any, channel: InputChannel) -> Dict[str, Any]:
        if isinstance(raw_input, dict): return raw_input
        if isinstance(raw_input, str):
            return {"text": raw_input, "type": "text_input", "channel": channel.value}
        return {"data": raw_input, "type": "raw", "channel": channel.value}

    def get_status(self) -> Dict[str, Any]:
        return {
            "channels": {ch.value: len(handlers) for ch, handlers in self._handlers.items()},
            "preprocessors": len(self._preprocessors)
        }


_ROUTER: Optional[CognitionInterfaceRouter] = None

def get_interface_router() -> CognitionInterfaceRouter:
    global _ROUTER
    if _ROUTER is None: _ROUTER = CognitionInterfaceRouter()
    return _ROUTER
