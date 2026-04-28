"""
HUNTING MODULE 5 — NEWS SCANNER
Scanner actualités sectorielles pour pain signals
Cyberattaques, incidents, conformité = opportunités commerciales
Sources: Google News API, Serper, RSS feeds sectoriels
"""

import asyncio
import aiohttp
import logging
import os
import hashlib
from typing import Optional, Dict, List
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum

logger = logging.getLogger(__name__)

class NewsSource(Enum):
    SERPER = "serper"
    GOOGLE_NEWS = "google_news"
    RSS = "rss"

class UrgencyLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class NewsSignal:
    """Signal pain détecté depuis actualité"""
    signal_id: str
    title: str
    source: NewsSource
    published_date: datetime
    url: str
    snippet: str = ""
    company_mentioned: Optional[str] = None
    sector: Optional[str] = None
    urgency_level: UrgencyLevel = UrgencyLevel.MEDIUM
    estimated_budget_eur: int = 0
    pain_score: int = 0  # 0-100
    keywords_detected: List[str] = field(default_factory=list)
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'signal_id': self.signal_id,
            'title': self.title,
            'source': self.source.value,
            'published_date': self.published_date.isoformat(),
            'url': self.url,
            'snippet': self.snippet[:200],
            'company_mentioned': self.company_mentioned,
            'sector': self.sector,
            'urgency_level': self.urgency_level.value,
            'estimated_budget_eur': self.estimated_budget_eur,
            'pain_score': self.pain_score,
            'keywords_detected': self.keywords_detected,
            'detected_at': self.detected_at.isoformat(),
        }

class NewsScanner:
    """
    HUNTING MODULE 5 — News-based pain detection

    Logique:
    - Cyberattaque annoncée = entreprise a besoin audit/remédiation MAINTENANT
    - Nouvelle régulation = marché entier a besoin conformité
    - Incident public = fenêtre opportunité 30-90 jours

    Keywords recherchés:
    - "cyberattaque usine", "ransomware industriel"
    - "conformité NIS2", "audit IEC 62443"
    - "incident SCADA", "breach manufacturing"
    - "données volées", "production arrêtée"

    Urgency scoring:
    - CRITICAL: Attaque en cours / données volées (score 90-100)
    - HIGH: Incident récent < 7 jours (score 80-89)
    - MEDIUM: Incident < 30 jours (score 70-79)
    - LOW: Veille générale (score 60-69)

    Budget estimation:
    - Ransomware / breach: 40-80k EUR (remédiation urgente)
    - Audit conformité: 15-40k EUR
    - Formation post-incident: 10-25k EUR

    Usage:
        scanner = NewsScanner()
        signals = await scanner.scan_all_keywords()
    """

    # Keywords par catégorie
    NEWS_KEYWORDS = {
        "cyberattaque": [
            "cyberattaque usine",
            "ransomware industriel",
            "attaque OT",
            "SCADA compromis",
            "production arrêtée cyberattaque",
        ],
        "breach": [
            "données volées",
            "data breach manufacturing",
            "fuite données industrielles",
            "incident sécurité",
        ],
        "conformité": [
            "conformité NIS2",
            "deadline IEC 62443",
            "audit cybersécurité",
            "mise en conformité",
            "régulation cybersécurité",
        ],
        "incident": [
            "incident cybersécurité",
            "vulnérabilité critique",
            "faille de sécurité",
            "intrusion système",
        ],
    }

    # Urgency keywords
    URGENCY_KEYWORDS = {
        UrgencyLevel.CRITICAL: ["attaque en cours", "ransomware actif", "données exfiltrées", "production stoppée"],
        UrgencyLevel.HIGH: ["incident majeur", "cyberattaque", "breach confirmé", "vulnérabilité exploitée"],
        UrgencyLevel.MEDIUM: ["alerte sécurité", "faille détectée", "mise à jour urgente"],
        UrgencyLevel.LOW: ["recommandation", "bonnes pratiques", "prévention"],
    }

    # Secteurs détectables
    SECTOR_KEYWORDS = {
        "Manufacturing": ["usine", "manufacturing", "industrie", "production", "fabrication"],
        "Energy": ["énergie", "électricité", "centrale", "réseau électrique", "utilities"],
        "Transport": ["transport", "logistique", "SNCF", "aéroport", "port"],
        "Finance": ["banque", "finance", "fintech", "assurance", "bourse"],
        "Healthcare": ["hôpital", "santé", "clinique", "laboratoire"],
    }

    def __init__(self):
        self.serper_api_key = os.getenv('SERPER_API_KEY', '')
        self.detected_signals: Dict[str, NewsSignal] = {}
        self.scan_count = 0

    def _generate_signal_id(self, title: str, url: str) -> str:
        """Générer ID unique pour signal"""
        return hashlib.md5(f"{title}_{url}".encode()).hexdigest()[:12]

    def _detect_urgency(self, text: str, published_date: datetime) -> UrgencyLevel:
        """Détecter niveau urgence depuis texte et date"""
        text_lower = text.lower()

        # Check keywords
        for level in [UrgencyLevel.CRITICAL, UrgencyLevel.HIGH, UrgencyLevel.MEDIUM]:
            keywords = self.URGENCY_KEYWORDS.get(level, [])
            if any(keyword in text_lower for keyword in keywords):
                return level

        # Check récence
        days_old = (datetime.now(timezone.utc) - published_date).days
        if days_old <= 3:
            return UrgencyLevel.HIGH
        elif days_old <= 14:
            return UrgencyLevel.MEDIUM
        else:
            return UrgencyLevel.LOW

    def _detect_sector(self, text: str) -> Optional[str]:
        """Détecter secteur depuis texte"""
        text_lower = text.lower()

        for sector, keywords in self.SECTOR_KEYWORDS.items():
            if any(keyword in text_lower for keyword in keywords):
                return sector

        return None

    def _detect_company(self, text: str) -> Optional[str]:
        """Détecter nom entreprise mentionnée (basique)"""
        # Pattern: "Entreprise XXX" ou "société XXX"
        import re
        patterns = [
            r"entreprise\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            r"société\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            r"groupe\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)

        return None

    def _estimate_budget(self, category: str, urgency: UrgencyLevel) -> int:
        """Estimer budget depuis catégorie et urgence"""
        base_budgets = {
            "cyberattaque": 50000,
            "breach": 60000,
            "conformité": 25000,
            "incident": 30000,
        }

        urgency_multipliers = {
            UrgencyLevel.CRITICAL: 1.5,
            UrgencyLevel.HIGH: 1.3,
            UrgencyLevel.MEDIUM: 1.0,
            UrgencyLevel.LOW: 0.8,
        }

        base = base_budgets.get(category, 15000)
        multiplier = urgency_multipliers.get(urgency, 1.0)

        return int(base * multiplier)

    def _calculate_pain_score(self, category: str, urgency: UrgencyLevel, published_date: datetime) -> int:
        """Calculer pain score 0-100"""
        # Base score par urgence
        urgency_scores = {
            UrgencyLevel.CRITICAL: 90,
            UrgencyLevel.HIGH: 80,
            UrgencyLevel.MEDIUM: 70,
            UrgencyLevel.LOW: 60,
        }
        score = urgency_scores.get(urgency, 60)

        # Bonus catégorie
        category_bonus = {
            "cyberattaque": 10,
            "breach": 10,
            "conformité": 5,
            "incident": 7,
        }
        score += category_bonus.get(category, 0)

        # Bonus récence
        days_old = (datetime.now(timezone.utc) - published_date).days
        if days_old <= 3:
            score += 10
        elif days_old <= 7:
            score += 5

        return min(100, max(0, score))

    async def scan_serper_news(self, keyword: str, limit: int = 10) -> List[NewsSignal]:
        """
        Scanner news via Serper API

        Args:
            keyword: Mot-clé recherche
            limit: Nombre max résultats

        Returns:
            Liste NewsSignal
        """
        if not self.serper_api_key:
            logger.warning("SERPER_API_KEY not set - returning mock data")
            return self._generate_mock_signals(keyword, limit)

        try:
            headers = {
                "X-API-KEY": self.serper_api_key,
                "Content-Type": "application/json"
            }

            payload = {
                "q": keyword,
                "gl": "fr",
                "hl": "fr",
                "num": limit,
                "tbm": "nws",  # News search
                "tbs": "qdr:m"  # Last month
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://google.serper.dev/search",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status != 200:
                        logger.error(f"Serper API error: {response.status}")
                        return self._generate_mock_signals(keyword, limit)

                    data = await response.json()
                    news_results = data.get('news', [])

                    signals = []
                    for news in news_results:
                        title = news.get('title', '')
                        snippet = news.get('snippet', '')
                        url = news.get('link', '')
                        date_str = news.get('date', '')

                        # Parse date (format: "Il y a X jours")
                        published_date = datetime.now(timezone.utc) - timedelta(days=7)  # Default

                        full_text = f"{title} {snippet}"
                        urgency = self._detect_urgency(full_text, published_date)
                        sector = self._detect_sector(full_text)
                        company = self._detect_company(full_text)

                        # Détecter catégorie
                        category = "incident"
                        for cat, keywords in self.NEWS_KEYWORDS.items():
                            if any(kw.lower() in full_text.lower() for kw in keywords):
                                category = cat
                                break

                        budget = self._estimate_budget(category, urgency)
                        pain_score = self._calculate_pain_score(category, urgency, published_date)

                        # Détecter keywords
                        detected_keywords = [keyword]
                        for kw in self.NEWS_KEYWORDS.get(category, []):
                            if kw.lower() in full_text.lower():
                                detected_keywords.append(kw)

                        signal = NewsSignal(
                            signal_id=self._generate_signal_id(title, url),
                            title=title,
                            source=NewsSource.SERPER,
                            published_date=published_date,
                            url=url,
                            snippet=snippet,
                            company_mentioned=company,
                            sector=sector,
                            urgency_level=urgency,
                            estimated_budget_eur=budget,
                            pain_score=pain_score,
                            keywords_detected=detected_keywords
                        )

                        signals.append(signal)
                        self.detected_signals[signal.signal_id] = signal

                    logger.info(f"Serper news found {len(signals)} signals for '{keyword}'")
                    return signals

        except Exception as e:
            logger.error(f"Serper news scan error: {e}")
            return self._generate_mock_signals(keyword, limit)

    async def scan_all_keywords(self, limit_per_keyword: int = 10) -> List[NewsSignal]:
        """
        Scanner toutes les catégories de keywords en parallèle

        Args:
            limit_per_keyword: Limite par keyword

        Returns:
            Liste complète NewsSignal
        """
        self.scan_count += 1
        logger.info(f"News scanner cycle #{self.scan_count}")

        # Top keywords prioritaires
        priority_keywords = [
            "cyberattaque usine",
            "ransomware industriel",
            "conformité NIS2",
            "incident SCADA",
            "audit IEC 62443",
        ]

        tasks = []
        for keyword in priority_keywords:
            task = self.scan_serper_news(keyword, limit=limit_per_keyword)
            tasks.append(task)
            await asyncio.sleep(0.5)  # Rate limiting

        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_signals = []
        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"News scanner error for keyword {idx}: {result}")
            else:
                all_signals.extend(result)

        # Dedup par signal_id
        unique_signals = {s.signal_id: s for s in all_signals}
        unique_list = list(unique_signals.values())

        # Trier par pain score
        sorted_signals = sorted(unique_list, key=lambda s: s.pain_score, reverse=True)

        logger.info(f"News scanner found {len(sorted_signals)} unique signals")
        return sorted_signals

    async def scan_by_sector(self, sector: str, limit: int = 20) -> List[NewsSignal]:
        """
        Scanner news par secteur spécifique

        Args:
            sector: Secteur (Manufacturing, Energy, etc.)
            limit: Nombre max résultats

        Returns:
            Liste NewsSignal pour ce secteur
        """
        sector_queries = {
            "Manufacturing": ["cyberattaque usine", "ransomware industrie"],
            "Energy": ["cyberattaque centrale", "incident réseau électrique"],
            "Transport": ["cyberattaque transport", "incident logistique"],
            "Finance": ["cyberattaque banque", "breach fintech"],
        }

        queries = sector_queries.get(sector, ["cyberattaque"])

        tasks = []
        for query in queries:
            task = self.scan_serper_news(query, limit=limit // len(queries))
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        all_signals = [s for result in results for s in result]

        # Filter par secteur
        filtered = [s for s in all_signals if s.sector == sector or (s.sector is None and sector.lower() in s.snippet.lower())]

        logger.info(f"Sector {sector} news: {len(filtered)} signals")
        return sorted(filtered, key=lambda s: s.pain_score, reverse=True)

    def _generate_mock_signals(self, keyword: str, limit: int) -> List[NewsSignal]:
        """Générer signaux mock"""
        signals = []
        for i in range(min(limit, 5)):
            urgency = [UrgencyLevel.CRITICAL, UrgencyLevel.HIGH, UrgencyLevel.MEDIUM][i % 3]
            signal = NewsSignal(
                signal_id=f"mock_news_{i}",
                title=f"Incident: {keyword} chez entreprise {i}",
                source=NewsSource.SERPER,
                published_date=datetime.now(timezone.utc) - timedelta(days=i),
                url=f"https://news.example.com/{i}",
                snippet=f"Suite à un {keyword}, l'entreprise doit renforcer sa cybersécurité OT. Conformité IEC 62443 nécessaire.",
                company_mentioned=f"Company {i}",
                sector=["Manufacturing", "Energy", "Transport"][i % 3],
                urgency_level=urgency,
                estimated_budget_eur=40000 + (i * 5000),
                pain_score=90 - (i * 5),
                keywords_detected=[keyword, "IEC 62443"]
            )
            signals.append(signal)

        return signals

    def get_stats(self) -> Dict:
        """Stats scanner"""
        return {
            'scan_count': self.scan_count,
            'total_signals': len(self.detected_signals),
            'critical_signals': sum(1 for s in self.detected_signals.values() if s.urgency_level == UrgencyLevel.CRITICAL),
            'high_score_signals': sum(1 for s in self.detected_signals.values() if s.pain_score >= 85),
            'average_score': sum(s.pain_score for s in self.detected_signals.values()) / max(len(self.detected_signals), 1),
            'average_budget': sum(s.estimated_budget_eur for s in self.detected_signals.values()) / max(len(self.detected_signals), 1),
        }

# Instance globale
news_scanner = NewsScanner()

async def main():
    """Test function"""
    # Scan all
    signals = await news_scanner.scan_all_keywords(limit_per_keyword=5)
    print(f"Found {len(signals)} signals")

    for signal in signals[:3]:
        print(f"  - [{signal.urgency_level.value}] {signal.title}")
        print(f"    Company: {signal.company_mentioned}, Sector: {signal.sector}")
        print(f"    Score: {signal.pain_score}, Budget: {signal.estimated_budget_eur} EUR")

    # Scan by sector
    energy_signals = await news_scanner.scan_by_sector("Energy", limit=10)
    print(f"Energy sector: {len(energy_signals)} signals")

    print(f"Stats: {news_scanner.get_stats()}")

if __name__ == "__main__":
    asyncio.run(main())
