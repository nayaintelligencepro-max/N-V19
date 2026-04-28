"""
AMÉLIORATION REVENU #6 — Gestionnaire de revenus récurrents (MRR/ARR).

Transforme les missions ponctuelles en revenus récurrents via des abonnements
de monitoring continu, conformité et accompagnement.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class Subscription:
    """Abonnement récurrent d'un client."""
    subscription_id: str
    client_id: str
    plan: str
    mrr_eur: float
    start_date: str
    status: str  # active / paused / cancelled / churned
    months_active: int = 0
    churn_risk_score: float = 0.0
    next_renewal: str = ""
    lifetime_value_eur: float = 0.0


SUBSCRIPTION_PLANS: Dict[str, Dict[str, Any]] = {
    "essential": {
        "name": "NAYA Essential",
        "mrr_eur": 500,
        "features": [
            "Veille réglementaire mensuelle (NIS2, IEC 62443)",
            "Rapport de sécurité trimestriel",
            "Support email 48h",
            "1 scan de vulnérabilités par trimestre",
        ],
    },
    "professional": {
        "name": "NAYA Professional",
        "mrr_eur": 1500,
        "features": [
            "Veille réglementaire hebdomadaire",
            "Monitoring continu des assets OT",
            "Rapport de sécurité mensuel",
            "Support prioritaire 24h",
            "2 scans de vulnérabilités par mois",
            "Alertes incidents en temps réel",
        ],
    },
    "enterprise": {
        "name": "NAYA Enterprise",
        "mrr_eur": 3500,
        "features": [
            "Veille réglementaire en temps réel",
            "Monitoring 24/7 de tous les assets OT/IT",
            "Rapport de sécurité hebdomadaire",
            "Support dédié avec SLA 4h",
            "Scans illimités + tests d'intrusion trimestriels",
            "Conformité continue automatisée",
            "Formation équipe incluse (2 sessions/an)",
            "Accès dashboard temps réel personnalisé",
        ],
    },
}


class RecurringRevenueManager:
    """
    Gère le portefeuille d'abonnements récurrents.

    Objectif: transformer chaque client ponctuel en client récurrent
    pour construire un MRR prévisible et croissant.
    """

    def __init__(self) -> None:
        self._subscriptions: Dict[str, Subscription] = {}
        self._total_mrr: float = 0.0
        self._churn_prevented: int = 0
        logger.info("[RecurringRevenueManager] Initialisé — 3 plans disponibles")

    def create_subscription(
        self,
        client_id: str,
        plan: str = "professional",
    ) -> Subscription:
        """Crée un nouvel abonnement pour un client."""
        plan_data = SUBSCRIPTION_PLANS.get(plan, SUBSCRIPTION_PLANS["professional"])

        sub_id = f"SUB_{client_id}_{plan}"
        now = datetime.now(timezone.utc).isoformat()

        sub = Subscription(
            subscription_id=sub_id,
            client_id=client_id,
            plan=plan,
            mrr_eur=plan_data["mrr_eur"],
            start_date=now,
            status="active",
        )

        self._subscriptions[sub_id] = sub
        self._total_mrr += sub.mrr_eur

        logger.info(f"[RecurringRevenueManager] Nouvel abonnement {sub_id}: {plan_data['name']} ({plan_data['mrr_eur']} EUR/mois)")
        return sub

    def detect_churn_risk(self) -> List[Subscription]:
        """Détecte les abonnements à risque de churn."""
        at_risk: List[Subscription] = []
        for sub in self._subscriptions.values():
            if sub.status != "active":
                continue

            risk_score = 0.0
            if sub.months_active <= 2:
                risk_score += 0.3
            if sub.plan == "essential":
                risk_score += 0.2

            sub.churn_risk_score = min(1.0, risk_score)
            if risk_score >= 0.4:
                at_risk.append(sub)

        at_risk.sort(key=lambda s: s.churn_risk_score, reverse=True)
        return at_risk

    def prevent_churn(self, subscription_id: str, action: str = "discount_20pct") -> bool:
        """Applique une action de rétention pour prévenir le churn."""
        sub = self._subscriptions.get(subscription_id)
        if not sub:
            return False

        if action == "discount_20pct":
            sub.mrr_eur *= 0.8
            self._churn_prevented += 1
        elif action == "upgrade_free_month":
            self._churn_prevented += 1
        elif action == "personal_call":
            self._churn_prevented += 1

        logger.info(f"[RecurringRevenueManager] Rétention {subscription_id}: {action}")
        return True

    def get_mrr_breakdown(self) -> Dict[str, Any]:
        """Retourne le détail du MRR par plan."""
        breakdown: Dict[str, float] = {}
        for sub in self._subscriptions.values():
            if sub.status == "active":
                breakdown[sub.plan] = breakdown.get(sub.plan, 0) + sub.mrr_eur

        return {
            "total_mrr_eur": sum(breakdown.values()),
            "total_arr_eur": sum(breakdown.values()) * 12,
            "by_plan": breakdown,
            "active_subscriptions": len([s for s in self._subscriptions.values() if s.status == "active"]),
            "churn_prevented": self._churn_prevented,
        }

    def stats(self) -> Dict[str, Any]:
        return self.get_mrr_breakdown()


recurring_revenue_manager = RecurringRevenueManager()
