"""
NAYA CORE — AGENT 2 — RESEARCHER
Enrichissement complet des prospects détectés par Pain Hunter
Sources: Apollo.io, Hunter.io, Scraping, LinkedIn, Pattern guessing
Outpute enriched_prospect avec email, phone, LinkedIn, company data
"""

import asyncio
import json
import logging
import os
import re
import hashlib
from typing import Optional, List, Dict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger(__name__)

class EnrichmentSource(Enum):
    APOLLO = "apollo"
    HUNTER = "hunter"
    SCRAPE = "scrape"
    LINKEDIN = "linkedin"
    PATTERN = "pattern"

@dataclass
class EnrichedProspect:
    """Prospect fully enriched"""
    prospect_id: str
    company_name: str
    decision_maker_name: Optional[str] = None
    decision_maker_title: str = ""
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    company_size: Optional[str] = None
    company_revenue: Optional[str] = None
    company_tech_stack: List[str] = field(default_factory=list)
    ot_signals: List[str] = field(default_factory=list)
    enrichment_sources: List[EnrichmentSource] = field(default_factory=list)
    confidence_score: float = 0.0
    enriched_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    manual_review_required: bool = False
    
    def to_dict(self):
        return {
            'prospect_id': self.prospect_id,
            'company_name': self.company_name,
            'decision_maker_name': self.decision_maker_name,
            'decision_maker_title': self.decision_maker_title,
            'email': self.email,
            'phone': self.phone,
            'linkedin_url': self.linkedin_url,
            'company_size': self.company_size,
            'company_revenue': self.company_revenue,
            'company_tech_stack': self.company_tech_stack,
            'ot_signals': self.ot_signals,
            'enrichment_sources': [s.value for s in self.enrichment_sources],
            'confidence_score': self.confidence_score,
            'enriched_at': self.enriched_at.isoformat(),
            'manual_review_required': self.manual_review_required,
        }

class ApolloEnricher:
    """Enrichissement via Apollo.io API"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('APOLLO_API_KEY', '')
        self.base_url = "https://api.apollo.io/v1"
    
    async def enrich(self, company_name: str, decision_maker_title: str) -> Optional[EnrichedProspect]:
        """Enrichir via Apollo"""
        if not self.api_key:
            return None
        
        try:
            logger.info(f"Apollo enriching: {company_name} - {decision_maker_title}")
            
            # Mock Apollo response
            prospect = EnrichedProspect(
                prospect_id=f"apollo_{hashlib.md5(company_name.encode()).hexdigest()[:8]}",
                company_name=company_name,
                decision_maker_name=f"John {decision_maker_title.split()[0]}",
                decision_maker_title=decision_maker_title,
                email=f"john.{decision_maker_title.lower().replace(' ', '_')}@{company_name.lower().replace(' ', '')}.com",
                phone="+33612345678",
                linkedin_url=f"https://linkedin.com/in/user-apollo",
                company_size="1000-5000",
                company_revenue="50M-100M EUR",
                company_tech_stack=["Windows Server", "Cisco OT", "Honeywell SCADA"],
                ot_signals=["SCADA infrastructure", "IEC 62443 relevant"],
                enrichment_sources=[EnrichmentSource.APOLLO],
                confidence_score=0.85
            )
            
            await asyncio.sleep(0.2)  # Simulate API latency
            return prospect
        
        except Exception as e:
            logger.error(f"Apollo error: {e}")
            return None

class HunterEnricher:
    """Enrichissement via Hunter.io API"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('HUNTER_API_KEY', '')
        self.base_url = "https://api.hunter.io/v2"
    
    async def enrich(self, company_name: str, first_name: str = "Contact") -> Optional[Dict]:
        """Enrichir via Hunter.io"""
        if not self.api_key:
            return None
        
        try:
            logger.info(f"Hunter enriching: {company_name}")
            
            # Mock Hunter response
            domain = company_name.lower().replace(' ', '') + ".com"
            email = f"{first_name.lower()}@{domain}"
            
            result = {
                'domain': domain,
                'email': email,
                'confidence': 0.82,
                'company_name': company_name,
            }
            
            await asyncio.sleep(0.2)
            return result
        
        except Exception as e:
            logger.error(f"Hunter error: {e}")
            return None

class WebScrapeEnricher:
    """Enrichissement via web scraping"""
    
    async def enrich(self, company_name: str) -> Optional[Dict]:
        """Scraper company website pour enrichissement"""
        try:
            logger.info(f"Scraping: {company_name}")
            
            # Mock scrape results
            result = {
                'company_size': '500-2000',
                'tech_stack': ['Linux', 'Cisco', 'Fortinet'],
                'website': f"https://{company_name.lower().replace(' ', '')}.com",
                'phone': '+33612345678',
                'confidence': 0.70,
            }
            
            await asyncio.sleep(0.3)
            return result
        
        except Exception as e:
            logger.error(f"Scrape error: {e}")
            return None

class LinkedInEnricher:
    """Enrichissement via LinkedIn signals"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('LINKEDIN_API_KEY', '')
    
    async def enrich(self, company_name: str, decision_maker_title: str) -> Optional[Dict]:
        """Enrichir via LinkedIn"""
        if not self.api_key:
            return None
        
        try:
            logger.info(f"LinkedIn enriching: {company_name}")
            
            # Mock LinkedIn response
            result = {
                'company_size': '1000-5000',
                'company_url': f"https://linkedin.com/company/{company_name.lower()}",
                'linkedin_profile': f"https://linkedin.com/in/user-{company_name.lower()}",
                'confidence': 0.78,
            }
            
            await asyncio.sleep(0.15)
            return result
        
        except Exception as e:
            logger.error(f"LinkedIn error: {e}")
            return None

class PatternEnricher:
    """Enrichissement par pattern guessing (fallback)"""
    
    COMMON_PATTERNS = [
        "{first}.{last}@{domain}",
        "{first}@{domain}",
        "{last}@{domain}",
        "{first}{last}@{domain}",
    ]
    
    async def enrich(self, company_name: str, decision_maker_name: Optional[str] = None) -> Dict:
        """Générer emails par pattern"""
        domain = company_name.lower().replace(' ', '') + ".com"
        
        emails = []
        if decision_maker_name:
            parts = decision_maker_name.split()
            first = parts[0].lower() if len(parts) > 0 else "contact"
            last = parts[-1].lower() if len(parts) > 1 else ""
            
            for pattern in self.COMMON_PATTERNS:
                email = pattern.format(first=first, last=last, domain=domain)
                emails.append(email)
        
        result = {
            'domain': domain,
            'possible_emails': emails,
            'confidence': 0.45,
        }
        
        await asyncio.sleep(0.1)
        return result

class ResearcherAgent:
    """AGENT 2 — RESEARCHER
    Enrichir prospects détectés par Pain Hunter
    Utilise 3 sources: Apollo → Hunter → Scrape / LinkedIn / Pattern
    Si email pas trouvé après 3 sources → manual_review_required
    """
    
    def __init__(self):
        self.apollo = ApolloEnricher()
        self.hunter = HunterEnricher()
        self.scraper = WebScrapeEnricher()
        self.linkedin = LinkedInEnricher()
        self.pattern = PatternEnricher()
        self.enriched_prospects: Dict[str, EnrichedProspect] = {}
        self.run_count = 0
    
    async def enrich_single(self, company_name: str, decision_maker_title: str, 
                           decision_maker_name: Optional[str] = None) -> EnrichedProspect:
        """Enrichir UN prospect"""
        
        logger.info(f"Enriching: {company_name} / {decision_maker_title}")
        
        # Try Apollo first
        apollo_result = await self.apollo.enrich(company_name, decision_maker_title)
        if apollo_result and apollo_result.email:
            apollo_result.enrichment_sources.append(EnrichmentSource.APOLLO)
            return apollo_result
        
        # Try Hunter second
        hunter_result = await self.hunter.enrich(company_name, decision_maker_name or "Contact")
        if hunter_result and hunter_result.get('email'):
            prospect = EnrichedProspect(
                prospect_id=f"hunter_{hashlib.md5(company_name.encode()).hexdigest()[:8]}",
                company_name=company_name,
                decision_maker_title=decision_maker_title,
                email=hunter_result['email'],
                enrichment_sources=[EnrichmentSource.HUNTER],
                confidence_score=hunter_result.get('confidence', 0.7)
            )
            return prospect
        
        # Try Scrape + LinkedIn + Pattern
        scrape_result = await self.scraper.enrich(company_name)
        linkedin_result = await self.linkedin.enrich(company_name, decision_maker_title)
        pattern_result = await self.pattern.enrich(company_name, decision_maker_name)
        
        # Merge all results
        prospect = EnrichedProspect(
            prospect_id=f"merged_{hashlib.md5(company_name.encode()).hexdigest()[:8]}",
            company_name=company_name,
            decision_maker_title=decision_maker_title,
            decision_maker_name=decision_maker_name,
            company_size=scrape_result.get('company_size') or linkedin_result.get('company_size'),
            company_tech_stack=scrape_result.get('tech_stack', []),
            linkedin_url=linkedin_result.get('linkedin_profile'),
            enrichment_sources=[EnrichmentSource.SCRAPE, EnrichmentSource.LINKEDIN, EnrichmentSource.PATTERN],
            confidence_score=0.65,
            manual_review_required=True  # Email pas trouvé automatiquement
        )
        
        # Si pattern_result a des emails, on les ajoute
        if pattern_result.get('possible_emails'):
            prospect.email = pattern_result['possible_emails'][0]  # Meilleur pattern
            prospect.manual_review_required = False
            prospect.confidence_score = 0.50
        
        return prospect
    
    async def enrich_batch(self, pains: List[Dict]) -> List[EnrichedProspect]:
        """Enrichir batch de pains"""
        tasks = []
        for pain in pains:
            task = self.enrich_single(
                pain['company_name'],
                pain['decision_maker_title'],
                pain.get('decision_maker_name')
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        for prospect in results:
            self.enriched_prospects[prospect.prospect_id] = prospect
        
        return results
    
    async def run_cycle(self, pains: List[Dict]) -> Dict:
        """Cycle complet: enrichir batch de pains"""
        self.run_count += 1
        
        logger.info(f"Researcher cycle #{self.run_count} for {len(pains)} pains")
        
        enriched = await self.enrich_batch(pains)
        
        manual_review_count = sum(1 for p in enriched if p.manual_review_required)
        
        result = {
            'run_count': self.run_count,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'total_enriched': len(enriched),
            'manual_review_required': manual_review_count,
            'enriched_prospects': [p.to_dict() for p in enriched],
        }
        
        return result
    
    def get_stats(self) -> Dict:
        """Stats du Researcher"""
        return {
            'run_count': self.run_count,
            'total_enriched': len(self.enriched_prospects),
            'manual_review_count': sum(1 for p in self.enriched_prospects.values() if p.manual_review_required),
        }

# Instance globale
researcher = ResearcherAgent()

async def main():
    test_pains = [
        {
            'company_name': 'Acme Corp',
            'decision_maker_title': 'RSSI',
            'decision_maker_name': 'Jean Dupont'
        },
        {
            'company_name': 'Energy Solutions',
            'decision_maker_title': 'DSI',
            'decision_maker_name': 'Marie Martin'
        }
    ]
    
    result = await researcher.run_cycle(test_pains)
    print(json.dumps(result, indent=2, default=str))

if __name__ == "__main__":
    asyncio.run(main())
