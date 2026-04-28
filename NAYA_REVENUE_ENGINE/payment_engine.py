"""
NAYA V19 — Payment Engine (Polynésie française)
Méthodes disponibles :
  1. PayPal.Me       — principal, universel (PAYPAL_ME_URL)
  2. Deblock.Me      — secondaire, fallback auto si indisponible (DEBLOCK_ME_URL)

Stripe supprimé : pas de compte disponible pour la Polynésie française.
Si Stripe devient disponible plus tard → ajouter PAYPAL_ME_URL dans payments.env.
"""
import os, time, logging
from typing import Dict, Optional
from datetime import datetime, timezone

log = logging.getLogger("NAYA.PAYMENT")


def _gs(k: str, d: str = "") -> str:
    try:
        from SECRETS.secrets_loader import get_secret
        return get_secret(k, d) or d
    except Exception:
        return os.environ.get(k, d)


class PaymentEngine:
    """
    Polynésie française — PayPal.Me principal, Deblock.Me secondaire.
    Génère des liens avec montant pré-rempli.
    Format PayPal : https://www.paypal.me/USER/MONTANT
    Format Deblock: https://deblock.me/USER/MONTANT (ou lien fixe)
    """

    CURRENCY      = "EUR"
    SUPPORT_EMAIL = "contact@nayabot.online"
    SUPPORT_PHONE = "+68989559088"

    # Seuil au-delà duquel on propose les deux méthodes en parallèle
    DUAL_METHOD_THRESHOLD_EUR = 500

    def __init__(self) -> None:
        self._payments: Dict[str, Dict] = {}

    # ── Propriétés dynamiques ────────────────────────────────────────────────

    @property
    def paypal_url(self) -> str:
        return _gs("PAYPAL_ME_URL", "https://www.paypal.me/Myking987")

    @property
    def deblock_url(self) -> str:
        """Lien Deblock.Me — peut être un lien fixe ou un lien dynamique."""
        # Chercher d'abord dans payments.env, puis dans deblock_payment.json
        url = _gs("DEBLOCK_ME_URL", "")
        if not url:
            # Fallback : lire depuis le fichier JSON
            try:
                import json
                from pathlib import Path
                f = Path(__file__).parent.parent / "SECRETS/keys/deblock_payment.json"
                if f.exists():
                    data = json.loads(f.read_text())
                    url = data.get("link", "")
            except Exception:
                pass
        return url

    @property
    def has_paypal(self) -> bool:
        return "paypal.me/" in self.paypal_url

    @property
    def has_deblock(self) -> bool:
        url = self.deblock_url
        return bool(url) and "deblock.me/" in url

    @property
    def revolut_url(self) -> str:
        """Lien Revolut.Me — optionnel, configuré via REVOLUT_ME_URL."""
        return _gs("REVOLUT_ME_URL", "")

    @property
    def has_revolut(self) -> bool:
        url = self.revolut_url
        return bool(url) and "revolut.me/" in url

    @property
    def available(self) -> bool:
        return self.has_paypal or self.has_deblock or self.has_revolut

    @property
    def primary_method(self) -> str:
        """PayPal en premier, Deblock en fallback, Revolut en option."""
        if self.has_paypal:
            return "paypal"
        if self.has_deblock:
            return "deblock"
        if self.has_revolut:
            return "revolut"
        return "none"

    # ── Méthode principale ───────────────────────────────────────────────────

    def create_payment_link(self, amount_eur: float, description: str,
                             client_email: str = "", client_name: str = "") -> Dict:
        """
        Crée le ou les liens de paiement selon les méthodes configurées.
        - Toujours PayPal en priorité
        - Deblock ajouté en complément si montant > seuil ou si PayPal indisponible
        """
        if not self.available:
            return {
                "created": False,
                "reason": "Aucun moyen de paiement configuré",
                "fix": "Ajouter PAYPAL_ME_URL dans SECRETS/keys/payments.env"
            }

        # Méthode principale : PayPal
        if self.has_paypal:
            result = self._create_paypal_link(amount_eur, description, client_email, client_name)
        elif self.has_revolut:
            result = self._create_revolut_link(amount_eur, description, client_email, client_name)
        else:
            result = self._create_deblock_link(amount_eur, description, client_email, client_name)

        # Ajouter Revolut en option sur les gros montants
        if self.has_revolut and amount_eur >= self.DUAL_METHOD_THRESHOLD_EUR:
            rev = self._create_revolut_link(amount_eur, description, client_email, client_name)
            if rev.get("created"):
                result["revolut_url"] = rev["url"]

        # Ajouter Deblock en option secondaire sur les gros montants
        if self.has_deblock and self.has_paypal and amount_eur >= self.DUAL_METHOD_THRESHOLD_EUR:
            rev = self._create_deblock_link(amount_eur, description, client_email, client_name)
            if rev.get("created"):
                result["deblock_url"] = rev["url"]
                result["telegram_msg"] += (
                    f"\n\n💸 <b>Alternative Deblock:</b>\n{rev['url']}"
                )

        return result

    # ── PayPal.Me ────────────────────────────────────────────────────────────

    def _create_paypal_link(self, amount: float, desc: str,
                             email: str = "", name: str = "") -> Dict:
        """PayPal.Me avec montant pré-rempli — aucune API requise."""
        base = self.paypal_url.rstrip("/")
        url  = f"{base}/{amount:.2f}"
        ref  = f"NAYA-{int(amount)}-{__import__('uuid').uuid4().hex[:6].upper()}"
        pay_id = f"PAY_{int(time.time())}"

        self._payments[pay_id] = {
            "id": pay_id, "url": url, "amount": amount, "desc": desc,
            "provider": "paypal_me", "email": email, "name": name,
            "ref": ref, "ts": datetime.now(timezone.utc).isoformat(),
        }

        log.info(f"[PAYMENT] PayPal.Me: {amount:.0f}€ → {url}")

        tg_msg = (
            f"💳 <b>LIEN PAIEMENT — {amount:.0f}€</b>\n\n"
            f"👤 Client : {name or 'Non précisé'}\n"
            f"📋 Service: {desc[:60]}\n\n"
            f"🔗 <b>PayPal (paiement direct):</b>\n{url}\n\n"
            f"📌 Référence : <code>{ref}</code>\n"
            f"📧 {email if email else self.SUPPORT_EMAIL}\n\n"
            f"<i>Montant {amount:.0f}€ pré-rempli — carte ou compte PayPal acceptés</i>"
        )

        email_body = (
            f"Bonjour {name or 'Madame/Monsieur'},\n\n"
            f"Suite à notre échange, voici votre lien de règlement sécurisé :\n\n"
            f"🔗 {url}\n\n"
            f"Montant  : {amount:.0f}€\n"
            f"Service  : {desc}\n"
            f"Référence: {ref}\n\n"
            f"Le lien vous permet de payer directement par carte bancaire ou compte PayPal.\n"
            f"Une fois le paiement effectué, votre service sera activé sous 2H.\n\n"
            f"Des questions ?\n"
            f"📧 {self.SUPPORT_EMAIL}\n"
            f"📱 WhatsApp : {self.SUPPORT_PHONE}\n\n"
            f"Bien à vous,\nNAYA SUPREME"
        )

        return {
            "created":    True,
            "url":        url,
            "amount":     amount,
            "provider":   "paypal_me",
            "reference":  ref,
            "payment_id": pay_id,
            "client_name":  name,
            "client_email": email,
            "telegram_msg": tg_msg,
            "email_body":   email_body,
        }

    # ── Revolut.Me ───────────────────────────────────────────────────────────

    def _create_revolut_link(self, amount: float, desc: str,
                              email: str = "", name: str = "") -> Dict:
        """
        Revolut.Me — lien pocket avec note de montant.
        Le montant n'est pas pré-rempli automatiquement sur tous les liens Revolut,
        une note est incluse pour préciser le montant au payeur.
        """
        base = self.revolut_url.rstrip("/")
        pay_id = f"REV_{int(time.time())}"
        ref = f"NAYA-R{int(amount)}-{__import__('uuid').uuid4().hex[:6].upper()}"
        note = f"{desc[:40]} — {amount:.0f}EUR — ref:{ref}"

        self._payments[pay_id] = {
            "id": pay_id, "url": base, "amount": amount, "desc": desc,
            "provider": "revolut_me", "email": email, "name": name,
            "ref": ref, "ts": datetime.now(timezone.utc).isoformat(),
        }

        log.info(f"[PAYMENT] Revolut.Me: {amount:.0f}€ → {base}")

        return {
            "created": True,
            "pay_id": pay_id,
            "url": base,
            "amount": amount,
            "currency": self.CURRENCY,
            "provider": "revolut_me",
            "reference": ref,
            "note": note,
            "email_body": (
                f"Bonjour {name or 'Madame/Monsieur'},\n\n"
                f"Suite à notre échange, voici votre lien de règlement :\n\n"
                f"🔗 {base}\n\n"
                f"Montant  : {amount:.0f}€\n"
                f"Service  : {desc}\n"
                f"Note     : {note}\n\n"
                f"Merci de préciser la référence {ref} lors du paiement.\n\n"
                f"Bien à vous,\nNAYA SUPREME"
            ),
            "telegram_msg": (
                f"💳 <b>LIEN REVOLUT — {amount:.0f}€</b>\n\n"
                f"👤 {name or 'Non précisé'}\n"
                f"📋 {desc[:60]}\n\n"
                f"🔗 <b>Revolut:</b>\n{base}\n"
                f"📌 Note: <code>{note}</code>"
            ),
        }

    # ── Deblock.Me ───────────────────────────────────────────────────────────

    def _create_deblock_link(self, amount: float, desc: str,
                              email: str = "", name: str = "") -> Dict:
        """
        Deblock.Me — lien fixe ou dynamique.
        Note : le lien dans deblock_payment.json est un lien de collecte fixe
        (pocket). Le montant n'est PAS pré-rempli automatiquement — à préciser
        dans le message au client.
        """
        url = self.deblock_url
        if not url:
            return {"created": False, "reason": "DEBLOCK_ME_URL non configuré"}

        ref    = f"REV-{int(amount)}-{__import__('uuid').uuid4().hex[:6].upper()}"
        pay_id = f"REV_{int(time.time())}"

        self._payments[pay_id] = {
            "id": pay_id, "url": url, "amount": amount, "desc": desc,
            "provider": "deblock_me", "email": email, "name": name,
            "ref": ref, "ts": datetime.now(timezone.utc).isoformat(),
        }

        log.info(f"[PAYMENT] Deblock.Me: {amount:.0f}€ → {url}")

        tg_msg = (
            f"💳 <b>PAIEMENT DEBLOCK — {amount:.0f}€</b>\n\n"
            f"👤 Client : {name or 'Non précisé'}\n"
            f"📋 Service: {desc[:60]}\n\n"
            f"🔗 <b>Lien Deblock:</b>\n{url}\n\n"
            f"⚠️ <i>Indiquer le montant exact ({amount:.0f}€) et la référence</i>\n"
            f"📌 Référence : <code>{ref}</code>"
        )

        return {
            "created":       True,
            "url":           url,
            "amount":        amount,
            "provider":      "deblock_me",
            "reference":     ref,
            "payment_id":    pay_id,
            "client_name":   name,
            "client_email":  email,
            "telegram_msg":  tg_msg,
            "note":          f"Montant à préciser au client : {amount:.0f}€ — réf {ref}",
        }

    # ── Vérification Deblock (lien encore actif ?) ───────────────────────────

    def check_deblock_status(self) -> Dict:
        """
        Vérifie si le lien Deblock répond encore (HEAD request).
        Utile pour détecter la fermeture du compte Polynésie.
        """
        url = self.deblock_url
        if not url:
            return {"available": False, "reason": "Non configuré"}
        try:
            import httpx
            r = httpx.head(url, timeout=5, follow_redirects=True)
            alive = r.status_code < 400
            return {
                "available":   alive,
                "status_code": r.status_code,
                "url":         url,
                "note":        "OK" if alive else "Lien inactif — compte peut-être fermé",
            }
        except Exception as e:
            return {"available": False, "url": url, "error": str(e)[:60]}

    # ── Stats ────────────────────────────────────────────────────────────────

    def get_stats(self) -> Dict:
        paypal_links  = sum(1 for p in self._payments.values() if p.get("provider") == "paypal_me")
        deblock_links = sum(1 for p in self._payments.values() if p.get("provider") == "deblock_me")
        total_amount  = sum(p.get("amount", 0) for p in self._payments.values())

        return {
            "available":          self.available,
            "primary_method":     self.primary_method,
            "paypal_configured":  self.has_paypal,
            "deblock_configured": self.has_deblock,
            "total_links":        len(self._payments),
            "paypal_links":       paypal_links,
            "deblock_links":      deblock_links,
            "total_amount_eur":   round(total_amount, 2),
            "note": "PayPal.me + Deblock.me (Polynésie française)",
        }


# ── Singleton thread-safe ────────────────────────────────────────────────────
_pe: Optional[PaymentEngine] = None
_pe_lock = __import__("threading").Lock()


def get_payment_engine() -> PaymentEngine:
    global _pe
    if _pe is None:
        with _pe_lock:
            if _pe is None:
                _pe = PaymentEngine()
    return _pe
