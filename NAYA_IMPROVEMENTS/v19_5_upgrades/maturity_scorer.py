"""
NAYA SUPREME V19.5 — AMÉLIORATION #11 : MATURITY SCORER
═══════════════════════════════════════════════════════════
Évalue la maturité d'achat d'un prospect (readiness-to-buy).
Complète le PredictiveLeadScorer en ajoutant la dimension temporelle.

Un prospect HOT mais pas mûr = effort gaspillé.
Un prospect WARM mais mûr = quick win ignoré.

Signaux de maturité :
  - Budget voté / en cours d'allocation
  - Obligation réglementaire imminente (< 6 mois)
  - Incident de sécurité récent
  - Changement de direction / RSSI
  - Appel d'offres publié
  - Projet de transformation digitale en cours
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List

log = logging.getLogger("NAYA.MATURITY_SCORER")


class MaturityLevel(Enum):
    READY_NOW = "ready_now"
    READY_3_MONTHS = "ready_3_months"
    READY_6_MONTHS = "ready_6_months"
    READY_12_MONTHS = "ready_12_months"
    NOT_READY = "not_ready"


class BuyingSignal(Enum):
    BUDGET_VOTED = "budget_voted"
    REGULATORY_DEADLINE = "regulatory_deadline"
    SECURITY_INCIDENT = "security_incident"
    NEW_CISO = "new_ciso"
    RFP_PUBLISHED = "rfp_published"
    DIGITAL_TRANSFORMATION = "digital_transformation"
    COMPETITOR_BREACH = "competitor_breach"
    AUDIT_MANDATE = "audit_mandate"
    BOARD_PRESSURE = "board_pressure"
    INSURANCE_REQUIREMENT = "insurance_requirement"


SIGNAL_WEIGHTS = {
    BuyingSignal.BUDGET_VOTED: 0.25,
    BuyingSignal.REGULATORY_DEADLINE: 0.20,
    BuyingSignal.SECURITY_INCIDENT: 0.20,
    BuyingSignal.NEW_CISO: 0.10,
    BuyingSignal.RFP_PUBLISHED: 0.30,
    BuyingSignal.DIGITAL_TRANSFORMATION: 0.08,
    BuyingSignal.COMPETITOR_BREACH: 0.15,
    BuyingSignal.AUDIT_MANDATE: 0.25,
    BuyingSignal.BOARD_PRESSURE: 0.15,
    BuyingSignal.INSURANCE_REQUIREMENT: 0.18,
}

SIGNAL_URGENCY_DAYS = {
    BuyingSignal.BUDGET_VOTED: 90,
    BuyingSignal.REGULATORY_DEADLINE: 60,
    BuyingSignal.SECURITY_INCIDENT: 14,
    BuyingSignal.NEW_CISO: 120,
    BuyingSignal.RFP_PUBLISHED: 30,
    BuyingSignal.DIGITAL_TRANSFORMATION: 180,
    BuyingSignal.COMPETITOR_BREACH: 30,
    BuyingSignal.AUDIT_MANDATE: 60,
    BuyingSignal.BOARD_PRESSURE: 90,
    BuyingSignal.INSURANCE_REQUIREMENT: 90,
}


@dataclass
class MaturitySignalInput:
    signal: BuyingSignal
    detected_date: str
    confidence: float = 0.8
    details: str = ""


@dataclass
class MaturityAssessment:
    prospect_id: str
    maturity_level: MaturityLevel
    maturity_score: float
    signals_detected: List[MaturitySignalInput]
    recommended_action: str
    optimal_contact_window: str
    estimated_days_to_decision: int
    confidence: float


class MaturityScorer:
    """
    Évalue la maturité d'achat d'un prospect.
    """

    def __init__(self) -> None:
        self.assessments: Dict[str, MaturityAssessment] = {}
        self.stats = {
            "total_assessed": 0,
            "ready_now": 0,
            "ready_3_months": 0,
            "not_ready": 0,
        }

    def assess(
        self,
        prospect_id: str,
        signals: List[MaturitySignalInput],
        has_budget: bool = False,
        company_size: str = "pme",
    ) -> MaturityAssessment:
        score = 0.0
        for sig in signals:
            weight = SIGNAL_WEIGHTS.get(sig.signal, 0.05)
            score += weight * sig.confidence

        if has_budget:
            score += 0.20

        size_bonus = {
            "startup": -0.05,
            "pme": 0.0,
            "eti": 0.05,
            "grandes_entreprises": 0.10,
            "multinationale": 0.08,
        }
        score += size_bonus.get(company_size, 0.0)

        score = min(score, 1.0)

        if score >= 0.70:
            level = MaturityLevel.READY_NOW
            days = 14
            action = "CLOSER IMMÉDIAT — Proposer un RDV cette semaine"
        elif score >= 0.50:
            level = MaturityLevel.READY_3_MONTHS
            days = 60
            action = "NURTURING ACCÉLÉRÉ — Envoyer proposition + case study"
        elif score >= 0.30:
            level = MaturityLevel.READY_6_MONTHS
            days = 120
            action = "NURTURING STANDARD — Séquence email + contenu éducatif"
        elif score >= 0.15:
            level = MaturityLevel.READY_12_MONTHS
            days = 270
            action = "VEILLE — Ajouter à la watchlist, relancer dans 6 mois"
        else:
            level = MaturityLevel.NOT_READY
            days = 365
            action = "RECYCLER — Remettre dans le pool pour relance ultérieure"

        min_urgency = 365
        for sig in signals:
            urgency = SIGNAL_URGENCY_DAYS.get(sig.signal, 180)
            if urgency < min_urgency:
                min_urgency = urgency

        if min_urgency < days:
            days = min_urgency
            if days <= 30 and level != MaturityLevel.READY_NOW:
                level = MaturityLevel.READY_NOW
                action = "URGENCE — Signal détecté avec deadline < 30 jours"

        now = datetime.now(timezone.utc)
        from datetime import timedelta
        optimal_window = (now + timedelta(days=max(0, days - 14))).strftime("%Y-%m-%d")

        confidence = min(len(signals) * 0.15 + 0.30, 0.95)

        assessment = MaturityAssessment(
            prospect_id=prospect_id,
            maturity_level=level,
            maturity_score=round(score, 3),
            signals_detected=signals,
            recommended_action=action,
            optimal_contact_window=optimal_window,
            estimated_days_to_decision=days,
            confidence=round(confidence, 2),
        )

        self.assessments[prospect_id] = assessment
        self.stats["total_assessed"] += 1
        if level == MaturityLevel.READY_NOW:
            self.stats["ready_now"] += 1
        elif level in (MaturityLevel.READY_3_MONTHS, MaturityLevel.READY_6_MONTHS):
            self.stats["ready_3_months"] += 1
        else:
            self.stats["not_ready"] += 1

        log.info(
            "Maturity assessed: %s level=%s score=%.2f action=%s",
            prospect_id, level.value, score, action[:50],
        )
        return assessment

    def get_ready_now_prospects(self) -> List[MaturityAssessment]:
        return [
            a for a in self.assessments.values()
            if a.maturity_level == MaturityLevel.READY_NOW
        ]

    def get_stats(self) -> Dict[str, Any]:
        return dict(self.stats)


maturity_scorer = MaturityScorer()
