"""
NAYA SUPREME V14 — WhatsApp Business Integration
Envoi messages WhatsApp via WhatsApp Cloud API (Meta) ou Twilio.
Utilisé pour : Botanica customer support, alertes paiement, Telegram fallback.
"""
import os, json, logging, urllib.request
from typing import Dict, Optional

log = logging.getLogger("NAYA.WHATSAPP")

def _gs(k, d=""):
    try:
        from SECRETS.secrets_loader import get_secret
        return get_secret(k, d) or d
    except Exception:
        return os.environ.get(k, d)


class WhatsAppEngine:
    """
    Envoi WhatsApp via Meta Cloud API ou Twilio.
    Fallback automatique entre les deux.
    """

    @property
    def wa_token(self): return _gs("WHATSAPP_TOKEN")
    @property
    def wa_phone_id(self): return _gs("WHATSAPP_PHONE_NUMBER_ID")
    @property
    def twilio_sid(self): return _gs("TWILIO_ACCOUNT_SID")
    @property
    def twilio_token(self): return _gs("TWILIO_AUTH_TOKEN")
    @property
    def twilio_wa_from(self): return _gs("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")

    def send_text(self, to_phone: str, message: str) -> Dict:
        """Envoie un message texte WhatsApp."""
        if self.wa_token and self.wa_phone_id:
            return self._send_meta(to_phone, message)
        if self.twilio_sid:
            return self._send_twilio(to_phone, message)
        # Log pour envoi manuel si pas de clé
        log.info("[WhatsApp] MSG → %s: %s", to_phone, message[:80])
        return {"status": "logged", "message": "Configurer WHATSAPP_TOKEN ou TWILIO pour envoi automatique"}

    def send_botanica_order_confirmation(self, phone: str, order_id: str, total: float, payment_link: str) -> Dict:
        """Message de confirmation de commande Botanica."""
        msg = f"""✨ *NAYA Botanica — Commande confirmée*

Bonjour ! Votre commande *{order_id}* est enregistrée.

💰 Total : *{total:.2f}€*
🔗 Paiement : {payment_link}

Expédition sous 48h après paiement.
Pour toute question, répondez à ce message.

Merci de votre confiance 🌿"""
        return self.send_text(phone, msg)

    def send_payment_received(self, phone: str, name: str, amount: float) -> Dict:
        """Alerte paiement reçu."""
        msg = f"✅ *Paiement reçu* — {name} — {amount:.2f}€\n\nMerci ! Votre commande est en préparation."
        return self.send_text(phone, msg)

    def _send_meta(self, to: str, text: str) -> Dict:
        """Envoi via Meta Cloud API."""
        url = f"https://graph.facebook.com/v18.0/{self.wa_phone_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "to": to.replace("+", "").replace(" ", ""),
            "type": "text",
            "text": {"body": text},
        }
        try:
            req = urllib.request.Request(
                url, data=json.dumps(payload).encode(),
                headers={"Authorization": f"Bearer {self.wa_token}", "Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(req, timeout=15)
            log.info("[WhatsApp/Meta] Envoyé → %s", to)
            return {"status": "sent", "provider": "meta"}
        except Exception as e:
            log.warning("[WhatsApp/Meta] Erreur: %s", e)
            return {"status": "error", "error": str(e)[:80]}

    def _send_twilio(self, to: str, text: str) -> Dict:
        """Envoi via Twilio WhatsApp."""
        try:
            import base64, urllib.parse
            credentials = base64.b64encode(f"{self.twilio_sid}:{self.twilio_token}".encode()).decode()
            data = urllib.parse.urlencode({
                "From": self.twilio_wa_from,
                "To": f"whatsapp:{to}",
                "Body": text,
            }).encode()
            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_sid}/Messages.json"
            req = urllib.request.Request(url, data=data, headers={"Authorization": f"Basic {credentials}"}, method="POST")
            urllib.request.urlopen(req, timeout=15)
            log.info("[WhatsApp/Twilio] Envoyé → %s", to)
            return {"status": "sent", "provider": "twilio"}
        except Exception as e:
            log.warning("[WhatsApp/Twilio] Erreur: %s", e)
            return {"status": "error", "error": str(e)[:80]}


_WA: Optional[WhatsAppEngine] = None
def get_whatsapp_engine() -> WhatsAppEngine:
    global _WA
    if _WA is None:
        _WA = WhatsAppEngine()
    return _WA
