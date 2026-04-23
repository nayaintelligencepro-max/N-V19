"""
NAYA CORE — AGENT 9 — REVENUE TRACKER
Tracking 4 streams de revenus en temps réel + projection OODA
Stream 1: Outreach deals (1k-20k EUR/deal)
Stream 2: Audits automatisés (5k-20k EUR/audit)
Stream 3: Contenu B2B récurrent (3k-15k EUR/mois)
Stream 4: SaaS NIS2 Checker (500-2k EUR/mois/client)
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum

logger = logging.getLogger(__name__)


class RevenueStream(Enum):
    """Les 4 streams de revenus NAYA"""
    OUTREACH_DEALS = "outreach_deals"
    AUDITS = "audits"
    CONTENT_RECURRING = "content_recurring"
    SAAS_NIS2 = "saas_nis2"


@dataclass
class RevenueEntry:
    """Entrée de revenu"""
    entry_id: str
    stream: RevenueStream
    amount_eur: Decimal
    client_company: str
    description: str
    recorded_at: datetime
    received_at: Optional[datetime] = None
    is_recurring: bool = False
    recurring_period: Optional[str] = None  # 'monthly', 'quarterly', 'annual'


@dataclass
class MonthlyTarget:
    """Objectif mensuel OODA"""
    month: int  # 1-12
    target_eur: Decimal
    max_eur: Decimal
    focus: str
    reached: bool = False
    actual_eur: Decimal = Decimal('0')

    @property
    def progress_pct(self) -> float:
        return float(self.actual_eur / self.target_eur * 100) if self.target_eur > 0 else 0

    @property
    def is_exceeded(self) -> bool:
        return self.actual_eur > self.max_eur


# Roadmap OODA M1-M12 (depuis CLAUDE.md)
OODA_ROADMAP = [
    MonthlyTarget(1, Decimal('5000'), Decimal('12000'), "OBSERVE — cartographier 50 prospects OT"),
    MonthlyTarget(2, Decimal('15000'), Decimal('25000'), "ORIENT — qualifier top 10, pitcher Audit Express"),
    MonthlyTarget(3, Decimal('25000'), Decimal('40000'), "DECIDE — 3 deals chauds, closing calls"),
    MonthlyTarget(4, Decimal('35000'), Decimal('50000'), "ACT — convertir one-shot en récurrents"),
    MonthlyTarget(5, Decimal('45000'), Decimal('60000'), "OBSERVE — partenariats Siemens/ABB + upsell"),
    MonthlyTarget(6, Decimal('60000'), Decimal('80000'), "ORIENT — lancer SaaS NIS2 MVP + MRR"),
    MonthlyTarget(7, Decimal('70000'), Decimal('90000'), "DECIDE — 3 grands comptes CAC40 OT"),
    MonthlyTarget(8, Decimal('80000'), Decimal('100000'), "ACT — MRR 10k EUR + deal Premium 80k EUR"),
    MonthlyTarget(9, Decimal('85000'), Decimal('110000'), "OBSERVE — analyser conv par secteur"),
    MonthlyTarget(10, Decimal('90000'), Decimal('115000'), "ORIENT — upsell 100% clients existants +30%"),
    MonthlyTarget(11, Decimal('95000'), Decimal('120000'), "DECIDE — contrats annuels avant clôture budgets"),
    MonthlyTarget(12, Decimal('100000'), Decimal('130000'), "ACT — 2 consultants OT + MRR > 20k EUR")
]


class RevenueTrackerAgent:
    """
    Agent 9 — Revenue Tracker

    Capacités:
    - Tracking en temps réel des 4 streams de revenus
    - Comparaison avec objectifs OODA mensuels
    - Projection cashflow 90 jours
    - Détection automatique des déviations (> 20% target)
    - Briefing quotidien Telegram 8h00 Polynésie
    - Métriques: MRR, ARR, CAC, LTV, churn
    """

    def __init__(self,
                 telegram_notifier=None,
                 persistence_manager=None,
                 start_month: int = 1):
        """
        Initialise le Revenue Tracker Agent

        Args:
            telegram_notifier: Service de notifications Telegram
            persistence_manager: Gestionnaire de persistance
            start_month: Mois de démarrage (1-12)
        """
        self.telegram_notifier = telegram_notifier
        self.persistence_manager = persistence_manager
        self.start_month = start_month
        self.current_month = start_month

        # Roadmap OODA (copie modifiable)
        self.roadmap = [MonthlyTarget(t.month, t.target_eur, t.max_eur, t.focus) for t in OODA_ROADMAP]

        # Revenus enregistrés
        self.revenue_entries: List[RevenueEntry] = []

        # Revenus par stream
        self.by_stream: Dict[RevenueStream, Decimal] = {
            stream: Decimal('0') for stream in RevenueStream
        }

        # MRR (Monthly Recurring Revenue)
        self.current_mrr_eur = Decimal('0')

        # Métriques globales
        self.total_revenue_eur = Decimal('0')
        self.total_deals = 0
        self.total_clients = set()

        logger.info(f"RevenueTrackerAgent initialized (start month: M{start_month})")

    async def track_revenue(self,
                           stream: RevenueStream,
                           amount_eur: float,
                           client_company: str,
                           description: str,
                           is_recurring: bool = False,
                           recurring_period: Optional[str] = None) -> RevenueEntry:
        """
        Enregistre un revenu

        Args:
            stream: Stream de revenu
            amount_eur: Montant en EUR
            client_company: Nom de l'entreprise cliente
            description: Description du revenu
            is_recurring: True si revenu récurrent
            recurring_period: Période de récurrence ('monthly', 'quarterly', 'annual')

        Returns:
            RevenueEntry créée
        """
        amount = Decimal(str(amount_eur))

        # Générer entry_id
        entry_id = f"REV_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{stream.value[:4].upper()}"

        # Créer l'entrée
        entry = RevenueEntry(
            entry_id=entry_id,
            stream=stream,
            amount_eur=amount,
            client_company=client_company,
            description=description,
            recorded_at=datetime.now(timezone.utc),
            is_recurring=is_recurring,
            recurring_period=recurring_period
        )

        # Enregistrer
        self.revenue_entries.append(entry)
        self.by_stream[stream] += amount
        self.total_revenue_eur += amount
        self.total_deals += 1
        self.total_clients.add(client_company)

        # Si récurrent mensuel, ajouter au MRR
        if is_recurring and recurring_period == 'monthly':
            self.current_mrr_eur += amount

        # Mettre à jour l'objectif du mois courant
        await self._update_monthly_target(amount)

        logger.info(f"Revenue tracked: {stream.value} - {amount} EUR - {client_company} - Total: {self.total_revenue_eur} EUR")

        # Sauvegarder en persistence
        if self.persistence_manager:
            await self.persistence_manager.save_revenue_entry(entry_id, entry.__dict__)

        # Vérifier si alerte nécessaire
        await self._check_alerts()

        return entry

    async def _update_monthly_target(self, amount: Decimal) -> None:
        """Met à jour l'objectif du mois courant"""
        if self.current_month < 1 or self.current_month > 12:
            return

        target = self.roadmap[self.current_month - 1]
        target.actual_eur += amount

        # Vérifier si objectif atteint
        if not target.reached and target.actual_eur >= target.target_eur:
            target.reached = True
            logger.info(f"🎯 OBJECTIF M{self.current_month} ATTEINT ! {target.actual_eur} EUR / {target.target_eur} EUR ({target.progress_pct:.1f}%)")

            # Notification Telegram
            if self.telegram_notifier:
                await self.telegram_notifier.send(
                    f"🎯 OBJECTIF M{self.current_month} ATTEINT !\n\n"
                    f"Réalisé : {target.actual_eur} EUR\n"
                    f"Target : {target.target_eur} EUR\n"
                    f"Progress : {target.progress_pct:.1f}%\n\n"
                    f"Focus : {target.focus}"
                )

        # Vérifier si dépassement max
        if target.is_exceeded:
            logger.warning(f"⚠️ MAX M{self.current_month} DÉPASSÉ ! {target.actual_eur} EUR > {target.max_eur} EUR")

    async def _check_alerts(self) -> None:
        """Vérifie si des alertes doivent être envoyées"""
        target = self.roadmap[self.current_month - 1]

        # Alerte si < 50% de l'objectif après 50% du mois écoulé
        days_in_month = 30
        current_day = datetime.now(timezone.utc).day

        if current_day > days_in_month / 2:
            expected_progress = 50.0
            actual_progress = target.progress_pct

            if actual_progress < expected_progress - 20:  # Retard de 20%+
                logger.warning(f"⚠️ RETARD M{self.current_month} : {actual_progress:.1f}% vs {expected_progress:.1f}% attendu")

                if self.telegram_notifier:
                    await self.telegram_notifier.send(
                        f"⚠️ ALERTE RETARD M{self.current_month}\n\n"
                        f"Progress actuel : {actual_progress:.1f}%\n"
                        f"Progress attendu : {expected_progress:.1f}%\n"
                        f"Retard : {expected_progress - actual_progress:.1f}%\n\n"
                        f"Action requise : {target.focus}"
                    )

    async def mark_revenue_received(self, entry_id: str) -> bool:
        """Marque un revenu comme effectivement reçu"""
        for entry in self.revenue_entries:
            if entry.entry_id == entry_id:
                entry.received_at = datetime.now(timezone.utc)
                logger.info(f"Revenue {entry_id} marked as RECEIVED")
                return True
        return False

    def get_stream_total(self, stream: RevenueStream) -> Decimal:
        """Obtient le total d'un stream"""
        return self.by_stream.get(stream, Decimal('0'))

    def get_current_month_target(self) -> Optional[MonthlyTarget]:
        """Obtient l'objectif du mois courant"""
        if self.current_month < 1 or self.current_month > 12:
            return None
        return self.roadmap[self.current_month - 1]

    def get_all_month_targets(self) -> List[Dict[str, Any]]:
        """Retourne tous les objectifs mensuels"""
        return [
            {
                'month': t.month,
                'target_eur': float(t.target_eur),
                'max_eur': float(t.max_eur),
                'actual_eur': float(t.actual_eur),
                'progress_pct': t.progress_pct,
                'reached': t.reached,
                'exceeded': t.is_exceeded,
                'focus': t.focus
            }
            for t in self.roadmap
        ]

    def get_revenue_by_period(self,
                             start_date: datetime,
                             end_date: datetime) -> List[RevenueEntry]:
        """Récupère les revenus pour une période"""
        return [
            entry for entry in self.revenue_entries
            if start_date <= entry.recorded_at <= end_date
        ]

    def get_mrr_breakdown(self) -> Dict[str, Any]:
        """Détail du MRR (Monthly Recurring Revenue)"""
        content_mrr = sum(
            e.amount_eur for e in self.revenue_entries
            if e.stream == RevenueStream.CONTENT_RECURRING and e.is_recurring and e.recurring_period == 'monthly'
        )

        saas_mrr = sum(
            e.amount_eur for e in self.revenue_entries
            if e.stream == RevenueStream.SAAS_NIS2 and e.is_recurring and e.recurring_period == 'monthly'
        )

        return {
            'total_mrr_eur': float(self.current_mrr_eur),
            'content_mrr_eur': float(content_mrr),
            'saas_mrr_eur': float(saas_mrr),
            'arr_projection_eur': float(self.current_mrr_eur * 12)
        }

    def get_cashflow_projection_90d(self) -> Dict[str, Any]:
        """Projection cashflow 90 jours"""
        # MRR * 3 mois
        recurring_projection = self.current_mrr_eur * 3

        # Deals one-shot moyens (estimation basée sur historique)
        avg_deal_size = Decimal('0')
        deal_count = 0

        for entry in self.revenue_entries:
            if entry.stream == RevenueStream.OUTREACH_DEALS and not entry.is_recurring:
                avg_deal_size += entry.amount_eur
                deal_count += 1

        if deal_count > 0:
            avg_deal_size = avg_deal_size / deal_count
        else:
            avg_deal_size = Decimal('15000')  # Estimation par défaut

        # Projection deals: 2 deals/mois * 3 mois
        deals_projection = avg_deal_size * 6

        # Audits: 1 audit/mois * 3 mois
        audit_projection = Decimal('15000') * 3

        total_projection = recurring_projection + deals_projection + audit_projection

        return {
            'projection_90d_eur': float(total_projection),
            'recurring_90d_eur': float(recurring_projection),
            'deals_90d_eur': float(deals_projection),
            'audits_90d_eur': float(audit_projection),
            'avg_deal_size_eur': float(avg_deal_size)
        }

    async def generate_daily_briefing(self) -> str:
        """
        Génère le briefing quotidien 8h00 Polynésie

        Returns:
            Texte du briefing formaté pour Telegram
        """
        today = datetime.now(timezone.utc).strftime('%d/%m/%Y')
        current_target = self.get_current_month_target()

        # Revenus hier
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        yesterday_start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday_end = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
        yesterday_revenues = self.get_revenue_by_period(yesterday_start, yesterday_end)
        yesterday_total = sum(e.amount_eur for e in yesterday_revenues)

        # Revenus ce mois
        month_revenues = [e for e in self.revenue_entries
                        if e.recorded_at.month == datetime.now(timezone.utc).month]
        month_total = sum(e.amount_eur for e in month_revenues)

        # MRR
        mrr_data = self.get_mrr_breakdown()

        # Projection 90j
        cashflow = self.get_cashflow_projection_90d()

        briefing = f"""📊 NAYA BRIEFING — {today}

💰 REVENUS
├── Hier : {yesterday_total} EUR
├── Ce mois : {month_total} EUR
└── Objectif M{self.current_month} : {current_target.target_eur if current_target else 0} EUR ({current_target.progress_pct if current_target else 0:.1f}% atteint)

📈 MRR (Recurring Revenue)
├── Total MRR : {mrr_data['total_mrr_eur']} EUR
├── Content B2B : {mrr_data['content_mrr_eur']} EUR
└── SaaS NIS2 : {mrr_data['saas_mrr_eur']} EUR

💵 PAR STREAM
├── Outreach Deals : {self.get_stream_total(RevenueStream.OUTREACH_DEALS)} EUR
├── Audits : {self.get_stream_total(RevenueStream.AUDITS)} EUR
├── Content B2B : {self.get_stream_total(RevenueStream.CONTENT_RECURRING)} EUR
└── SaaS NIS2 : {self.get_stream_total(RevenueStream.SAAS_NIS2)} EUR

🔮 PROJECTION 90 JOURS
└── Total estimé : {cashflow['projection_90d_eur']} EUR

🎯 FOCUS M{self.current_month}
{current_target.focus if current_target else 'N/A'}

📌 STATS
├── Total deals : {self.total_deals}
├── Clients uniques : {len(self.total_clients)}
└── Total collecté : {self.total_revenue_eur} EUR
"""

        return briefing

    async def send_daily_briefing_telegram(self) -> None:
        """Envoie le briefing quotidien via Telegram"""
        if not self.telegram_notifier:
            logger.warning("Telegram notifier not configured, skipping daily briefing")
            return

        briefing = await self.generate_daily_briefing()

        await self.telegram_notifier.send(briefing)
        logger.info("Daily briefing sent to Telegram")

    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques globales"""
        current_target = self.get_current_month_target()
        mrr = self.get_mrr_breakdown()

        return {
            'total_revenue_eur': float(self.total_revenue_eur),
            'total_deals': self.total_deals,
            'total_clients': len(self.total_clients),
            'current_month': self.current_month,
            'current_target_eur': float(current_target.target_eur) if current_target else 0,
            'current_progress_pct': current_target.progress_pct if current_target else 0,
            'target_reached': current_target.reached if current_target else False,
            'mrr_eur': mrr['total_mrr_eur'],
            'arr_projection_eur': mrr['arr_projection_eur'],
            'by_stream': {
                stream.value: float(amount)
                for stream, amount in self.by_stream.items()
            }
        }

    def advance_month(self) -> None:
        """Avance au mois suivant (à appeler automatiquement)"""
        if self.current_month < 12:
            self.current_month += 1
            logger.info(f"Advanced to M{self.current_month}")
        else:
            logger.warning("Already at M12, cannot advance further")


    # ------------------------------------------------------------------
    # V19.3 — Cycle unifié pour le multi_agent_orchestrator
    # ------------------------------------------------------------------
    async def run_cycle(self, received_payments: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Cycle revenue appelé par multi_agent_orchestrator.

        - Traque les paiements reçus depuis le dernier cycle
        - Met à jour les targets mensuels et le MRR
        - Envoie le briefing quotidien (Telegram) si configuré
        """
        received_payments = received_payments or []
        tracked = 0
        errors = 0

        for pay in received_payments:
            try:
                stream_key = str(pay.get('stream', 'CONSULTING_OT')).upper()
                try:
                    stream = RevenueStream[stream_key]
                except KeyError:
                    stream = RevenueStream.CONSULTING_OT
                await self.track_revenue(
                    stream=stream,
                    amount_eur=float(pay.get('amount_eur', 0)),
                    client_company=pay.get('client_company', 'unknown'),
                    description=pay.get('description', ''),
                    is_recurring=bool(pay.get('is_recurring', False)),
                    recurring_period=pay.get('recurring_period'),
                )
                tracked += 1
            except Exception as exc:
                errors += 1
                logger.warning(f"[revenue_tracker] track failed: {exc}")

        # Briefing quotidien
        try:
            await self.send_daily_briefing_telegram()
        except Exception:
            pass

        current_target = self.get_current_month_target()

        return {
            'total_tracked': tracked,
            'total_revenue_eur': float(self.total_revenue_eur),
            'current_mrr_eur': float(self.current_mrr_eur),
            'total_deals': self.total_deals,
            'total_clients': len(self.total_clients),
            'current_month': self.current_month,
            'month_target_progress_pct': current_target.progress_pct if current_target else 0.0,
            'cashflow_90d': self.get_cashflow_projection_90d(),
            'errors': errors,
        }


# ---------------------------------------------------------------------------
# Singleton partagé
# ---------------------------------------------------------------------------
def _build_revenue_tracker_agent() -> "RevenueTrackerAgent":
    """Construit l'instance avec les vraies dépendances."""
    telegram_notifier = None
    persistence_manager = None

    try:
        from NAYA_CORE.notifier import get_notifier
        telegram_notifier = get_notifier()
    except Exception:
        pass

    try:
        from PERSISTENCE.database.db_manager import DatabaseManager

        class _DBAdapter:
            """Adapter pour exposer save_revenue_entry au-dessus du DatabaseManager SQLite."""

            def __init__(self) -> None:
                self._db = DatabaseManager()

            async def save_revenue_entry(self, entry_id: str, entry_data: Dict[str, Any]) -> None:
                # Utilise la table naya_events pour stocker les revenus (WAL, thread-safe)
                try:
                    self._db.log_event(
                        event_type='revenue_tracked',
                        payload={
                            'entry_id': entry_id,
                            **{k: (str(v) if not isinstance(v, (int, float, str, bool, type(None))) else v)
                               for k, v in entry_data.items()},
                        },
                        source='revenue_tracker_agent',
                        priority='HIGH',
                    )
                except Exception as exc:
                    logger.warning(f"[revenue_tracker] DB save failed: {exc}")

        persistence_manager = _DBAdapter()
    except Exception as exc:
        logger.warning(f"[revenue_tracker] persistence unavailable: {exc}")

    return RevenueTrackerAgent(
        telegram_notifier=telegram_notifier,
        persistence_manager=persistence_manager,
    )


revenue_tracker_agent = _build_revenue_tracker_agent()


__all__ = [
    'RevenueTrackerAgent',
    'RevenueStream',
    'RevenueEntry',
    'MonthlyTarget',
    'OODA_ROADMAP',
    'revenue_tracker_agent',
]
