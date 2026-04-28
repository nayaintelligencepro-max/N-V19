"""
NAYA V19 - Offer Generator
Genere automatiquement des propositions commerciales professionnelles.
ROI calcule, timeline, appel a action - pret a closer.
"""
import time, logging, hashlib, json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

log = logging.getLogger("NAYA.OFFER")

@dataclass
class GeneratedOffer:
    offer_id: str
    title: str
    prospect_name: str
    pain_description: str
    solution_description: str
    price: float
    roi_description: str
    timeline_days: int
    deliverables: List[str]
    payment_options: List[Dict]
    urgency_hook: str
    call_to_action: str
    created_at: float = field(default_factory=time.time)
    status: str = "draft"

class OfferGenerator:
    """Genere des offres commerciales irresistibles basees sur la douleur detectee."""

    OFFER_TEMPLATES = {
        "audit_diagnostic": {
            "title_template": "Diagnostic {sector} - Eliminez {pain_amount}EUR de pertes",
            "solution": "Audit complet de votre {area} avec plan d action concret en {days} jours",
            "deliverables": ["Rapport diagnostic complet", "Plan action prioritise", "ROI projete", "Session restitution 1h"],
            "urgency": "Les entreprises qui agissent dans les 48h recuperent en moyenne 3x plus vite"
        },
        "chatbot_ia": {
            "title_template": "Automatisation IA - Liberez {hours}h/semaine pour votre equipe",
            "solution": "Chatbot IA sur-mesure deploye en {days} jours, autonome 24/7",
            "deliverables": ["Chatbot IA personnalise", "Integration site/WhatsApp", "Dashboard analytics", "Formation equipe", "Support 30 jours"],
            "urgency": "Vos concurrents automatisent deja - chaque jour d attente est un client perdu"
        },
        "saas_solution": {
            "title_template": "Solution SaaS {sector} - {pain_amount}EUR d economie annuelle",
            "solution": "Plateforme SaaS cle-en-main deployee en {days} jours",
            "deliverables": ["Plateforme personnalisee", "Migration donnees", "Formation utilisateurs", "Support prioritaire 90j"],
            "urgency": "Offre limitee aux 3 premiers clients de votre secteur"
        },
        "service_premium_custom": {
            "title_template": "Solution Premium {sector} - ROI garanti {roi}x",
            "solution": "Service sur-mesure concu pour eliminer votre {pain_type} en {days} jours",
            "deliverables": ["Analyse approfondie", "Solution sur-mesure", "Implementation complete", "Suivi performance 60j"],
            "urgency": "Nous n acceptons que {max_clients} clients simultanement pour garantir l excellence"
        }
    }

    def __init__(self):
        self._offers: Dict[str, GeneratedOffer] = {}
        self._total_generated = 0

    def generate(self, pain: Dict[str, Any], pricing_result: Dict = None) -> GeneratedOffer:
        """Genere une offre complete a partir d une douleur et du pricing."""
        offer_type = pain.get("offer_type", "service_premium_custom")
        template = self.OFFER_TEMPLATES.get(offer_type, self.OFFER_TEMPLATES["service_premium_custom"])

        price = pricing_result.get("recommended_price", 5000) if pricing_result else pain.get("price", 5000)
        pain_cost = pain.get("annual_cost", price * 5)
        roi = round(pain_cost / price, 1) if price > 0 else 5

        sector = pain.get("sector", "")
        offer_id = f"OFF_{hashlib.md5(f'{sector}{time.time()}'.encode()).hexdigest()[:8].upper()}"

        title = template["title_template"].format(
            sector=pain.get("sector", "votre secteur"),
            pain_amount=f"{pain_cost:,.0f}",
            hours=pain.get("hours_lost", 20),
            roi=roi
        )

        solution = template["solution"].format(
            area=pain.get("area", "processus"),
            days=pain.get("timeline_days", 7),
            pain_type=pain.get("pain_type", "problematique")
        )

        payment_opts = pricing_result.get("payment_options", []) if pricing_result else [
            {"type": "full", "amount": price, "description": "Paiement integral"}
        ]

        offer = GeneratedOffer(
            offer_id=offer_id,
            title=title,
            prospect_name=pain.get("entity", "Votre entreprise"),
            pain_description=pain.get("description", ""),
            solution_description=solution,
            price=price,
            roi_description=f"ROI {roi}x - Vous recuperez {roi} fois votre investissement la premiere annee",
            timeline_days=pain.get("timeline_days", 7),
            deliverables=template["deliverables"],
            payment_options=payment_opts,
            urgency_hook=template["urgency"].format(max_clients=3),
            call_to_action=f"Reservez votre session decouverte gratuite de 30min"
        )

        self._offers[offer_id] = offer
        self._total_generated += 1
        log.info(f"[OFFER] Generee: {offer_id} | {price}EUR | {pain.get('sector','')}")
        return offer

    def to_markdown(self, offer: GeneratedOffer) -> str:
        """Convertit une offre en document Markdown professionnel."""
        lines = [
            f"# {offer.title}",
            f"",
            f"**Prepare pour:** {offer.prospect_name}",
            f"**Reference:** {offer.offer_id}",
            f"**Date:** {time.strftime('%d/%m/%Y')}",
            f"",
            f"---",
            f"",
            f"## Le probleme",
            f"{offer.pain_description}",
            f"",
            f"## Notre solution",
            f"{offer.solution_description}",
            f"",
            f"## Ce que vous recevez",
        ]
        for d in offer.deliverables:
            lines.append(f"- {d}")
        lines += [
            f"",
            f"## Retour sur investissement",
            f"{offer.roi_description}",
            f"",
            f"## Investissement: {offer.price:,.0f} EUR",
            f"",
            f"### Options de paiement",
        ]
        for po in offer.payment_options:
            lines.append(f"- {po.get('description', '')}")
        lines += [
            f"",
            f"## Delai de livraison: {offer.timeline_days} jours",
            f"",
            f"> {offer.urgency_hook}",
            f"",
            f"**{offer.call_to_action}**",
        ]
        return "\n".join(lines)

    def get_stats(self) -> Dict:
        return {
            "total_generated": self._total_generated,
            "active_offers": len([o for o in self._offers.values() if o.status == "draft"]),
        }

_gen = None
def get_offer_generator() -> OfferGenerator:
    global _gen
    if _gen is None:
        _gen = OfferGenerator()
    return _gen
