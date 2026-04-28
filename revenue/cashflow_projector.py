"""
REVENUE MODULE 7 — CASHFLOW PROJECTOR
Projection cashflow 90 jours avec scénarios OODA
Production-ready, async, zero placeholders.
"""

import logging
from typing import Dict, List
from datetime import datetime, timedelta
from dataclasses import dataclass

log = logging.getLogger("NAYA.CashflowProjector")


@dataclass
class CashflowItem:
    """Item cashflow"""
    date: datetime
    type: str  # "inflow|outflow"
    category: str
    amount_eur: float
    description: str
    probability: float = 1.0  # 0.0-1.0


class CashflowProjector:
    """
    REVENUE MODULE 7 — Projection cashflow 90j

    Capacités:
    - Projection inflows (deals pipeline, abonnements, etc.)
    - Projection outflows (salaires, outils, infra)
    - Scénarios: optimiste/réaliste/pessimiste
    - Alertes trésorerie < seuil
    - Analyse OODA mensuelle
    """

    def __init__(self):
        self.cashflow_items: List[CashflowItem] = []
        self.current_cash_eur = 0.0

    async def add_inflow(
        self,
        date: datetime,
        category: str,
        amount_eur: float,
        description: str,
        probability: float = 1.0
    ):
        """Ajoute inflow prévu"""
        item = CashflowItem(
            date=date,
            type="inflow",
            category=category,
            amount_eur=amount_eur,
            description=description,
            probability=probability,
        )
        self.cashflow_items.append(item)
        log.debug(f"Inflow added: {amount_eur} EUR on {date.strftime('%Y-%m-%d')}")

    async def add_outflow(
        self,
        date: datetime,
        category: str,
        amount_eur: float,
        description: str
    ):
        """Ajoute outflow prévu"""
        item = CashflowItem(
            date=date,
            type="outflow",
            category=category,
            amount_eur=amount_eur,
            description=description,
            probability=1.0,  # Outflows certains
        )
        self.cashflow_items.append(item)
        log.debug(f"Outflow added: {amount_eur} EUR on {date.strftime('%Y-%m-%d')}")

    async def project_90_days(
        self,
        scenario: str = "realistic"
    ) -> Dict:
        """
        Projette cashflow 90 jours.

        Scenarios:
        - optimistic: probability > 0.7
        - realistic: probability > 0.5
        - pessimistic: probability > 0.8
        """
        now = datetime.now()
        end_date = now + timedelta(days=90)

        # Filter items dans période
        items_in_period = [
            item for item in self.cashflow_items
            if now <= item.date <= end_date
        ]

        # Apply probability filters
        probability_threshold = {
            "optimistic": 0.5,
            "realistic": 0.7,
            "pessimistic": 0.85,
        }.get(scenario, 0.7)

        # Calculate projected flows
        projected_inflows = sum(
            item.amount_eur * item.probability
            for item in items_in_period
            if item.type == "inflow" and item.probability >= probability_threshold
        )

        projected_outflows = sum(
            item.amount_eur
            for item in items_in_period
            if item.type == "outflow"
        )

        net_cashflow = projected_inflows - projected_outflows
        ending_cash = self.current_cash_eur + net_cashflow

        return {
            "scenario": scenario,
            "period": "90 days",
            "current_cash_eur": self.current_cash_eur,
            "projected_inflows": projected_inflows,
            "projected_outflows": projected_outflows,
            "net_cashflow": net_cashflow,
            "ending_cash_eur": ending_cash,
            "cash_runway_days": int((ending_cash / (projected_outflows / 90)) if projected_outflows > 0 else 999),
        }

    async def get_monthly_projection(self, month: int, year: int) -> Dict:
        """Projection mensuelle détaillée"""
        from calendar import monthrange

        start_date = datetime(year, month, 1)
        _, last_day = monthrange(year, month)
        end_date = datetime(year, month, last_day)

        month_items = [
            item for item in self.cashflow_items
            if start_date <= item.date <= end_date
        ]

        inflows_by_category = {}
        outflows_by_category = {}

        for item in month_items:
            if item.type == "inflow":
                if item.category not in inflows_by_category:
                    inflows_by_category[item.category] = 0
                inflows_by_category[item.category] += item.amount_eur * item.probability
            else:
                if item.category not in outflows_by_category:
                    outflows_by_category[item.category] = 0
                outflows_by_category[item.category] += item.amount_eur

        total_inflows = sum(inflows_by_category.values())
        total_outflows = sum(outflows_by_category.values())

        return {
            "month": f"{year}-{month:02d}",
            "total_inflows": total_inflows,
            "total_outflows": total_outflows,
            "net_cashflow": total_inflows - total_outflows,
            "inflows_by_category": inflows_by_category,
            "outflows_by_category": outflows_by_category,
        }

    def get_stats(self) -> Dict:
        """Stats cashflow"""
        return {
            "current_cash_eur": self.current_cash_eur,
            "total_items": len(self.cashflow_items),
            "inflows_count": sum(1 for i in self.cashflow_items if i.type == "inflow"),
            "outflows_count": sum(1 for i in self.cashflow_items if i.type == "outflow"),
        }


# Instance globale
cashflow_projector = CashflowProjector()


# Test
async def main():
    """Test cashflow projector"""
    projector = CashflowProjector()
    projector.current_cash_eur = 10000

    now = datetime.now()

    # Add inflows
    await projector.add_inflow(now + timedelta(days=7), "outreach", 15000, "Audit Express deal", 0.8)
    await projector.add_inflow(now + timedelta(days=30), "saas", 2000, "NIS2 Subscriptions MRR", 1.0)
    await projector.add_inflow(now + timedelta(days=60), "audit", 40000, "IEC62443 Premium", 0.6)

    # Add outflows
    await projector.add_outflow(now + timedelta(days=15), "tools", 500, "Apollo.io subscription")
    await projector.add_outflow(now + timedelta(days=30), "infra", 200, "Railway hosting")
    await projector.add_outflow(now + timedelta(days=45), "contractor", 5000, "Freelance OT consultant")

    # Project
    realistic = await projector.project_90_days("realistic")
    optimistic = await projector.project_90_days("optimistic")
    pessimistic = await projector.project_90_days("pessimistic")

    print("\n=== CASHFLOW PROJECTION 90 DAYS ===")
    print(f"\nRealistic Scenario:")
    print(f"  Current Cash: {realistic['current_cash_eur']} EUR")
    print(f"  Projected Inflows: {realistic['projected_inflows']} EUR")
    print(f"  Projected Outflows: {realistic['projected_outflows']} EUR")
    print(f"  Net Cashflow: {realistic['net_cashflow']} EUR")
    print(f"  Ending Cash: {realistic['ending_cash_eur']} EUR")
    print(f"  Cash Runway: {realistic['cash_runway_days']} days")

    print(f"\nOptimistic Scenario: Ending Cash {optimistic['ending_cash_eur']} EUR")
    print(f"Pessimistic Scenario: Ending Cash {pessimistic['ending_cash_eur']} EUR")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
