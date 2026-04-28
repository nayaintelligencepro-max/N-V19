"""
NAYA V21 — Telegram Bot V2
Commandes avancées : /ooda, /simulate, /approve, /veto, /mrr, /velocity.
Mode décisionnel IA : recommandations OODA automatiques.
"""
import json
import logging
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

log = logging.getLogger("NAYA.TELEGRAM_BOT_V2")

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "telegram"
DATA_DIR.mkdir(parents=True, exist_ok=True)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_OWNER_CHAT_ID = os.getenv("TELEGRAM_OWNER_CHAT_ID", "")


@dataclass
class PendingAction:
    """Action en attente de validation (> 500 EUR ou critique)."""
    action_id: str
    action_type: str
    description: str
    amount_eur: int
    payload: Dict[str, Any]
    status: str = "pending"  # pending|approved|vetoed
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


class TelegramBotV2:
    """
    Telegram Bot V21 — interface de contrôle en temps réel.
    Commandes : /ooda /simulate /approve /veto /mrr /velocity /status /agents
    """

    DECISION_THRESHOLD_EUR = int(os.getenv("DECISION_THRESHOLD_EUR", "500"))

    def __init__(self):
        self._pending_actions: Dict[str, PendingAction] = {}
        self._load_data()
        log.info("✅ TelegramBotV2 initialisé")

    def _data_path(self) -> Path:
        return DATA_DIR / "pending_actions.json"

    def _load_data(self) -> None:
        p = self._data_path()
        if p.exists():
            try:
                raw = json.loads(p.read_text())
                for k, v in raw.items():
                    self._pending_actions[k] = PendingAction(**v)
            except Exception as exc:
                log.warning("Telegram data load error: %s", exc)

    def _save_data(self) -> None:
        p = self._data_path()
        try:
            p.write_text(json.dumps(
                {k: v.to_dict() for k, v in self._pending_actions.items()},
                ensure_ascii=False, indent=2,
            ))
        except Exception as exc:
            log.warning("Telegram save error: %s", exc)

    # ── Public commands ───────────────────────────────────────────────────────

    def cmd_ooda(self) -> str:
        """
        /ooda → Prochaine action recommandée par IA.
        Analyse l'état du pipeline et retourne la décision optimale OODA.
        """
        try:
            pipeline = self._get_pipeline_summary()
            mrr = self._get_mrr_summary()
            pending = [a for a in self._pending_actions.values() if a.status == "pending"]

            recommendations = self._compute_ooda_recommendations(pipeline, mrr)

            lines = [
                "🎯 OODA — PROCHAINE ACTION RECOMMANDÉE",
                f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                "",
            ]
            for i, rec in enumerate(recommendations[:3], 1):
                lines.append(f"{i}. {rec}")
            if pending:
                lines.append("")
                lines.append(f"⚠️ {len(pending)} action(s) en attente de validation")
                lines.append("→ Utiliser /validate [id] pour chaque action")
            lines.append("")
            lines.append(f"💰 MRR actuel: {mrr.get('mrr_eur', 0):,} EUR / Objectif: 10,000 EUR")
            return "\n".join(lines)
        except Exception as exc:
            return f"⚠️ OODA error: {exc}"

    def cmd_simulate(self, scenario: str) -> str:
        """
        /simulate [scenario] → Simule l'impact d'une décision sur les revenus.
        """
        scenarios = {
            "10_deals_15k": {
                "description": "Signer 10 deals audit (15k EUR chacun)",
                "m3": 50_000, "m6": 150_000, "m12": 600_000,
                "probability": "35%",
                "required_actions": ["Activer BlitzHunter 24/7", "Séquence outreach automatisée"],
            },
            "saas_20_clients": {
                "description": "20 clients SaaS NIS2 à 500 EUR/mois",
                "m3": 5_000, "m6": 10_000, "m12": 10_000,
                "probability": "60%",
                "required_actions": ["Lancer TORI_APP NIS2 Checker", "Activer PayPal MRR"],
            },
            "1_grand_compte": {
                "description": "1 grand compte 80k EUR (CAC40)",
                "m3": 80_000, "m6": 80_000, "m12": 240_000,
                "probability": "15%",
                "required_actions": ["Cibler DSI CAC40", "Préparer offre Pack Premium Full"],
            },
        }
        sc = scenarios.get(scenario.lower().replace(" ", "_"), None)
        if not sc:
            available = ", ".join(scenarios.keys())
            return f"⚠️ Scénario inconnu. Disponibles: {available}"

        return (
            f"📊 SIMULATION: {sc['description']}\n\n"
            f"💰 Impact revenus:\n"
            f"  M3  : {sc['m3']:,} EUR\n"
            f"  M6  : {sc['m6']:,} EUR\n"
            f"  M12 : {sc['m12']:,} EUR\n\n"
            f"📈 Probabilité: {sc['probability']}\n\n"
            f"⚡ Actions requises:\n"
            + "\n".join(f"  → {a}" for a in sc["required_actions"])
        )

    def cmd_approve(self, action_id: str) -> str:
        """
        /approve [action_id] → Valide une action en attente en 1 tap.
        """
        action = self._pending_actions.get(action_id)
        if not action:
            return f"⚠️ Action {action_id} non trouvée"
        if action.status != "pending":
            return f"⚠️ Action déjà {action.status}"
        action.status = "approved"
        self._save_data()
        log.info("Action %s approuvée: %s", action_id, action.description)
        return (
            f"✅ ACTION APPROUVÉE\n"
            f"ID: {action_id}\n"
            f"Type: {action.action_type}\n"
            f"Description: {action.description}\n"
            f"Montant: {action.amount_eur:,} EUR\n"
            f"→ Exécution en cours..."
        )

    def cmd_veto(self, action_id: str) -> str:
        """
        /veto [action_id] → Bloque une action automatique.
        """
        action = self._pending_actions.get(action_id)
        if not action:
            return f"⚠️ Action {action_id} non trouvée"
        if action.status != "pending":
            return f"⚠️ Action déjà {action.status}"
        action.status = "vetoed"
        self._save_data()
        log.info("Action %s vetoed: %s", action_id, action.description)
        return (
            f"🚫 ACTION BLOQUÉE\n"
            f"ID: {action_id}\n"
            f"Description: {action.description}\n"
            f"→ Action annulée, pipeline continue."
        )

    def cmd_mrr(self) -> str:
        """
        /mrr → MRR + ARR temps réel avec projection M6.
        """
        mrr_data = self._get_mrr_summary()
        mrr = mrr_data.get("mrr_eur", 0)
        arr = mrr_data.get("arr_eur", 0)
        active = mrr_data.get("active_subscriptions", 0)
        progress = mrr_data.get("progress_pct", 0)
        return (
            f"💰 MRR DASHBOARD\n"
            f"MRR actuel : {mrr:,} EUR/mois\n"
            f"ARR actuel : {arr:,} EUR/an\n"
            f"Abonnements actifs : {active}\n"
            f"Objectif M6 : 10,000 EUR\n"
            f"Progression : {progress}%\n"
            + ("✅ OBJECTIF ATTEINT" if mrr >= 10_000 else f"→ Manque : {10_000 - mrr:,} EUR")
        )

    def cmd_velocity(self) -> str:
        """
        /velocity → Pipeline ventes : deals/jour, time-to-close, conversion rate.
        """
        try:
            from NAYA_ACCELERATION.sales_velocity_tracker import get_velocity_tracker
            tracker = get_velocity_tracker()
            metrics = tracker.get_metrics()
            d = metrics.to_dict()
            return (
                f"⚡ SALES VELOCITY V21\n"
                f"Ventes aujourd'hui : {d.get('sales_today', 0)}\n"
                f"Ventes ce mois : {d.get('sales_this_month', 0)}\n"
                f"Revenue mois : {d.get('revenue_this_month_eur', 0):,} EUR\n"
                f"Conversion rate : {d.get('conversion_rate_pct', 0):.1f}%\n"
                f"Time-to-close moy : {d.get('avg_time_to_close_hours', 0):.1f}h\n"
                f"Objectif/jour : 2 ventes minimum\n"
            )
        except Exception as exc:
            return f"⚠️ Velocity error: {exc}"

    def cmd_challenge(self) -> str:
        """
        /challenge → Dashboard temps réel du défi 10 ventes en 10 jours.
        """
        try:
            from NAYA_REAL_SALES.ten_day_challenge import get_ten_day_challenge
            from NAYA_REAL_SALES.real_sales_engine import get_real_sales_engine

            challenge = get_ten_day_challenge()
            sales_engine = get_real_sales_engine()

            current_day = challenge.get_current_day()
            stats = challenge.get_stats()

            if not current_day:
                return (
                    f"⚠️ Challenge terminé ou non actif\n"
                    f"Démarré: {challenge.start_date.strftime('%d/%m/%Y')}\n"
                    f"Statistique finale: {stats['total_confirmed_sales']} ventes, "
                    f"{stats['total_confirmed_revenue_eur']:,} EUR"
                )

            # Ventes confirmées vs pending
            confirmed = sales_engine.get_confirmed_sales()
            pending = [s for s in sales_engine.sales if s.payment_status == "pending"]

            total_confirmed_revenue = sum(s.amount_eur for s in confirmed)
            total_pending_revenue = sum(s.amount_eur for s in pending)

            # Progress vs target
            progress_pct = (total_confirmed_revenue / stats['total_target_eur']) * 100 if stats['total_target_eur'] > 0 else 0

            lines = [
                "🎯 CHALLENGE 10 VENTES / 10 JOURS",
                f"📅 Jour {current_day.day_number}/10 — {current_day.focus}",
                "",
                "💰 REVENUS",
                f"├── Confirmés : {total_confirmed_revenue:,} EUR ({len(confirmed)} ventes)",
                f"├── En attente : {total_pending_revenue:,} EUR ({len(pending)} ventes)",
                f"└── Target J{current_day.day_number} : {current_day.target_eur:,} EUR",
                "",
                f"📊 PROGRESSION GLOBALE : {progress_pct:.1f}%",
                f"├── Objectif total : {stats['total_target_eur']:,} EUR",
                f"└── Reste à faire : {stats['total_target_eur'] - total_confirmed_revenue:,} EUR",
                "",
                "⚡ ACTIONS RECOMMANDÉES",
            ]

            for action in current_day.recommended_actions[:3]:
                lines.append(f"→ {action}")

            # Status indicator
            if total_confirmed_revenue >= current_day.target_eur:
                lines.append("")
                lines.append("✅ Objectif du jour ATTEINT !")
            else:
                lines.append("")
                lines.append(f"🔴 Manque : {current_day.target_eur - total_confirmed_revenue:,} EUR pour aujourd'hui")

            return "\n".join(lines)

        except Exception as exc:
            log.error("Challenge command error: %s", exc, exc_info=True)
            return f"⚠️ Challenge error: {exc}"

    def register_pending_action(
        self,
        action_type: str,
        description: str,
        amount_eur: int,
        payload: Dict[str, Any],
    ) -> PendingAction:
        """Enregistre une action nécessitant validation si > seuil."""
        import uuid
        action = PendingAction(
            action_id=str(uuid.uuid4())[:8],
            action_type=action_type,
            description=description,
            amount_eur=amount_eur,
            payload=payload,
        )
        self._pending_actions[action.action_id] = action
        self._save_data()

        if amount_eur >= self.DECISION_THRESHOLD_EUR:
            self._send_alert(
                f"⚠️ ACTION REQUISE\n"
                f"ID: {action.action_id}\n"
                f"Type: {action_type}\n"
                f"Description: {description}\n"
                f"Montant: {amount_eur:,} EUR\n"
                f"→ /approve {action.action_id} ou /veto {action.action_id}"
            )
        return action

    def is_action_approved(self, action_id: str) -> bool:
        action = self._pending_actions.get(action_id)
        return action is not None and action.status == "approved"

    def get_pending_actions(self) -> List[PendingAction]:
        return [a for a in self._pending_actions.values() if a.status == "pending"]

    def send_sale_notification(
        self, company: str, amount_eur: int, sector: str
    ) -> bool:
        """Notifie une vente sur Telegram."""
        msg = (
            f"🎉 VENTE SIGNÉE\n"
            f"Client: {company}\n"
            f"Secteur: {sector}\n"
            f"Montant: {amount_eur:,} EUR\n"
            f"→ Contrat à générer via ContractGeneratorAgent"
        )
        return self._send_alert(msg)

    # ── Internals ─────────────────────────────────────────────────────────────

    def _send_alert(self, message: str) -> bool:
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_OWNER_CHAT_ID:
            log.debug("Telegram non configuré — message: %s", message[:50])
            return False
        try:
            import urllib.request
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            data = json.dumps({
                "chat_id": TELEGRAM_OWNER_CHAT_ID,
                "text": message,
                "parse_mode": "HTML",
            }).encode()
            req = urllib.request.Request(url, data=data,
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                result = json.loads(resp.read())
                return result.get("ok", False)
        except Exception as exc:
            log.warning("Telegram send error: %s", exc)
            return False

    def _get_pipeline_summary(self) -> Dict:
        try:
            from NAYA_ACCELERATION.sales_velocity_tracker import get_velocity_tracker
            return get_velocity_tracker().get_metrics().to_dict()
        except Exception:
            return {}

    def _get_mrr_summary(self) -> Dict:
        try:
            from SAAS_NIS2.subscription_manager import get_subscription_manager
            return get_subscription_manager().get_mrr()
        except Exception:
            return {"mrr_eur": 0, "arr_eur": 0, "active_subscriptions": 0, "progress_pct": 0}

    def _compute_ooda_recommendations(
        self, pipeline: Dict, mrr: Dict
    ) -> List[str]:
        recs = []
        sales_today = pipeline.get("sales_today", 0)
        mrr_eur = mrr.get("mrr_eur", 0)
        pending = len([a for a in self._pending_actions.values() if a.status == "pending"])

        if pending > 0:
            recs.append(f"🔴 URGENT: {pending} action(s) en attente → /validate")
        if sales_today < 2:
            recs.append("🔴 Lancer BlitzHunter sur secteur Énergie (signal NIS2 + urgence)")
        if mrr_eur < 2_000:
            recs.append("🟠 Activer TORI_APP NIS2 Checker → 1er abonnement gratuit puis 500 EUR")
        if mrr_eur >= 5_000:
            recs.append("🟢 Upsell clients NIS2 → IEC 62443 Portal (2 000 EUR/mois)")
        if sales_today >= 2:
            recs.append("✅ Objectif journalier atteint → Préparer contrats")

        if not recs:
            recs = [
                "→ Scanner LinkedIn pour signaux RSSI OT (attaque récente)",
                "→ Envoyer séquence J+3 aux prospects en cours",
                "→ Générer offre Flash pour prospects score ≥ 70",
            ]
        return recs


# ── Singleton ─────────────────────────────────────────────────────────────────
_bot: Optional[TelegramBotV2] = None


def get_telegram_bot_v2() -> TelegramBotV2:
    global _bot
    if _bot is None:
        _bot = TelegramBotV2()
    return _bot
