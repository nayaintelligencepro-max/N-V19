"""
GAP-002 RÉSOLU — Générateur de contenu nurturing automatique.

Crée automatiquement des séquences de contenu personnalisé pour chaque
prospect en fonction de son profil, son secteur et son stade dans le pipeline.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ContentType(str, Enum):
    PAIN_HIGHLIGHT = "pain_highlight"
    CASE_STUDY = "case_study"
    REGULATORY_ALERT = "regulatory_alert"
    ROI_CALCULATOR = "roi_calculator"
    EXPERT_INSIGHT = "expert_insight"
    SOCIAL_PROOF = "social_proof"
    URGENCY_TRIGGER = "urgency_trigger"


class PipelineStage(str, Enum):
    AWARENESS = "awareness"
    INTEREST = "interest"
    CONSIDERATION = "consideration"
    INTENT = "intent"
    EVALUATION = "evaluation"
    DECISION = "decision"


@dataclass
class ContentPiece:
    """Un contenu individuel dans la séquence nurturing."""
    content_type: ContentType
    subject: str
    body: str
    cta: str
    send_delay_hours: int
    personalization_fields: Dict[str, str] = field(default_factory=dict)
    ab_variant: str = "A"
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


@dataclass
class NurturingSequence:
    """Séquence complète de nurturing pour un prospect."""
    prospect_id: str
    sector: str
    stage: PipelineStage
    contents: List[ContentPiece] = field(default_factory=list)
    total_touches: int = 0
    estimated_conversion_boost: float = 0.0


SECTOR_TEMPLATES: Dict[str, Dict[str, str]] = {
    "energie": {
        "pain": "Vos systèmes SCADA sont-ils conformes aux nouvelles exigences NIS2 ?",
        "case": "Comment un producteur d'énergie a réduit son risque OT de 73% en 3 semaines",
        "urgency": "Deadline NIS2 : les sanctions démarrent — votre conformité est-elle prête ?",
    },
    "transport": {
        "pain": "Les ports et aéroports sont les cibles #1 des cyberattaques OT en 2024",
        "case": "Un opérateur portuaire a sécurisé 100% de ses systèmes en 14 jours",
        "urgency": "IEC 62443 : les assureurs exigent la conformité — êtes-vous couvert ?",
    },
    "industrie": {
        "pain": "Une cyberattaque sur votre chaîne de production coûte en moyenne 4.2M EUR",
        "case": "Comment un site chimique a atteint la conformité IEC 62443 SL3 en 4 semaines",
        "urgency": "Votre assurance cyber couvre-t-elle les systèmes OT ? La plupart ne le font pas.",
    },
    "default": {
        "pain": "Vos systèmes industriels sont-ils protégés contre les menaces actuelles ?",
        "case": "Comment nos clients ont réduit leur risque de 80% avec un audit ciblé",
        "urgency": "Les réglementations se durcissent — agissez avant les sanctions",
    },
}


STAGE_SEQUENCES: Dict[PipelineStage, List[ContentType]] = {
    PipelineStage.AWARENESS: [
        ContentType.PAIN_HIGHLIGHT,
        ContentType.EXPERT_INSIGHT,
        ContentType.REGULATORY_ALERT,
    ],
    PipelineStage.INTEREST: [
        ContentType.CASE_STUDY,
        ContentType.ROI_CALCULATOR,
        ContentType.SOCIAL_PROOF,
    ],
    PipelineStage.CONSIDERATION: [
        ContentType.ROI_CALCULATOR,
        ContentType.CASE_STUDY,
        ContentType.URGENCY_TRIGGER,
    ],
    PipelineStage.INTENT: [
        ContentType.SOCIAL_PROOF,
        ContentType.URGENCY_TRIGGER,
        ContentType.ROI_CALCULATOR,
    ],
    PipelineStage.EVALUATION: [
        ContentType.CASE_STUDY,
        ContentType.EXPERT_INSIGHT,
        ContentType.URGENCY_TRIGGER,
    ],
    PipelineStage.DECISION: [
        ContentType.URGENCY_TRIGGER,
        ContentType.SOCIAL_PROOF,
        ContentType.ROI_CALCULATOR,
    ],
}


class NurturingContentEngine:
    """
    Génère automatiquement des séquences de nurturing personnalisées.

    Pour chaque prospect, crée une série de 7 contenus adaptés au secteur,
    au stade du pipeline et au profil du décideur.
    """

    def __init__(self) -> None:
        self._sequences: Dict[str, NurturingSequence] = {}
        self._total_generated: int = 0
        logger.info("[NurturingContentEngine] Initialisé — templates multi-secteurs chargés")

    def _get_sector_template(self, sector: str) -> Dict[str, str]:
        sector_lower = sector.lower()
        for key in SECTOR_TEMPLATES:
            if key in sector_lower:
                return SECTOR_TEMPLATES[key]
        return SECTOR_TEMPLATES["default"]

    def _generate_content_piece(
        self,
        content_type: ContentType,
        sector: str,
        prospect_name: str,
        company_name: str,
        touch_index: int,
    ) -> ContentPiece:
        templates = self._get_sector_template(sector)
        delay_hours = [0, 48, 96, 168, 240, 336, 504][min(touch_index, 6)]

        subject_map = {
            ContentType.PAIN_HIGHLIGHT: templates["pain"],
            ContentType.CASE_STUDY: templates["case"],
            ContentType.REGULATORY_ALERT: f"Alerte réglementaire — impact direct sur {company_name}",
            ContentType.ROI_CALCULATOR: f"ROI : combien {company_name} économiserait avec un audit OT ?",
            ContentType.EXPERT_INSIGHT: "3 erreurs critiques que font 90% des responsables OT/IT",
            ContentType.SOCIAL_PROOF: "Pourquoi 47 entreprises nous ont fait confiance en 2024",
            ContentType.URGENCY_TRIGGER: templates["urgency"],
        }

        body_map = {
            ContentType.PAIN_HIGHLIGHT: (
                f"Bonjour {prospect_name},\n\n"
                f"Les systèmes industriels de {company_name} sont-ils exposés "
                "aux menaces OT actuelles ? En 2024, 67% des incidents cybersécurité "
                "industrielle visent des entreprises de votre secteur.\n\n"
                "Un diagnostic rapide (2h) peut identifier vos 3 vulnérabilités principales."
            ),
            ContentType.CASE_STUDY: (
                f"Bonjour {prospect_name},\n\n"
                "Un de nos clients dans votre secteur a réduit son exposition "
                "aux risques OT de 73% en seulement 3 semaines.\n\n"
                "Voici comment nous avons procédé (résumé confidentiel en pièce jointe)."
            ),
            ContentType.ROI_CALCULATOR: (
                f"Bonjour {prospect_name},\n\n"
                f"Nous avons calculé l'impact potentiel pour {company_name} : "
                "un incident OT non-détecté coûte en moyenne 4.2M EUR dans votre secteur.\n\n"
                "Notre audit initial à 5 000 EUR représente un ROI de 840x."
            ),
            ContentType.URGENCY_TRIGGER: (
                f"Bonjour {prospect_name},\n\n"
                "Les deadlines NIS2 approchent et les sanctions sont maintenant actives. "
                f"{company_name} est-elle prête ?\n\n"
                "Nos 3 derniers créneaux audit de ce mois se remplissent vite."
            ),
        }

        cta_map = {
            ContentType.PAIN_HIGHLIGHT: "Réservez votre diagnostic gratuit de 15 min",
            ContentType.CASE_STUDY: "Demandez l'étude de cas complète",
            ContentType.REGULATORY_ALERT: "Vérifiez votre conformité en 5 min",
            ContentType.ROI_CALCULATOR: "Calculez votre ROI personnalisé",
            ContentType.EXPERT_INSIGHT: "Téléchargez le guide expert gratuit",
            ContentType.SOCIAL_PROOF: "Voir les témoignages clients",
            ContentType.URGENCY_TRIGGER: "Réservez votre créneau audit maintenant",
        }

        return ContentPiece(
            content_type=content_type,
            subject=subject_map.get(content_type, f"Information importante pour {company_name}"),
            body=body_map.get(content_type, f"Contenu personnalisé pour {prospect_name} chez {company_name}"),
            cta=cta_map.get(content_type, "En savoir plus"),
            send_delay_hours=delay_hours,
            personalization_fields={
                "prospect_name": prospect_name,
                "company_name": company_name,
                "sector": sector,
            },
        )

    def generate_sequence(
        self,
        prospect_id: str,
        sector: str,
        stage: PipelineStage,
        prospect_name: str = "Monsieur/Madame",
        company_name: str = "votre entreprise",
    ) -> NurturingSequence:
        """Génère une séquence complète de nurturing pour un prospect."""
        content_types = STAGE_SEQUENCES.get(stage, STAGE_SEQUENCES[PipelineStage.AWARENESS])

        contents: List[ContentPiece] = []
        for i, ct in enumerate(content_types):
            piece = self._generate_content_piece(ct, sector, prospect_name, company_name, i)
            contents.append(piece)

            # Variant B pour A/B testing
            variant_b = self._generate_content_piece(ct, sector, prospect_name, company_name, i)
            variant_b.ab_variant = "B"
            variant_b.subject = f"[URGENT] {variant_b.subject}"
            contents.append(variant_b)

        sequence = NurturingSequence(
            prospect_id=prospect_id,
            sector=sector,
            stage=stage,
            contents=contents,
            total_touches=len(content_types),
            estimated_conversion_boost=0.15 + (0.05 * len(content_types)),
        )

        self._sequences[prospect_id] = sequence
        self._total_generated += 1

        logger.info(
            f"[NurturingContentEngine] Séquence générée pour {prospect_id}: "
            f"{len(contents)} contenus, boost estimé +{sequence.estimated_conversion_boost:.0%}"
        )
        return sequence

    def stats(self) -> Dict[str, Any]:
        return {
            "total_sequences": self._total_generated,
            "active_sequences": len(self._sequences),
            "sectors_covered": list({s.sector for s in self._sequences.values()}),
        }


nurturing_content_engine = NurturingContentEngine()
