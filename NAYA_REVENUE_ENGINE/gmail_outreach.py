"""
NAYA V19 — Gmail Outreach via OAuth2
Envoie des cold emails depuis nayaintelligencepro@gmail.com
sans mot de passe — utilise le token OAuth stocké dans google_token.json.

Avantages vs SMTP:
  - Pas de "mot de passe d'application" à créer
  - Token déjà configuré avec gmail.send scope
  - 500 emails/jour gratuit (Gmail standard)
  - Réputation expéditeur bien meilleure que SMTP
"""
import os, json, base64, logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Dict, Optional

log = logging.getLogger("NAYA.GMAIL")

KEYS_DIR = Path(__file__).parent.parent / "SECRETS/keys"


def _get_oauth_creds():
    """Charge les credentials OAuth depuis google_token.json."""
    try:
        data = json.loads((KEYS_DIR / "google_token.json").read_text())
        return {
            "client_id":     data.get("client_id", ""),
            "client_secret": data.get("client_secret", ""),
            "refresh_token": data.get("refresh_token", ""),
            "token":         data.get("token", ""),
        }
    except Exception as e:
        log.debug(f"[GMAIL] Chargement token: {e}")
        return {}


def _refresh_access_token(creds: dict) -> str:
    """Rafraîchit l'access token via OAuth2."""
    try:
        import urllib.request, urllib.parse
        data = urllib.parse.urlencode({
            "client_id":     creds["client_id"],
            "client_secret": creds["client_secret"],
            "refresh_token": creds["refresh_token"],
            "grant_type":    "refresh_token",
        }).encode()
        req = urllib.request.Request(
            "https://oauth2.googleapis.com/token",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            resp = json.loads(r.read())
            return resp.get("access_token", "")
    except Exception as e:
        log.warning(f"[GMAIL] Refresh token: {e}")
        return ""


def send_email_oauth(to: str, subject: str, body_html: str,
                     sender_name: str = "NAYA Service") -> Dict:
    """
    Envoie un email via Gmail API OAuth2.
    Pas besoin de SMTP, pas de mot de passe.
    """
    creds = _get_oauth_creds()
    if not creds.get("refresh_token"):
        return {"sent": False, "error": "Token OAuth non configuré — google_token.json"}

    access_token = _refresh_access_token(creds)
    if not access_token:
        return {"sent": False, "error": "Impossible de rafraîchir le token OAuth"}

    sender_email = os.environ.get("GMAIL_OAUTH_USER", "nayaintelligencepro@gmail.com")

    # Construire l'email MIME
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"{sender_name} <{sender_email}>"
    msg["To"]      = to
    msg.attach(MIMEText(body_html, "html", "utf-8"))

    # Encoder en base64 URL-safe
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

    try:
        import urllib.request
        payload = json.dumps({"raw": raw}).encode()
        req = urllib.request.Request(
            "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
            data=payload,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type":  "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            resp = json.loads(r.read())
            msg_id = resp.get("id", "")
            log.info(f"[GMAIL] ✅ Envoyé à {to} — ID: {msg_id}")
            return {"sent": True, "message_id": msg_id, "to": to}
    except Exception as e:
        log.warning(f"[GMAIL] Erreur envoi à {to}: {e}")
        return {"sent": False, "error": str(e)[:80]}


class GmailOutreach:
    """Moteur d'outreach email via Gmail OAuth — prêt à l'emploi."""

    def __init__(self):
        self._sent_count = 0
        self._failed_count = 0
        creds = _get_oauth_creds()
        self.available = bool(creds.get("refresh_token"))

    def send_cold_email(self, prospect: dict, offer: dict) -> Dict:
        """Envoie un cold email personnalisé à un prospect."""
        company   = prospect.get("company_name", prospect.get("company", "votre entreprise"))
        contact   = prospect.get("contact_name", "")
        email     = prospect.get("email", "")
        pain      = prospect.get("pain_category", "").replace("_", " ")
        city      = prospect.get("city", "")
        price     = float(offer.get("price", prospect.get("offer_price", 0)))
        title     = offer.get("title", "Solution NAYA")
        pain_cost = float(prospect.get("pain_annual_cost_eur", 0))
        roi       = round(pain_cost / max(price, 1), 1)

        if not email:
            return {"sent": False, "error": "Email prospect manquant"}

        subject = f"Question rapide — {pain} chez {company}"

        salutation = f"Bonjour {contact.split()[0]}," if contact else "Bonjour,"

        body = f"""<!DOCTYPE html>
<html><body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;color:#333;">
<p>{salutation}</p>

<p>Je travaille avec des entreprises{f' de {city}' if city else ''} dans votre secteur.</p>

<p>En analysant votre situation, j'ai identifié un problème de <strong>{pain}</strong>
qui coûte généralement <strong>{pain_cost:,.0f}€/an</strong> aux entreprises similaires à la vôtre.</p>

<p>Nous avons développé <em>{title}</em> — nos clients récupèrent en moyenne
<strong>×{roi} leur investissement</strong> dans les 60 premiers jours.</p>

<p><strong>Une question directe</strong> : est-ce que ce problème vous concerne actuellement ?</p>

<p>Si oui, je peux vous montrer comment nous l'avons résolu pour 3 entreprises similaires,
en 15 minutes par téléphone cette semaine.</p>

<p>Bien à vous,<br>
<strong>NAYA Service</strong><br>
📱 WhatsApp : +68989559088<br>
🌐 nayabot.online</p>

<p style="font-size:11px;color:#999;margin-top:30px;">
Pour ne plus recevoir ces messages, répondez simplement "STOP".</p>
</body></html>"""

        result = send_email_oauth(email, subject, body)
        if result["sent"]:
            self._sent_count += 1
        else:
            self._failed_count += 1
        return result

    def send_payment_reminder(self, prospect: dict, payment_url: str, amount: float) -> Dict:
        """Relance de paiement — envoie le lien PayPal/Revolut."""
        email   = prospect.get("email", "")
        company = prospect.get("company_name", "")
        contact = prospect.get("contact_name", "")

        if not email:
            return {"sent": False, "error": "Email manquant"}

        subject = f"Lien de règlement — {amount:.0f}€ — {company}"
        salutation = f"Bonjour {contact.split()[0]}," if contact else "Bonjour,"

        body = f"""<!DOCTYPE html>
<html><body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;color:#333;">
<p>{salutation}</p>
<p>Suite à notre échange, voici votre lien de règlement sécurisé :</p>

<p style="text-align:center;margin:30px 0;">
<a href="{payment_url}" style="background:#0070ba;color:white;padding:15px 30px;
   border-radius:6px;text-decoration:none;font-size:18px;font-weight:bold;">
💳 Payer {amount:.0f}€ maintenant
</a></p>

<p>Montant : <strong>{amount:.0f}€</strong><br>
Lien : {payment_url}</p>

<p>Une fois le paiement effectué, nous démarrons sous 2H.</p>

<p>Des questions ? WhatsApp : +68989559088</p>

<p>Bien à vous,<br><strong>NAYA Service</strong></p>
</body></html>"""

        return send_email_oauth(email, subject, body)

    def get_stats(self) -> Dict:
        return {
            "available": self.available,
            "sent": self._sent_count,
            "failed": self._failed_count,
            "sender": os.environ.get("GMAIL_OAUTH_USER", "nayaintelligencepro@gmail.com"),
        }


_gmail: Optional[GmailOutreach] = None
_gmail_lock = __import__("threading").Lock()

def get_gmail_outreach() -> GmailOutreach:
    global _gmail
    if _gmail is None:
        with _gmail_lock:
            if _gmail is None:
                _gmail = GmailOutreach()
    return _gmail
