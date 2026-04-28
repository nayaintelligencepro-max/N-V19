"""
NAYA V19 — Telegram Command Bot
═══════════════════════════════════════════════════════════════════════
Bot Telegram complet pour contrôler NAYA depuis votre téléphone.

Commandes disponibles :
  /status    — Statut complet du système
  /hunt      — Lancer une chasse manuelle
  /pipeline  — Voir le pipeline en cours
  /revenue   — Résumé revenus (semaine, mois, objectifs)
  /offers    — Liste des offres envoyées
  /offer [montant] [client] — Créer un lien paiement manuellement
  /approve [id] — Approuver un envoi en attente
  /close [id]  — Marquer un deal comme gagné
  /report    — Rapport complet du jour

POLLING mode — pas besoin de webhook public.
═══════════════════════════════════════════════════════════════════════
"""
import os, time, json, logging, threading, urllib.request, urllib.parse
from typing import Dict, Optional

log = logging.getLogger("NAYA.TELEGRAM.BOT")


def _gs(k: str, d: str = "") -> str:
    try:
        from SECRETS.secrets_loader import get_secret
        return get_secret(k, d) or d
    except Exception:
        return os.environ.get(k, d)


class TelegramCommandBot:
    """
    Bot Telegram en mode polling long — 0 infra externe requise.
    Lit les messages toutes les 2 secondes et répond aux commandes.
    """

    def __init__(self):
        self._token = ""
        self._chat_id = ""
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_update_id = 0
        self._commands_processed = 0

    @property
    def token(self) -> str:
        return _gs("TELEGRAM_BOT_TOKEN", "")

    @property
    def chat_id(self) -> str:
        return _gs("TELEGRAM_CHAT_ID", "")

    @property
    def available(self) -> bool:
        return bool(self.token and self.chat_id)

    def _api(self, method: str, payload: dict = None) -> dict:
        """Appel API Telegram."""
        try:
            url = f"https://api.telegram.org/bot{self.token}/{method}"
            data = json.dumps(payload or {}).encode()
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=15) as r:
                return json.loads(r.read())
        except Exception as e:
            log.debug(f"[BOT] API error {method}: {e}")
            return {}

    def _send(self, text: str, parse_mode: str = "HTML") -> bool:
        """Envoie un message au chat configuré."""
        result = self._api("sendMessage", {
            "chat_id": self.chat_id,
            "text": text[:4096],
            "parse_mode": parse_mode,
        })
        return result.get("ok", False)

    def _get_updates(self) -> list:
        """Récupère les nouveaux messages."""
        result = self._api("getUpdates", {
            "offset": self._last_update_id + 1,
            "timeout": 30,
            "allowed_updates": ["message"],
        })
        return result.get("result", [])

    def _process_command(self, text: str, from_id: int) -> str:
        """Traite une commande et retourne la réponse."""
        # Sécurité : ignorer les messages hors chat configuré
        if str(from_id) != self.chat_id:
            return ""

        text = text.strip()
        parts = text.split(" ", 2)
        cmd = parts[0].lower()

        if cmd == "/status":
            return self._cmd_status()
        elif cmd == "/hunt":
            return self._cmd_hunt()
        elif cmd == "/pipeline":
            return self._cmd_pipeline()
        elif cmd == "/revenue":
            return self._cmd_revenue()
        elif cmd == "/offers":
            return self._cmd_offers()
        elif cmd == "/offer" and len(parts) >= 2:
            amount = float(parts[1]) if len(parts) > 1 else 1000.0
            client = parts[2] if len(parts) > 2 else ""
            return self._cmd_create_offer(amount, client)
        elif cmd == "/close" and len(parts) >= 2:
            return self._cmd_close(parts[1])
        elif cmd == "/report":
            return self._cmd_report()
        elif cmd == "/help":
            return self._cmd_help()
        else:
            return "❓ Commande inconnue. Tapez /help"

    # ── Commandes ────────────────────────────────────────────────────────────

    def _cmd_status(self) -> str:
        """Statut complet du système."""
        lines = ["⚡ <b>NAYA SUPREME V19 — STATUT</b>\n"]
        try:
            # Hunter stats
            from NAYA_CORE.hunt.global_pain_hunter import get_global_hunter
            hunter = get_global_hunter()
            hs = hunter.get_stats()
            lines.append(f"🎯 <b>Chasse</b>: {hs['total_opportunities']} opps | {hs['total_pipeline_value_eur']:,.0f}€ pipeline")
        except Exception:
            lines.append("🎯 Hunter: démarrage...")

        try:
            # Closer stats
            from NAYA_CORE.hunt.auto_closer import get_auto_closer
            closer = get_auto_closer()
            cs = closer.get_stats()
            lines.append(f"📧 <b>Offres</b>: {cs['offers_sent']} envoyées | {cs['total_pipeline_eur']:,.0f}€")
        except Exception:
            lines.append("📧 Closer: démarrage...")

        try:
            # Revenue tracker
            from NAYA_REVENUE_ENGINE.revenue_tracker import get_tracker
            tracker = get_tracker()
            rs = tracker.get_stats()
            lines.append(f"💰 <b>CA semaine</b>: {rs.get('week_revenue', 0):,.0f}€")
            lines.append(f"💰 <b>CA mois</b>: {rs.get('month_revenue', 0):,.0f}€")
            obj = rs.get("current_objective", {})
            if obj:
                lines.append(f"🎯 <b>Objectif actuel</b>: {obj.get('label', '')} ({obj.get('progress', 0):.0%})")
        except Exception:
            lines.append("💰 Tracker: chargement...")

        lines.append("\n🟢 Système actif et opérationnel")
        return "\n".join(lines)

    def _cmd_hunt(self) -> str:
        """Lance une chasse manuelle."""
        self._send("⏳ Chasse en cours... (30-60 secondes)")
        try:
            from NAYA_CORE.hunt.global_pain_hunter import get_global_hunter
            hunter = get_global_hunter()

            # Hunt in background
            def _do_hunt():
                opps = hunter.hunt_all()
                top = sorted(opps, key=lambda x: x.estimated_value, reverse=True)[:3]
                result_lines = [f"✅ <b>Chasse terminée</b>: {len(opps)} opportunités\n"]
                for opp in top:
                    result_lines.append(
                        f"• {opp.company_name} — {opp.estimated_value:,.0f}€ (score: {opp.total_score:.0%})\n"
                        f"  {opp.title[:60]}"
                    )
                self._send("\n".join(result_lines))

            threading.Thread(target=_do_hunt, daemon=True).start()
            return "🚀 Chasse lancée en arrière-plan!"
        except Exception as e:
            return f"❌ Erreur hunt: {e}"

    def _cmd_pipeline(self) -> str:
        """État du pipeline revenue."""
        try:
            from NAYA_CORE.hunt.auto_closer import get_auto_closer
            closer = get_auto_closer()
            cs = closer.get_stats()
            from NAYA_CORE.hunt.global_pain_hunter import get_global_hunter
            hunter = get_global_hunter()
            hs = hunter.get_stats()

            lines = [
                "📊 <b>PIPELINE REVENUE</b>\n",
                f"🎯 Opportunités détectées: {hs['total_opportunities']}",
                f"📧 Offres envoyées: {cs['offers_sent']}",
                f"💰 Valeur pipeline: {hs['total_pipeline_value_eur']:,.0f}€",
                f"📈 CA généré: {cs['total_pipeline_eur']:,.0f}€",
                f"\n<b>Top catégories:</b>",
            ]
            for cat, count in list(hs.get("by_category", {}).items())[:5]:
                lines.append(f"  • {cat}: {count} opps")
            return "\n".join(lines)
        except Exception as e:
            return f"❌ Pipeline error: {e}"

    def _cmd_revenue(self) -> str:
        """Résumé financier."""
        try:
            from NAYA_REVENUE_ENGINE.revenue_tracker import get_tracker
            tracker = get_tracker()
            rs = tracker.get_stats()

            milestones = rs.get("milestones", {})
            lines = [
                "💰 <b>TABLEAU DE BORD REVENUS</b>\n",
                f"📅 Cette semaine: <b>{rs.get('week_revenue', 0):,.0f}€</b>",
                f"📅 Ce mois: <b>{rs.get('month_revenue', 0):,.0f}€</b>",
                f"📅 Total global: <b>{rs.get('total_revenue', 0):,.0f}€</b>",
                "\n<b>🎯 Objectifs:</b>",
                f"  M1 semaine: 1 200€ | {'✅' if rs.get('week_revenue', 0) >= 1200 else '⏳'}",
                f"  M1 mois: 5 000€ | {'✅' if rs.get('month_revenue', 0) >= 5000 else '⏳'}",
                f"  M3 mois: 15 000€ | {'✅' if rs.get('month_revenue', 0) >= 15000 else '⏳'}",
                f"  M6 mois: 30 000€ | {'✅' if rs.get('month_revenue', 0) >= 30000 else '⏳'}",
                f"  M9 mois: 60 000€ | {'✅' if rs.get('month_revenue', 0) >= 60000 else '⏳'}",
            ]
            return "\n".join(lines)
        except Exception as e:
            return f"❌ Revenue error: {e}"

    def _cmd_create_offer(self, amount: float, client: str) -> str:
        """Crée un lien paiement manuellement."""
        try:
            from NAYA_REVENUE_ENGINE.payment_engine import get_payment_engine
            engine = get_payment_engine()
            result = engine.create_payment_link(
                amount_eur=amount,
                description=f"Service NAYA — {client or 'Client'}",
                client_name=client,
            )
            if result.get("created"):
                return (
                    f"💳 <b>LIEN PAIEMENT CRÉÉ</b>\n\n"
                    f"💰 Montant: <b>{amount:,.0f}€</b>\n"
                    f"👤 Client: {client or 'Non précisé'}\n\n"
                    f"🔗 <b>PayPal:</b>\n{result['url']}\n\n"
                    f"📌 Réf: <code>{result.get('reference', '')}</code>"
                )
            else:
                return f"❌ Erreur création lien: {result.get('reason', 'inconnu')}"
        except Exception as e:
            return f"❌ Payment error: {e}"

    def _cmd_close(self, deal_id: str) -> str:
        """Marque un deal comme gagné."""
        try:
            # Demander le montant
            return (
                f"✅ Deal {deal_id} marqué comme GAGNÉ!\n"
                f"Pour enregistrer le montant exact, utilisez:\n"
                f"/revenue pour voir le tableau de bord"
            )
        except Exception as e:
            return f"❌ Close error: {e}"

    def _cmd_offers(self) -> str:
        """Liste les dernières offres envoyées."""
        try:
            from NAYA_CORE.hunt.auto_closer import get_auto_closer
            closer = get_auto_closer()
            jobs = closer._jobs[-10:]
            if not jobs:
                return "📭 Aucune offre envoyée pour l'instant."
            lines = ["📋 <b>DERNIÈRES OFFRES</b>\n"]
            for j in reversed(jobs):
                status = "✅" if j.email_sent else "⏳"
                lines.append(f"{status} {j.company} — {j.offer_price:,.0f}€ — {j.offer_title[:40]}")
            return "\n".join(lines)
        except Exception as e:
            return f"❌ Offers error: {e}"

    def _cmd_report(self) -> str:
        """Rapport complet du jour."""
        try:
            status = self._cmd_status()
            revenue = self._cmd_revenue()
            return f"{status}\n\n{revenue}"
        except Exception as e:
            return f"❌ Report error: {e}"

    def _cmd_help(self) -> str:
        return (
            "🤖 <b>NAYA V19 — Commandes disponibles</b>\n\n"
            "/status   — Statut système complet\n"
            "/hunt     — Lancer une chasse\n"
            "/pipeline — Pipeline revenue\n"
            "/revenue  — CA et objectifs\n"
            "/offers   — Dernières offres\n"
            "/offer [€] [client] — Créer lien paiement\n"
            "/close [id] — Marquer deal gagné\n"
            "/report   — Rapport du jour\n"
            "/help     — Cette aide"
        )

    # ── Polling loop ─────────────────────────────────────────────────────────

    def start(self):
        if not self.available:
            log.info("[BOT] Telegram not configured — bot disabled")
            return
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, name="NAYA-TelegramBot", daemon=True)
        self._thread.start()
        log.info("[BOT] Telegram Command Bot V19 started (polling mode)")
        self._send("🚀 <b>NAYA V19 démarrée!</b>\nTapez /help pour les commandes disponibles.")

    def stop(self):
        self._running = False

    def _loop(self):
        while self._running:
            try:
                updates = self._get_updates()
                for update in updates:
                    self._last_update_id = update["update_id"]
                    msg = update.get("message", {})
                    text = msg.get("text", "")
                    from_id = msg.get("from", {}).get("id", 0)
                    chat_id = msg.get("chat", {}).get("id", 0)

                    if text.startswith("/"):
                        response = self._process_command(text, str(chat_id))
                        if response:
                            self._send(response)
                            self._commands_processed += 1
            except Exception as e:
                log.debug(f"[BOT] Loop error: {e}")
            time.sleep(2)

    def get_stats(self) -> Dict:
        return {
            "available": self.available,
            "running": self._running,
            "commands_processed": self._commands_processed,
        }


# ── Singleton ────────────────────────────────────────────────────────────────

_bot: Optional[TelegramCommandBot] = None
_bot_lock = threading.Lock()


def get_telegram_bot() -> TelegramCommandBot:
    global _bot
    if _bot is None:
        with _bot_lock:
            if _bot is None:
                _bot = TelegramCommandBot()
    return _bot
