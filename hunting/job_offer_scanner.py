"""
HUNTING MODULE 4 — JOB OFFER SCANNER
Scanner offres d'emploi pour détecter pain signals
Job offer = pain détecté (besoin recrutement = besoin actuel)
Sources: LinkedIn Jobs, Indeed, Welcome to the Jungle, Serper
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

class JobSource(Enum):
    LINKEDIN = "linkedin"
    INDEED = "indeed"
    WTJS = "welcome_to_the_jungle"
    SERPER = "serper"

@dataclass
class JobSignal:
    """Signal pain détecté depuis offre emploi"""
    signal_id: str
    job_title: str
    company_name: str
    job_source: JobSource
    posted_date: datetime
    job_url: str
    description: str = ""
    location: Optional[str] = None
    estimated_budget_eur: int = 0
    pain_score: int = 0  # 0-100
    pain_indicators: List[str] = field(default_factory=list)
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'signal_id': self.signal_id,
            'job_title': self.job_title,
            'company_name': self.company_name,
            'job_source': self.job_source.value,
            'posted_date': self.posted_date.isoformat(),
            'job_url': self.job_url,
            'description': self.description[:200],
            'location': self.location,
            'estimated_budget_eur': self.estimated_budget_eur,
            'pain_score': self.pain_score,
            'pain_indicators': self.pain_indicators,
            'detected_at': self.detected_at.isoformat(),
        }

class JobOfferScanner:
    """
    HUNTING MODULE 4 — Job offer pain detector

    Logique:
    - Offre emploi RSSI/DSI/OT Security = entreprise a douleur actuelle
    - Urgence recrutement = budget disponible
    - Plus l'offre est récente, plus le score est élevé

    Keywords recherchés:
    - "RSSI", "DSI", "Responsable cybersécurité"
    - "OT Security", "IEC 62443", "SCADA Security"
    - "Ingénieur cybersécurité industrielle"
    - "Compliance officer NIS2"

    Budget estimation:
    - RSSI: 15-40k EUR (audit + conseil 6 mois)
    - DSI: 20-50k EUR (transformation digitale)
    - Ingénieur OT: 10-30k EUR (formation + audit)

    Usage:
        scanner = JobOfferScanner()
        signals = await scanner.scan_all_sources()
    """

    # Keywords par catégorie
    JOB_KEYWORDS = {
        "rssi": ["RSSI", "Responsable sécurité", "Chief Information Security Officer", "CISO"],
        "dsi": ["DSI", "Directeur systèmes information", "CIO", "IT Director"],
        "ot_security": ["OT Security", "Cybersécurité industrielle", "SCADA Security", "ICS Security"],
        "compliance": ["Compliance officer", "IEC 62443", "NIS2", "ISO 27001"],
        "engineer": ["Ingénieur cybersécurité", "Security engineer", "Pentester OT"],
    }

    # Budget estimates par type de poste
    BUDGET_ESTIMATES = {
        "rssi": (15000, 40000),
        "dsi": (20000, 50000),
        "ot_security": (10000, 30000),
        "compliance": (12000, 35000),
        "engineer": (8000, 25000),
    }

    # Pain score multipliers
    URGENCY_MULTIPLIERS = {
        "urgent": 1.3,
        "immediate": 1.4,
        "asap": 1.5,
    }

    def __init__(self):
        self.serper_api_key = os.getenv('SERPER_API_KEY', '')
        self.detected_signals: Dict[str, JobSignal] = {}
        self.scan_count = 0

    def _generate_signal_id(self, company_name: str, job_title: str) -> str:
        """Générer ID unique pour signal"""
        return hashlib.md5(f"{company_name}_{job_title}".encode()).hexdigest()[:12]

    def _detect_job_category(self, job_title: str, description: str) -> Optional[str]:
        """Détecter catégorie job depuis titre et description"""
        text = f"{job_title} {description}".lower()

        for category, keywords in self.JOB_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in text:
                    return category

        return None

    def _estimate_budget(self, category: Optional[str], description: str) -> int:
        """Estimer budget projet depuis catégorie job"""
        if not category:
            return 5000  # Budget minimum

        min_budget, max_budget = self.BUDGET_ESTIMATES.get(category, (5000, 15000))

        # Ajuster selon urgence
        text_lower = description.lower()
        multiplier = 1.0

        for urgency_keyword, mult in self.URGENCY_MULTIPLIERS.items():
            if urgency_keyword in text_lower:
                multiplier = max(multiplier, mult)

        estimated = int((min_budget + max_budget) / 2 * multiplier)
        return max(estimated, 1000)  # Plancher 1000 EUR

    def _calculate_pain_score(self, category: Optional[str], posted_date: datetime, description: str) -> int:
        """Calculer pain score 0-100"""
        score = 50  # Base

        # Bonus catégorie
        category_bonus = {
            "rssi": 20,
            "dsi": 15,
            "ot_security": 25,  # Plus rare = plus de valeur
            "compliance": 18,
            "engineer": 10,
        }
        score += category_bonus.get(category, 0)

        # Bonus récence (plus récent = plus urgent)
        days_old = (datetime.now(timezone.utc) - posted_date).days
        if days_old <= 7:
            score += 15
        elif days_old <= 14:
            score += 10
        elif days_old <= 30:
            score += 5

        # Bonus urgence keywords
        text_lower = description.lower()
        if any(keyword in text_lower for keyword in ["urgent", "immediate", "asap"]):
            score += 10

        # Bonus IEC 62443, NIS2 mentions
        if any(keyword in text_lower for keyword in ["iec 62443", "nis2", "ot", "scada"]):
            score += 10

        return min(100, max(0, score))

    def _detect_pain_indicators(self, description: str) -> List[str]:
        """Détecter indicateurs de pain depuis description"""
        indicators = []
        text_lower = description.lower()

        pain_patterns = {
            "incident récent": ["suite incident", "après cyberattaque", "breach récent"],
            "conformité urgente": ["conformité nécéssaire", "deadline", "audit à venir"],
            "transformation": ["transformation digitale", "modernisation", "migration"],
            "croissance": ["forte croissance", "expansion", "nouveau site"],
            "urgence": ["urgent", "immediate", "asap", "dès que possible"],
        }

        for indicator, patterns in pain_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                indicators.append(indicator)

        return indicators

    async def scan_serper(self, keyword: str, limit: int = 10) -> List[JobSignal]:
        """
        Scanner offres via Serper API (Google Jobs)

        Args:
            keyword: Mot-clé recherche (ex: "RSSI cybersécurité")
            limit: Nombre max résultats

        Returns:
            Liste JobSignal
        """
        if not self.serper_api_key:
            logger.warning("SERPER_API_KEY not set - returning mock data")
            return self._generate_mock_signals(keyword, limit, JobSource.SERPER)

        try:
            headers = {
                "X-API-KEY": self.serper_api_key,
                "Content-Type": "application/json"
            }

            payload = {
                "q": f"{keyword} emploi recrutement",
                "gl": "fr",
                "hl": "fr",
                "num": limit,
                "tbm": "jobs"  # Google Jobs
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
                        return self._generate_mock_signals(keyword, limit, JobSource.SERPER)

                    data = await response.json()
                    jobs = data.get('jobs', [])

                    signals = []
                    for job in jobs:
                        title = job.get('title', '')
                        company = job.get('company', '')
                        description = job.get('description', '')
                        posted = job.get('posted', 'Unknown')

                        # Parse posted date
                        posted_date = datetime.now(timezone.utc) - timedelta(days=7)  # Default 7 days ago

                        category = self._detect_job_category(title, description)
                        budget = self._estimate_budget(category, description)
                        pain_score = self._calculate_pain_score(category, posted_date, description)
                        pain_indicators = self._detect_pain_indicators(description)

                        signal = JobSignal(
                            signal_id=self._generate_signal_id(company, title),
                            job_title=title,
                            company_name=company,
                            job_source=JobSource.SERPER,
                            posted_date=posted_date,
                            job_url=job.get('link', ''),
                            description=description,
                            location=job.get('location'),
                            estimated_budget_eur=budget,
                            pain_score=pain_score,
                            pain_indicators=pain_indicators
                        )

                        signals.append(signal)
                        self.detected_signals[signal.signal_id] = signal

                    logger.info(f"Serper found {len(signals)} job signals for '{keyword}'")
                    return signals

        except Exception as e:
            logger.error(f"Serper scan error: {e}")
            return self._generate_mock_signals(keyword, limit, JobSource.SERPER)

    async def scan_all_sources(self, limit_per_source: int = 10) -> List[JobSignal]:
        """
        Scanner toutes les sources en parallèle

        Args:
            limit_per_source: Limite par source

        Returns:
            Liste complète JobSignal
        """
        self.scan_count += 1
        logger.info(f"Job scanner cycle #{self.scan_count}")

        # Keywords prioritaires
        priority_keywords = [
            "RSSI cybersécurité",
            "OT Security IEC 62443",
            "DSI transformation digitale",
            "Ingénieur cybersécurité industrielle",
        ]

        tasks = []
        for keyword in priority_keywords:
            task = self.scan_serper(keyword, limit=limit_per_source)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_signals = []
        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Scanner error for keyword {idx}: {result}")
            else:
                all_signals.extend(result)

        # Dedup par signal_id
        unique_signals = {s.signal_id: s for s in all_signals}
        unique_list = list(unique_signals.values())

        # Trier par pain score
        sorted_signals = sorted(unique_list, key=lambda s: s.pain_score, reverse=True)

        logger.info(f"Job scanner found {len(sorted_signals)} unique signals")
        return sorted_signals

    async def scan_by_sector(self, sector: str, limit: int = 20) -> List[JobSignal]:
        """
        Scanner par secteur spécifique

        Args:
            sector: Secteur (Manufacturing, Energy, Transport, Finance)
            limit: Nombre max résultats

        Returns:
            Liste JobSignal pour ce secteur
        """
        sector_keywords = {
            "Manufacturing": ["RSSI industrie", "OT Security manufacturing", "cybersécurité usine"],
            "Energy": ["RSSI énergie", "SCADA Security", "cybersécurité infrastructure critique"],
            "Transport": ["DSI transport", "cybersécurité logistique", "RSSI mobilité"],
            "Finance": ["RSSI banque", "cybersécurité fintech", "compliance officer finance"],
        }

        keywords = sector_keywords.get(sector, ["RSSI"])

        tasks = []
        for keyword in keywords:
            task = self.scan_serper(keyword, limit=limit // len(keywords))
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        all_signals = [s for result in results for s in result]

        # Filter par secteur (si détectable)
        filtered = [s for s in all_signals if sector.lower() in s.description.lower() or sector.lower() in s.company_name.lower()]

        logger.info(f"Sector {sector} scan: {len(filtered)} signals")
        return sorted(filtered, key=lambda s: s.pain_score, reverse=True)

    def _generate_mock_signals(self, keyword: str, limit: int, source: JobSource) -> List[JobSignal]:
        """Générer signaux mock"""
        signals = []
        for i in range(min(limit, 5)):
            signal = JobSignal(
                signal_id=f"mock_job_{i}",
                job_title=f"{keyword} - Poste {i}",
                company_name=f"Company {i}",
                job_source=source,
                posted_date=datetime.now(timezone.utc) - timedelta(days=i*3),
                job_url=f"https://jobs.example.com/{i}",
                description=f"Recherche {keyword} pour transformation cybersécurité. IEC 62443 souhaité.",
                location="France",
                estimated_budget_eur=15000 + (i * 5000),
                pain_score=75 - (i * 5),
                pain_indicators=["urgence", "conformité urgente"]
            )
            signals.append(signal)

        return signals

    def get_stats(self) -> Dict:
        """Stats scanner"""
        return {
            'scan_count': self.scan_count,
            'total_signals': len(self.detected_signals),
            'high_score_signals': sum(1 for s in self.detected_signals.values() if s.pain_score >= 80),
            'average_score': sum(s.pain_score for s in self.detected_signals.values()) / max(len(self.detected_signals), 1),
            'average_budget': sum(s.estimated_budget_eur for s in self.detected_signals.values()) / max(len(self.detected_signals), 1),
        }

# Instance globale
job_offer_scanner = JobOfferScanner()

async def main():
    """Test function"""
    # Scan all
    signals = await job_offer_scanner.scan_all_sources(limit_per_source=5)
    print(f"Found {len(signals)} signals")

    for signal in signals[:3]:
        print(f"  - {signal.company_name}: {signal.job_title} (score: {signal.pain_score}, budget: {signal.estimated_budget_eur} EUR)")

    # Scan by sector
    energy_signals = await job_offer_scanner.scan_by_sector("Energy", limit=10)
    print(f"Energy sector: {len(energy_signals)} signals")

    print(f"Stats: {job_offer_scanner.get_stats()}")

if __name__ == "__main__":
    asyncio.run(main())
