"""
NAYA SUPREME V19.5 — AMÉLIORATION #6 : SILENT PROSPECT REACTIVATOR
═══════════════════════════════════════════════════════════════════════
Récupère les prospects silencieux qui n'ont pas répondu
mais n'ont pas dit non. Relance avec un nouvel angle.

Stratégie : 40-60% des deals B2B se ferment après le 5ème contact.
  - J+30 : Relance avec nouvel incident sécurité dans leur secteur
  - J+60 : Relance avec nouvelle réglementation applicable
  - J+90 : Relance avec case study similaire
  - J+180 : Dernière tentative avec offre exclusive

PRINCIPE ZÉRO DÉCHET : Aucun prospect n'est jamais abandonné.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List

log = logging.getLogger("NAYA.REACTIVATOR")


class SilenceReason(Enum):
    NO_RESPONSE = "no_response"
    READ_NO_REPLY = "read_no_reply"
    PARTIAL_INTEREST = "partial_interest"
    TIMING_NOT_RIGHT = "timing_not_right"
    BUDGET_DEFERRED = "budget_deferred"


class ReactivationAngle(Enum):
    SECURITY_INCIDENT = "security_incident"
    REGULATORY_UPDATE = "regulatory_update"
    CASE_STUDY = "case_study"
    EXCLUSIVE_OFFER = "exclusive_offer"
    INDUSTRY_REPORT = "industry_report"
    PEER_PRESSURE = "peer_pressure"


@dataclass
class SilentProspect:
    prospect_id: str
    name: str
    company: str
    email: str
    sector: str
    last_contact_date: str
    sequence_stage: int
    total_emails_sent: int
    total_opens: int
    estimated_value_eur: float
    silence_reason: SilenceReason = SilenceReason.NO_RESPONSE
    reactivation_attempts: int = 0
    last_reactivation_date: str = ""


@dataclass
class ReactivationPlan:
    prospect_id: str
    angle: ReactivationAngle
    subject: str
    body_preview: str
    send_date: str
    follow_up_date: str
    confidence: float


REACTIVATION_SCHEDULE = [
    {"days_since_silence": 30, "angle": ReactivationAngle.SECURITY_INCIDENT},
    {"days_since_silence": 60, "angle": ReactivationAngle.REGULATORY_UPDATE},
    {"days_since_silence": 90, "angle": ReactivationAngle.CASE_STUDY},
    {"days_since_silence": 180, "angle": ReactivationAngle.EXCLUSIVE_OFFER},
]

ANGLE_TEMPLATES = {
    ReactivationAngle.SECURITY_INCIDENT: {
        "subject": "Incident de sécurité dans votre secteur — {sector}",
        "body": (
            "Bonjour {name},\n\n"
            "Un incident de sécurité majeur a récemment touché le secteur {sector}. "
            "Les entreprises non conformes IEC 62443 sont les premières exposées.\n\n"
            "Nous proposons un diagnostic rapide (2h) pour évaluer votre exposition. "
            "Sans engagement.\n\n"
            "Êtes-vous disponible cette semaine pour un échange de 15 minutes ?"
        ),
    },
    ReactivationAngle.REGULATORY_UPDATE: {
        "subject": "NIS2 — Nouvelle échéance pour {sector}",
        "body": (
            "Bonjour {name},\n\n"
            "La directive NIS2 impose de nouvelles obligations aux entreprises du secteur {sector} "
            "dès octobre 2024. Les sanctions peuvent atteindre 10M€ ou 2% du CA mondial.\n\n"
            "Notre audit de conformité permet d'identifier les écarts en 2 semaines "
            "et de construire un plan de remédiation priorisé.\n\n"
            "Pouvons-nous en discuter ?"
        ),
    },
    ReactivationAngle.CASE_STUDY: {
        "subject": "Comment une entreprise de votre secteur a sécurisé ses systèmes OT",
        "body": (
            "Bonjour {name},\n\n"
            "Nous venons de terminer un audit IEC 62443 pour une entreprise similaire "
            "à {company} dans le secteur {sector}.\n\n"
            "Résultat : 23 vulnérabilités critiques identifiées et corrigées en 3 semaines. "
            "ROI estimé : 15x le coût de l'audit en risques évités.\n\n"
            "Souhaitez-vous recevoir le résumé anonymisé ?"
        ),
    },
    ReactivationAngle.EXCLUSIVE_OFFER: {
        "subject": "Offre exclusive — Audit de sécurité pour {company}",
        "body": (
            "Bonjour {name},\n\n"
            "Nous réservons 3 créneaux d'audit prioritaires ce mois-ci pour les entreprises "
            "du secteur {sector}.\n\n"
            "Offre spéciale : audit complet IEC 62443 avec -15% et livraison en 2 semaines.\n\n"
            "Cette offre expire dans 7 jours. "
            "Répondez simplement 'intéressé' pour réserver votre créneau."
        ),
    },
    ReactivationAngle.INDUSTRY_REPORT: {
        "subject": "Rapport gratuit — État de la cybersécurité OT {sector} 2024",
        "body": (
            "Bonjour {name},\n\n"
            "Nous venons de publier notre rapport annuel sur l'état de la cybersécurité "
            "industrielle dans le secteur {sector}.\n\n"
            "Points clés : 67% des entreprises ont au moins une vulnérabilité critique non patchée. "
            "Le coût moyen d'un incident est de 2.8M€.\n\n"
            "Souhaitez-vous recevoir le rapport complet ?"
        ),
    },
    ReactivationAngle.PEER_PRESSURE: {
        "subject": "Vos concurrents investissent dans la sécurité OT",
        "body": (
            "Bonjour {name},\n\n"
            "Selon nos données, 3 de vos concurrents directs dans le secteur {sector} "
            "ont lancé des programmes de conformité IEC 62443 cette année.\n\n"
            "La cybersécurité industrielle devient un avantage compétitif. "
            "Ne pas agir est un risque en soi.\n\n"
            "Un échange de 15 minutes pour évaluer votre position ?"
        ),
    },
}


class SilentProspectReactivator:
    """
    Réactive les prospects silencieux avec des angles de relance
    personnalisés et temporellement espacés.
    """

    def __init__(self) -> None:
        self.prospects: Dict[str, SilentProspect] = {}
        self.plans: List[ReactivationPlan] = []
        self.stats = {
            "total_prospects": 0,
            "reactivations_sent": 0,
            "reactivations_replied": 0,
            "reactivations_converted": 0,
            "recovered_value_eur": 0.0,
        }

    def register_silent_prospect(self, prospect: SilentProspect) -> None:
        self.prospects[prospect.prospect_id] = prospect
        self.stats["total_prospects"] = len(self.prospects)

    def scan_for_reactivation(self) -> List[ReactivationPlan]:
        now = datetime.now(timezone.utc)
        plans = []

        for pid, prospect in self.prospects.items():
            if prospect.reactivation_attempts >= len(REACTIVATION_SCHEDULE):
                continue

            last_contact = datetime.fromisoformat(
                prospect.last_reactivation_date or prospect.last_contact_date
            )
            if last_contact.tzinfo is None:
                last_contact = last_contact.replace(tzinfo=timezone.utc)
            days_silent = (now - last_contact).days

            schedule_entry = None
            for entry in REACTIVATION_SCHEDULE:
                if days_silent >= entry["days_since_silence"]:
                    if prospect.reactivation_attempts < REACTIVATION_SCHEDULE.index(entry) + 1:
                        schedule_entry = entry
                        break

            if not schedule_entry:
                continue

            angle = schedule_entry["angle"]
            template = ANGLE_TEMPLATES.get(angle, ANGLE_TEMPLATES[ReactivationAngle.SECURITY_INCIDENT])

            subject = template["subject"].format(
                name=prospect.name, company=prospect.company, sector=prospect.sector,
            )
            body = template["body"].format(
                name=prospect.name, company=prospect.company, sector=prospect.sector,
            )

            confidence = 0.3 - (prospect.reactivation_attempts * 0.05)
            if prospect.total_opens > 0:
                confidence += 0.15
            if prospect.silence_reason == SilenceReason.PARTIAL_INTEREST:
                confidence += 0.10
            confidence = max(confidence, 0.05)

            plan = ReactivationPlan(
                prospect_id=pid,
                angle=angle,
                subject=subject,
                body_preview=body[:200],
                send_date=now.isoformat(),
                follow_up_date=(now + timedelta(days=7)).isoformat(),
                confidence=confidence,
            )
            plans.append(plan)

        self.plans.extend(plans)
        return plans

    def mark_reactivation_sent(self, prospect_id: str) -> None:
        prospect = self.prospects.get(prospect_id)
        if prospect:
            prospect.reactivation_attempts += 1
            prospect.last_reactivation_date = datetime.now(timezone.utc).isoformat()
            self.stats["reactivations_sent"] += 1

    def mark_reactivation_replied(self, prospect_id: str) -> None:
        self.stats["reactivations_replied"] += 1

    def mark_reactivation_converted(self, prospect_id: str, value_eur: float) -> None:
        self.stats["reactivations_converted"] += 1
        self.stats["recovered_value_eur"] += value_eur
        if prospect_id in self.prospects:
            del self.prospects[prospect_id]

    def get_stats(self) -> Dict[str, Any]:
        return dict(self.stats)

    def generate_telegram_report(self) -> str:
        s = self.stats
        reply_rate = (
            s["reactivations_replied"] / s["reactivations_sent"] * 100
            if s["reactivations_sent"] > 0 else 0
        )
        return (
            "NAYA REACTIVATOR — Rapport\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Prospects silencieux : {s['total_prospects']}\n"
            f"Relances envoyées    : {s['reactivations_sent']}\n"
            f"Réponses obtenues    : {s['reactivations_replied']} ({reply_rate:.0f}%)\n"
            f"Convertis            : {s['reactivations_converted']}\n"
            f"Valeur récupérée     : {s['recovered_value_eur']:,.0f}€\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )


silent_prospect_reactivator = SilentProspectReactivator()
