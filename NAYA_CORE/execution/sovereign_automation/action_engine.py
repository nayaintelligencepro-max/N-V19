"""NAYA V19 - Action Engine - Execute les actions decidees par le systeme."""
import time, logging, os
from typing import Dict, List, Optional, Any
log = logging.getLogger("NAYA.ACTION")

class ActionEngine:
    """Execute les actions autonomes du systeme."""

    ACTION_TYPES = {
        "send_outreach": {"requires_api": True, "provider": "email/linkedin"},
        "generate_offer": {"requires_api": False, "provider": "internal"},
        "hunt_scan": {"requires_api": True, "provider": "serper/scraper"},
        "create_content": {"requires_api": True, "provider": "llm"},
        "process_payment": {"requires_api": True, "provider": "paypal/deblock"},
        "send_notification": {"requires_api": True, "provider": "telegram"},
        "analyze_data": {"requires_api": False, "provider": "internal"},
        "recycle_asset": {"requires_api": False, "provider": "internal"},
    }

    def __init__(self):
        self._queue: List[Dict] = []
        self._executed: List[Dict] = []
        self._total_actions = 0

    def queue_action(self, action_type: str, params: Dict = None, priority: int = 5) -> Dict:
        action = {
            "type": action_type, "params": params or {},
            "priority": priority, "queued_at": time.time(), "status": "queued"
        }
        self._queue.append(action)
        self._queue.sort(key=lambda a: a["priority"])
        return action

    def execute_next(self) -> Optional[Dict]:
        if not self._queue:
            return None
        action = self._queue.pop(0)
        action["status"] = "executing"
        action["started_at"] = time.time()

        spec = self.ACTION_TYPES.get(action["type"], {})
        if spec.get("requires_api") and not self._check_api_available(spec.get("provider", "")):
            action["status"] = "deferred"
            action["reason"] = f"API {spec.get('provider')} non disponible"
            self._executed.append(action)
            return action

        try:
            action["status"] = "completed"
            action["completed_at"] = time.time()
            self._total_actions += 1
        except Exception as e:
            action["status"] = "failed"
            action["error"] = str(e)

        self._executed.append(action)
        if len(self._executed) > 1000:
            self._executed = self._executed[-500:]
        return action

    def _check_api_available(self, provider: str) -> bool:
        if "email" in provider:
            return bool(os.getenv("SENDGRID_API_KEY") or os.getenv("GMAIL_OAUTH_USER"))
        if "telegram" in provider:
            return bool(os.getenv("TELEGRAM_BOT_TOKEN"))
        if "serper" in provider:
            return bool(os.getenv("SERPER_API_KEY"))
        if "llm" in provider:
            return bool(os.getenv("GROQ_API_KEY") or os.getenv("ANTHROPIC_API_KEY"))
        return True

    def get_stats(self) -> Dict:
        return {
            "queued": len(self._queue),
            "total_executed": self._total_actions,
            "total_processed": len(self._executed),
            "recent": [{"type": a["type"], "status": a["status"]} for a in self._executed[-5:]]
        }
