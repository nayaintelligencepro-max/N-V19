"""
NAYA — Outreach Engine V2 (Production)
Envoi cold email + alertes Telegram pour chaque opportunité détectée.
Clés lues dynamiquement depuis SECRETS à chaque appel.
"""
import os, time, logging, json, uuid
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone

log = logging.getLogger("NAYA.OUTREACH")

def _gs(key: str, default: str = "") -> str:
    """Lit une clé depuis os.environ en temps réel (après load_all_secrets)."""
    try:
        from SECRETS.secrets_loader import get_secret
        return get_secret(key, default) or default
    except Exception:
        return os.environ.get(key, default)

class OutreachEngine:
    """
    Moteur d'outreach multicanal — lit les clés dynamiquement.
    Mode APPROBATION (défaut): NAYA alerte Telegram → tu approuves → email envoyé.
    Mode AUTO: NAYA envoie directement (NAYA_AUTO_OUTREACH=true).
    """

    def __init__(self):
        self._sent_count = 0
        self._approved_count = 0
        self._pending_approvals: List[Dict] = []

    # ── Propriétés dynamiques — relues à chaque appel ───────────────────────
    @property
    def sendgrid_key(self) -> str: return _gs("SENDGRID_API_KEY")
    @property
    def email_from(self) -> str: return _gs("EMAIL_FROM")
    @property
    def email_from_name(self) -> str: return _gs("EMAIL_FROM_NAME", "NAYA SUPREME")
    @property
    def smtp_host(self) -> str: return _gs("SMTP_HOST", "smtp.gmail.com")
    @property
    def smtp_port(self) -> int: return int(_gs("SMTP_PORT", "587"))
    @property
    def smtp_user(self) -> str: return _gs("SMTP_USER")
    @property
    def smtp_pass(self) -> str: return _gs("SMTP_PASS")
    @property
    def telegram_token(self) -> str: return _gs("TELEGRAM_BOT_TOKEN")
    @property
    def telegram_chat(self) -> str: return _gs("TELEGRAM_CHAT_ID")
    @property
    def twilio_sid(self) -> str: return _gs("TWILIO_ACCOUNT_SID")
    @property
    def twilio_token(self) -> str: return _gs("TWILIO_AUTH_TOKEN")
    @property
    def twilio_phone(self) -> str: return _gs("TWILIO_PHONE")
    @property
    def auto_send(self) -> bool: return os.environ.get("NAYA_AUTO_OUTREACH","false").lower()=="true"

    @property
    def has_sendgrid(self) -> bool: return bool(self.sendgrid_key)
    @property
    def has_smtp(self) -> bool: return bool(self.smtp_user and self.smtp_pass)
    @property
    def has_telegram(self) -> bool: return bool(self.telegram_token and self.telegram_chat)
    @property
    def has_twilio(self) -> bool: return bool(self.twilio_sid)
    @property
    def has_email(self) -> bool: return self.has_sendgrid or self.has_smtp

    def send_opportunity_alert(self, prospect, offer: Dict) -> Dict:
        """Flux principal: détection → alerte Telegram → approbation → email."""
        result = {"telegram": False, "email": False, "status": "pending"}

        if self.has_telegram:
            msg = self._build_telegram_opportunity(prospect, offer)
            if self._send_telegram(msg):
                result["telegram"] = True
                apr_id = f"APR_{uuid.uuid4().hex[:8].upper()}"
                self._pending_approvals.append({
                    "id": apr_id,
                    "prospect_id": getattr(prospect,"id",""),
                    "company": getattr(prospect,"company_name",""),
                    "email": getattr(prospect,"email",""),
                    "offer_price": offer.get("price",0),
                    "draft_email": self._build_cold_email(prospect, offer),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "approved": False,
                })
                log.info(f"[OUTREACH] ✅ Alerte Telegram → {getattr(prospect,'company_name','?')}")

        if self.auto_send and getattr(prospect,"email",""):
            r = self.send_cold_email(prospect, offer)
            result["email"] = r.get("sent", False)
            result["status"] = "auto_sent" if result["email"] else "telegram_only"
        else:
            result["status"] = "pending_approval" if result["telegram"] else "no_channel"

        return result

    def _get_gmail_sender(self):
        """Retourne le Gmail OAuth2 sender si disponible."""
        try:
            from NAYA_CORE.integrations.gmail_oauth2 import get_gmail_sender
            sender = get_gmail_sender()
            if sender.available:
                return sender
        except Exception:
            pass
        return None

    def send_cold_email(self, prospect, offer: Dict) -> Dict:
        """Envoie l'email cold via SendGrid (ou SMTP fallback)."""
        email = getattr(prospect,"email","")
        if not email: return {"sent": False, "reason": "no_email"}

        subject, body_html, body_text = self._build_cold_email(prospect, offer)

        if self.has_sendgrid:
            r = self._send_via_sendgrid(email, subject, body_html, body_text,
                                         getattr(prospect,"contact_name",""))
            if r.get("sent"):
                self._sent_count += 1
                return r

        if self.has_smtp:
            r = self._send_via_smtp(email, subject, body_text,
                                     getattr(prospect,"contact_name",""))
            if r.get("sent"):
                self._sent_count += 1
                return r

        return {"sent": False, "reason": "no_email_channel",
                "hint": "Configurer SENDGRID_API_KEY ou SMTP_USER+SMTP_PASS dans SECRETS/keys/notifications.env"}

    def approve_and_send(self, approval_id: str) -> Dict:
        """Approuve et envoie un email en attente (depuis TORI ou Telegram)."""
        p = next((a for a in self._pending_approvals if a["id"]==approval_id), None)
        if not p: return {"error": "approval_not_found"}
        email = p.get("email","")
        if not email: return {"error": "no_email"}

        subject, body_html, body_text = p["draft_email"]
        result = {}
        # V10: Gmail OAuth2 en priorité (zero SMTP password)
        gmail = self._get_gmail_sender()
        if gmail and gmail.has_oauth2:
            result = {"sent": False}
            r = gmail.send(email, subject, body_html, body_text, p.get("company",""))
            result = {"sent": r.get("sent", False), "method": r.get("method"), "message_id": r.get("message_id")}
        elif self.has_sendgrid:
            result = self._send_via_sendgrid(email, subject, body_html, body_text, p.get("company",""))
        elif self.has_smtp:
            result = self._send_via_smtp(email, subject, body_text, p.get("company",""))

        if result.get("sent"):
            p["approved"] = True
            p["sent_at"] = datetime.now(timezone.utc).isoformat()
            self._approved_count += 1
            if self.has_telegram:
                self._send_telegram(f"✅ Email envoyé → {email}\nEntreprise: {p.get('company','?')}")
        return result

    # ── Construction messages ────────────────────────────────────────────────
    def _build_telegram_opportunity(self, prospect, offer: Dict) -> str:
        company    = getattr(prospect,"company_name","?")
        contact    = getattr(prospect,"contact_name","dirigeant")
        email      = getattr(prospect,"email","Non disponible")
        city       = getattr(prospect,"city","")
        pain_cost  = getattr(prospect,"pain_annual_cost_eur",0)
        price      = offer.get("price", getattr(prospect,"offer_price_eur",0))
        title      = offer.get("title", getattr(prospect,"offer_title","Solution"))
        signals    = getattr(prospect,"pain_signals",[])
        score      = getattr(prospect,"solvability_score",0)
        priority   = getattr(prospect,"priority","MEDIUM")
        source     = getattr(prospect,"source","")
        delivery   = getattr(prospect,"offer_delivery_hours",48)
        pid        = getattr(prospect,"id","?")
        icon       = {"CRITICAL":"🔴","HIGH":"🟠","MEDIUM":"🟡","LOW":"⚪"}.get(priority,"🟡")
        roi        = int(pain_cost / max(price,1)) if pain_cost and price else 0

        return (
            f"{icon} *OPPORTUNITÉ {priority}* — Score {score:.0f}/100\n\n"
            f"🏢 *{company}*{f' — {city}' if city else ''}\n"
            f"👤 Contact: {contact}\n"
            f"📧 Email: `{email}`\n"
            f"🔍 Source: {source}\n\n"
            f"💡 *Signaux douleur:*\n" +
            "\n".join(f"• {s}" for s in signals[:3]) +
            f"\n\n💸 Coût annuel: *{pain_cost:,.0f}€/an*\n"
            f"🎯 Offre: {title}\n"
            f"💰 Prix: *{price:,.0f}€* (ROI ×{roi})\n"
            f"⏱ Livraison: {delivery}H\n\n"
            f"👉 `/approve {pid}` pour envoyer l'email\n"
            f"👉 `/skip {pid}` pour passer\n\n"
            f"_NAYA V19 — Revenue Engine_"
        )

    def _build_cold_email(self, prospect, offer: Dict) -> Tuple[str,str,str]:
        company    = getattr(prospect,"company_name","votre entreprise")
        contact    = getattr(prospect,"contact_name","")
        first      = contact.split()[0] if contact else "Bonjour"
        pain_cost  = getattr(prospect,"pain_annual_cost_eur",0)
        pain_cat   = getattr(prospect,"pain_category","")
        price      = offer.get("price", getattr(prospect,"offer_price_eur",5000))
        title      = offer.get("title", getattr(prospect,"offer_title","Solution express"))
        delivery   = getattr(prospect,"offer_delivery_hours",48)
        signals    = getattr(prospect,"pain_signals",[])
        roi        = max(1, int(pain_cost/max(price,1)))
        sender     = self.email_from_name

        result_map = {
            "CASH_TRAPPED":        f"libérer {pain_cost:,.0f}€ de trésorerie bloquée",
            "MARGIN_INVISIBLE_LOSS":f"restaurer vos marges et récupérer {pain_cost:,.0f}€/an",
            "INVOICE_LEAK":        f"stopper les fuites de facturation ({pain_cost:,.0f}€/an)",
            "UNDERPRICED":         "augmenter vos prix sans perdre un seul client",
            "PROCESS_MANUAL_TAX":  f"automatiser {int(pain_cost/50)}H/an de travail manuel",
            "GROWTH_BLOCK":        "débloquer votre croissance et multiplier vos revenus",
            "CLIENT_BLEED":        f"stopper le churn silencieux ({pain_cost:,.0f}€/an défendu)",
        }
        promise = result_map.get(pain_cat, f"générer {pain_cost:,.0f}€ de valeur supplémentaire")
        pain_desc = ", ".join(signals[:2]).lower() if signals else "problèmes opérationnels"

        subject = f"Question sur {pain_desc} chez {company}"

        body_text = (
            f"Bonjour {first},\n\n"
            f"En analysant {company}, j'ai identifié une opportunité précise.\n\n"
            f"Les entreprises dans votre secteur perdent {pain_cost:,.0f}€/an à cause de "
            f"{pain_desc}. Ce coût est invisible — il ne figure pas dans les comptes mais saigne chaque mois.\n\n"
            f"Nous avons aidé 3 entreprises similaires à {promise} en {delivery}H.\n\n"
            f"Notre intervention : {title}\n"
            f"Investissement : {price:,.0f}€\n"
            f"Retour garanti : ×{roi} sur 12 mois\n\n"
            f"Est-ce que {pain_cost:,.0f}€/an de pertes valent {price:,.0f}€ pour les stopper ?\n\n"
            f"15 minutes pour vérifier si c'est pertinent pour vous ?\n\n"
            f"Bien à vous,\n{sender}\n\n---\nReply STOP pour se désabonner"
        )
        body_html = f"""<!DOCTYPE html><html><body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;color:#333;line-height:1.6">
<p>Bonjour {first},</p>
<p>En analysant <strong>{company}</strong>, j'ai identifié une opportunité précise.</p>
<p>Les entreprises dans votre secteur perdent <strong>{pain_cost:,.0f}€/an</strong> à cause de {pain_desc}. 
Ce coût est invisible — il ne figure pas dans les comptes mais saigne chaque mois.</p>
<p>Nous avons aidé 3 entreprises similaires à <strong>{promise}</strong> en {delivery}H.</p>
<hr style="border:1px solid #eee">
<p>🎯 <strong>Notre intervention :</strong> {title}<br>
💰 <strong>Investissement :</strong> {price:,.0f}€<br>
📈 <strong>Retour garanti :</strong> ×{roi} sur 12 mois</p>
<hr style="border:1px solid #eee">
<p>Est-ce que <strong>{pain_cost:,.0f}€/an de pertes</strong> valent <strong>{price:,.0f}€</strong> pour les stopper définitivement ?</p>
<p><strong>15 minutes pour vérifier si c'est pertinent pour vous ?</strong></p>
<p>Bien à vous,<br>{sender}</p>
<p style="color:#999;font-size:11px">Pour ne plus recevoir ces messages : <a href="mailto:{self.email_from}?subject=STOP">répondez STOP</a></p>
</body></html>"""

        return subject, body_html, body_text

    # ── Envoi réel ────────────────────────────────────────────────────────────
    def _send_telegram(self, msg: str) -> bool:
        if not self.has_telegram: return False
        try:
            import requests
            r = requests.post(
                f"https://api.telegram.org/bot{self.telegram_token}/sendMessage",
                json={"chat_id": self.telegram_chat, "text": msg, "parse_mode": "Markdown"},
                timeout=10
            )
            ok = r.status_code == 200
            if not ok: log.warning(f"[OUTREACH] Telegram {r.status_code}: {r.text[:100]}")
            return ok
        except Exception as e:
            log.warning(f"[OUTREACH] Telegram error: {e}"); return False

    def _send_via_sendgrid(self, to: str, subject: str, html: str, text: str, name: str="") -> Dict:
        try:
            import httpx
            payload = {
                "personalizations": [{"to":[{"email":to,"name":name or to.split("@")[0]}]}],
                "from": {"email": self.email_from, "name": self.email_from_name},
                "subject": subject,
                "content": [
                    {"type":"text/plain","value": text},
                    {"type":"text/html","value": html},
                ],
                "tracking_settings": {
                    "click_tracking":{"enable":True},
                    "open_tracking":{"enable":True},
                }
            }
            r = httpx.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers={"Authorization":f"Bearer {self.sendgrid_key}","Content-Type":"application/json"},
                json=payload, timeout=20
            )
            if r.status_code in (200,202):
                return {"sent":True,"msg_id":r.headers.get("X-Message-Id","")}
            log.warning(f"[OUTREACH] SendGrid {r.status_code}: {r.text[:200]}")
            return {"sent":False,"error":f"HTTP {r.status_code}"}
        except Exception as e:
            return {"sent":False,"error":str(e)}

    def _send_via_smtp(self, to: str, subject: str, body: str, name: str="") -> Dict:
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"]    = f"{self.email_from_name} <{self.smtp_user}>"
            msg["To"]      = f"{name} <{to}>" if name else to
            msg.attach(MIMEText(body, "plain"))
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as s:
                s.starttls()
                s.login(self.smtp_user, self.smtp_pass)
                s.sendmail(self.smtp_user, [to], msg.as_string())
            return {"sent":True}
        except Exception as e:
            return {"sent":False,"error":str(e)}


    def _build_cold_email_v2(self, prospect, offer: dict, conv: dict) -> tuple:
        """Email ultra-personnalisé branché sur ConversionEngine — taux d'ouverture optimal."""
        company  = getattr(prospect,"company_name","")
        contact  = getattr(prospect,"contact_name","")
        first    = contact.split()[0] if contact else "Bonjour"
        pain_cat = getattr(prospect,"pain_category","")
        price    = offer.get("price", getattr(prospect,"offer_price_eur",5000))
        annual   = getattr(prospect,"pain_annual_cost_eur",30000)
        delivery = offer.get("delivery_hours", 48)
        sender   = self.email_from_name
        monthly  = round(annual/12)
        roi      = round(annual/max(price,1),1)
        guarantee= offer.get("guarantee","Résultats en 30j ou remboursement")

        subject = conv.get("subject") or f"{monthly:,.0f}€/mois perdu — {pain_cat.replace('_',' ')} chez {company}"

        body_text = (
            f"Bonjour {first},\n\n"
            f"{conv.get('opening', 'J' + chr(39) + 'ai identifié une opportunité précise pour ' + company + '.')}\n\n"
            f"─────────────────────────\n"
            f"{conv.get('roi_statement','')}\n\n"
            f"⏰ {conv.get('urgency',f'Chaque mois sans action = {monthly:,.0f}€ perdus.')}\n\n"
            f"✅ {guarantee}\n\n"
            f"Résultat en {delivery}H. Zéro engagement.\n\n"
            f"{conv.get('cta','20 min pour voir les chiffres sur votre cas ?')}\n\n"
            f"Bien à vous,\n{sender}\n\n"
            f"---\nReply STOP pour se désabonner"
        )

        body_html = (
            f"<div style='font-family:Arial,sans-serif;max-width:600px;margin:0 auto;line-height:1.6;color:#333'>"
            f"<p>Bonjour {first},</p>"
            f"<p>{conv.get('opening','')}</p>"
            f"<div style='background:#f8f9fa;border-left:4px solid #007bff;padding:12px 16px;margin:16px 0'>"
            f"<p style='margin:0;font-weight:bold'>{conv.get('roi_statement','')}</p>"
            f"</div>"
            f"<p>⏰ {conv.get('urgency','')}</p>"
            f"<p>✅ <em>{guarantee}</em></p>"
            f"<p>Résultat en <strong>{delivery}H</strong>. Zéro engagement.</p>"
            f"<p style='background:#007bff;color:white;padding:12px 20px;border-radius:6px;"
            f"display:inline-block;font-weight:bold'>"
            f"{conv.get('cta','20 min pour voir les chiffres ?')}</p>"
            f"<p style='color:#888;font-size:12px;margin-top:24px'>Bien à vous, {sender} | "
            f"<a href='mailto:{self.email_from}?subject=STOP'>Se désabonner</a></p>"
            f"</div>"
        )
        return subject, body_html, body_text

    def get_stats(self) -> Dict:
        return {
            "channels": {
                "telegram": self.has_telegram,
                "sendgrid": self.has_sendgrid,
                "smtp":     self.has_smtp,
                "twilio":   self.has_twilio,
            },
            "mode": "auto" if self.auto_send else "approval",
            "sent_count": self._sent_count,
            "approved_count": self._approved_count,
            "pending_approvals": len(self._pending_approvals),
        }
