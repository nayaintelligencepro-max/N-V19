"""
NAYA CORE — AGENT 3 — OFFER WRITER ADVANCED
Génération d'offres commerciales ultra-personnalisées
Sources: LLM (Claude/Groq), Mémoire vectorielle offres gagnantes
Output: PDF + Email subject + Body + LinkedIn message + Prix + Tier
"""

import asyncio
import json
import logging
import hashlib
from typing import Optional, List, Dict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger(__name__)

class OfferTier(Enum):
    TIER1 = "tier1"      # 1k-5k
    TIER2 = "tier2"      # 5k-20k
    TIER3 = "tier3"      # 20k-100k
    TIER4 = "tier4"      # 100k+

@dataclass
class Offer:
    """Commercial offer"""
    offer_id: str
    prospect_id: str
    company_name: str
    decision_maker_name: str
    decision_maker_title: str
    offer_title: str
    offer_description: str
    email_subject: str
    email_body: str
    linkedin_message: str
    price_eur: int
    tier: OfferTier
    pdf_path: Optional[str] = None
    personalization_level: float = 0.8
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self):
        return {
            'offer_id': self.offer_id,
            'prospect_id': self.prospect_id,
            'company_name': self.company_name,
            'decision_maker_name': self.decision_maker_name,
            'decision_maker_title': self.decision_maker_title,
            'offer_title': self.offer_title,
            'offer_description': self.offer_description,
            'email_subject': self.email_subject,
            'email_body': self.email_body,
            'linkedin_message': self.linkedin_message,
            'price_eur': self.price_eur,
            'tier': self.tier.value,
            'personalization_level': self.personalization_level,
            'generated_at': self.generated_at.isoformat(),
        }

class OfferMemory:
    """Vector memory des offres gagnantes pour apprentissage"""
    
    def __init__(self):
        self.winning_offers: List[Dict] = []
        self.conversion_history: Dict[str, float] = {}
    
    async def search_similar(self, sector: str, decision_maker_title: str, price_range: tuple) -> List[Dict]:
        """Chercher offres similaires gagnantes"""
        logger.info(f"Searching memory: {sector} / {decision_maker_title}")
        
        # Mock search results
        similar = [
            {
                'sector': sector,
                'title': 'Audit IEC 62443 + Remediation',
                'conversion_rate': 0.85,
                'avg_price': 15000,
            },
            {
                'sector': sector,
                'title': 'Conformité NIS2 - Audit Complet',
                'conversion_rate': 0.80,
                'avg_price': 12000,
            }
        ]
        
        await asyncio.sleep(0.1)
        return similar
    
    async def add_winning_offer(self, offer: Offer, converted: bool, final_price: int):
        """Ajouter une offre gagnante à la mémoire"""
        self.winning_offers.append({
            'offer_id': offer.offer_id,
            'title': offer.offer_title,
            'sector': offer.company_name,
            'tier': offer.tier.value,
            'conversion': converted,
            'final_price': final_price,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
        logger.info(f"Winning offer added: {offer.offer_id}")

class OfferGenerator:
    """Générateur d'offres basé LLM"""
    
    OFFER_TEMPLATES = {
        'RSSI': {
            'TIER1': 'Audit Cybersécurité OT Express (3 jours)',
            'TIER2': 'Audit Complet IEC 62443 Niveau 2',
            'TIER3': 'Programme Complet NIS2 + Remediation',
            'TIER4': 'Transformation Sécurité Industrielle (12 mois)',
        },
        'DSI': {
            'TIER1': 'Audit Cloud Security Quick Check',
            'TIER2': 'Audit ISO 27001 Complet',
            'TIER3': 'Migration Infrastructure Sécurisée',
            'TIER4': 'SOC Managé 24/7 (12 mois)',
        },
        'CTO': {
            'TIER1': 'Secure DevOps Assessment',
            'TIER2': 'Secure Software Development Training',
            'TIER3': 'Secure Architecture Design + Implementation',
            'TIER4': 'Product Security Program (12 mois)',
        }
    }
    
    def __init__(self):
        self.memory = OfferMemory()
    
    def _determine_tier(self, budget_estimate: int, sector: str) -> OfferTier:
        """Déterminer le tier basé budget"""
        if budget_estimate >= 100000:
            return OfferTier.TIER4
        elif budget_estimate >= 20000:
            return OfferTier.TIER3
        elif budget_estimate >= 5000:
            return OfferTier.TIER2
        else:
            return OfferTier.TIER1
    
    def _calculate_price(self, tier: OfferTier, sector: str) -> int:
        """Calculer le prix basé sur le tier"""
        base_prices = {
            OfferTier.TIER1: 2500,
            OfferTier.TIER2: 12000,
            OfferTier.TIER3: 50000,
            OfferTier.TIER4: 250000,
        }
        
        price = base_prices[tier]
        
        # Ajustements sectoriels
        sector_multipliers = {
            'Energy': 1.3,
            'Manufacturing': 1.1,
            'Finance': 1.2,
            'Transport': 1.0,
        }
        
        multiplier = sector_multipliers.get(sector, 1.0)
        return int(price * multiplier)
    
    async def generate(self, prospect: Dict, budget_estimate: int, sector: str) -> Offer:
        """Générer une offre complète"""
        
        logger.info(f"Generating offer for {prospect['company_name']}")
        
        # Déterminer tier
        tier = self._determine_tier(budget_estimate, sector)
        price = self._calculate_price(tier, sector)
        
        # Chercher offres similaires dans memory
        decision_maker_title = prospect.get('decision_maker_title', 'DSI')
        similar_offers = await self.memory.search_similar(sector, decision_maker_title, (price * 0.8, price * 1.2))
        
        # Construire l'offre
        offer_title = self.OFFER_TEMPLATES.get(decision_maker_title, {}).get(tier.value.upper(), 'Service Professionnel')
        
        offer = Offer(
            offer_id=f"offer_{hashlib.md5(prospect['prospect_id'].encode()).hexdigest()[:8]}",
            prospect_id=prospect['prospect_id'],
            company_name=prospect['company_name'],
            decision_maker_name=prospect.get('decision_maker_name', 'Monsieur/Madame'),
            decision_maker_title=decision_maker_title,
            offer_title=offer_title,
            offer_description=f"Solution personnalisée pour {sector}: {offer_title}",
            email_subject=f"Améliorer votre conformité OT: {offer_title}",
            email_body=self._generate_email_body(prospect, offer_title, price),
            linkedin_message=self._generate_linkedin_message(prospect, offer_title),
            price_eur=price,
            tier=tier,
            personalization_level=0.85,
        )
        
        return offer
    
    def _generate_email_body(self, prospect: Dict, title: str, price: int) -> str:
        """Générer le corps de l'email"""
        return f"""Monsieur/Madame {prospect.get('decision_maker_name', '')},

Nous avons identifié une opportunité importante pour optimiser votre conformité en cybersécurité industrielle.

Notre service "{title}" est spécialement conçu pour les entreprises comme {prospect['company_name']}.

✓ Diagnostic personnalisé
✓ Feuille de route priorisée
✓ Réduction des risques opérationnels

Budget d'investissement: {price:,} EUR

Nous serions ravis de discuter de comment nous pouvons vous aider.

Pouvez-vous nous accorder 15 minutes cette semaine?

Cordialement,
NAYA SUPREME
"""
    
    def _generate_linkedin_message(self, prospect: Dict, title: str) -> str:
        """Générer le message LinkedIn"""
        return f"""Bonjour {prospect.get('decision_maker_name', '')},

J'ai remarqué que {prospect['company_name']} pourrait bénéficier de notre expertise en conformité OT.

Nous aidons les organisations comme la vôtre à:
• Réduire les risques cyber industriels
• Atteindre la conformité NIS2/IEC 62443
• Optimiser la continuité opérationnelle

Intéressé par une discussion rapide (15 min)?

{title}

Cordialement,
NAYA SUPREME
"""

class OfferWriterAdvanced:
    """AGENT 3 — OFFER WRITER ADVANCED
    Générer offres personnalisées basées on enriched prospects
    Consulte offer_memory pour apprendre des victoires
    Output: Offer avec PDF + Email + LinkedIn + Prix
    """
    
    def __init__(self):
        self.generator = OfferGenerator()
        self.offers_created: Dict[str, Offer] = {}
        self.run_count = 0
    
    async def create_for_prospect(self, prospect: Dict, budget_estimate: int, sector: str) -> Offer:
        """Créer une offre pour UN prospect"""
        offer = await self.generator.generate(prospect, budget_estimate, sector)
        self.offers_created[offer.offer_id] = offer
        
        logger.info(f"Offer created: {offer.offer_id} - {offer.price_eur} EUR")
        
        return offer
    
    async def create_batch(self, prospects: List[Dict], budgets: List[int], sectors: List[str]) -> List[Offer]:
        """Créer offres en batch"""
        tasks = []
        for prospect, budget, sector in zip(prospects, budgets, sectors):
            task = self.create_for_prospect(prospect, budget, sector)
            tasks.append(task)
        
        return await asyncio.gather(*tasks)
    
    async def run_cycle(self, enriched_prospects: List[Dict], budgets: List[int], sectors: List[str]) -> Dict:
        """Cycle complet"""
        self.run_count += 1
        
        logger.info(f"Offer Writer cycle #{self.run_count}")
        
        offers = await self.create_batch(enriched_prospects, budgets, sectors)
        
        result = {
            'run_count': self.run_count,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'total_created': len(offers),
            'total_revenue_potential': sum(o.price_eur for o in offers),
            'offers': [o.to_dict() for o in offers],
        }
        
        return result
    
    async def record_win(self, offer_id: str, final_price: int):
        """Enregistrer une victoire dans memory"""
        if offer_id in self.offers_created:
            offer = self.offers_created[offer_id]
            await self.generator.memory.add_winning_offer(offer, True, final_price)
    
    def get_stats(self) -> Dict:
        """Stats"""
        return {
            'run_count': self.run_count,
            'total_offers_created': len(self.offers_created),
            'total_revenue_potential': sum(o.price_eur for o in self.offers_created.values()),
        }

# Instance globale
offer_writer = OfferWriterAdvanced()

async def main():
    test_prospects = [
        {
            'prospect_id': 'p1',
            'company_name': 'EnergieCorp',
            'decision_maker_name': 'Jean Dupont',
            'decision_maker_title': 'RSSI',
        }
    ]
    
    result = await offer_writer.run_cycle(test_prospects, [15000], ['Energy'])
    print(json.dumps(result, indent=2, default=str))

if __name__ == "__main__":
    asyncio.run(main())

# Alias for backwards compatibility
OfferWriterAgent = OfferWriterAdvanced
