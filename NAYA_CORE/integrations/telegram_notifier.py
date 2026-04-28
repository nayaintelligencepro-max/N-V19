"""
NAYA V19 — Telegram Notifier Production
Toutes les alertes critiques, paiements, deals en temps réel.
"""
import os, logging, urllib.request, urllib.parse, json, threading, time
from typing import Optional, List
from queue import Queue

log = logging.getLogger("NAYA.TELEGRAM")


def _gs(k: str, d: str = "") -> str:
    try:
        from SECRETS.secrets_loader import get_secret
        return get_secret(k, d) or d
    except Exception:
        return os.environ.get(k, d)


class TelegramNotifier:
    """Notificateur Telegram async avec queue et retry."""

    def __init__(self):
        self._queue: Queue = Queue()
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._sent = 0
        self._failed = 0
        self._start_worker()

    def _start_worker(self):
        self._running = True
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def _worker(self):
        while self._running:
            try:
                msg = self._queue.get(timeout=5)
                self._send_now(msg)
                self._queue.task_done()
            except Exception:
                pass

    def _send_now(self, text: str, retries: int = 3) -> bool:
        token = _gs("TELEGRAM_BOT_TOKEN", "")
        chat_id = _gs("TELEGRAM_CHAT_ID", "")
        if not token or not chat_id:
            log.debug("[TELEGRAM] No token/chat_id configured")
            return False
        for attempt in range(retries):
            try:
                url = f"https://api.telegram.org/bot{token}/sendMessage"
                data = urllib.parse.urlencode({
                    "chat_id": chat_id, "text": text, "parse_mode": "HTML"
                }).encode()
                urllib.request.urlopen(url, data=data, timeout=10)
                self._sent += 1
                return True
            except Exception as e:
                log.debug(f"[TELEGRAM] Attempt {attempt+1} failed: {e}")
                time.sleep(2 ** attempt)
        self._failed += 1
        return False

    def send(self, text: str):
        """Envoie un message (async via queue)."""
        self._queue.put(text[:4096])

    def alert_payment(self, amount: float, client: str, method: str = "paypal"):
        self.send(
            f"💰 <b>PAIEMENT REÇU</b>\n"
            f"Client: {client}\nMontant: {amount:,.2f}€\nVia: {method.upper()}\n"
            f"⏰ {time.strftime('%d/%m %H:%M')}"
        )

    def alert_deal_found(self, company: str, value: float, category: str):
        self.send(
            f"🎯 <b>DEAL DÉTECTÉ</b>\n"
            f"Entreprise: {company}\nValeur estimée: {value:,.0f}€\n"
            f"Catégorie: {category}\n⏰ {time.strftime('%d/%m %H:%M')}"
        )

    def alert_outreach_sent(self, prospect: str, method: str):
        self.send(
            f"📤 <b>OUTREACH ENVOYÉ</b>\n"
            f"Prospect: {prospect}\nCanal: {method}\n"
            f"⏰ {time.strftime('%d/%m %H:%M')}"
        )

    def alert_system(self, msg: str, level: str = "INFO"):
        icon = {"INFO": "ℹ️", "WARNING": "⚠️", "ERROR": "🚨", "SUCCESS": "✅"}.get(level, "📢")
        self.send(f"{icon} <b>NAYA V19 SYSTÈME</b>\n{msg}\n⏰ {time.strftime('%d/%m %H:%M')}")

    def stats(self) -> dict:
        return {"sent": self._sent, "failed": self._failed, "queued": self._queue.qsize()}

    def stop(self):
        self._running = False


_instance: Optional[TelegramNotifier] = None

def get_notifier() -> TelegramNotifier:
    global _instance
    if _instance is None:
        _instance = TelegramNotifier()
    return _instance
