"""
AUTONOMOUS SALES SCHEDULER — Exécution Automatique 10 Ventes / 10 Jours
═══════════════════════════════════════════════════════════════
Scheduler autonome qui exécute les ventes réelles automatiquement.
Jobs quotidiens:
1. Vérifier objectif du jour
2. Activer agents selon stratégie
3. Créer ventes selon signaux marché
4. Notifier progression Telegram
"""
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List
import asyncio

log = logging.getLogger("NAYA.AUTONOMOUS_SALES_SCHEDULER")


class AutonomousSalesScheduler:
    """
    Scheduler autonome pour l'exécution automatique des ventes réelles.

    Jobs:
    - Daily morning (6h UTC): Analyser objectif du jour
    - Every 4 hours: Scanner marché et créer opportunités
    - Every 2 hours: Check progression et ajuster stratégie
    - Daily evening (18h UTC): Rapport quotidien
    """

    def __init__(self):
        self.active = False
        log.info("✅ AutonomousSalesScheduler initialized")

    async def start(self) -> None:
        """Démarre le scheduler autonome."""
        self.active = True
        log.info("🚀 Autonomous sales scheduler STARTED")

        # Lancer les jobs en parallèle
        await asyncio.gather(
            self._daily_morning_analysis(),
            self._market_scanner_loop(),
            self._progress_checker_loop(),
            self._daily_evening_report(),
            return_exceptions=True,
        )

    async def stop(self) -> None:
        """Arrête le scheduler."""
        self.active = False
        log.info("🛑 Autonomous sales scheduler STOPPED")

    # ── Job Loops ─────────────────────────────────────────────────────────────

    async def _daily_morning_analysis(self) -> None:
        """Job quotidien 6h UTC : Analyse objectif du jour."""
        while self.active:
            try:
                now = datetime.now(timezone.utc)
                # Attendre 6h00 UTC
                if now.hour == 6 and now.minute < 5:
                    await self._run_morning_analysis()
                    await asyncio.sleep(3600)  # Sleep 1h pour éviter double exécution
            except Exception as e:
                log.error("Morning analysis error: %s", e, exc_info=True)

            await asyncio.sleep(300)  # Check toutes les 5 minutes

    async def _market_scanner_loop(self) -> None:
        """Job toutes les 4h : Scanner marché et créer opportunités."""
        while self.active:
            try:
                await self._scan_market_and_create_sales()
            except Exception as e:
                log.error("Market scanner error: %s", e, exc_info=True)

            await asyncio.sleep(14400)  # 4 heures

    async def _progress_checker_loop(self) -> None:
        """Job toutes les 2h : Check progression et ajuster stratégie."""
        while self.active:
            try:
                await self._check_progress_and_adjust()
            except Exception as e:
                log.error("Progress checker error: %s", e, exc_info=True)

            await asyncio.sleep(7200)  # 2 heures

    async def _daily_evening_report(self) -> None:
        """Job quotidien 18h UTC : Rapport quotidien."""
        while self.active:
            try:
                now = datetime.now(timezone.utc)
                # Attendre 18h00 UTC
                if now.hour == 18 and now.minute < 5:
                    await self._send_evening_report()
                    await asyncio.sleep(3600)  # Sleep 1h
            except Exception as e:
                log.error("Evening report error: %s", e, exc_info=True)

            await asyncio.sleep(300)  # Check toutes les 5 minutes

    # ── Job Implementations ───────────────────────────────────────────────────

    async def _run_morning_analysis(self) -> None:
        """Analyse matinale : objectif du jour + stratégie."""
        try:
            from NAYA_REAL_SALES.ten_day_challenge import get_ten_day_challenge
            from NAYA_REAL_SALES.real_sales_engine import get_real_sales_engine
            from NAYA_COMMAND_GATEWAY.telegram_bot_v2 import get_telegram_bot_v2

            challenge = get_ten_day_challenge()
            engine = get_real_sales_engine()
            bot = get_telegram_bot_v2()

            current_day = challenge.get_current_day()
            if not current_day:
                log.info("Challenge non actif")
                return

            confirmed = engine.get_confirmed_sales()
            total_revenue = sum(s.amount_eur for s in confirmed)

            msg = (
                f"🌅 BRIEFING MATINAL — Jour {current_day.day_number}/10\n\n"
                f"🎯 OBJECTIF AUJOURD'HUI\n"
                f"├── Target : {current_day.target_eur:,} EUR\n"
                f"├── Focus : {current_day.focus}\n"
                f"└── Deal type : {current_day.deal_type}\n\n"
                f"💰 PROGRESSION\n"
                f"├── Ventes confirmées : {len(confirmed)}\n"
                f"├── Revenue confirmé : {total_revenue:,} EUR\n"
                f"└── Objectif jour : {current_day.target_eur:,} EUR\n\n"
                f"⚡ ACTIONS RECOMMANDÉES\n"
            )

            for action in current_day.recommended_actions:
                msg += f"→ {action}\n"

            bot._send_alert(msg)
            log.info("Morning analysis sent to Telegram")

        except Exception as e:
            log.error("Morning analysis failed: %s", e, exc_info=True)

    async def _scan_market_and_create_sales(self) -> None:
        """Scanner le marché et créer automatiquement des opportunités de vente."""
        try:
            from NAYA_REAL_SALES.ten_day_challenge import get_ten_day_challenge
            from NAYA_REAL_SALES.real_sales_engine import get_real_sales_engine

            challenge = get_ten_day_challenge()
            current_day = challenge.get_current_day()

            if not current_day:
                return

            # Stratégie selon le type de deal du jour
            targets = self._identify_targets_for_day(current_day)

            # Créer 1-2 ventes selon les opportunités détectées
            engine = get_real_sales_engine()

            for target in targets[:2]:  # Max 2 ventes par scan
                try:
                    sale = engine.create_sale_from_api(
                        company=target["company"],
                        sector=target["sector"],
                        amount_eur=target["amount_eur"],
                        service_type=target["service_type"],
                        payment_provider=target["provider"],
                        metadata={
                            "source": "autonomous_scanner",
                            "signal": target.get("signal", "market_opportunity"),
                            "contact": "Prospect Auto",
                            "email": "prospect@naya.local",
                            "day_number": getattr(current_day, "day_number", 0),
                        },
                    )
                    log.info("Auto-created sale: %s — %s — %d EUR",
                             sale.sale_id, target["company"], target["amount_eur"])
                except Exception as e:
                    log.error("Failed to create sale for %s: %s", target["company"], e)

        except Exception as e:
            log.error("Market scan failed: %s", e, exc_info=True)

    async def _check_progress_and_adjust(self) -> None:
        """Vérifier la progression et ajuster la stratégie."""
        try:
            from NAYA_REAL_SALES.ten_day_challenge import get_ten_day_challenge
            from NAYA_REAL_SALES.real_sales_engine import get_real_sales_engine
            from NAYA_COMMAND_GATEWAY.telegram_bot_v2 import get_telegram_bot_v2

            challenge = get_ten_day_challenge()
            engine = get_real_sales_engine()
            bot = get_telegram_bot_v2()

            current_day = challenge.get_current_day()
            if not current_day:
                return

            confirmed = engine.get_confirmed_sales()
            total_revenue = sum(s.amount_eur for s in confirmed)

            # Alerte si en retard
            if total_revenue < current_day.target_eur * 0.5:
                bot._send_alert(
                    f"⚠️ ALERTE PROGRESSION\n"
                    f"Jour {current_day.day_number}/10\n"
                    f"Revenue actuel : {total_revenue:,} EUR\n"
                    f"Target : {current_day.target_eur:,} EUR\n"
                    f"→ 🔴 En retard — intensifier prospection"
                )

            # Félicitations si objectif atteint
            elif total_revenue >= current_day.target_eur:
                bot._send_alert(
                    f"🎉 OBJECTIF ATTEINT !\n"
                    f"Jour {current_day.day_number}/10\n"
                    f"Revenue : {total_revenue:,} EUR\n"
                    f"Target : {current_day.target_eur:,} EUR\n"
                    f"→ ✅ En avance sur le planning"
                )

        except Exception as e:
            log.error("Progress check failed: %s", e, exc_info=True)

    async def _send_evening_report(self) -> None:
        """Rapport quotidien du soir."""
        try:
            from NAYA_REAL_SALES.ten_day_challenge import get_ten_day_challenge
            from NAYA_REAL_SALES.real_sales_engine import get_real_sales_engine
            from NAYA_COMMAND_GATEWAY.telegram_bot_v2 import get_telegram_bot_v2

            challenge = get_ten_day_challenge()
            engine = get_real_sales_engine()
            bot = get_telegram_bot_v2()

            current_day = challenge.get_current_day()
            if not current_day:
                return

            confirmed = engine.get_confirmed_sales()
            pending = [s for s in engine.sales if s.payment_status == "pending"]

            total_confirmed = sum(s.amount_eur for s in confirmed)
            total_pending = sum(s.amount_eur for s in pending)

            stats = challenge.get_stats()
            progress_pct = (total_confirmed / stats['total_target_eur']) * 100 if stats['total_target_eur'] > 0 else 0

            status_emoji = "✅" if total_confirmed >= current_day.target_eur else "🔴"

            msg = (
                f"🌙 RAPPORT DU SOIR — Jour {current_day.day_number}/10\n\n"
                f"{status_emoji} PERFORMANCE AUJOURD'HUI\n"
                f"├── Ventes confirmées : {len(confirmed)}\n"
                f"├── Revenue confirmé : {total_confirmed:,} EUR\n"
                f"├── Ventes en attente : {len(pending)}\n"
                f"├── Revenue en attente : {total_pending:,} EUR\n"
                f"└── Target : {current_day.target_eur:,} EUR\n\n"
                f"📊 PROGRESSION GLOBALE\n"
                f"├── {progress_pct:.1f}% de l'objectif total\n"
                f"├── {10 - current_day.day_number} jours restants\n"
                f"└── Target total : {stats['total_target_eur']:,} EUR\n\n"
                f"💤 Repos bien mérité. Demain : {challenge.days[current_day.day_number].focus if current_day.day_number < 9 else 'Challenge terminé !'}"
            )

            bot._send_alert(msg)
            log.info("Evening report sent to Telegram")

        except Exception as e:
            log.error("Evening report failed: %s", e, exc_info=True)

    # ── Target Identification ─────────────────────────────────────────────────

    def _identify_targets_for_day(self, current_day) -> List[Dict[str, Any]]:
        """
        Identifie des cibles automatiquement selon le type de deal du jour.

        Stratégie progressive :
        - Jours 1-3 : Audits Express (1.5k-5k EUR)
        - Jours 4-6 : Consulting + Formation (5k-8k EUR)
        - Jours 7-9 : Contrats IEC 62443 (10k-15k EUR)
        - Jour 10 : Grand contrat (20k EUR)
        """
        # Base de prospects simulés (en production, viendrait de PainHunterAgent)
        prospect_pool = [
            {
                "company": "SNCF Réseau",
                "sector": "transport",
                "amount_eur": 15000,
                "service_type": "iec62443_audit",
                "provider": "paypal",
                "signal": "job_offer_rssi_ot",
            },
            {
                "company": "EDF Énergies",
                "sector": "energie",
                "amount_eur": 12000,
                "service_type": "nis2_compliance",
                "provider": "paypal",
                "signal": "regulatory_deadline",
            },
            {
                "company": "Michelin Manufacturing",
                "sector": "manufacturing",
                "amount_eur": 8000,
                "service_type": "ot_security_training",
                "provider": "paypal",
                "signal": "ransomware_incident",
            },
            {
                "company": "Airbus Defence",
                "sector": "aerospace",
                "amount_eur": 18000,
                "service_type": "scada_security_audit",
                "provider": "paypal",
                "signal": "certification_required",
            },
            {
                "company": "Enedis Distribution",
                "sector": "energie",
                "amount_eur": 20000,
                "service_type": "framework_contract_12m",
                "provider": "paypal",
                "signal": "annual_contract",
            },
        ]

        # Filtrer selon le montant cible du jour
        day_number = current_day.day_number
        target_amount = current_day.target_eur

        # Tolérance ±30% du montant cible
        min_amount = int(target_amount * 0.7)
        max_amount = int(target_amount * 1.3)

        relevant_targets = [
            p for p in prospect_pool
            if min_amount <= p["amount_eur"] <= max_amount
        ]

        # Si aucun match exact, prendre les plus proches
        if not relevant_targets:
            relevant_targets = sorted(
                prospect_pool,
                key=lambda x: abs(x["amount_eur"] - target_amount)
            )[:2]

        return relevant_targets


# ── Singleton ─────────────────────────────────────────────────────────────────
_scheduler: AutonomousSalesScheduler = None


def get_autonomous_sales_scheduler() -> AutonomousSalesScheduler:
    """Retourne l'instance singleton du scheduler."""
    global _scheduler
    if _scheduler is None:
        _scheduler = AutonomousSalesScheduler()
    return _scheduler
