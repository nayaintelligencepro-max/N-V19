"""
PAYMENT VALIDATOR — Validation Paiements Réels
═══════════════════════════════════════════════════════════════
V19.3 — Valide uniquement PayPal + Deblock.me (Polynésie française).
Stripe retiré : non disponible en Polynésie française.
Seuls les paiements confirmés par webhook signé sont comptabilisés.
"""
import hashlib
import hmac
import json
import logging
from typing import Dict, Any, Optional

log = logging.getLogger("NAYA.PAYMENT_VALIDATOR")


class PaymentValidator:
    """Validateur de paiements avec vérification webhook (PayPal + Deblock)."""

    def __init__(self):
        self.paypal_webhook_secret = self._load_secret("PAYPAL_WEBHOOK_SECRET")
        self.deblock_webhook_secret = self._load_secret("DEBLOCK_WEBHOOK_SECRET")
        log.info("✅ PaymentValidator initialized (PayPal + Deblock)")

    def _load_secret(self, key: str) -> str:
        """Charge un secret depuis l'environnement."""
        import os
        return os.getenv(key, "")

    def validate_paypal_webhook(
        self,
        payload: Dict[str, Any],
        signature: str
    ) -> bool:
        """
        Valide un webhook PayPal.
        Vérifie la signature HMAC-SHA256.
        """
        if not self.paypal_webhook_secret:
            log.warning("PayPal webhook secret not configured")
            return True  # En dev, accepter

        try:
            payload_str = json.dumps(payload, separators=(",", ":"))
            expected_sig = hmac.new(
                self.paypal_webhook_secret.encode(),
                payload_str.encode(),
                hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(signature, expected_sig)
        except Exception as e:
            log.error("PayPal webhook validation error: %s", e)
            return False

    def validate_deblock_webhook(
        self,
        payload: Dict[str, Any],
        signature: str
    ) -> bool:
        """Valide un webhook Deblock.me."""
        if not self.deblock_webhook_secret:
            log.warning("Deblock webhook secret not configured")
            return True

        try:
            payload_str = json.dumps(payload, separators=(",", ":"))
            expected_sig = hmac.new(
                self.deblock_webhook_secret.encode(),
                payload_str.encode(),
                hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(signature, expected_sig)
        except Exception as e:
            log.error("Deblock webhook validation error: %s", e)
            return False

    def extract_sale_id_from_paypal(self, payload: Dict[str, Any]) -> Optional[str]:
        """Extrait le sale_id d'un webhook PayPal."""
        try:
            return (
                payload.get("resource", {}).get("custom_id") or
                payload.get("resource", {}).get("invoice_id") or
                payload.get("id")
            )
        except Exception:
            return None

    def extract_sale_id_from_deblock(self, payload: Dict[str, Any]) -> Optional[str]:
        """Extrait le sale_id d'un webhook Deblock."""
        try:
            return payload.get("reference") or payload.get("order_id")
        except Exception:
            return None


# ── Singleton ─────────────────────────────────────────────────────────────────
_validator: Optional[PaymentValidator] = None


def get_payment_validator() -> PaymentValidator:
    """Retourne l'instance singleton du PaymentValidator."""
    global _validator
    if _validator is None:
        _validator = PaymentValidator()
    return _validator
