"""NAYA V19 — Notifier central. Telegram + Slack + Email. Clés dynamiques."""
import os, logging, json
from typing import List, Optional, Dict
log = logging.getLogger("NAYA.NOTIFIER")

def _gs(k, d=""):
    try:
        from SECRETS.secrets_loader import get_secret
        return get_secret(k, d) or d
    except Exception: return os.environ.get(k, d)

class TelegramNotifier:
    @property
    def _token(self) -> str: return _gs("TELEGRAM_BOT_TOKEN")
    @property
    def _chat(self) -> str: return _gs("TELEGRAM_CHAT_ID")
    @property
    def available(self) -> bool: return bool(self._token and self._chat)

    def send(self, msg: str, parse_mode: str = "HTML",
             buttons: List[List[Dict]] = None) -> bool:
        if not self.available: return False
        try:
            import requests
            payload = {"chat_id":self._chat,"text":msg,"parse_mode":parse_mode}
            if buttons:
                payload["reply_markup"] = json.dumps({"inline_keyboard":buttons})
            r = requests.post(f"https://api.telegram.org/bot{self._token}/sendMessage",
                json=payload, timeout=10)
            return r.status_code == 200
        except Exception as e: log.warning(f"[TG] {e}"); return False

class SlackNotifier:
    @property
    def _token(self) -> str: return _gs("SLACK_BOT_TOKEN")
    @property
    def _channel(self) -> str: return _gs("SLACK_CHANNEL_ALERTS","#naya-alerts")
    @property
    def available(self) -> bool: return bool(self._token)

    def send(self, msg: str) -> bool:
        if not self.available: return False
        try:
            import requests
            r = requests.post("https://slack.com/api/chat.postMessage",
                headers={"Authorization":f"Bearer {self._token}"},
                json={"channel":self._channel,"text":msg}, timeout=10)
            return r.json().get("ok", False)
        except Exception as e: log.warning(f"[SLACK] {e}"); return False

class MultiNotifier:
    def __init__(self):
        self.telegram = TelegramNotifier()
        self.slack = SlackNotifier()

    @property
    def channels_online(self) -> List[str]:
        ch = []
        if self.telegram.available: ch.append("telegram")
        if self.slack.available: ch.append("slack")
        return ch

    def send(self, title: str, body: str, level: str = "info",
             buttons: List = None) -> bool:
        icon = {"success":"✅","error":"❌","warning":"⚠️","info":"ℹ️",
                "money":"💰","critical":"🔴"}.get(level,"ℹ️")
        msg = f"{icon} <b>{title}</b>\n{body}"
        ok = False
        if self.telegram.available: ok = self.telegram.send(msg, buttons=buttons) or ok
        if self.slack.available: self.slack.send(f"{icon} {title}\n{body}")
        return ok

_N: Optional[MultiNotifier] = None
def get_notifier() -> MultiNotifier:
    global _N
    if _N is None: _N = MultiNotifier()
    return _N
