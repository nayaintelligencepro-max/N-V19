"""
AMÉLIORATION REVENU #2 — Générateur de propositions instantanées.

Crée des propositions commerciales personnalisées en < 30 secondes,
adaptées au secteur, à la douleur détectée et au budget estimé du prospect.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ProposalSection:
    title: str
    content: str
    order: int


@dataclass
class Proposal:
    proposal_id: str
    prospect_name: str
    company_name: str
    sector: str
    pain_detected: str
    sections: List[ProposalSection]
    total_price_eur: float
    discount_pct: float
    validity_days: int
    payment_link: str
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    @property
    def final_price_eur(self) -> float:
        return round(self.total_price_eur * (1 - self.discount_pct / 100), 2)


SERVICE_CATALOGUE: Dict[str, Dict[str, Any]] = {
    "audit_iec62443": {
        "name": "Audit de conformité IEC 62443",
        "base_price_eur": 8000,
        "deliverables": [
            "Cartographie complète des assets OT/SCADA",
            "Évaluation de maturité SL1-SL4",
            "Rapport de conformité avec gap analysis",
            "Plan de remédiation priorisé (90 jours)",
        ],
        "timeline": "2-3 semaines",
    },
    "audit_nis2": {
        "name": "Accompagnement conformité NIS2",
        "base_price_eur": 12000,
        "deliverables": [
            "Diagnostic d'éligibilité NIS2",
            "Audit des 10 mesures de sécurité requises",
            "Politique de gestion des incidents",
            "Déclaration de conformité prête pour l'ANSSI",
            "Formation équipes dirigeantes",
        ],
        "timeline": "3-4 semaines",
    },
    "security_assessment": {
        "name": "Évaluation de sécurité OT/IT rapide",
        "base_price_eur": 5000,
        "deliverables": [
            "Scan de vulnérabilités systèmes industriels",
            "Tests d'intrusion ciblés (non-destructifs)",
            "Rapport exécutif avec top 10 risques",
            "Recommandations immédiates",
        ],
        "timeline": "1-2 semaines",
    },
    "formation_ot": {
        "name": "Formation cybersécurité OT/IT",
        "base_price_eur": 3000,
        "deliverables": [
            "Formation sur mesure (1-2 jours)",
            "Supports de formation personnalisés",
            "Exercice de simulation d'incident",
            "Certificat de participation",
        ],
        "timeline": "1 semaine (préparation + formation)",
    },
    "remediation_plan": {
        "name": "Plan de remédiation et accompagnement",
        "base_price_eur": 15000,
        "deliverables": [
            "Plan de remédiation détaillé 6-12 mois",
            "Accompagnement mise en oeuvre mensuel",
            "Revue trimestrielle de progression",
            "Reporting conformité pour la direction",
        ],
        "timeline": "6-12 mois (accompagnement continu)",
    },
}


class InstantProposalGenerator:
    """
    Génère des propositions commerciales personnalisées en < 30 secondes.

    Sélectionne automatiquement les services adaptés à la douleur détectée,
    calcule le prix optimal et génère un document structuré prêt à envoyer.
    """

    def __init__(self, payment_link: str = "https://deblock.com/a-ftp860") -> None:
        self._payment_link = payment_link
        self._proposals_generated: int = 0
        logger.info("[InstantProposalGenerator] Initialisé — catalogue de 5 services chargé")

    def _select_services(self, sector: str, pain: str, budget_eur: float) -> List[str]:
        """Sélectionne les services adaptés au prospect."""
        pain_lower = pain.lower()
        selected = []

        if "nis2" in pain_lower or "conformité" in pain_lower or "compliance" in pain_lower:
            selected.append("audit_nis2")
        if "iec" in pain_lower or "62443" in pain_lower or "scada" in pain_lower:
            selected.append("audit_iec62443")
        if "vuln" in pain_lower or "sécurité" in pain_lower or "security" in pain_lower:
            selected.append("security_assessment")
        if "formation" in pain_lower or "training" in pain_lower or "équipe" in pain_lower:
            selected.append("formation_ot")

        if not selected:
            selected.append("security_assessment")

        total = sum(SERVICE_CATALOGUE[s]["base_price_eur"] for s in selected)
        if total > budget_eur * 1.5 and len(selected) > 1:
            selected = selected[:1]

        return selected

    def _calculate_discount(self, total_eur: float, service_count: int) -> float:
        """Calcule la remise selon le volume."""
        if service_count >= 3:
            return 15.0
        if service_count >= 2:
            return 10.0
        if total_eur >= 15000:
            return 5.0
        return 0.0

    def generate(
        self,
        prospect_name: str,
        company_name: str,
        sector: str,
        pain_detected: str,
        budget_estimate_eur: float = 10000,
    ) -> Proposal:
        """Génère une proposition commerciale personnalisée."""
        services = self._select_services(sector, pain_detected, budget_estimate_eur)

        sections: List[ProposalSection] = []

        sections.append(ProposalSection(
            title="Contexte et compréhension de vos enjeux",
            content=(
                f"Suite à notre analyse, nous avons identifié que {company_name} "
                f"fait face à des enjeux critiques dans le domaine : {pain_detected}. "
                f"Dans le secteur {sector}, ces problématiques représentent un risque "
                f"estimé à {budget_estimate_eur * 10:,.0f} EUR en cas d'incident non-traité."
            ),
            order=1,
        ))

        total_price = 0.0
        for i, service_key in enumerate(services):
            service = SERVICE_CATALOGUE[service_key]
            total_price += service["base_price_eur"]
            deliverables_text = "\n".join(f"  - {d}" for d in service["deliverables"])
            sections.append(ProposalSection(
                title=f"Service proposé {i+1} : {service['name']}",
                content=(
                    f"Prix : {service['base_price_eur']:,.0f} EUR HT\n"
                    f"Durée : {service['timeline']}\n"
                    f"Livrables :\n{deliverables_text}"
                ),
                order=i + 2,
            ))

        discount = self._calculate_discount(total_price, len(services))

        sections.append(ProposalSection(
            title="Conditions et paiement",
            content=(
                f"Prix total : {total_price:,.0f} EUR HT"
                f"{f' (remise {discount:.0f}% appliquée : {total_price * (1 - discount/100):,.0f} EUR HT)' if discount else ''}\n"
                f"Validité : 30 jours\n"
                f"Paiement : Deblock, PayPal ou virement\n"
                f"Garantie : Satisfaction ou remboursement sous 14 jours"
            ),
            order=len(services) + 2,
        ))

        proposal = Proposal(
            proposal_id=f"PROP-{self._proposals_generated + 1:04d}",
            prospect_name=prospect_name,
            company_name=company_name,
            sector=sector,
            pain_detected=pain_detected,
            sections=sections,
            total_price_eur=total_price,
            discount_pct=discount,
            validity_days=30,
            payment_link=self._payment_link,
        )

        self._proposals_generated += 1
        logger.info(
            f"[InstantProposalGenerator] Proposition {proposal.proposal_id} générée: "
            f"{company_name} — {total_price:,.0f} EUR ({len(services)} services)"
        )
        return proposal

    def stats(self) -> Dict[str, Any]:
        return {
            "proposals_generated": self._proposals_generated,
            "services_available": len(SERVICE_CATALOGUE),
        }


instant_proposal_generator = InstantProposalGenerator()
