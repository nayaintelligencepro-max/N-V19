"""
NAYA ACCELERATION — SalesVelocityTracker
Compteur de ventes réelles encaissées : jour / mois / an.
Métriques velocity : taux conversion, ticket moyen, time-to-close.
Projections OODA basées sur la vélocité réelle observée.
"""

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger("NAYA.VELOCITY")

VELOCITY_DB = Path("data/validation/sales_velocity.json")
MIN_CONTRACT_VALUE_EUR = 1_000


@dataclass
class SaleRecord:
    """Vente réelle enregistrée."""
    sale_id: str
    company: str
    contact_email: str
    amount_eur: int
    sector: str
    pain_type: str
    payment_method: str
    time_to_close_hours: float   # Temps entre détection du pain et encaissement
    signal_source: str           # blitz_hunter | manual | referral
    recorded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict:
        return {
            "sale_id": self.sale_id,
            "company": self.company,
            "contact_email": self.contact_email,
            "amount_eur": self.amount_eur,
            "sector": self.sector,
            "pain_type": self.pain_type,
            "payment_method": self.payment_method,
            "time_to_close_hours": self.time_to_close_hours,
            "signal_source": self.signal_source,
            "recorded_at": self.recorded_at.isoformat(),
        }


@dataclass
class VelocityMetrics:
    """Métriques de vélocité calculées."""
    sales_today: int
    sales_this_month: int
    sales_this_year: int
    revenue_today_eur: int
    revenue_this_month_eur: int
    revenue_this_year_eur: int
    avg_ticket_eur: int
    avg_time_to_close_hours: float
    conversion_rate_pct: float      # % prospects → ventes
    daily_velocity: float           # ventes/jour sur 30j rolling
    monthly_run_rate_eur: int       # projection MRR basée sur velocity
    annual_run_rate_eur: int        # ARR projection
    top_sector: str
    top_pain_type: str
    projected_month_eur: int        # Projection fin de mois
    ooda_recommendation: str

    def to_dict(self) -> Dict:
        return {
            "sales_today": self.sales_today,
            "sales_this_month": self.sales_this_month,
            "sales_this_year": self.sales_this_year,
            "revenue_today_eur": self.revenue_today_eur,
            "revenue_this_month_eur": self.revenue_this_month_eur,
            "revenue_this_year_eur": self.revenue_this_year_eur,
            "avg_ticket_eur": self.avg_ticket_eur,
            "avg_time_to_close_hours": round(self.avg_time_to_close_hours, 1),
            "conversion_rate_pct": round(self.conversion_rate_pct, 1),
            "daily_velocity": round(self.daily_velocity, 2),
            "monthly_run_rate_eur": self.monthly_run_rate_eur,
            "annual_run_rate_eur": self.annual_run_rate_eur,
            "top_sector": self.top_sector,
            "top_pain_type": self.top_pain_type,
            "projected_month_eur": self.projected_month_eur,
            "ooda_recommendation": self.ooda_recommendation,
        }


class SalesVelocityTracker:
    """
    Track toutes les ventes réelles et calcule les métriques velocity.
    Projette les revenus basé sur la vélocité observée.
    """

    def __init__(self):
        VELOCITY_DB.parent.mkdir(parents=True, exist_ok=True)
        self._db: Dict = self._load()

    def record_sale(
        self,
        company: str,
        amount_eur: int,
        sector: str,
        pain_type: str,
        contact_email: str = "",
        payment_method: str = "paypal",
        time_to_close_hours: float = 0.0,
        signal_source: str = "blitz_hunter",
    ) -> SaleRecord:
        """
        Enregistre une vente réelle encaissée.
        Plancher : amount_eur >= MIN_CONTRACT_VALUE_EUR.
        """
        if amount_eur < MIN_CONTRACT_VALUE_EUR:
            raise ValueError(
                f"Montant {amount_eur} EUR inférieur au plancher "
                f"{MIN_CONTRACT_VALUE_EUR} EUR. INTERDIT."
            )

        import uuid
        sale_id = str(uuid.uuid4())[:16]
        record = SaleRecord(
            sale_id=sale_id,
            company=company,
            contact_email=contact_email,
            amount_eur=amount_eur,
            sector=sector,
            pain_type=pain_type,
            payment_method=payment_method,
            time_to_close_hours=time_to_close_hours,
            signal_source=signal_source,
        )
        self._db.setdefault("sales", []).append(record.to_dict())
        self._save()
        logger.info(
            f"Sale recorded: {company} | {amount_eur} EUR | {sector} | "
            f"close={time_to_close_hours:.1f}h"
        )
        return record

    def get_metrics(self, prospects_count: int = 0) -> VelocityMetrics:
        """Calcule toutes les métriques velocity."""
        sales = self._db.get("sales", [])
        now = datetime.now(timezone.utc)
        today = now.date()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        rolling_30d = now - timedelta(days=30)

        sales_today_list = []
        sales_month_list = []
        sales_year_list = []
        sales_30d_list = []
        amounts = []
        close_times = []
        sectors: Dict[str, int] = {}
        pain_types: Dict[str, int] = {}

        for s in sales:
            try:
                dt = datetime.fromisoformat(s["recorded_at"].replace("Z", "+00:00"))
            except Exception:
                continue
            amt = s.get("amount_eur", 0)
            amounts.append(amt)
            close_times.append(s.get("time_to_close_hours", 0))
            sectors[s.get("sector", "unknown")] = sectors.get(s.get("sector", "unknown"), 0) + 1
            pain_types[s.get("pain_type", "unknown")] = pain_types.get(s.get("pain_type", "unknown"), 0) + 1

            if dt.date() == today:
                sales_today_list.append(amt)
            if dt >= month_start:
                sales_month_list.append(amt)
            if dt >= year_start:
                sales_year_list.append(amt)
            if dt >= rolling_30d:
                sales_30d_list.append(amt)

        avg_ticket = int(sum(amounts) / max(len(amounts), 1))
        avg_close = sum(close_times) / max(len(close_times), 1)
        daily_velocity = len(sales_30d_list) / 30.0
        conv_rate = (len(sales) / max(prospects_count, 1)) * 100 if prospects_count > 0 else 0.0
        mrr = int(daily_velocity * 30 * avg_ticket)
        arr = mrr * 12

        # Projection fin de mois
        days_in_month = 30
        days_elapsed = max((now - month_start).days, 1)
        projected_month = int((sum(sales_month_list) / days_elapsed) * days_in_month)

        top_sector = max(sectors, key=sectors.get) if sectors else "iec62443"
        top_pain = max(pain_types, key=pain_types.get) if pain_types else "nis2_compliance"

        ooda = self._compute_ooda_recommendation(
            daily_velocity, avg_ticket, avg_close, len(sales_month_list)
        )

        return VelocityMetrics(
            sales_today=len(sales_today_list),
            sales_this_month=len(sales_month_list),
            sales_this_year=len(sales_year_list),
            revenue_today_eur=sum(sales_today_list),
            revenue_this_month_eur=sum(sales_month_list),
            revenue_this_year_eur=sum(sales_year_list),
            avg_ticket_eur=avg_ticket,
            avg_time_to_close_hours=avg_close,
            conversion_rate_pct=conv_rate,
            daily_velocity=daily_velocity,
            monthly_run_rate_eur=mrr,
            annual_run_rate_eur=arr,
            top_sector=top_sector,
            top_pain_type=top_pain,
            projected_month_eur=projected_month,
            ooda_recommendation=ooda,
        )

    def get_sales_by_period(self, period: str = "month") -> List[Dict]:
        """Retourne les ventes pour la période : today | week | month | year."""
        now = datetime.now(timezone.utc)
        cutoffs = {
            "today": now.replace(hour=0, minute=0, second=0, microsecond=0),
            "week": now - timedelta(days=7),
            "month": now.replace(day=1, hour=0, minute=0, second=0, microsecond=0),
            "year": now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0),
        }
        cutoff = cutoffs.get(period, cutoffs["month"])
        result = []
        for s in self._db.get("sales", []):
            try:
                dt = datetime.fromisoformat(s["recorded_at"].replace("Z", "+00:00"))
                if dt >= cutoff:
                    result.append(s)
            except Exception:
                pass
        return result

    # ── Persistence ────────────────────────────────────────────────────────

    def _load(self) -> Dict:
        if VELOCITY_DB.exists():
            try:
                with open(VELOCITY_DB, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"sales": [], "prospects_seen": 0}

    def _save(self) -> None:
        try:
            with open(VELOCITY_DB, "w") as f:
                json.dump(self._db, f, indent=2)
        except Exception as exc:
            logger.error(f"Velocity DB save failed: {exc}")

    def _compute_ooda_recommendation(
        self, velocity: float, avg_ticket: int, avg_close: float, sales_month: int
    ) -> str:
        """Recommandation OODA basée sur les métriques actuelles."""
        if velocity < 0.1:
            return "OBSERVE: Velocity quasi-nulle. Lancer BlitzHunter immédiatement sur 5 secteurs."
        if velocity < 0.3:
            return "ORIENT: Velocity faible. Augmenter fréquence hunt à 15min. Revoir score threshold."
        if avg_close > 48:
            return f"DECIDE: Time-to-close trop long ({avg_close:.0f}h). Activer InstantCloser après chaque signal."
        if avg_ticket < 10_000:
            return "ACT: Ticket moyen bas. Cibler secteurs énergie/défense pour upsell ≥ 40k EUR."
        if sales_month < 3:
            return "ORIENT: < 3 ventes/mois. Doubler le volume prospects. Activer séquences J+1/J+3."
        return f"ACT: Velocity={velocity:.2f}/j, Ticket={avg_ticket:,} EUR. Maintenir et upsell clients actifs."


_tracker_instance: Optional[SalesVelocityTracker] = None


def get_velocity_tracker() -> SalesVelocityTracker:
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = SalesVelocityTracker()
    return _tracker_instance
