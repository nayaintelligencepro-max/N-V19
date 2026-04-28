"""
NAYA V19 — Deblock.me Payment Engine
Moteur dédié Deblock : génération liens, suivi paiements, webhooks, relances.
Deblock = payment principal pour Polynésie française (pas de Stripe).
"""
import os, time, json, logging, uuid, threading
from typing import Dict, Optional, List
from dataclasses import dataclass, field
from pathlib import Path

log = logging.getLogger("NAYA.PAYMENT.DEBLOCK")

def _gs(k: str, d: str = "") -> str:
    try:
        from SECRETS.secrets_loader import get_secret
        return get_secret(k, d) or d
    except Exception:
        return os.environ.get(k, d)


@dataclass
class DeblockPayment:
    payment_id: str
    prospect_name: str
    amount_eur: float
    description: str
    link: str = ""
    status: str = "pending"  # pending / sent / paid / overdue
    created_at: float = field(default_factory=time.time)
    paid_at: Optional[float] = None
    reminders_sent: int = 0


DATA_FILE = Path("data/cache/deblock_payments.json")


class DeblockEngine:
    """
    Moteur Deblock.me production.
    - Génère liens pré-remplis avec montant
    - Suit les paiements (polling webhook ou manuel)
    - Envoie relances automatiques via Telegram
    - Réconciliation comptable quotidienne
    """

    BASE_URL: str = ""          # chargé depuis SECRETS/keys/payment/deblock.json
    FALLBACK_URL: str = "https://deblock.com/a-ftp860"

    def __init__(self):
        self._payments: Dict[str, DeblockPayment] = {}
        self._lock = threading.RLock()
        self._total_invoiced = 0.0
        self._total_collected = 0.0
        self._load()
        self._base = self._resolve_base()

    def _resolve_base(self) -> str:
        url = _gs("DEBLOCK_ME_URL", "")
        if not url:
            try:
                f = Path(__file__).parent.parent / "SECRETS/keys/payment/deblock.json"
                if f.exists():
                    data = json.loads(f.read_text())
                    url = data.get("link", data.get("url", ""))
            except Exception:
                pass
        return url or self.FALLBACK_URL

    def generate_link(self, amount: float, description: str,
                      prospect_name: str = "") -> Dict:
        """Génère un lien Deblock avec montant pré-rempli."""
        pid = str(uuid.uuid4())[:12]
        # Deblock.me format: base_url?amount=X&description=Y
        safe_desc = description.replace(" ", "+")[:80]
        link = f"{self._base}?amount={amount:.2f}&description={safe_desc}&ref={pid}"

        p = DeblockPayment(
            payment_id=pid,
            prospect_name=prospect_name,
            amount_eur=amount,
            description=description,
            link=link,
            status="pending",
        )
        with self._lock:
            self._payments[pid] = p
            self._total_invoiced += amount
        self._save()
        log.info(f"[DEBLOCK] Lien généré {pid} — {amount}€ — {prospect_name}")
        return {"payment_id": pid, "link": link, "amount": amount, "status": "pending"}

    def mark_paid(self, payment_id: str, amount_received: Optional[float] = None) -> bool:
        with self._lock:
            p = self._payments.get(payment_id)
            if not p:
                return False
            p.status = "paid"
            p.paid_at = time.time()
            paid = amount_received or p.amount_eur
            self._total_collected += paid
        self._save()
        log.info(f"[DEBLOCK] Paiement confirmé {payment_id} — {paid}€")
        self._notify_payment(p, paid)
        return True

    def _notify_payment(self, p: DeblockPayment, amount: float):
        """Envoie notification Telegram sur paiement reçu."""
        try:
            token = _gs("TELEGRAM_BOT_TOKEN", "")
            chat_id = _gs("TELEGRAM_CHAT_ID", "")
            if not token or not chat_id:
                return
            msg = (
                f"💰 PAIEMENT REÇU — NAYA V19\n"
                f"Client: {p.prospect_name}\n"
                f"Montant: {amount:.2f}€\n"
                f"Ref: {p.payment_id}\n"
                f"Via: Deblock.me\n"
                f"Total collecté: {self._total_collected:.2f}€"
            )
            import urllib.request, urllib.parse
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            data = urllib.parse.urlencode({"chat_id": chat_id, "text": msg}).encode()
            urllib.request.urlopen(url, data=data, timeout=10)
        except Exception as e:
            log.debug(f"[DEBLOCK] Telegram notify failed: {e}")

    def get_pending(self) -> List[DeblockPayment]:
        with self._lock:
            return [p for p in self._payments.values() if p.status in ("pending", "sent")]

    def get_overdue(self, hours: int = 72) -> List[DeblockPayment]:
        cutoff = time.time() - (hours * 3600)
        with self._lock:
            return [p for p in self._payments.values()
                    if p.status in ("pending", "sent") and p.created_at < cutoff]

    def dashboard(self) -> Dict:
        with self._lock:
            paid = [p for p in self._payments.values() if p.status == "paid"]
            pending = [p for p in self._payments.values() if p.status in ("pending", "sent")]
            return {
                "total_invoiced": self._total_invoiced,
                "total_collected": self._total_collected,
                "outstanding": self._total_invoiced - self._total_collected,
                "paid_count": len(paid),
                "pending_count": len(pending),
                "conversion_rate": round(len(paid) / max(len(self._payments), 1) * 100, 1),
            }

    def _load(self):
        try:
            if DATA_FILE.exists():
                raw = json.loads(DATA_FILE.read_text())
                for pid, d in raw.get("payments", {}).items():
                    self._payments[pid] = DeblockPayment(**d)
                self._total_invoiced = raw.get("total_invoiced", 0.0)
                self._total_collected = raw.get("total_collected", 0.0)
        except Exception as e:
            log.debug(f"[DEBLOCK] Load failed: {e}")

    def _save(self):
        try:
            DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
            with self._lock:
                raw = {
                    "payments": {pid: vars(p) for pid, p in self._payments.items()},
                    "total_invoiced": self._total_invoiced,
                    "total_collected": self._total_collected,
                }
            DATA_FILE.write_text(json.dumps(raw, indent=2))
        except Exception as e:
            log.debug(f"[DEBLOCK] Save failed: {e}")


# Singleton
_instance: Optional[DeblockEngine] = None


def get_deblock() -> DeblockEngine:
    global _instance
    if _instance is None:
        _instance = DeblockEngine()
    return _instance
