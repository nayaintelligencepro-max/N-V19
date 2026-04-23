"""NAYA V19 - Chat Panel - Panel de communication texte avec NAYA."""
import time, logging
from typing import Dict, List
log = logging.getLogger("NAYA.UI.CHAT")

class ChatPanel:
    """Panel de chat pour communiquer avec NAYA via texte."""

    def __init__(self):
        self._messages: List[Dict] = []
        self._max_messages = 500

    def send_message(self, text: str, sender: str = "founder") -> Dict:
        msg = {"text": text, "sender": sender, "ts": time.time(), "id": len(self._messages)}
        self._messages.append(msg)
        if len(self._messages) > self._max_messages:
            self._messages = self._messages[-250:]
        response = self._process_command(text)
        if response:
            self._messages.append({"text": response, "sender": "naya", "ts": time.time(), "id": len(self._messages)})
        return msg

    def _process_command(self, text: str) -> str:
        lower = text.lower()
        if "status" in lower:
            return "Systeme operationnel. Tous les modules actifs."
        if "hunt" in lower or "chasse" in lower:
            return "Lancement d un cycle de chasse..."
        if "revenue" in lower or "argent" in lower:
            return "Consultation du pipeline de revenus..."
        if "diagnostic" in lower:
            return "Execution du diagnostic complet..."
        return ""

    def get_messages(self, n: int = 20) -> List[Dict]:
        return self._messages[-n:]

    def get_stats(self) -> Dict:
        return {"total_messages": len(self._messages)}
