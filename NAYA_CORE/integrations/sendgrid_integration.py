"""
NAYA — SendGrid Integration
Cold outreach emails transactionnels avec tracking.
Chaque email est personnalisé depuis la douleur détectée.
"""
import os
import time
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field

log = logging.getLogger("NAYA.SENDGRID")

def _gs(key: str, default: str = "") -> str:
    try:
        from SECRETS.secrets_loader import get_secret
        return get_secret(key, default) or default
    except Exception:
        return os.environ.get(key, default)


@dataclass
class EmailResult:
    sent: bool = False
    message_id: str = ""
    to_email: str = ""
    subject: str = ""
    error: str = ""
    timestamp: float = field(default_factory=time.time)


class SendGridIntegration:
    """
    Client SendGrid pour l'outreach cold email NAYA.
    API Docs: https://docs.sendgrid.com/api-reference
    """

    API_URL = "https://api.sendgrid.com/v3/mail/send"

    def __init__(self):
        self._sent_count = 0
        self._failed_count = 0

    @property
    def api_key(self) -> str: return _gs("SENDGRID_API_KEY")
    @property
    def from_email(self) -> str: return _gs("EMAIL_FROM")
    @property
    def from_name(self) -> str: return _gs("EMAIL_FROM_NAME", "NAYA SUPREME")
    @property
    def reply_to(self) -> str: return _gs("EMAIL_REPLY_TO") or self.from_email

    @property
    def available(self) -> bool:
        return bool(self.api_key) and bool(self.from_email)

    def send(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: str = "",
        to_name: str = "",
        categories: List[str] = None,
        custom_args: Dict = None,
    ) -> EmailResult:
        """Envoie un email via SendGrid."""
        if not self.available:
            log.info(f"[SENDGRID] Désactivé — log email: {subject[:60]} → {to_email}")
            return EmailResult(sent=False, error="SendGrid non configuré", to_email=to_email)

        payload = {
            "personalizations": [{
                "to": [{"email": to_email, "name": to_name or to_email.split("@")[0]}],
                "subject": subject,
            }],
            "from": {"email": self.from_email, "name": self.from_name},
            "reply_to": {"email": self.reply_to or self.from_email},
            "content": [{"type": "text/html", "value": body_html}],
            "tracking_settings": {
                "click_tracking": {"enable": True},
                "open_tracking": {"enable": True},
            },
        }

        if body_text:
            payload["content"].insert(0, {"type": "text/plain", "value": body_text})
        if categories:
            payload["categories"] = categories[:10]
        if custom_args:
            payload["personalizations"][0]["custom_args"] = {
                str(k): str(v) for k, v in custom_args.items()
            }

        try:
            import httpx
            resp = httpx.post(
                self.API_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=20,
            )
            if resp.status_code in (200, 202):
                self._sent_count += 1
                msg_id = resp.headers.get("X-Message-Id", "")
                log.info(f"[SENDGRID] ✉️ Email envoyé: {subject[:50]} → {to_email}")
                return EmailResult(sent=True, message_id=msg_id, to_email=to_email, subject=subject)
            else:
                self._failed_count += 1
                error = resp.text[:200]
                log.warning(f"[SENDGRID] Échec HTTP {resp.status_code}: {error}")
                return EmailResult(sent=False, error=f"HTTP {resp.status_code}: {error}", to_email=to_email)
        except Exception as e:
            self._failed_count += 1
            log.warning(f"[SENDGRID] Exception: {e}")
            return EmailResult(sent=False, error=str(e), to_email=to_email)

    def send_cold_outreach(
        self,
        to_email: str,
        to_name: str,
        company: str,
        pain: str,
        solution: str,
        price_eur: float,
        roi_multiplier: float,
        sender_name: str = "Stéphanie",
    ) -> EmailResult:
        """
        Template cold email optimisé pour NAYA.
        Format: Pain → Solution → ROI → CTA simple.
        """
        subject = f"[{company}] {pain[:50]} — solution en 48H"
        
        body_html = f"""
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; color: #333;">
  <p>Bonjour {to_name or 'Madame/Monsieur'},</p>

  <p>En analysant {company}, j'ai identifié un point critique : <strong>{pain}</strong>.</p>

  <p>Ce problème coûte souvent <strong>{price_eur * roi_multiplier:,.0f}€/an</strong> 
  en pertes cachées — et il existe une solution rapide.</p>

  <p>Nous proposons : <em>{solution}</em><br>
  Prix : <strong>{price_eur:,.0f}€</strong> — ROI ×{roi_multiplier:.0f} la première année.</p>

  <p><strong>Une question simple :</strong> est-ce un sujet prioritaire pour vous en ce moment ?</p>

  <p>Si oui, je vous envoie un diagnostic gratuit de 15 minutes.<br>
  Sinon, je ne vous recontacte pas.</p>

  <p>Cordialement,<br>
  <strong>{sender_name}</strong><br>
  {self.from_name}</p>
</div>
"""
        body_text = (
            f"Bonjour {to_name},\n\n"
            f"J'ai identifié chez {company} : {pain}\n\n"
            f"Solution : {solution} — {price_eur:,.0f}€ — ROI ×{roi_multiplier:.0f}\n\n"
            f"Est-ce prioritaire pour vous ?\n\n{sender_name}"
        )

        return self.send(
            to_email=to_email,
            subject=subject,
            body_html=body_html,
            body_text=body_text,
            to_name=to_name,
            categories=["cold_outreach", "naya_revenue"],
            custom_args={"company": company, "pain": pain[:50]},
        )

    def get_stats(self) -> Dict:
        return {
            "available": self.available,
            "sent": self._sent_count,
            "failed": self._failed_count,
            "from_email": self.from_email if self.available else "",
        }


_sendgrid: Optional[SendGridIntegration] = None

def get_sendgrid() -> SendGridIntegration:
    global _sendgrid
    if _sendgrid is None:
        _sendgrid = SendGridIntegration()
    return _sendgrid
