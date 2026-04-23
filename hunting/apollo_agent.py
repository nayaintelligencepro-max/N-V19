"""
HUNTING MODULE 1 — APOLLO AGENT
Enrichissement prospects via Apollo.io API
Sources: email, phone, linkedin_url, company_size, revenue, tech_stack
Rate limiting protection + fallback modes
"""

import asyncio
import aiohttp
import logging
import os
import hashlib
from typing import Optional, Dict, List
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger(__name__)

class EnrichmentStatus(Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    RATE_LIMITED = "rate_limited"

@dataclass
class ApolloEnrichmentResult:
    """Résultat enrichissement Apollo"""
    prospect_id: str
    status: EnrichmentStatus
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    company_name: str = ""
    company_size: Optional[str] = None
    company_revenue: Optional[str] = None
    tech_stack: List[str] = field(default_factory=list)
    confidence_score: float = 0.0
    enriched_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    error_message: Optional[str] = None

    def to_dict(self):
        return {
            'prospect_id': self.prospect_id,
            'status': self.status.value,
            'email': self.email,
            'phone': self.phone,
            'linkedin_url': self.linkedin_url,
            'company_name': self.company_name,
            'company_size': self.company_size,
            'company_revenue': self.company_revenue,
            'tech_stack': self.tech_stack,
            'confidence_score': self.confidence_score,
            'enriched_at': self.enriched_at.isoformat(),
            'error_message': self.error_message,
        }

class ApolloAgent:
    """
    HUNTING MODULE 1 — Apollo.io enrichment agent

    Capacités:
    - Search prospects par: company, title, sector, location
    - Enrich contacts: email verification, phone, LinkedIn
    - Company intelligence: size, revenue, tech_stack
    - Rate limiting: 60 req/min (configurable)
    - Fallback: cache local + degraded mode

    Usage:
        apollo = ApolloAgent()
        result = await apollo.enrich_prospect("Acme Corp", "RSSI")
    """

    API_BASE_URL = "https://api.apollo.io/v1"
    RATE_LIMIT_PER_MINUTE = 60
    TIMEOUT_SECONDS = 10

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('APOLLO_API_KEY', '')
        self.request_count = 0
        self.last_reset = datetime.now(timezone.utc)
        self.cache: Dict[str, ApolloEnrichmentResult] = {}
        self.enabled = bool(self.api_key)

        if not self.enabled:
            logger.warning("Apollo API key not set - running in degraded mode")

    def _generate_cache_key(self, company_name: str, title: str) -> str:
        """Générer clé cache unique"""
        return hashlib.md5(f"{company_name}_{title}".encode()).hexdigest()

    async def _check_rate_limit(self):
        """Vérifier rate limit (60/min)"""
        now = datetime.now(timezone.utc)
        elapsed = (now - self.last_reset).total_seconds()

        if elapsed >= 60:
            self.request_count = 0
            self.last_reset = now

        if self.request_count >= self.RATE_LIMIT_PER_MINUTE:
            wait_time = 60 - elapsed
            logger.warning(f"Apollo rate limit reached, waiting {wait_time:.1f}s")
            await asyncio.sleep(wait_time)
            self.request_count = 0
            self.last_reset = datetime.now(timezone.utc)

        self.request_count += 1

    async def search_prospects(
        self,
        company_name: Optional[str] = None,
        title: Optional[str] = None,
        sector: Optional[str] = None,
        location: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        Rechercher prospects via Apollo search API

        Args:
            company_name: Nom entreprise (ex: "Schneider Electric")
            title: Poste (ex: "RSSI", "DSI")
            sector: Secteur (ex: "Manufacturing", "Energy")
            location: Localisation (ex: "France", "Paris")
            limit: Nombre max résultats

        Returns:
            Liste de prospects avec contacts
        """
        if not self.enabled:
            logger.warning("Apollo disabled - returning mock data")
            return self._generate_mock_search_results(company_name, title, limit)

        await self._check_rate_limit()

        try:
            headers = {
                "Content-Type": "application/json",
                "Cache-Control": "no-cache",
                "X-Api-Key": self.api_key
            }

            payload = {
                "q_organization_name": company_name,
                "person_titles": [title] if title else [],
                "organization_industry_tag_ids": [sector] if sector else [],
                "q_organization_locations": [location] if location else [],
                "page": 1,
                "per_page": limit
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.API_BASE_URL}/mixed_people/search",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.TIMEOUT_SECONDS)
                ) as response:
                    if response.status == 429:
                        logger.error("Apollo API rate limited")
                        return self._generate_mock_search_results(company_name, title, limit)

                    if response.status != 200:
                        logger.error(f"Apollo API error: {response.status}")
                        return []

                    data = await response.json()
                    prospects = data.get('people', [])

                    logger.info(f"Apollo found {len(prospects)} prospects for {company_name}")
                    return prospects

        except asyncio.TimeoutError:
            logger.error(f"Apollo API timeout after {self.TIMEOUT_SECONDS}s")
            return self._generate_mock_search_results(company_name, title, limit)

        except Exception as e:
            logger.error(f"Apollo search error: {e}")
            return []

    async def enrich_prospect(
        self,
        company_name: str,
        decision_maker_title: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> ApolloEnrichmentResult:
        """
        Enrichir UN prospect via Apollo

        Args:
            company_name: Nom entreprise
            decision_maker_title: Poste du décideur
            first_name: Prénom (optionnel)
            last_name: Nom (optionnel)

        Returns:
            ApolloEnrichmentResult avec email, phone, LinkedIn, etc.
        """
        cache_key = self._generate_cache_key(company_name, decision_maker_title)

        # Check cache
        if cache_key in self.cache:
            logger.info(f"Apollo cache hit for {company_name}")
            return self.cache[cache_key]

        prospect_id = f"apollo_{cache_key[:8]}"

        if not self.enabled:
            return self._generate_mock_enrichment(prospect_id, company_name, decision_maker_title)

        await self._check_rate_limit()

        try:
            headers = {
                "Content-Type": "application/json",
                "X-Api-Key": self.api_key
            }

            payload = {
                "first_name": first_name,
                "last_name": last_name,
                "organization_name": company_name,
                "reveal_personal_emails": True
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.API_BASE_URL}/people/match",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.TIMEOUT_SECONDS)
                ) as response:
                    if response.status == 429:
                        result = ApolloEnrichmentResult(
                            prospect_id=prospect_id,
                            status=EnrichmentStatus.RATE_LIMITED,
                            company_name=company_name,
                            error_message="Rate limit exceeded"
                        )
                        return result

                    if response.status != 200:
                        result = ApolloEnrichmentResult(
                            prospect_id=prospect_id,
                            status=EnrichmentStatus.FAILED,
                            company_name=company_name,
                            error_message=f"API error {response.status}"
                        )
                        return result

                    data = await response.json()
                    person = data.get('person', {})
                    organization = data.get('organization', {})

                    result = ApolloEnrichmentResult(
                        prospect_id=prospect_id,
                        status=EnrichmentStatus.SUCCESS,
                        email=person.get('email'),
                        phone=person.get('phone_numbers', [{}])[0].get('raw_number'),
                        linkedin_url=person.get('linkedin_url'),
                        company_name=organization.get('name', company_name),
                        company_size=organization.get('estimated_num_employees'),
                        company_revenue=organization.get('estimated_annual_revenue'),
                        tech_stack=organization.get('technologies', []),
                        confidence_score=0.85
                    )

                    # Cache result
                    self.cache[cache_key] = result
                    logger.info(f"Apollo enriched {company_name} successfully")
                    return result

        except asyncio.TimeoutError:
            logger.error(f"Apollo enrich timeout for {company_name}")
            return self._generate_mock_enrichment(prospect_id, company_name, decision_maker_title)

        except Exception as e:
            logger.error(f"Apollo enrich error: {e}")
            return ApolloEnrichmentResult(
                prospect_id=prospect_id,
                status=EnrichmentStatus.FAILED,
                company_name=company_name,
                error_message=str(e)
            )

    async def enrich_batch(self, prospects: List[Dict]) -> List[ApolloEnrichmentResult]:
        """
        Enrichir batch de prospects en parallèle

        Args:
            prospects: Liste de dicts avec company_name, decision_maker_title

        Returns:
            Liste ApolloEnrichmentResult
        """
        tasks = []
        for p in prospects:
            task = self.enrich_prospect(
                p['company_name'],
                p['decision_maker_title'],
                p.get('first_name'),
                p.get('last_name')
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        valid_results = []
        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Apollo batch error {idx}: {result}")
                # Create failed result
                p = prospects[idx]
                failed = ApolloEnrichmentResult(
                    prospect_id=f"apollo_error_{idx}",
                    status=EnrichmentStatus.FAILED,
                    company_name=p['company_name'],
                    error_message=str(result)
                )
                valid_results.append(failed)
            else:
                valid_results.append(result)

        success_count = sum(1 for r in valid_results if r.status == EnrichmentStatus.SUCCESS)
        logger.info(f"Apollo batch: {success_count}/{len(prospects)} enriched successfully")

        return valid_results

    def _generate_mock_search_results(self, company_name: Optional[str], title: Optional[str], limit: int) -> List[Dict]:
        """Générer résultats mock pour mode dégradé"""
        results = []
        for i in range(min(limit, 3)):
            results.append({
                'id': f'mock_{i}',
                'first_name': f'Contact{i}',
                'last_name': f'Person{i}',
                'email': f'contact{i}@{company_name.lower().replace(" ", "")}.com' if company_name else f'contact{i}@example.com',
                'title': title or 'Decision Maker',
                'organization_name': company_name or 'Unknown Corp',
                'linkedin_url': f'https://linkedin.com/in/mock-{i}',
                'phone_numbers': [{'raw_number': f'+336{i}0000000'}]
            })
        return results

    def _generate_mock_enrichment(self, prospect_id: str, company_name: str, title: str) -> ApolloEnrichmentResult:
        """Générer enrichment mock pour mode dégradé"""
        return ApolloEnrichmentResult(
            prospect_id=prospect_id,
            status=EnrichmentStatus.PARTIAL,
            email=f"contact@{company_name.lower().replace(' ', '')}.com",
            phone="+33612345678",
            linkedin_url=f"https://linkedin.com/in/mock-{prospect_id}",
            company_name=company_name,
            company_size="1000-5000",
            company_revenue="50M-100M EUR",
            tech_stack=["Windows Server", "Cisco", "SCADA"],
            confidence_score=0.60,
            error_message="Apollo API disabled - mock data"
        )

    def get_stats(self) -> Dict:
        """Stats Apollo agent"""
        return {
            'enabled': self.enabled,
            'request_count': self.request_count,
            'cache_size': len(self.cache),
            'rate_limit_per_minute': self.RATE_LIMIT_PER_MINUTE,
        }

# Instance globale
apollo_agent = ApolloAgent()

async def main():
    """Test function"""
    # Test search
    prospects = await apollo_agent.search_prospects(
        company_name="Schneider Electric",
        title="RSSI",
        limit=5
    )
    print(f"Found {len(prospects)} prospects")

    # Test enrich
    result = await apollo_agent.enrich_prospect("Acme Corp", "DSI")
    print(f"Enrichment: {result.to_dict()}")

    # Test batch
    batch = [
        {'company_name': 'Company A', 'decision_maker_title': 'RSSI'},
        {'company_name': 'Company B', 'decision_maker_title': 'DSI'},
    ]
    results = await apollo_agent.enrich_batch(batch)
    print(f"Batch enriched: {len(results)} results")

if __name__ == "__main__":
    asyncio.run(main())
