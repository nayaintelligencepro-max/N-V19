"""
NAYA — Telegram Integration
Alertes temps réel, commandes via Telegram Bot.
Requiert: TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID dans .env
"""
import os
import logging
from typing import Dict, Optional

log = logging.getLogger("NAYA.TELEGRAM")

def _gs(key, default=""):
    try:
        from SECRETS.secrets_loader import get_secret
        return get_secret(key, default) or default
    except Exception:
        return __import__("os").environ.get(key, default)


BASE_URL = "https://api.telegram.org/bot{token}"


class TelegramIntegration:
    """Bot Telegram NAYA pour alertes et commandes à distance."""

    def __init__(self):
        self.token = _gs("TELEGRAM_BOT_TOKEN")
        self.chat_id = _gs("TELEGRAM_CHAT_ID")
        self.available = bool(self.token and self.chat_id)

    def send(self, message: str, parse_mode: str = "Markdown", silent: bool = False) -> bool:
        if not self.available:
            log.debug("Telegram non configuré")
            return False
        try:
            import httpx
            resp = httpx.post(
                f"https://api.telegram.org/bot{self.token}/sendMessage",
                json={
                    "chat_id": self.chat_id,
                    "text": message[:4096],
                    "parse_mode": parse_mode,
                    "disable_notification": silent,
                },
                timeout=10,
            )
            return resp.status_code == 200
        except Exception as e:
            log.warning(f"Telegram send error: {e}")
            return False

    def send_opportunity(self, name: str, value: float, sector: str, actions: list) -> bool:
        msg = f"""🎯 *NOUVELLE OPPORTUNITÉ NAYA*

💼 *{name}*
💰 Valeur: *{value:,.0f}€*
🏭 Secteur: {sector}

*Actions 72h:*
{chr(10).join(f'• {a}' for a in (actions or [])[:3])}

_NAYA Supreme V6 — Autonomie Maximale_"""
        return self.send(msg)

    def send_alert(self, title: str, body: str, level: str = "info") -> bool:
        icons = {"success": "✅", "warning": "⚠️", "error": "🚨", "info": "ℹ️"}
        icon = icons.get(level, "🔔")
        msg = f"{icon} *{title}*\n\n{body}"
        return self.send(msg)

    def send_status(self, status: Dict) -> bool:
        comps = status.get("component_list", [])
        msg = f"""📊 *NAYA STATUS*

Version: `{status.get('version', '?')}`
Status: *{status.get('status', '?')}*
Uptime: `{status.get('uptime', '?')}`
Modules: {status.get('components', 0)}

*Active:* {', '.join(comps[:5])}"""
        return self.send(msg)
