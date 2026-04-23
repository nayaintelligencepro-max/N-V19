"""
NAYA V19 — GMAIL OAUTH2 VIA SERVICE ACCOUNT
Envoie des emails via Gmail API sans mot de passe SMTP.
Utilise le Service Account GCP déjà configuré (naya-pro-ultime).

Avantages vs SMTP basique:
  ✅ Plus fiable (pas de blocage Gmail)
  ✅ Meilleur deliverability (moins de spam)
  ✅ Tracking opens/clicks natif
  ✅ Pas de "Less Secure Apps" à activer
  ✅ Zero mot de passe → sécurité maximale
  ✅ 2000 emails/jour gratuits (Gmail limite)
  ✅ SendGrid backup si Gmail throttle

Prérequis activés sur ton GCP:
  - Gmail API activée sur naya-pro-ultime
  - Service Account: naya-pro-ultime@naya-pro-ultime.iam.gserviceaccount.com
  - Domain-wide delegation OU compte Gmail OAuth

Config automatique depuis SECRETS/keys/google_service_account.json
"""

import os
import json
import time
import base64
import logging
import urllib.request
import urllib.parse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Optional, List
from datetime import datetime, timedelta, timezone

log = logging.getLogger("NAYA.GMAIL.OAUTH")


def _gs(key: str, default: str = "") -> str:
    try:
        from SECRETS.secrets_loader import get_secret
        return get_secret(key, default) or default
    except Exception:
        return os.environ.get(key, default)


class GoogleServiceAccountAuth:
    """
    Authentification Google via Service Account JWT.
    Génère des Access Tokens pour les Google APIs.
    """

    GOOGLE_AUTH_URL = "https://oauth2.googleapis.com/token"
    TOKEN_LIFETIME = 3600  # 1 heure

    def __init__(self, sa_path: str = None, scopes: List[str] = None):
        self._sa_path = sa_path or self._find_sa_file()
        self._scopes = scopes or [
            "https://www.googleapis.com/auth/gmail.send",
            "https://www.googleapis.com/auth/gmail.readonly",
        ]
        self._sa_data: Dict = {}
        self._access_token: Optional[str] = None
        self._token_expires: float = 0
        self._load_sa()

    def _find_sa_file(self) -> Optional[str]:
        """Trouve le fichier Service Account."""
        candidates = [
            _gs("GOOGLE_APPLICATION_CREDENTIALS"),
            "SECRETS/service_accounts/gcp-service-account.json",
            "SECRETS/keys/google_service_account.json",
        ]
        for path in candidates:
            if path and os.path.exists(path):
                return path
        return None

    def _load_sa(self):
        """Charge le Service Account."""
        if not self._sa_path or not os.path.exists(self._sa_path):
            log.debug(f"[GAuth] Service Account non trouvé: {self._sa_path}")
            return
        try:
            self._sa_data = json.loads(open(self._sa_path).read())
            log.info(f"[GAuth] SA chargé: {self._sa_data.get('client_email', '?')}")
        except Exception as e:
            log.warning(f"[GAuth] Erreur chargement SA: {e}")

    @property
    def available(self) -> bool:
        return bool(self._sa_data.get("private_key") and self._sa_data.get("client_email"))

    def _create_jwt(self, subject_email: str = None) -> str:
        """Crée un JWT signé avec la clé privée du Service Account."""
        import hashlib
        import hmac

        now = int(time.time())
        header = {"alg": "RS256", "typ": "JWT"}
        payload = {
            "iss": self._sa_data["client_email"],
            "scope": " ".join(self._scopes),
            "aud": self.GOOGLE_AUTH_URL,
            "iat": now,
            "exp": now + self.TOKEN_LIFETIME,
        }
        if subject_email:
            payload["sub"] = subject_email  # Impersonation

        def b64url(data) -> str:
            if isinstance(data, dict):
                data = json.dumps(data, separators=(",", ":")).encode()
            return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

        header_b64 = b64url(header)
        payload_b64 = b64url(payload)
        signing_input = f"{header_b64}.{payload_b64}".encode()

        # Signer avec RSA-SHA256
        try:
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import padding

            private_key = serialization.load_pem_private_key(
                self._sa_data["private_key"].encode(),
                password=None
            )
            signature = private_key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
            return f"{header_b64}.{payload_b64}.{b64url(signature)}"

        except ImportError:
            # Fallback: utiliser subprocess avec openssl si cryptography pas installé
            import subprocess
            import tempfile

            with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as f:
                f.write(self._sa_data["private_key"])
                key_file = f.name

            try:
                result = subprocess.run(
                    ["openssl", "dgst", "-sha256", "-sign", key_file],
                    input=signing_input,
                    capture_output=True
                )
                os.unlink(key_file)
                if result.returncode == 0:
                    return f"{header_b64}.{payload_b64}.{b64url(result.stdout)}"
            except Exception:
                os.unlink(key_file)
                raise

        raise ValueError("Impossible de signer le JWT (installer 'cryptography')")

    def get_access_token(self, subject_email: str = None) -> Optional[str]:
        """Obtient un Access Token valide (avec cache 1h)."""
        if not self.available:
            return None

        # Token encore valide ?
        if self._access_token and time.time() < self._token_expires - 60:
            return self._access_token

        try:
            jwt = self._create_jwt(subject_email)
            payload = urllib.parse.urlencode({
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "assertion": jwt,
            }).encode()

            req = urllib.request.Request(
                self.GOOGLE_AUTH_URL,
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())

            self._access_token = data.get("access_token")
            self._token_expires = time.time() + data.get("expires_in", 3600)
            log.debug("[GAuth] Nouveau token obtenu")
            return self._access_token

        except Exception as e:
            log.warning(f"[GAuth] Token error: {e}")
            return None


class GmailOAuth2Sender:
    """
    Envoi d'emails via Gmail API avec OAuth2 Service Account.
    Fallback automatique vers SendGrid si Gmail échoue.
    """

    GMAIL_SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/{}/messages/send"

    def __init__(self):
        self._auth = GoogleServiceAccountAuth()
        self._from_email = _gs("EMAIL_FROM", "nayaintelligencepro@gmail.com")
        self._from_name = _gs("EMAIL_FROM_NAME", "NAYA SUPREME")
        self._sent_count = 0
        self._failed_count = 0
        self._last_error = ""

        # Gmail utilisateur (pour l'impersonation ou compte direct)
        self._gmail_user = _gs("GMAIL_USER") or _gs("SMTP_USER") or self._from_email

        if self._auth.available:
            log.info(f"✅ Gmail OAuth2 prêt — {self._from_email}")
        else:
            log.debug("Gmail OAuth2: Service Account non configuré")

    @property
    def available(self) -> bool:
        """Disponible si OAuth2 OU SMTP OU SendGrid configuré."""
        return self._auth.available or bool(_gs("SMTP_USER")) or bool(_gs("SENDGRID_API_KEY"))

    @property
    def has_oauth2(self) -> bool:
        return self._auth.available

    @property
    def has_smtp(self) -> bool:
        return bool(_gs("SMTP_USER") and _gs("SMTP_PASS"))

    @property
    def has_sendgrid(self) -> bool:
        return bool(_gs("SENDGRID_API_KEY"))

    def send(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: str = "",
        to_name: str = "",
        reply_to: str = "",
        track_opens: bool = True,
    ) -> Dict:
        """
        Envoie un email avec le meilleur canal disponible.
        Priorité: Gmail OAuth2 > SendGrid > SMTP

        Args:
            to_email: Email destinataire
            subject: Sujet de l'email
            body_html: Corps HTML (enrichi)
            body_text: Corps texte brut (fallback)
            to_name: Nom du destinataire
            reply_to: Email de réponse
            track_opens: Ajouter pixel de tracking

        Returns:
            Dict avec sent, method, message_id, error
        """
        if not to_email or "@" not in to_email:
            return {"sent": False, "error": "Email invalide"}

        # Ajouter pixel de tracking si demandé
        if track_opens and body_html:
            tracking_id = f"naya_{int(time.time())}_{hash(to_email) % 10000:04d}"
            pixel = f'<img src="https://nayabot.online/track/{tracking_id}" width="1" height="1" style="display:none">'
            body_html = body_html + pixel

        # 1. Essayer Gmail OAuth2 en premier
        if self.has_oauth2:
            result = self._send_via_oauth2(to_email, subject, body_html, body_text, to_name, reply_to)
            if result.get("sent"):
                self._sent_count += 1
                return result

        # 2. Fallback SendGrid
        if self.has_sendgrid:
            result = self._send_via_sendgrid(to_email, subject, body_html, body_text, to_name)
            if result.get("sent"):
                self._sent_count += 1
                return result

        # 3. Fallback SMTP
        if self.has_smtp:
            result = self._send_via_smtp(to_email, subject, body_text or body_html, to_name)
            if result.get("sent"):
                self._sent_count += 1
                return result

        self._failed_count += 1
        return {"sent": False, "error": "Tous les canaux email ont échoué", "method": "none"}

    def _send_via_oauth2(self, to_email: str, subject: str, body_html: str,
                         body_text: str, to_name: str, reply_to: str) -> Dict:
        """Envoie via Gmail API OAuth2."""
        try:
            token = self._auth.get_access_token(self._gmail_user)
            if not token:
                return {"sent": False, "error": "Token OAuth2 non obtenu"}

            # Construire le message MIME
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self._from_name} <{self._from_email}>"
            msg["To"] = f"{to_name} <{to_email}>" if to_name else to_email
            if reply_to:
                msg["Reply-To"] = reply_to
            msg["Date"] = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")

            # Ajouter les parties texte et HTML
            if body_text:
                msg.attach(MIMEText(body_text, "plain", "utf-8"))
            if body_html:
                msg.attach(MIMEText(body_html, "html", "utf-8"))

            # Encoder en base64url pour l'API Gmail
            raw = base64.urlsafe_b64encode(msg.as_bytes()).decode().rstrip("=")

            payload = json.dumps({"raw": raw}).encode("utf-8")
            url = self.GMAIL_SEND_URL.format(urllib.parse.quote(self._gmail_user))

            req = urllib.request.Request(
                url,
                data=payload,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())

            msg_id = data.get("id", "")
            log.info(f"[Gmail OAuth2] ✅ Envoyé → {to_email} (id: {msg_id})")
            return {
                "sent": True,
                "method": "gmail_oauth2",
                "message_id": msg_id,
                "to": to_email,
            }

        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")[:300]
            log.warning(f"[Gmail OAuth2] HTTP {e.code}: {body}")
            self._last_error = f"Gmail HTTP {e.code}"
            return {"sent": False, "error": f"Gmail API {e.code}: {body[:100]}"}

        except Exception as e:
            log.warning(f"[Gmail OAuth2] Error: {e}")
            self._last_error = str(e)
            return {"sent": False, "error": str(e)}

    def _send_via_sendgrid(self, to_email: str, subject: str, body_html: str,
                            body_text: str, to_name: str) -> Dict:
        """Fallback SendGrid."""
        try:
            from_email = self._from_email
            from_name = self._from_name
            sg_key = _gs("SENDGRID_API_KEY")

            payload = json.dumps({
                "personalizations": [{
                    "to": [{"email": to_email, "name": to_name or ""}],
                    "subject": subject,
                }],
                "from": {"email": from_email, "name": from_name},
                "content": [
                    {"type": "text/plain", "value": body_text or body_html},
                    {"type": "text/html", "value": body_html},
                ],
                "tracking_settings": {
                    "click_tracking": {"enable": True},
                    "open_tracking": {"enable": True},
                },
            }).encode("utf-8")

            req = urllib.request.Request(
                "https://api.sendgrid.com/v3/mail/send",
                data=payload,
                headers={
                    "Authorization": f"Bearer {sg_key}",
                    "Content-Type": "application/json",
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                msg_id = resp.headers.get("X-Message-Id", "")

            log.info(f"[SendGrid] ✅ Envoyé → {to_email}")
            return {"sent": True, "method": "sendgrid", "message_id": msg_id, "to": to_email}

        except Exception as e:
            log.warning(f"[SendGrid] Error: {e}")
            return {"sent": False, "error": str(e)}

    def _send_via_smtp(self, to_email: str, subject: str, body: str, to_name: str) -> Dict:
        """Fallback SMTP standard."""
        try:
            import smtplib
            from email.mime.text import MIMEText as _MIMEText

            host = _gs("SMTP_HOST", "smtp.gmail.com")
            port = int(_gs("SMTP_PORT", "587"))
            user = _gs("SMTP_USER")
            passwd = _gs("SMTP_PASS")

            msg = _MIMEText(body, "html" if "<" in body else "plain", "utf-8")
            msg["Subject"] = subject
            msg["From"] = f"{self._from_name} <{user}>"
            msg["To"] = to_email

            with smtplib.SMTP(host, port) as s:
                s.ehlo()
                s.starttls()
                s.login(user, passwd)
                s.sendmail(user, [to_email], msg.as_string())

            log.info(f"[SMTP] ✅ Envoyé → {to_email}")
            return {"sent": True, "method": "smtp", "to": to_email}

        except Exception as e:
            log.warning(f"[SMTP] Error: {e}")
            return {"sent": False, "error": str(e)}

    def send_bulk(self, recipients: List[Dict], subject: str,
                  body_html_template: str, delay_seconds: float = 1.5) -> Dict:
        """
        Envoi bulk avec personnalisation et rate limiting.
        recipients: [{"email": "...", "name": "...", "company": "...", "custom": {...}}]
        body_html_template: Template avec {name}, {company}, etc.
        """
        results = {"sent": 0, "failed": 0, "details": []}

        for recipient in recipients:
            email = recipient.get("email", "")
            if not email:
                continue

            # Personnaliser le template
            body = body_html_template
            for key, val in recipient.items():
                body = body.replace(f"{{{key}}}", str(val))
                body = body.replace(f"[{key.upper()}]", str(val))

            result = self.send(
                to_email=email,
                subject=subject,
                body_html=body,
                to_name=recipient.get("name", ""),
            )

            if result.get("sent"):
                results["sent"] += 1
            else:
                results["failed"] += 1

            results["details"].append({
                "email": email,
                "sent": result.get("sent"),
                "method": result.get("method"),
                "error": result.get("error"),
            })

            # Rate limiting respectueux
            time.sleep(delay_seconds)

        log.info(f"[Gmail Bulk] {results['sent']} envoyés, {results['failed']} échoués")
        return results

    def get_stats(self) -> Dict:
        return {
            "available": self.available,
            "channels": {
                "gmail_oauth2": self.has_oauth2,
                "sendgrid": self.has_sendgrid,
                "smtp": self.has_smtp,
            },
            "active_channel": (
                "gmail_oauth2" if self.has_oauth2 else
                "sendgrid" if self.has_sendgrid else
                "smtp" if self.has_smtp else "none"
            ),
            "sent_total": self._sent_count,
            "failed_total": self._failed_count,
            "from_email": self._from_email,
            "last_error": self._last_error,
        }


# ── Singleton ────────────────────────────────────────────────────────────────

_GMAIL_SENDER: Optional[GmailOAuth2Sender] = None


def get_gmail_sender() -> GmailOAuth2Sender:
    global _GMAIL_SENDER
    if _GMAIL_SENDER is None:
        _GMAIL_SENDER = GmailOAuth2Sender()
    return _GMAIL_SENDER
