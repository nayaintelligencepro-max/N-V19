"""
NAYA V19 - Multi-Persona Outreach
Cree plusieurs personas adaptees au contexte pour multiplier les taux de reponse.
Chaque persona a son ton, angle et credibilite.
"""
import logging, hashlib, time, random
from typing import Dict, List, Optional
from dataclasses import dataclass, field

log = logging.getLogger("NAYA.OUTREACH.PERSONA")

@dataclass
class Persona:
    name: str
    role: str
    company: str
    email_domain: str
    tone: str
    angle: str
    expertise: List[str] = field(default_factory=list)
    signature: str = ""

@dataclass
class OutreachMessage:
    persona: Persona
    subject: str
    body: str
    prospect_name: str
    sector: str
    created_at: float = field(default_factory=time.time)

class MultiPersonaOutreach:
    """Genere des approches multi-persona pour maximiser les conversions."""

    PERSONAS = [
        Persona("Alexandre Moreau", "Directeur Conseil", "Nexus Strategy",
                "nexus-strategy.fr", "professionnel_autorite",
                "Expert reconnu qui apporte une solution eprouvee",
                ["strategie", "transformation", "performance"]),
        Persona("Claire Dubois", "Consultante Innovation", "Apex Digital",
                "apex-digital.io", "empathique_solution",
                "Comprend votre douleur et propose une solution humaine",
                ["innovation", "digital", "automatisation"]),
        Persona("Marc Lefebvre", "Partenaire Technologique", "TechBridge Partners",
                "techbridge.eu", "technique_pragmatique",
                "Approche technique avec ROI chiffre et timeline precise",
                ["tech", "data", "ia", "saas"]),
        Persona("Sophie Renard", "Directrice Commerciale", "ValueFirst Group",
                "valuefirst.com", "commercial_direct",
                "Va droit au but avec une proposition concrete irresistible",
                ["vente", "business development", "partenariat"]),
        Persona("Thomas Lambert", "Expert Sectoriel", "Sector Insights",
                "sector-insights.fr", "expert_sectoriel",
                "Connaissance approfondie du secteur du prospect",
                ["sectoriel", "benchmark", "analyse marche"]),
    ]

    TEMPLATES = {
        "professionnel_autorite": {
            "subject": "{pain_keyword}: {prospect}, une solution existe",
            "body": ("Bonjour {prospect_name},\n\n"
                    "En tant que {role} chez {company}, j accompagne des organisations comme la votre "
                    "a resoudre {pain_description}.\n\n"
                    "Nos clients dans votre secteur ont obtenu un ROI de {roi}x en moyenne.\n\n"
                    "Seriez-vous disponible pour un echange de 20 minutes cette semaine ?\n\n"
                    "Cordialement,\n{name}\n{role} - {company}")
        },
        "empathique_solution": {
            "subject": "{prospect}, j ai identifie un levier pour vous",
            "body": ("Bonjour {prospect_name},\n\n"
                    "Je comprends que {pain_description} represente un defi quotidien. "
                    "C est exactement pourquoi nous avons developpe une approche qui a deja "
                    "aide des entreprises similaires a economiser {savings}EUR par an.\n\n"
                    "Puis-je vous envoyer une etude de cas de 2 minutes ?\n\n"
                    "Bien a vous,\n{name}\n{role} - {company}")
        },
        "technique_pragmatique": {
            "subject": "Solution technique: {pain_keyword} - ROI {roi}x",
            "body": ("Bonjour {prospect_name},\n\n"
                    "J ai analyse votre situation concernant {pain_description}.\n\n"
                    "Voici ce que je propose :\n"
                    "- Deploiement en {timeline} jours\n"
                    "- ROI mesurable de {roi}x\n"
                    "- Zero risque: paiement au resultat\n\n"
                    "Disponible pour un call de 15 min ?\n\n"
                    "{name} - {company}")
        },
        "commercial_direct": {
            "subject": "{prospect}: proposition a {price}EUR (offre limitee)",
            "body": ("Bonjour {prospect_name},\n\n"
                    "Je vais droit au but : nous pouvons resoudre {pain_description} "
                    "pour {price}EUR, deploye en {timeline} jours.\n\n"
                    "3 places disponibles ce mois-ci. Interesse(e) ?\n\n"
                    "{name} - {company}")
        },
        "expert_sectoriel": {
            "subject": "Tendance {sector}: ce que font vos concurrents",
            "body": ("Bonjour {prospect_name},\n\n"
                    "En etudiant le secteur {sector}, j ai constate que {pain_description} "
                    "touche 70% des acteurs. Les leaders resolvent ce probleme avec "
                    "des solutions comme la notre.\n\n"
                    "Voulez-vous savoir comment ?\n\n"
                    "{name} - {company}")
        },
    }

    def __init__(self):
        self._messages_generated = 0
        self._best_performers: Dict[str, int] = {}

    def generate_outreach(self, prospect: Dict, n_personas: int = 3) -> List[OutreachMessage]:
        """Genere des messages d approche avec differentes personas."""
        prospect_name = prospect.get("name", "Madame, Monsieur")
        sector = prospect.get("sector", "votre secteur")
        pain = prospect.get("pain_description", "votre problematique")
        price = prospect.get("price", 5000)
        roi = prospect.get("roi", 5)
        timeline = prospect.get("timeline_days", 7)
        savings = prospect.get("annual_savings", price * roi)

        # Selectionner les personas les plus adaptees
        selected = self._select_personas(sector, n_personas)
        messages = []

        for persona in selected:
            template = self.TEMPLATES.get(persona.tone, self.TEMPLATES["professionnel_autorite"])
            subject = template["subject"].format(
                prospect=prospect_name, pain_keyword=pain[:30],
                roi=roi, price=price, sector=sector
            )
            body = template["body"].format(
                prospect_name=prospect_name, pain_description=pain,
                roi=roi, price=price, timeline=timeline, savings=savings,
                name=persona.name, role=persona.role, company=persona.company,
                sector=sector
            )

            msg = OutreachMessage(
                persona=persona, subject=subject, body=body,
                prospect_name=prospect_name, sector=sector
            )
            messages.append(msg)
            self._messages_generated += 1

        log.info(f"[PERSONA] {len(messages)} messages generes pour {prospect_name} ({sector})")
        return messages

    def _select_personas(self, sector: str, n: int) -> List[Persona]:
        """Selectionne les n personas les plus adaptees au secteur."""
        scored = []
        for p in self.PERSONAS:
            score = 0.5
            if any(e in sector.lower() for e in p.expertise):
                score += 0.3
            # Varier les personas pour ne pas toujours envoyer les memes
            history_count = self._best_performers.get(p.name, 0)
            score -= history_count * 0.05
            scored.append((p, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [p for p, _ in scored[:n]]

    def record_response(self, persona_name: str, got_response: bool) -> None:
        if got_response:
            self._best_performers[persona_name] = self._best_performers.get(persona_name, 0) + 1

    def get_best_persona_for(self, sector: str) -> Persona:
        selected = self._select_personas(sector, 1)
        return selected[0] if selected else self.PERSONAS[0]

    def get_stats(self) -> Dict:
        return {
            "total_generated": self._messages_generated,
            "personas_available": len(self.PERSONAS),
            "best_performers": dict(sorted(
                self._best_performers.items(), key=lambda x: x[1], reverse=True
            )[:5])
        }

_outreach = None
def get_multi_persona():
    global _outreach
    if _outreach is None:
        _outreach = MultiPersonaOutreach()
    return _outreach
