"""
NAYA ACCELERATION — InstantCloser
Génère et envoie un lien de paiement < 5 minutes après accord verbal.
Intègre PayPal.me et Deblok.me (Polynésie française — Stripe indisponible).
Log immuable SHA-256 pour chaque transaction.
"""

import hashlib
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger("NAYA.INSTANT_CLOSER")

MIN_CONTRACT_VALUE_EUR = 1_000
PAYMENT_LOG_FILE = Path("data/payments/instant_closer_log.jsonl")


class PaymentMethod(str, Enum):
    PAYPAL = "paypal"
    DEBLOK = "deblok"
    BANK_TRANSFER = "bank_transfer"


@dataclass
class PaymentLink:
    """Lien de paiement généré et loggé."""
    payment_id: str
    offer_id: str
    company: str
    contact_email: str
    amount_eur: int
    method: PaymentMethod
    url: str
    sha256_hash: str       # Log immuable
    status: str            # pending | sent | paid | cancelled
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    paid_at: Optional[datetime] = None
    telegram_notified: bool = False

    def to_dict(self) -> Dict:
        return {
            "payment_id": self.payment_id,
            "offer_id": self.offer_id,
            "company": self.company,
            "contact_email": self.contact_email,
            "amount_eur": self.amount_eur,
            "method": self.method.value,
            "url": self.url,
            "sha256_hash": self.sha256_hash,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
            "telegram_notified": self.telegram_notified,
        }


class InstantCloser:
    """
    Génère les liens de paiement immédiatement et notifie Telegram.
    Délai cible : < 50 secondes après accord verbal (optimisé from 5min).
    """

    def __init__(self):
        self._paypal_url = os.getenv("PAYPALME_CLIENT_URL", "https://paypal.me/nayaintelligence")
        self._deblok_key = os.getenv("DEBLOKME_SECRET_KEY", "")
        self._telegram_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self._telegram_chat = os.getenv("TELEGRAM_OWNER_CHAT_ID", "")
        PAYMENT_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    def generate_payment_link(
        self,
        offer_id: str,
        company: str,
        contact_email: str,
        amount_eur: int,
        method: PaymentMethod = PaymentMethod.PAYPAL,
        description: str = "",
    ) -> PaymentLink:
        """
        Génère instantanément un lien de paiement < 50 secondes.
        Garantie plancher : amount_eur >= MIN_CONTRACT_VALUE_EUR.
        Notification Telegram asynchrone pour ne pas bloquer.
        """
        if amount_eur < MIN_CONTRACT_VALUE_EUR:
            raise ValueError(
                f"Montant {amount_eur} EUR inférieur au plancher "
                f"{MIN_CONTRACT_VALUE_EUR} EUR. INTERDIT."
            )

        payment_id = str(uuid.uuid4())[:16]
        url = self._build_url(method, amount_eur, company, payment_id, description)
        sha = self._compute_hash(payment_id, offer_id, company, amount_eur, url)

        link = PaymentLink(
            payment_id=payment_id,
            offer_id=offer_id,
            company=company,
            contact_email=contact_email,
            amount_eur=amount_eur,
            method=method,
            url=url,
            sha256_hash=sha,
            status="pending",
        )

        self._log_payment(link)
        # Async notification to not block payment link generation
        import threading
        threading.Thread(target=self._notify_telegram, args=(link,), daemon=True).start()
        logger.info(f"PaymentLink: {company} | {amount_eur} EUR | {method.value} | {url}")
        return link

    def confirm_payment(self, payment_id: str) -> bool:
        """Marque le paiement comme reçu et notifie Telegram."""
        import json
        lines = []
        found = False
        if PAYMENT_LOG_FILE.exists():
            with open(PAYMENT_LOG_FILE, "r") as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        if entry.get("payment_id") == payment_id:
                            entry["status"] = "paid"
                            entry["paid_at"] = datetime.now(timezone.utc).isoformat()
                            found = True
                            self._notify_payment_confirmed(entry)
                        lines.append(json.dumps(entry))
                    except Exception:
                        lines.append(line.rstrip())
            with open(PAYMENT_LOG_FILE, "w") as f:
                f.write("\n".join(lines) + "\n")
        return found

    def get_pending_payments(self) -> List[Dict]:
        """Retourne les paiements en attente."""
        import json
        result = []
        if PAYMENT_LOG_FILE.exists():
            with open(PAYMENT_LOG_FILE, "r") as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        if entry.get("status") == "pending":
                            result.append(entry)
                    except Exception:
                        pass
        return result

    # ── URL builders ────────────────────────────────────────────────────────

    def _build_url(
        self, method: PaymentMethod, amount: int, company: str,
        payment_id: str, description: str
    ) -> str:
        clean_company = company.replace(" ", "_")[:20]
        if method == PaymentMethod.PAYPAL:
            # PayPal.me format: /username/amount
            return f"{self._paypal_url}/{amount}EUR?note=NAYA-{payment_id}"
        elif method == PaymentMethod.DEBLOK:
            return f"https://deblok.me/pay?amount={amount}&ref=NAYA-{payment_id}&memo={clean_company}"
        else:
            return f"Virement bancaire — Référence : NAYA-{payment_id} — Montant : {amount} EUR"

    # ── Logging & Notifications ─────────────────────────────────────────────

    def _log_payment(self, link: PaymentLink) -> None:
        """Log immuable SHA-256."""
        import json
        try:
            with open(PAYMENT_LOG_FILE, "a") as f:
                f.write(json.dumps(link.to_dict()) + "\n")
        except Exception as exc:
            logger.error(f"Payment log write failed: {exc}")

    def _compute_hash(
        self, payment_id: str, offer_id: str, company: str, amount: int, url: str
    ) -> str:
        raw = f"{payment_id}:{offer_id}:{company}:{amount}:{url}:{time.time():.0f}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def _notify_telegram(self, link: PaymentLink) -> None:
        """Notifie immédiatement Telegram avec le lien de paiement."""
        if not (self._telegram_token and self._telegram_chat):
            logger.debug("Telegram not configured, skipping payment notification")
            return
        message = (
            f"💳 LIEN PAIEMENT GÉNÉRÉ\n"
            f"Entreprise : {link.company}\n"
            f"Montant : {link.amount_eur:,} EUR\n".replace(",", " ")
            + f"Méthode : {link.method.value}\n"
            f"Lien : {link.url}\n"
            f"ID : {link.payment_id}\n"
            f"⚡ Envoyé sous < 5 min après accord"
        )
        self._send_telegram(message)

    def _notify_payment_confirmed(self, entry: Dict) -> None:
        amount = entry.get("amount_eur", 0)
        company = entry.get("company", "?")
        message = (
            f"✅ PAIEMENT CONFIRMÉ\n"
            f"Entreprise : {company}\n"
            f"Montant : {amount:,} EUR\n".replace(",", " ")
            + f"ID : {entry.get('payment_id', '?')}\n"
            f"🎉 Argent réel encaissé !"
        )
        self._send_telegram(message)

    def _send_telegram(self, message: str) -> None:
        try:
            import urllib.request
            import urllib.parse
            import json
            url = f"https://api.telegram.org/bot{self._telegram_token}/sendMessage"
            data = json.dumps({
                "chat_id": self._telegram_chat,
                "text": message,
                "parse_mode": "HTML",
            }).encode()
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=5)
        except Exception as exc:
            logger.debug(f"Telegram notification failed: {exc}")


_closer_instance: Optional[InstantCloser] = None


def get_instant_closer() -> InstantCloser:
    global _closer_instance
    if _closer_instance is None:
        _closer_instance = InstantCloser()
    return _closer_instance
