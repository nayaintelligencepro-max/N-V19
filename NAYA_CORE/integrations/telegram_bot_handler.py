"""
NAYA V19 — TELEGRAM BOT HANDLER
Traite les callbacks des boutons Telegram en temps réel.
Chaque bouton = une action business immédiate.

Boutons disponibles:
  ✅ Envoyer email    → envoie l'email cold automatiquement
  💳 Lien PayPal      → crée et envoie le lien de paiement
  ❌ Ignorer          → marque le prospect comme ignoré
  📋 Voir pipeline    → affiche le pipeline complet
  🔄 Nouveau scan     → lance un cycle Revenue Engine maintenant
  💰 Stats revenus    → affiche les KPIs financiers

Flux cash réel:
  NAYA détecte prospect CRITICAL
  → Alerte Telegram avec boutons
  → Tu cliques "✅ Envoyer email"
  → Email IA envoyé en 2 secondes
  → Prospect répond OUI
  → Tu cliques "💳 Lien PayPal"
  → Lien envoyé au client
  → Client paie → argent sur ton compte PayPal
  → NAYA marque WON + calcule prochain cycle
"""

import os
import json
import time
import logging
import threading
import urllib.request
import urllib.parse
from typing import Dict, Optional, List, Callable
from datetime import datetime

log = logging.getLogger("NAYA.TELEGRAM.BOT")


def _gs(key: str, default: str = "") -> str:
    try:
        from SECRETS.secrets_loader import get_secret
        return get_secret(key, default) or default
    except Exception:
        return os.environ.get(key, default)


class TelegramBotHandler:
    """
    Gestionnaire de bot Telegram avec traitement des callbacks.
    Polling long (getUpdates) pour recevoir les interactions boutons.
    """

    POLL_TIMEOUT = 30  # secondes
    POLL_INTERVAL = 1  # entre les polls

    def __init__(self):
        self._token = _gs("TELEGRAM_BOT_TOKEN")
        self._chat_id = _gs("TELEGRAM_CHAT_ID")
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_update_id = 0
        self._processed_callbacks: set = set()
        self._pending_approvals: Dict[str, Dict] = {}  # approval_id → draft
        self._callback_handlers: Dict[str, Callable] = {}
        self._revenue_engine = None
        self._pipeline = None

        if self.available:
            self._register_handlers()
            log.info("✅ Telegram Bot Handler prêt — polling actif")
        else:
            log.debug("Telegram Bot: token/chat non configuré")

    @property
    def available(self) -> bool:
        return bool(self._token and self._chat_id)

    def _api(self, method: str, payload: Dict = None) -> Optional[Dict]:
        """Appelle l'API Telegram."""
        try:
            url = f"https://api.telegram.org/bot{self._token}/{method}"
            if payload:
                data = json.dumps(payload).encode("utf-8")
                req = urllib.request.Request(
                    url, data=data,
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
            else:
                req = urllib.request.Request(url)

            with urllib.request.urlopen(req, timeout=35) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result if result.get("ok") else None
        except Exception as e:
            log.debug(f"[TG Bot] API {method}: {e}")
            return None

    def send(self, text: str, buttons: List[List[Dict]] = None, parse_mode: str = "HTML") -> bool:
        """Envoie un message au chat configuré."""
        payload = {
            "chat_id": self._chat_id,
            "text": text,
            "parse_mode": parse_mode,
        }
        if buttons:
            payload["reply_markup"] = {"inline_keyboard": buttons}

        result = self._api("sendMessage", payload)
        return bool(result)

    def answer_callback(self, callback_query_id: str, text: str = "", alert: bool = False):
        """Répond à un callback de bouton (ferme le spinner)."""
        self._api("answerCallbackQuery", {
            "callback_query_id": callback_query_id,
            "text": text,
            "show_alert": alert,
        })

    def edit_message(self, message_id: int, text: str, buttons: List = None):
        """Édite un message existant (après action)."""
        payload = {
            "chat_id": self._chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": "HTML",
        }
        if buttons:
            payload["reply_markup"] = {"inline_keyboard": buttons}
        else:
            payload["reply_markup"] = {"inline_keyboard": []}
        self._api("editMessageText", payload)

    def _register_handlers(self):
        """Enregistre les handlers de callbacks."""
        self._callback_handlers = {
            "approve": self._handle_approve_email,
            "paypal": self._handle_paypal_link,
            "skip": self._handle_skip,
            "pipeline": self._handle_pipeline_status,
            "scan": self._handle_trigger_scan,
            "stats": self._handle_revenue_stats,
            "won": self._handle_mark_won,
            "lost": self._handle_mark_lost,
        }

    def register_approval(self, approval_id: str, draft: Dict):
        """Enregistre un brouillon d'email pour approbation."""
        self._pending_approvals[approval_id] = draft
        # Pruner si trop d'entrées
        if len(self._pending_approvals) > 500:
            oldest_keys = list(self._pending_approvals.keys())[:100]
            for k in oldest_keys:
                del self._pending_approvals[k]

    def attach_revenue_engine(self, engine):
        """Attache le Revenue Engine pour les actions."""
        self._revenue_engine = engine
        if hasattr(engine, "_pipeline"):
            self._pipeline = engine._pipeline
        log.info("[TG Bot] Revenue Engine attaché")

    def start_polling(self):
        """Démarre le polling en arrière-plan."""
        if not self.available or self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._polling_loop,
            name="NAYA-TG-POLL",
            daemon=True
        )
        self._thread.start()
        log.info("[TG Bot] Polling démarré")

    def stop_polling(self):
        """Arrête le polling."""
        self._running = False

    def _polling_loop(self):
        """Boucle de polling principale."""
        while self._running:
            try:
                updates = self._get_updates()
                for update in updates:
                    self._process_update(update)
            except Exception as e:
                log.debug(f"[TG Bot] Polling error: {e}")
            time.sleep(self.POLL_INTERVAL)

    def _get_updates(self) -> List[Dict]:
        """Récupère les nouvelles mises à jour."""
        result = self._api("getUpdates", {
            "offset": self._last_update_id + 1,
            "timeout": self.POLL_TIMEOUT,
            "allowed_updates": ["callback_query", "message"],
        })
        if not result or not result.get("result"):
            return []

        updates = result["result"]
        if updates:
            self._last_update_id = updates[-1]["update_id"]
        return updates

    def _process_update(self, update: Dict):
        """Traite une mise à jour Telegram."""
        # Callback d'un bouton inline
        if "callback_query" in update:
            self._process_callback(update["callback_query"])

        # Message texte entrant
        elif "message" in update:
            self._process_message(update["message"])

    def _process_callback(self, callback: Dict):
        """Traite le clic d'un bouton inline."""
        callback_id = callback.get("id")
        data = callback.get("data", "")
        message = callback.get("message", {})
        message_id = message.get("message_id")

        # Éviter les doubles traitements
        if data in self._processed_callbacks:
            self.answer_callback(callback_id, "⚠️ Déjà traité")
            return
        self._processed_callbacks.add(data)

        # Parser la commande: "action:arg1:arg2"
        parts = data.split(":")
        action = parts[0]
        args = parts[1:]

        log.info(f"[TG Bot] Callback: {action} {args}")

        handler = self._callback_handlers.get(action)
        if handler:
            try:
                handler(callback_id, message_id, args)
            except Exception as e:
                log.error(f"[TG Bot] Handler {action}: {e}")
                self.answer_callback(callback_id, f"❌ Erreur: {str(e)[:50]}", alert=True)
        else:
            self.answer_callback(callback_id, "❓ Action inconnue")

    def _process_message(self, message: Dict):
        """Traite un message texte entrant."""
        text = message.get("text", "").strip().lower()
        chat_id = str(message.get("chat", {}).get("id", ""))

        # Sécurité: vérifier que c'est notre chat
        if chat_id != str(self._chat_id):
            return

        # Commandes rapides
        if text in ["/status", "status", "état"]:
            self._send_status_report()
        elif text in ["/scan", "scan", "chasse"]:
            self._trigger_scan_immediate()
        elif text in ["/pipeline", "pipeline"]:
            self._send_pipeline_report()
        elif text in ["/stats", "stats"]:
            self._send_revenue_stats()
        elif text in ["/help", "help", "aide"]:
            self._send_help()

    # ── Handlers des boutons ─────────────────────────────────────────────────

    def _handle_approve_email(self, callback_id: str, message_id: int, args: List[str]):
        """✅ Approuver et envoyer l'email."""
        approval_id = args[0] if args else ""
        draft = self._pending_approvals.get(approval_id)

        if not draft:
            self.answer_callback(callback_id, "⚠️ Brouillon expiré ou déjà envoyé", alert=True)
            return

        company = draft.get("company", "?")
        email = draft.get("email", "")
        subject = draft.get("draft_subject", draft.get("subject", ""))
        body = draft.get("draft_body", draft.get("body", ""))
        price = draft.get("offer_price", 0)

        if not email:
            self.answer_callback(callback_id, "⚠️ Pas d'email pour ce prospect", alert=True)
            return

        # Envoyer via Gmail OAuth2 ou fallback
        sent = False
        method = "none"
        try:
            from NAYA_CORE.integrations.gmail_oauth2 import get_gmail_sender
            sender = get_gmail_sender()
            body_html = f"<p>{body.replace(chr(10), '<br>')}</p>"
            result = sender.send(
                to_email=email,
                subject=subject,
                body_html=body_html,
                body_text=body,
            )
            sent = result.get("sent", False)
            method = result.get("method", "unknown")
        except Exception as e:
            log.warning(f"[TG Bot] Email send: {e}")

        if sent:
            # Mettre à jour le pipeline
            if self._pipeline and draft.get("prospect_id"):
                self._pipeline.update_status(
                    draft["prospect_id"], "CONTACTED",
                    f"Email approuvé et envoyé via Telegram ({method})"
                )
            del self._pending_approvals[approval_id]

            self.answer_callback(callback_id, f"✅ Email envoyé à {email}")
            self.edit_message(
                message_id,
                f"✅ <b>EMAIL ENVOYÉ</b>\n\n"
                f"🏢 {company}\n"
                f"📧 {email}\n"
                f"📋 {subject}\n"
                f"💰 Valeur: {price:,.0f}€\n"
                f"⏰ {datetime.now().strftime('%H:%M:%S')}\n\n"
                f"<i>Méthode: {method}</i>"
            )
        else:
            self.answer_callback(callback_id, "❌ Échec envoi email", alert=True)

    def _handle_paypal_link(self, callback_id: str, message_id: int, args: List[str]):
        """💳 Créer et envoyer le lien PayPal."""
        if len(args) < 2:
            self.answer_callback(callback_id, "❌ Arguments manquants", alert=True)
            return

        prospect_id = args[0]
        amount = float(args[1]) if len(args) > 1 else 5000

        # Créer le lien PayPal
        paypal_url = _gs("PAYPAL_ME_URL", "https://www.paypal.me/Myking987")
        payment_url = f"{paypal_url.rstrip('/')}/{amount:.2f}"
        ref = f"NAYA-{int(amount)}-{int(time.time()) % 10000:04d}"

        # Trouver info prospect
        company = "le client"
        email = ""
        if self._pipeline:
            entry = next((v for v in self._pipeline.all() if v.get("id") == prospect_id), None)
            if entry:
                company = entry.get("company", "le client")
                email = entry.get("email", "")
                # Envoyer lien par email si disponible
                if email:
                    try:
                        from NAYA_CORE.integrations.gmail_oauth2 import get_gmail_sender
                        sender = get_gmail_sender()
                        sender.send(
                            to_email=email,
                            subject=f"Votre lien de règlement — {amount:.0f}€",
                            body_html=(
                                f"<p>Bonjour,</p>"
                                f"<p>Suite à notre échange, voici votre lien de règlement sécurisé :</p>"
                                f"<p><strong><a href='{payment_url}'>{payment_url}</a></strong></p>"
                                f"<p>Montant : <strong>{amount:.0f}€</strong><br>"
                                f"Référence : {ref}</p>"
                                f"<p>Le paiement s'effectue par carte bancaire ou compte PayPal.</p>"
                                f"<p>Bien à vous,<br>NAYA SUPREME</p>"
                            ),
                            body_text=f"Lien PayPal: {payment_url}\nMontant: {amount:.0f}€\nRef: {ref}",
                        )
                    except Exception as e:
                        log.debug(f"[TG Bot] PayPal email: {e}")

                # Mettre à jour statut pipeline
                self._pipeline.update_status(prospect_id, "PROPOSAL_SENT", f"Lien PayPal: {payment_url}")

        self.answer_callback(callback_id, f"💳 Lien créé: {amount:.0f}€")
        self.edit_message(
            message_id,
            f"💳 <b>LIEN PAIEMENT CRÉÉ — {amount:.0f}€</b>\n\n"
            f"🏢 {company}\n"
            f"🔗 <code>{payment_url}</code>\n"
            f"📧 {f'Email envoyé à {email}' if email else 'Pas d email'}\n"
            f"📌 Réf: {ref}\n\n"
            f"⚡ Attente paiement client..."
        )

    def _handle_skip(self, callback_id: str, message_id: int, args: List[str]):
        """❌ Ignorer le prospect."""
        prospect_id = args[0] if args else ""
        if self._pipeline and prospect_id:
            self._pipeline.update_status(prospect_id, "CLOSED_LOST", "Ignoré manuellement")
        self.answer_callback(callback_id, "❌ Prospect ignoré")
        self.edit_message(message_id, "❌ <i>Prospect ignoré</i>")

    def _handle_pipeline_status(self, callback_id: str, message_id: int, args: List[str]):
        """📋 Afficher le pipeline."""
        self.answer_callback(callback_id, "📋 Chargement pipeline...")
        self._send_pipeline_report()

    def _handle_trigger_scan(self, callback_id: str, message_id: int, args: List[str]):
        """🔄 Lancer un scan immédiat."""
        self.answer_callback(callback_id, "🔄 Scan lancé!")
        self._trigger_scan_immediate()

    def _handle_revenue_stats(self, callback_id: str, message_id: int, args: List[str]):
        """💰 Afficher les stats revenus."""
        self.answer_callback(callback_id, "💰 Calcul stats...")
        self._send_revenue_stats()

    def _handle_mark_won(self, callback_id: str, message_id: int, args: List[str]):
        """✅ Marquer comme WON."""
        prospect_id = args[0] if args else ""
        amount = float(args[1]) if len(args) > 1 else 0
        if self._pipeline and prospect_id:
            self._pipeline.update_status(prospect_id, "CLOSED_WON", f"Marqué WON: {amount:.0f}€")
        self.answer_callback(callback_id, f"💰 WON — {amount:.0f}€ !")
        self.send(f"🎉 <b>DEAL WON — {amount:,.0f}€ !</b>\n\nBravo ! Argent en route. 💰")

    def _handle_mark_lost(self, callback_id: str, message_id: int, args: List[str]):
        """❌ Marquer comme LOST."""
        prospect_id = args[0] if args else ""
        if self._pipeline and prospect_id:
            self._pipeline.update_status(prospect_id, "CLOSED_LOST", "Marqué LOST manuellement")
        self.answer_callback(callback_id, "❌ Deal perdu enregistré")

    # ── Rapports automatiques ─────────────────────────────────────────────────

    def _send_status_report(self):
        """Envoie un rapport d'état complet."""
        try:
            from NAYA_CORE.execution.providers.free_llm_provider import get_free_llm
            llm = get_free_llm()
            llm_status = f"{llm.best_provider_name} ({'PREMIUM' if llm.is_premium else 'GRATUIT'})"
        except Exception:
            llm_status = "N/A"

        pipeline_info = ""
        if self._pipeline:
            try:
                kpis = self._pipeline.get_kpis()
                pipeline_info = (
                    f"\n💰 Pipeline: <b>{kpis.get('pipeline_eur', 0):,.0f}€</b>\n"
                    f"✅ Won total: <b>{kpis.get('revenue_won_eur', 0):,.0f}€</b>\n"
                    f"👥 Prospects actifs: {kpis.get('active_prospects', 0)}"
                )
            except Exception:
                pass

        text = (
            f"⚡ <b>NAYA SUPREME V10 — ÉTAT</b>\n\n"
            f"🧠 LLM: {llm_status}\n"
            f"🕐 {datetime.now().strftime('%H:%M:%S')}"
            f"{pipeline_info}\n\n"
            f"<i>Système autonome actif 24/7</i>"
        )
        buttons = [[
            {"text": "🔄 Scan maintenant", "callback_data": "scan:now"},
            {"text": "📊 Stats revenus", "callback_data": "stats:all"},
        ]]
        self.send(text, buttons)

    def _send_pipeline_report(self):
        """Envoie le rapport pipeline."""
        if not self._pipeline:
            self.send("📋 Pipeline non disponible")
            return

        try:
            kpis = self._pipeline.get_kpis()
            hot = self._pipeline.get_hot_prospects(5)

            text = (
                f"📊 <b>PIPELINE NAYA V19</b>\n\n"
                f"💰 Valeur totale: <b>{kpis.get('pipeline_eur', 0):,.0f}€</b>\n"
                f"✅ Won: <b>{kpis.get('revenue_won_eur', 0):,.0f}€</b>\n"
                f"👥 Actifs: {kpis.get('active_prospects', 0)}\n"
                f"📧 Contactés: {kpis.get('contacted', 0)}\n"
                f"🔥 Chauds: {kpis.get('hot_count', 0)}\n\n"
            )

            if hot:
                text += "<b>TOP 5 PROSPECTS CHAUDS:</b>\n"
                for p in hot[:5]:
                    text += (
                        f"• {p.get('company', '?')} — "
                        f"{p.get('offer_price', 0):,.0f}€ "
                        f"[{p.get('status', '?')}]\n"
                    )

            self.send(text)

        except Exception as e:
            self.send(f"📋 Erreur pipeline: {e}")

    def _send_revenue_stats(self):
        """Envoie les stats revenus."""
        if not self._revenue_engine:
            self.send("💰 Revenue Engine non disponible")
            return

        try:
            stats = self._revenue_engine.get_stats()
            pipeline = stats.get("pipeline", {})
            text = (
                f"💰 <b>STATS REVENUS NAYA V19</b>\n\n"
                f"🔄 Cycles: {stats.get('cycle_count', 0)}\n"
                f"👥 Prospects trouvés: {stats.get('total_found', 0)}\n"
                f"📧 Emails envoyés: {stats.get('total_emails', 0)}\n"
                f"💵 Pipeline total: <b>{pipeline.get('pipeline_eur', 0):,.0f}€</b>\n"
                f"✅ Won: <b>{pipeline.get('revenue_won_eur', 0):,.0f}€</b>\n"
                f"🎯 Taux conv: {pipeline.get('conversion_rate', 0):.1f}%\n\n"
                f"🕐 Prochaine chasse: {stats.get('scan_interval_s', 1800) // 60} min"
            )
            self.send(text)
        except Exception as e:
            self.send(f"💰 Erreur stats: {e}")

    def _send_help(self):
        """Envoie l'aide des commandes."""
        text = (
            f"🤖 <b>NAYA SUPREME V10 — COMMANDES</b>\n\n"
            f"/status — État du système\n"
            f"/scan — Lancer une chasse maintenant\n"
            f"/pipeline — Voir le pipeline complet\n"
            f"/stats — Stats revenus\n\n"
            f"<b>Boutons automatiques:</b>\n"
            f"✅ Approuver → envoie l'email\n"
            f"💳 PayPal → crée et envoie le lien\n"
            f"❌ Ignorer → supprime le prospect\n\n"
            f"<i>NAYA chasse 24/7 — tu valides les actions critiques</i>"
        )
        self.send(text)

    def _trigger_scan_immediate(self):
        """Lance un cycle Revenue Engine immédiatement."""
        def _run():
            try:
                if self._revenue_engine:
                    results = self._revenue_engine.run_cycle()
                    self.send(
                        f"🔄 <b>SCAN TERMINÉ</b>\n\n"
                        f"👥 Prospects: {results.get('new_prospects', 0)}\n"
                        f"📧 Emails: {results.get('emails_sent', 0)}\n"
                        f"💰 Pipeline: {results.get('pipeline_eur', 0):,.0f}€"
                    )
                else:
                    self.send("⚠️ Revenue Engine non démarré")
            except Exception as e:
                self.send(f"❌ Erreur scan: {e}")

        threading.Thread(target=_run, daemon=True).start()
        self.send("🔄 <b>Scan lancé...</b> Résultats dans ~30s")


# ── Singleton ────────────────────────────────────────────────────────────────

_BOT_HANDLER: Optional[TelegramBotHandler] = None


def get_telegram_bot() -> TelegramBotHandler:
    global _BOT_HANDLER
    if _BOT_HANDLER is None:
        _BOT_HANDLER = TelegramBotHandler()
    return _BOT_HANDLER
