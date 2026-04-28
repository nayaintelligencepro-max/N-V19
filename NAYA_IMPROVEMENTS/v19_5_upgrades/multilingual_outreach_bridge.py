"""
NAYA SUPREME V19.5 — AMÉLIORATION #8 : MULTILINGUAL OUTREACH BRIDGE
═══════════════════════════════════════════════════════════════════════
Connecte le MultilingualEngine existant au pipeline d'outreach.
Génère automatiquement les séquences email dans la langue du prospect.

Langues supportées : FR, EN, DE, ES, NL, IT, PT
Détection automatique basée sur le pays/domaine du prospect.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict

log = logging.getLogger("NAYA.MULTILINGUAL_OUTREACH")


COUNTRY_LANGUAGE_MAP = {
    "FR": "fr", "BE": "fr", "CH": "fr", "LU": "fr", "MC": "fr",
    "CA": "fr", "MA": "fr", "TN": "fr", "SN": "fr", "CI": "fr",
    "PF": "fr",
    "DE": "de", "AT": "de",
    "GB": "en", "UK": "en", "US": "en", "IE": "en", "AU": "en",
    "NZ": "en", "SG": "en", "IN": "en",
    "ES": "es", "MX": "es", "AR": "es", "CO": "es", "CL": "es",
    "NL": "nl",
    "IT": "it",
    "PT": "pt", "BR": "pt",
    "SE": "en", "NO": "en", "DK": "en", "FI": "en",
    "PL": "en", "CZ": "en", "RO": "en",
}

DOMAIN_COUNTRY_MAP = {
    ".fr": "FR", ".de": "DE", ".uk": "GB", ".co.uk": "GB",
    ".es": "ES", ".it": "IT", ".nl": "NL", ".be": "BE",
    ".ch": "CH", ".at": "AT", ".pt": "PT", ".br": "BR",
    ".pf": "PF", ".nc": "FR",
}

TEMPLATES = {
    "fr": {
        "greeting": "Bonjour {name}",
        "intro": "Je me permets de vous contacter car",
        "pain_iec62443": "la conformité IEC 62443 est devenue une obligation pour les entreprises du secteur {sector}",
        "pain_nis2": "la directive NIS2 impose de nouvelles exigences de cybersécurité aux organisations comme {company}",
        "value_prop": "Nous proposons un audit complet avec plan de remédiation livré en 2-4 semaines",
        "cta": "Seriez-vous disponible pour un échange de 15 minutes cette semaine ?",
        "closing": "Cordialement",
        "ps": "PS : Notre audit est livré avant tout paiement. Zéro risque pour vous.",
    },
    "en": {
        "greeting": "Dear {name}",
        "intro": "I'm reaching out because",
        "pain_iec62443": "IEC 62443 compliance has become mandatory for companies in the {sector} sector",
        "pain_nis2": "the NIS2 directive introduces new cybersecurity requirements for organizations like {company}",
        "value_prop": "We offer a comprehensive audit with remediation plan delivered in 2-4 weeks",
        "cta": "Would you be available for a 15-minute call this week?",
        "closing": "Best regards",
        "ps": "PS: Our audit is delivered before any payment. Zero risk for you.",
    },
    "de": {
        "greeting": "Sehr geehrte/r {name}",
        "intro": "Ich kontaktiere Sie, weil",
        "pain_iec62443": "die IEC 62443-Konformität für Unternehmen im Bereich {sector} verpflichtend geworden ist",
        "pain_nis2": "die NIS2-Richtlinie neue Cybersicherheitsanforderungen für Organisationen wie {company} einführt",
        "value_prop": "Wir bieten ein umfassendes Audit mit Maßnahmenplan, geliefert in 2-4 Wochen",
        "cta": "Hätten Sie diese Woche Zeit für ein 15-minütiges Gespräch?",
        "closing": "Mit freundlichen Grüßen",
        "ps": "PS: Unser Audit wird vor jeder Zahlung geliefert. Null Risiko für Sie.",
    },
    "es": {
        "greeting": "Estimado/a {name}",
        "intro": "Me pongo en contacto porque",
        "pain_iec62443": "el cumplimiento de IEC 62443 se ha vuelto obligatorio para empresas del sector {sector}",
        "pain_nis2": "la directiva NIS2 introduce nuevos requisitos de ciberseguridad para organizaciones como {company}",
        "value_prop": "Ofrecemos una auditoría completa con plan de remediación entregado en 2-4 semanas",
        "cta": "¿Estaría disponible para una llamada de 15 minutos esta semana?",
        "closing": "Atentamente",
        "ps": "PD: Nuestra auditoría se entrega antes de cualquier pago. Riesgo cero para usted.",
    },
    "nl": {
        "greeting": "Geachte {name}",
        "intro": "Ik neem contact met u op omdat",
        "pain_iec62443": "IEC 62443-compliance verplicht is geworden voor bedrijven in de {sector}-sector",
        "pain_nis2": "de NIS2-richtlijn nieuwe cyberbeveiligingseisen stelt aan organisaties zoals {company}",
        "value_prop": "Wij bieden een uitgebreide audit met herstelplan, geleverd in 2-4 weken",
        "cta": "Zou u deze week beschikbaar zijn voor een gesprek van 15 minuten?",
        "closing": "Met vriendelijke groet",
        "ps": "PS: Onze audit wordt geleverd vóór betaling. Nul risico voor u.",
    },
    "it": {
        "greeting": "Gentile {name}",
        "intro": "La contatto perché",
        "pain_iec62443": "la conformità IEC 62443 è diventata obbligatoria per le aziende del settore {sector}",
        "pain_nis2": "la direttiva NIS2 introduce nuovi requisiti di cybersicurezza per organizzazioni come {company}",
        "value_prop": "Offriamo un audit completo con piano di rimedio consegnato in 2-4 settimane",
        "cta": "Sarebbe disponibile per una chiamata di 15 minuti questa settimana?",
        "closing": "Cordiali saluti",
        "ps": "PS: Il nostro audit viene consegnato prima di qualsiasi pagamento. Zero rischio per voi.",
    },
    "pt": {
        "greeting": "Prezado/a {name}",
        "intro": "Entro em contato porque",
        "pain_iec62443": "a conformidade com a IEC 62443 tornou-se obrigatória para empresas do setor {sector}",
        "pain_nis2": "a diretiva NIS2 introduz novos requisitos de cibersegurança para organizações como {company}",
        "value_prop": "Oferecemos uma auditoria completa com plano de remediação entregue em 2-4 semanas",
        "cta": "Estaria disponível para uma conversa de 15 minutos esta semana?",
        "closing": "Atenciosamente",
        "ps": "PS: Nossa auditoria é entregue antes de qualquer pagamento. Risco zero para você.",
    },
}


@dataclass
class LocalizedEmail:
    language: str
    subject: str
    body: str
    prospect_country: str


class MultilingualOutreachBridge:
    """
    Détecte la langue du prospect et génère l'email dans sa langue.
    """

    def __init__(self) -> None:
        self.emails_generated: Dict[str, int] = {lang: 0 for lang in TEMPLATES}
        self.total_generated = 0

    def detect_language(self, email: str = "", country: str = "") -> str:
        if country:
            country_upper = country.upper()
            if country_upper in COUNTRY_LANGUAGE_MAP:
                return COUNTRY_LANGUAGE_MAP[country_upper]

        if email:
            email_lower = email.lower()
            for domain_suffix, country_code in sorted(
                DOMAIN_COUNTRY_MAP.items(), key=lambda x: len(x[0]), reverse=True,
            ):
                if email_lower.endswith(domain_suffix):
                    return COUNTRY_LANGUAGE_MAP.get(country_code, "en")

        return "en"

    def generate_email(
        self,
        prospect_name: str,
        prospect_email: str,
        company: str,
        sector: str,
        pain_type: str = "nis2",
        country: str = "",
    ) -> LocalizedEmail:
        lang = self.detect_language(prospect_email, country)
        template = TEMPLATES.get(lang, TEMPLATES["en"])

        pain_key = f"pain_{pain_type}" if f"pain_{pain_type}" in template else "pain_nis2"
        pain_text = template[pain_key].format(
            name=prospect_name, company=company, sector=sector,
        )

        subject_templates = {
            "fr": f"Cybersécurité {sector} — Êtes-vous conforme ?",
            "en": f"{sector} Cybersecurity — Are you compliant?",
            "de": f"Cybersicherheit {sector} — Sind Sie konform?",
            "es": f"Ciberseguridad {sector} — ¿Cumple con la normativa?",
            "nl": f"Cyberbeveiliging {sector} — Bent u compliant?",
            "it": f"Cybersicurezza {sector} — Siete conformi?",
            "pt": f"Cibersegurança {sector} — Está em conformidade?",
        }

        subject = subject_templates.get(lang, subject_templates["en"])

        body = (
            f"{template['greeting'].format(name=prospect_name)},\n\n"
            f"{template['intro']} {pain_text}.\n\n"
            f"{template['value_prop']}.\n\n"
            f"{template['cta']}\n\n"
            f"{template['closing']},\n"
            f"NAYA Intelligence\n\n"
            f"{template['ps']}"
        )

        self.emails_generated[lang] = self.emails_generated.get(lang, 0) + 1
        self.total_generated += 1

        detected_country = country or self._guess_country(prospect_email)

        return LocalizedEmail(
            language=lang,
            subject=subject,
            body=body,
            prospect_country=detected_country,
        )

    def _guess_country(self, email: str) -> str:
        email_lower = email.lower()
        for suffix, code in sorted(
            DOMAIN_COUNTRY_MAP.items(), key=lambda x: len(x[0]), reverse=True,
        ):
            if email_lower.endswith(suffix):
                return code
        return "UNKNOWN"

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_generated": self.total_generated,
            "by_language": dict(self.emails_generated),
        }


multilingual_outreach_bridge = MultilingualOutreachBridge()
