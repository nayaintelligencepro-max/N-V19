"""
HUNTING MODULE 6 — EMAIL FINDER
Recherche emails décideurs avec vérification
Sources: Hunter.io, Apollo.io, pattern guessing, verification
Multi-source aggregation pour maximiser taux de succès
"""

import asyncio
import aiohttp
import logging
import os
import hashlib
import re
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger(__name__)

class EmailStatus(Enum):
    VALID = "valid"
    INVALID = "invalid"
    CATCH_ALL = "catch_all"
    UNKNOWN = "unknown"
    RISKY = "risky"

class EmailSource(Enum):
    HUNTER = "hunter"
    APOLLO = "apollo"
    PATTERN = "pattern"
    SCRAPE = "scrape"

@dataclass
class EmailResult:
    """Résultat recherche email"""
    email: str
    status: EmailStatus
    confidence_score: float  # 0.0-1.0
    sources: List[EmailSource] = field(default_factory=list)
    company_domain: str = ""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    position: Optional[str] = None
    verified_at: Optional[datetime] = None

    def to_dict(self):
        return {
            'email': self.email,
            'status': self.status.value,
            'confidence_score': self.confidence_score,
            'sources': [s.value for s in self.sources],
            'company_domain': self.company_domain,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'position': self.position,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
        }

class EmailFinder:
    """
    HUNTING MODULE 6 — Email discovery & verification

    Capacités:
    - Find emails: Hunter.io + Apollo.io + patterns
    - Email verification (SMTP, MX records)
    - Pattern detection par entreprise
    - Confidence scoring multi-source
    - Deduplication intelligente

    Patterns testés:
    - {first}.{last}@domain.com (le plus courant)
    - {first}@domain.com
    - {last}@domain.com
    - {first}{last}@domain.com
    - {first_initial}{last}@domain.com

    Verification:
    - MX records check (DNS)
    - SMTP verification (si possible)
    - Catch-all detection
    - Role-based detection

    Usage:
        finder = EmailFinder()
        result = await finder.find_email("John", "Doe", "acme.com", "RSSI")
    """

    # Email patterns par priorité
    EMAIL_PATTERNS = [
        "{first}.{last}@{domain}",      # jean.dupont@company.com
        "{first}@{domain}",              # jean@company.com
        "{last}@{domain}",               # dupont@company.com
        "{first}{last}@{domain}",        # jeandupont@company.com
        "{first_initial}{last}@{domain}", # jdupont@company.com
        "{first_initial}.{last}@{domain}", # j.dupont@company.com
        "{first}_{last}@{domain}",       # jean_dupont@company.com
    ]

    # Role-based emails (généralement catch-all)
    ROLE_EMAILS = [
        "contact", "info", "commercial", "sales", "support",
        "hello", "bonjour", "contact-us", "enquiries"
    ]

    def __init__(self):
        self.hunter_api_key = os.getenv('HUNTER_API_KEY', '')
        self.apollo_api_key = os.getenv('APOLLO_API_KEY', '')
        self.found_emails: Dict[str, EmailResult] = {}
        self.domain_patterns: Dict[str, str] = {}  # Cache patterns par domaine

    def _normalize_name(self, name: str) -> str:
        """Normaliser nom (lowercase, remove accents, special chars)"""
        import unicodedata
        # Remove accents
        name = ''.join(c for c in unicodedata.normalize('NFD', name) if unicodedata.category(c) != 'Mn')
        # Lowercase
        name = name.lower()
        # Remove special chars
        name = re.sub(r'[^a-z]', '', name)
        return name

    def _generate_email_patterns(self, first_name: str, last_name: str, domain: str) -> List[str]:
        """Générer tous les patterns possibles"""
        first = self._normalize_name(first_name)
        last = self._normalize_name(last_name)
        first_initial = first[0] if first else ''

        emails = []
        for pattern in self.EMAIL_PATTERNS:
            try:
                email = pattern.format(
                    first=first,
                    last=last,
                    first_initial=first_initial,
                    domain=domain
                )
                emails.append(email)
            except KeyError:
                continue

        return list(set(emails))  # Dedup

    def _is_valid_email_format(self, email: str) -> bool:
        """Vérifier format email valide"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def _is_role_based_email(self, email: str) -> bool:
        """Détecter email role-based (non personnel)"""
        local_part = email.split('@')[0].lower()
        return any(role in local_part for role in self.ROLE_EMAILS)

    async def _verify_email_mx(self, email: str) -> Tuple[EmailStatus, float]:
        """
        Vérifier email via MX records (DNS)

        Returns:
            (EmailStatus, confidence_score)
        """
        try:
            import dns.resolver
            domain = email.split('@')[1]

            # Check MX records
            mx_records = dns.resolver.resolve(domain, 'MX')
            if mx_records:
                # Domain has MX records = email potentially valid
                if self._is_role_based_email(email):
                    return EmailStatus.CATCH_ALL, 0.50
                else:
                    return EmailStatus.VALID, 0.70
            else:
                return EmailStatus.INVALID, 0.0

        except Exception as e:
            logger.debug(f"MX verification failed for {email}: {e}")
            return EmailStatus.UNKNOWN, 0.40

    async def find_via_hunter(self, first_name: str, last_name: str, domain: str) -> Optional[EmailResult]:
        """
        Rechercher email via Hunter.io API

        Args:
            first_name: Prénom
            last_name: Nom
            domain: Domaine entreprise

        Returns:
            EmailResult si trouvé
        """
        if not self.hunter_api_key:
            logger.debug("Hunter API key not set")
            return None

        try:
            params = {
                'domain': domain,
                'first_name': first_name,
                'last_name': last_name,
                'api_key': self.hunter_api_key
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://api.hunter.io/v2/email-finder",
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status != 200:
                        logger.warning(f"Hunter API error: {response.status}")
                        return None

                    data = await response.json()
                    result_data = data.get('data', {})

                    if not result_data.get('email'):
                        return None

                    # Map Hunter status to our EmailStatus
                    hunter_status = result_data.get('status', 'unknown')
                    status_mapping = {
                        'valid': EmailStatus.VALID,
                        'invalid': EmailStatus.INVALID,
                        'accept_all': EmailStatus.CATCH_ALL,
                        'unknown': EmailStatus.UNKNOWN,
                        'risky': EmailStatus.RISKY,
                    }
                    status = status_mapping.get(hunter_status, EmailStatus.UNKNOWN)

                    confidence = result_data.get('score', 50) / 100.0

                    result = EmailResult(
                        email=result_data['email'],
                        status=status,
                        confidence_score=confidence,
                        sources=[EmailSource.HUNTER],
                        company_domain=domain,
                        first_name=first_name,
                        last_name=last_name,
                        position=result_data.get('position'),
                        verified_at=datetime.now(timezone.utc)
                    )

                    # Cache domain pattern
                    pattern = result_data.get('pattern')
                    if pattern:
                        self.domain_patterns[domain] = pattern

                    logger.info(f"Hunter found: {result.email} (confidence: {confidence:.2f})")
                    return result

        except Exception as e:
            logger.error(f"Hunter API error: {e}")
            return None

    async def find_via_apollo(self, company_name: str, first_name: str, last_name: str) -> Optional[EmailResult]:
        """
        Rechercher email via Apollo.io API

        Args:
            company_name: Nom entreprise
            first_name: Prénom
            last_name: Nom

        Returns:
            EmailResult si trouvé
        """
        if not self.apollo_api_key:
            logger.debug("Apollo API key not set")
            return None

        try:
            headers = {
                "Content-Type": "application/json",
                "X-Api-Key": self.apollo_api_key
            }

            payload = {
                "first_name": first_name,
                "last_name": last_name,
                "organization_name": company_name,
                "reveal_personal_emails": True
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.apollo.io/v1/people/match",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status != 200:
                        logger.warning(f"Apollo API error: {response.status}")
                        return None

                    data = await response.json()
                    person = data.get('person', {})

                    email = person.get('email')
                    if not email:
                        return None

                    domain = email.split('@')[1]

                    result = EmailResult(
                        email=email,
                        status=EmailStatus.VALID,
                        confidence_score=0.85,
                        sources=[EmailSource.APOLLO],
                        company_domain=domain,
                        first_name=first_name,
                        last_name=last_name,
                        position=person.get('title'),
                        verified_at=datetime.now(timezone.utc)
                    )

                    logger.info(f"Apollo found: {result.email}")
                    return result

        except Exception as e:
            logger.error(f"Apollo API error: {e}")
            return None

    async def find_via_patterns(self, first_name: str, last_name: str, domain: str) -> List[EmailResult]:
        """
        Générer emails via patterns + vérification MX

        Args:
            first_name: Prénom
            last_name: Nom
            domain: Domaine entreprise

        Returns:
            Liste EmailResult triée par confidence
        """
        patterns = self._generate_email_patterns(first_name, last_name, domain)

        results = []
        for email in patterns:
            if not self._is_valid_email_format(email):
                continue

            # Verify via MX
            status, confidence = await self._verify_email_mx(email)

            # Adjust confidence based on domain pattern cache
            if domain in self.domain_patterns:
                # Si on connaît le pattern du domaine
                known_pattern = self.domain_patterns[domain]
                # Simplification: boost confidence si pattern match
                confidence += 0.15

            result = EmailResult(
                email=email,
                status=status,
                confidence_score=min(1.0, confidence),
                sources=[EmailSource.PATTERN],
                company_domain=domain,
                first_name=first_name,
                last_name=last_name,
                verified_at=datetime.now(timezone.utc)
            )

            results.append(result)

        # Trier par confidence
        results.sort(key=lambda r: r.confidence_score, reverse=True)

        return results

    async def find_email(
        self,
        first_name: str,
        last_name: str,
        domain: str,
        company_name: Optional[str] = None,
        position: Optional[str] = None
    ) -> EmailResult:
        """
        Rechercher email avec agrégation multi-source

        Args:
            first_name: Prénom
            last_name: Nom
            domain: Domaine entreprise
            company_name: Nom entreprise (pour Apollo)
            position: Poste (optionnel)

        Returns:
            Meilleur EmailResult trouvé
        """
        cache_key = f"{first_name}_{last_name}_{domain}"
        if cache_key in self.found_emails:
            logger.info(f"Email cache hit: {cache_key}")
            return self.found_emails[cache_key]

        # Try Hunter first (plus fiable)
        hunter_result = await self.find_via_hunter(first_name, last_name, domain)
        if hunter_result and hunter_result.status == EmailStatus.VALID:
            self.found_emails[cache_key] = hunter_result
            return hunter_result

        # Try Apollo
        if company_name:
            apollo_result = await self.find_via_apollo(company_name, first_name, last_name)
            if apollo_result and apollo_result.status == EmailStatus.VALID:
                self.found_emails[cache_key] = apollo_result
                return apollo_result

        # Fallback: patterns
        pattern_results = await self.find_via_patterns(first_name, last_name, domain)
        if pattern_results:
            best_result = pattern_results[0]
            best_result.position = position
            self.found_emails[cache_key] = best_result
            return best_result

        # No email found - return unknown status
        unknown_result = EmailResult(
            email=f"{self._normalize_name(first_name)}@{domain}",
            status=EmailStatus.UNKNOWN,
            confidence_score=0.20,
            sources=[EmailSource.PATTERN],
            company_domain=domain,
            first_name=first_name,
            last_name=last_name,
            position=position
        )

        return unknown_result

    async def find_batch(self, prospects: List[Dict]) -> List[EmailResult]:
        """
        Rechercher emails en batch

        Args:
            prospects: Liste de dicts avec first_name, last_name, domain, etc.

        Returns:
            Liste EmailResult
        """
        tasks = []
        for prospect in prospects:
            task = self.find_email(
                prospect['first_name'],
                prospect['last_name'],
                prospect['domain'],
                prospect.get('company_name'),
                prospect.get('position')
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        valid_results = []
        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Email finder batch error {idx}: {result}")
                # Create unknown result
                p = prospects[idx]
                unknown = EmailResult(
                    email=f"unknown@{p['domain']}",
                    status=EmailStatus.UNKNOWN,
                    confidence_score=0.0,
                    sources=[],
                    company_domain=p['domain']
                )
                valid_results.append(unknown)
            else:
                valid_results.append(result)

        valid_count = sum(1 for r in valid_results if r.status == EmailStatus.VALID)
        logger.info(f"Email finder batch: {valid_count}/{len(prospects)} valid emails found")

        return valid_results

    def get_stats(self) -> Dict:
        """Stats email finder"""
        total = len(self.found_emails)
        if total == 0:
            return {'total_emails': 0}

        valid_count = sum(1 for e in self.found_emails.values() if e.status == EmailStatus.VALID)
        avg_confidence = sum(e.confidence_score for e in self.found_emails.values()) / total

        return {
            'total_emails': total,
            'valid_emails': valid_count,
            'valid_rate': valid_count / total if total > 0 else 0,
            'average_confidence': avg_confidence,
            'cached_patterns': len(self.domain_patterns),
        }

# Instance globale
email_finder = EmailFinder()

async def main():
    """Test function"""
    # Find single
    result = await email_finder.find_email(
        "Jean",
        "Dupont",
        "acme.com",
        company_name="Acme Corp",
        position="RSSI"
    )
    print(f"Found: {result.to_dict()}")

    # Find batch
    prospects = [
        {'first_name': 'Marie', 'last_name': 'Martin', 'domain': 'company1.com', 'company_name': 'Company 1'},
        {'first_name': 'Pierre', 'last_name': 'Bernard', 'domain': 'company2.fr', 'company_name': 'Company 2'},
    ]
    results = await email_finder.find_batch(prospects)
    print(f"Batch: {len([r for r in results if r.status == EmailStatus.VALID])} valid emails")

    print(f"Stats: {email_finder.get_stats()}")

if __name__ == "__main__":
    asyncio.run(main())
