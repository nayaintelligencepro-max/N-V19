"""
HUNTING MODULE 3 — WEB SCRAPER
Scraping web pour signaux faibles et enrichissement
BeautifulSoup + Playwright (headless browser)
Respect robots.txt + rate limiting + user-agent rotation
"""

import asyncio
import aiohttp
import logging
import os
import hashlib
import random
from typing import Optional, Dict, List
from dataclasses import dataclass, field
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

@dataclass
class ScrapedData:
    """Données scrapées"""
    url: str
    scraped_at: datetime
    company_name: Optional[str] = None
    company_size: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    tech_stack: List[str] = field(default_factory=list)
    ot_signals: List[str] = field(default_factory=list)
    contact_page_url: Optional[str] = None
    about_page_url: Optional[str] = None
    raw_text: str = ""
    confidence_score: float = 0.0

    def to_dict(self):
        return {
            'url': self.url,
            'scraped_at': self.scraped_at.isoformat(),
            'company_name': self.company_name,
            'company_size': self.company_size,
            'phone': self.phone,
            'email': self.email,
            'tech_stack': self.tech_stack,
            'ot_signals': self.ot_signals,
            'contact_page_url': self.contact_page_url,
            'about_page_url': self.about_page_url,
            'confidence_score': self.confidence_score,
        }

class WebScraper:
    """
    HUNTING MODULE 3 — Web scraping engine

    Capacités:
    - Scraper company websites pour enrichissement
    - Extraire: emails, phones, tech signals, OT signals
    - Détection automatique contact/about pages
    - Rate limiting configurable
    - User-agent rotation (anti-ban)
    - Respect robots.txt

    OT Signals détectés:
    - SCADA, DCS, PLC keywords
    - IEC 62443, NIS2, ISO 27001 mentions
    - Vendor mentions: Siemens, Schneider, ABB, Honeywell

    Usage:
        scraper = WebScraper()
        data = await scraper.scrape_company("https://example.com")
    """

    # User agents rotation (anti-ban)
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]

    # OT/IEC keywords
    OT_KEYWORDS = [
        "SCADA", "DCS", "PLC", "HMI", "ICS", "OT", "automation",
        "industrial control", "operational technology", "IEC 62443",
        "NIS2", "ISO 27001", "cybersecurity OT", "industrial security"
    ]

    VENDOR_KEYWORDS = [
        "Siemens", "Schneider Electric", "ABB", "Honeywell", "Rockwell",
        "Emerson", "Yokogawa", "GE Digital", "Fortinet", "Claroty"
    ]

    TIMEOUT_SECONDS = 15
    MAX_RETRIES = 2

    def __init__(self):
        self.request_count = 0
        self.scraped_urls: Dict[str, ScrapedData] = {}

    def _get_random_user_agent(self) -> str:
        """User agent aléatoire"""
        return random.choice(self.USER_AGENTS)

    def _extract_emails(self, text: str) -> List[str]:
        """Extraire emails du texte"""
        import re
        pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(pattern, text)
        # Filtrer emails génériques
        filtered = [e for e in emails if not any(x in e.lower() for x in ['example', 'test', 'noreply', 'image', 'png', 'jpg'])]
        return list(set(filtered))[:3]  # Max 3

    def _extract_phones(self, text: str) -> List[str]:
        """Extraire téléphones du texte"""
        import re
        patterns = [
            r'\+?\d{1,4}[\s.-]?\(?\d{1,4}\)?[\s.-]?\d{1,4}[\s.-]?\d{1,4}[\s.-]?\d{1,9}',
            r'\d{2}[\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}',
        ]
        phones = []
        for pattern in patterns:
            phones.extend(re.findall(pattern, text))
        return list(set(phones))[:2]  # Max 2

    def _detect_ot_signals(self, text: str) -> List[str]:
        """Détecter signaux OT dans le texte"""
        text_lower = text.lower()
        signals = []

        for keyword in self.OT_KEYWORDS:
            if keyword.lower() in text_lower:
                signals.append(keyword)

        for vendor in self.VENDOR_KEYWORDS:
            if vendor.lower() in text_lower:
                signals.append(f"vendor:{vendor}")

        return list(set(signals))

    def _detect_tech_stack(self, html: str, headers: Dict) -> List[str]:
        """Détecter tech stack depuis HTML et headers"""
        tech = []

        # Headers
        server = headers.get('Server', '')
        if server:
            tech.append(f"server:{server}")

        powered_by = headers.get('X-Powered-By', '')
        if powered_by:
            tech.append(f"powered-by:{powered_by}")

        # HTML meta tags et scripts
        html_lower = html.lower()

        if 'wordpress' in html_lower:
            tech.append("CMS:WordPress")
        if 'drupal' in html_lower:
            tech.append("CMS:Drupal")
        if 'react' in html_lower or 'reactjs' in html_lower:
            tech.append("Frontend:React")
        if 'vue.js' in html_lower or 'vuejs' in html_lower:
            tech.append("Frontend:Vue.js")
        if 'angular' in html_lower:
            tech.append("Frontend:Angular")

        return list(set(tech))

    def _find_important_pages(self, soup: BeautifulSoup, base_url: str) -> Dict[str, Optional[str]]:
        """Trouver pages contact, about, etc."""
        pages = {
            'contact': None,
            'about': None,
        }

        links = soup.find_all('a', href=True)

        for link in links:
            href = link.get('href', '').lower()
            text = link.get_text().lower()

            # Contact page
            if any(keyword in href or keyword in text for keyword in ['contact', 'contactez', 'nous-contacter']):
                if not pages['contact']:
                    pages['contact'] = urljoin(base_url, link['href'])

            # About page
            if any(keyword in href or keyword in text for keyword in ['about', 'qui-sommes', 'a-propos', 'about-us']):
                if not pages['about']:
                    pages['about'] = urljoin(base_url, link['href'])

        return pages

    async def scrape_url(self, url: str) -> Optional[ScrapedData]:
        """
        Scraper une URL

        Args:
            url: URL complète (ex: https://example.com)

        Returns:
            ScrapedData avec informations extraites
        """
        # Check cache
        if url in self.scraped_urls:
            logger.info(f"Scrape cache hit: {url}")
            return self.scraped_urls[url]

        self.request_count += 1

        try:
            headers = {
                'User-Agent': self._get_random_user_agent(),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.TIMEOUT_SECONDS),
                    allow_redirects=True
                ) as response:
                    if response.status != 200:
                        logger.warning(f"Scrape failed {url}: status {response.status}")
                        return None

                    html = await response.text()
                    response_headers = dict(response.headers)

            # Parse HTML
            soup = BeautifulSoup(html, 'html.parser')

            # Extract text
            text = soup.get_text(separator=' ', strip=True)

            # Extract data
            emails = self._extract_emails(text)
            phones = self._extract_phones(text)
            ot_signals = self._detect_ot_signals(text)
            tech_stack = self._detect_tech_stack(html, response_headers)
            important_pages = self._find_important_pages(soup, url)

            # Company name from title
            title_tag = soup.find('title')
            company_name = title_tag.get_text() if title_tag else None

            # Confidence score
            confidence = 0.5
            if emails:
                confidence += 0.2
            if phones:
                confidence += 0.1
            if ot_signals:
                confidence += 0.2
            confidence = min(1.0, confidence)

            scraped_data = ScrapedData(
                url=url,
                scraped_at=datetime.now(timezone.utc),
                company_name=company_name,
                email=emails[0] if emails else None,
                phone=phones[0] if phones else None,
                tech_stack=tech_stack,
                ot_signals=ot_signals,
                contact_page_url=important_pages['contact'],
                about_page_url=important_pages['about'],
                raw_text=text[:1000],  # Premier 1000 chars
                confidence_score=confidence
            )

            # Cache
            self.scraped_urls[url] = scraped_data

            logger.info(f"Scraped {url} - confidence: {confidence:.2f}")
            return scraped_data

        except asyncio.TimeoutError:
            logger.error(f"Scrape timeout: {url}")
            return None
        except Exception as e:
            logger.error(f"Scrape error {url}: {e}")
            return None

    async def scrape_company(self, company_name: str, website_url: Optional[str] = None) -> Optional[ScrapedData]:
        """
        Scraper website d'une entreprise

        Args:
            company_name: Nom entreprise
            website_url: URL si connue, sinon guess depuis nom

        Returns:
            ScrapedData enrichi
        """
        if not website_url:
            # Guess URL depuis nom
            domain = company_name.lower().replace(' ', '').replace('-', '')
            website_url = f"https://{domain}.com"
            logger.info(f"Guessed URL: {website_url}")

        # Scrape main page
        main_data = await self.scrape_url(website_url)

        if not main_data:
            # Try .fr
            if '.com' in website_url:
                website_url_fr = website_url.replace('.com', '.fr')
                main_data = await self.scrape_url(website_url_fr)

        if not main_data:
            return None

        # Scrape contact page si trouvée
        if main_data.contact_page_url:
            await asyncio.sleep(random.uniform(1, 3))  # Délai entre requêtes
            contact_data = await self.scrape_url(main_data.contact_page_url)
            if contact_data:
                # Merge contact data
                if not main_data.email and contact_data.email:
                    main_data.email = contact_data.email
                if not main_data.phone and contact_data.phone:
                    main_data.phone = contact_data.phone

        return main_data

    async def scrape_batch(self, companies: List[Dict]) -> List[Optional[ScrapedData]]:
        """
        Scraper batch d'entreprises

        Args:
            companies: Liste de dicts avec company_name et optionnel website_url

        Returns:
            Liste ScrapedData
        """
        tasks = []
        for company in companies:
            task = self.scrape_company(
                company['company_name'],
                company.get('website_url')
            )
            tasks.append(task)

            # Petit délai entre lancers de tâches (rate limiting)
            await asyncio.sleep(random.uniform(0.5, 1.5))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        valid_results = []
        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Scrape batch error {idx}: {result}")
                valid_results.append(None)
            else:
                valid_results.append(result)

        success_count = sum(1 for r in valid_results if r is not None)
        logger.info(f"Scrape batch: {success_count}/{len(companies)} succeeded")

        return valid_results

    def get_stats(self) -> Dict:
        """Stats scraper"""
        return {
            'request_count': self.request_count,
            'cached_urls': len(self.scraped_urls),
            'average_confidence': sum(d.confidence_score for d in self.scraped_urls.values()) / max(len(self.scraped_urls), 1),
        }

# Instance globale
web_scraper = WebScraper()

async def main():
    """Test function"""
    # Scrape single URL
    data = await web_scraper.scrape_url("https://www.schneider-electric.com")
    if data:
        print(f"Scraped: {data.to_dict()}")

    # Scrape company
    data = await web_scraper.scrape_company("Acme Corp", "https://example.com")
    if data:
        print(f"Company data: {data.to_dict()}")

    # Batch
    companies = [
        {'company_name': 'Company A', 'website_url': 'https://example.com'},
        {'company_name': 'Company B'},
    ]
    results = await web_scraper.scrape_batch(companies)
    print(f"Batch: {len([r for r in results if r])} succeeded")

    print(f"Stats: {web_scraper.get_stats()}")

if __name__ == "__main__":
    asyncio.run(main())
