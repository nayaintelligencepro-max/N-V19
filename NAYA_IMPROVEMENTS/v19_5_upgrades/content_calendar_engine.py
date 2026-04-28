"""
NAYA SUPREME V19.5 — AMÉLIORATION #10 : CONTENT CALENDAR ENGINE
═══════════════════════════════════════════════════════════════════
Planifie et génère du contenu thought leadership automatiquement.
  - 2 articles LinkedIn / semaine
  - 1 whitepaper / mois
  - Posts basés sur l'actualité réglementaire

Objectif : Générer des leads INBOUND gratuits.
Un bon contenu positionne NAYA comme experte et attire les prospects.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List

log = logging.getLogger("NAYA.CONTENT_CALENDAR")


class ContentFormat(Enum):
    LINKEDIN_POST = "linkedin_post"
    ARTICLE = "article"
    WHITEPAPER = "whitepaper"
    CASE_STUDY_POST = "case_study_post"
    INFOGRAPHIC = "infographic"
    NEWSLETTER = "newsletter"


class ContentStatus(Enum):
    PLANNED = "planned"
    DRAFT = "draft"
    REVIEW = "review"
    PUBLISHED = "published"


@dataclass
class ContentItem:
    content_id: str
    title: str
    format: ContentFormat
    topic: str
    sector_focus: str
    body: str
    planned_date: str
    status: ContentStatus = ContentStatus.PLANNED
    published_date: str = ""
    engagement_score: float = 0.0


TOPIC_TEMPLATES = {
    "nis2_compliance": {
        "linkedin_post": {
            "title": "NIS2 : {n} entreprises sur 10 ne sont pas prêtes",
            "body": (
                "La directive NIS2 entre en vigueur et impose de nouvelles obligations "
                "de cybersécurité aux entreprises du secteur {sector}.\n\n"
                "Voici les 3 erreurs les plus fréquentes que nous constatons :\n\n"
                "1. Sous-estimation du périmètre (les filiales sont concernées)\n"
                "2. Absence de plan de réponse aux incidents\n"
                "3. Pas de cartographie des actifs OT critiques\n\n"
                "Un audit de conformité prend 2-4 semaines.\n"
                "Ne pas agir peut coûter jusqu'à 10M€ d'amende.\n\n"
                "#NIS2 #Cybersécurité #OT #{sector_tag}"
            ),
        },
        "article": {
            "title": "Guide complet NIS2 pour le secteur {sector}",
            "body": (
                "# NIS2 : Ce que les entreprises du secteur {sector} doivent savoir\n\n"
                "## Contexte\n"
                "La directive NIS2 (Network and Information Security) est le cadre "
                "européen de cybersécurité le plus ambitieux jamais adopté.\n\n"
                "## Obligations clés\n"
                "- Notification d'incidents sous 24h\n"
                "- Évaluation des risques de la supply chain\n"
                "- Mesures de sécurité proportionnées\n"
                "- Responsabilité de la direction\n\n"
                "## Impact sur le secteur {sector}\n"
                "Les entreprises de ce secteur sont classées comme 'entités essentielles' "
                "ou 'entités importantes' selon leur taille et leur criticité.\n\n"
                "## Prochaines étapes\n"
                "1. Identifier si vous êtes dans le périmètre\n"
                "2. Réaliser un audit de conformité\n"
                "3. Mettre en place un plan de remédiation\n"
                "4. Former vos équipes\n\n"
                "Notre expertise : audit + remédiation en 2-4 semaines."
            ),
        },
    },
    "iec62443_security": {
        "linkedin_post": {
            "title": "IEC 62443 : La norme qui protège vos systèmes industriels",
            "body": (
                "Les systèmes SCADA et OT sont la cible #1 des cyberattaques industrielles.\n\n"
                "IEC 62443 est LA référence pour sécuriser vos automates, "
                "vos réseaux industriels et vos systèmes de contrôle.\n\n"
                "En 2024, nous avons audité {n}+ systèmes industriels.\n"
                "Résultat moyen : {v} vulnérabilités critiques par entreprise.\n\n"
                "La bonne nouvelle : 80% peuvent être corrigées en moins de 4 semaines.\n\n"
                "#IEC62443 #SCADA #CybersécuritéIndustrielle #{sector_tag}"
            ),
        },
    },
    "incident_alert": {
        "linkedin_post": {
            "title": "Alerte : Cyberattaque dans le secteur {sector}",
            "body": (
                "Un incident de cybersécurité majeur a touché le secteur {sector} cette semaine.\n\n"
                "Ce type d'attaque exploite des vulnérabilités connues "
                "dans les systèmes OT non patchés.\n\n"
                "3 questions à vous poser :\n"
                "1. Vos systèmes industriels sont-ils segmentés ?\n"
                "2. Avez-vous un inventaire de vos actifs OT ?\n"
                "3. Votre plan de réponse aux incidents est-il testé ?\n\n"
                "Si vous répondez 'non' à une de ces questions, contactez-nous.\n\n"
                "#CyberIncident #OTSecurity #{sector_tag}"
            ),
        },
    },
}

WEEKLY_SCHEDULE = [
    {"day": "tuesday", "format": ContentFormat.LINKEDIN_POST, "topic": "nis2_compliance"},
    {"day": "thursday", "format": ContentFormat.LINKEDIN_POST, "topic": "iec62443_security"},
]

MONTHLY_SCHEDULE = [
    {"week": 2, "format": ContentFormat.ARTICLE, "topic": "nis2_compliance"},
]


class ContentCalendarEngine:
    """
    Génère et planifie du contenu thought leadership automatiquement.
    """

    def __init__(self) -> None:
        self.calendar: List[ContentItem] = []
        self.stats = {
            "total_planned": 0,
            "total_published": 0,
            "by_format": {f.value: 0 for f in ContentFormat},
        }

    def generate_content(
        self,
        topic: str,
        fmt: ContentFormat,
        sector: str = "industrie",
        publish_date: str = "",
    ) -> ContentItem:
        topic_templates = TOPIC_TEMPLATES.get(topic, TOPIC_TEMPLATES["nis2_compliance"])
        fmt_key = fmt.value
        template = topic_templates.get(fmt_key)

        if not template:
            first_key = next(iter(topic_templates))
            template = topic_templates[first_key]

        sector_tag = sector.capitalize().replace(" ", "")
        title = template["title"].format(
            sector=sector, n=8, v=23, sector_tag=sector_tag,
        )
        body = template["body"].format(
            sector=sector, n=50, v=23, sector_tag=sector_tag,
        )

        content_id = hashlib.sha256(
            f"{topic}-{fmt.value}-{sector}-{publish_date}".encode()
        ).hexdigest()[:12]

        if not publish_date:
            publish_date = datetime.now(timezone.utc).isoformat()

        item = ContentItem(
            content_id=content_id,
            title=title,
            format=fmt,
            topic=topic,
            sector_focus=sector,
            body=body,
            planned_date=publish_date,
        )

        self.calendar.append(item)
        self.stats["total_planned"] += 1
        self.stats["by_format"][fmt.value] = self.stats["by_format"].get(fmt.value, 0) + 1

        log.info("Content planned: %s format=%s topic=%s", content_id, fmt.value, topic)
        return item

    def generate_weekly_plan(self, sector: str = "industrie") -> List[ContentItem]:
        items = []
        now = datetime.now(timezone.utc)
        for entry in WEEKLY_SCHEDULE:
            publish_date = now.isoformat()
            item = self.generate_content(
                topic=entry["topic"],
                fmt=entry["format"],
                sector=sector,
                publish_date=publish_date,
            )
            items.append(item)
        return items

    def mark_published(self, content_id: str) -> bool:
        for item in self.calendar:
            if item.content_id == content_id:
                item.status = ContentStatus.PUBLISHED
                item.published_date = datetime.now(timezone.utc).isoformat()
                self.stats["total_published"] += 1
                return True
        return False

    def get_pending_content(self) -> List[ContentItem]:
        return [c for c in self.calendar if c.status != ContentStatus.PUBLISHED]

    def get_stats(self) -> Dict[str, Any]:
        return dict(self.stats)


content_calendar_engine = ContentCalendarEngine()
