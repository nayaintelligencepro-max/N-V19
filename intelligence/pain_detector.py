#!/usr/bin/env python3
"""
NAYA SUPREME V19 — Pain Detector
Scan discrete B2B pains from job offers, cyberattack news, LinkedIn signals, regulatory deadlines.
Score ≥ 70/100 → feed ProspectionWorkflow.
"""

import asyncio
import hashlib
import json
import logging
import os
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

log = logging.getLogger("NAYA.PainDetector")

# ── Configuration ─────────────────────────────────────────────────────────────
PAIN_SIGNALS = {
    "job_offers": [
        "RSSI OT",
        "IEC 62443",
        "OT Security Engineer",
        "SCADA Security",
        "Responsable cybersécurité industrielle",
        "Cybersecurity OT Manager",
        "Industrial Security Specialist",
        "OT/ICS Security Architect",
    ],
    "news_triggers": [
        "cyberattaque usine",
        "ransomware industriel",
        "conformité NIS2",
        "audit OT",
        "incident SCADA",
        "faille automate",
        "vulnérabilité SCADA",
        "attaque infrastructure critique",
        "breach OT",
    ],
    "linkedin_signals": [
        "poste ouvert cybersécurité OT",
        "changement de RSSI",
        "nouveau DSI",
        "recrutement cyber",
        "security transformation",
        "digital security",
    ],
    "regulatory": [
        "deadline NIS2",
        "audit certification",
        "renouvellement ISO 27001",
        "conformité IEC 62443",
        "deadline réglementaire",
        "mise en conformité cyber",
    ],
}

SCORING_GRID = {
    "budget_estime_gte_1000": 25,
    "decideur_identifie_contactable": 20,
    "signal_recent_30j": 20,
    "secteur_prioritaire": 15,
    "douleur_discrete_peu_concurrence": 10,
    "connexion_linkedin_commune": 10,
}

SECTEURS_PRIORITAIRES = {
    "transport_logistique": 1.0,
    "energie_utilities": 1.2,  # Bonus secteur critique
    "manufacturing": 0.9,
    "iec62443": 1.1,  # Bonus niche
}


# ── Data Model ────────────────────────────────────────────────────────────────
@dataclass
class Pain:
    """Pain détecté sur le marché avec scoring."""
    pain_id: str
    sector: str
    company: str
    decision_maker: Optional[str]
    signal_source: str  # job_offer, news, linkedin, regulatory
    signal_text: str
    budget_estimate: float
    score: float
    detected_at: str
    urgency: str  # low, medium, high, critical
    metadata: Dict = None

    def to_dict(self) -> Dict:
        return asdict(self)


# ── Pain Detector Engine ──────────────────────────────────────────────────────
class PainDetector:
    """
    Détection de douleurs économiques solvables discrètes sur les marchés B2B.
    Sources: offres d'emploi RSSI, actualités cyberattaques, LinkedIn, appels d'offres.
    Scoring GRID: ≥70/100 → ProspectionWorkflow.
    """

    def __init__(self, storage_path: str = "data/intelligence/pains.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.pains: List[Pain] = []
        self._load_pains()
        log.info("✅ PainDetector initialized")

    # ── Storage ───────────────────────────────────────────────────────────────
    def _load_pains(self) -> None:
        """Load pains from storage."""
        if self.storage_path.exists():
            try:
                data = json.loads(self.storage_path.read_text())
                self.pains = [Pain(**p) for p in data]
                log.info("Loaded %d pains from storage", len(self.pains))
            except Exception as exc:
                log.warning("Failed to load pains: %s", exc)
                self.pains = []
        else:
            self.pains = []

    def _save_pains(self) -> None:
        """Save pains to storage."""
        try:
            data = [p.to_dict() for p in self.pains]
            self.storage_path.write_text(json.dumps(data, indent=2, default=str))
        except Exception as exc:
            log.warning("Failed to save pains: %s", exc)

    # ── Scanning ──────────────────────────────────────────────────────────────
    async def scan_all_sources(self) -> List[Pain]:
        """
        Scan all sources in parallel and return detected pains with score ≥ 70.
        """
        log.info("🔍 Scanning all pain sources...")
        results = await asyncio.gather(
            self.scan_job_offers(),
            self.scan_news(),
            self.scan_linkedin(),
            self.scan_regulatory(),
            return_exceptions=True,
        )

        # Flatten results
        all_pains = []
        for result in results:
            if isinstance(result, list):
                all_pains.extend(result)
            elif isinstance(result, Exception):
                log.warning("Scan error: %s", result)

        # Score and filter
        qualified_pains = [p for p in all_pains if p.score >= 70]

        # Save all pains
        self.pains.extend(qualified_pains)
        self._save_pains()

        log.info("✅ Detected %d pains (score ≥70) from %d scanned",
                 len(qualified_pains), len(all_pains))
        return qualified_pains

    async def scan_job_offers(self) -> List[Pain]:
        """
        Scan job offers for RSSI OT, IEC 62443 positions.
        Signal = company is hiring security = pain exists.
        """
        pains = []
        serper_key = os.getenv("SERPER_API_KEY", "")

        if not serper_key:
            log.warning("SERPER_API_KEY not set, using mock data")
            # Mock data for testing
            mock_jobs = [
                {
                    "company": "SNCF",
                    "title": "RSSI OT - Cybersécurité ferroviaire",
                    "sector": "transport_logistique",
                    "url": "https://example.com/job1",
                },
                {
                    "company": "EDF",
                    "title": "IEC 62443 Security Architect",
                    "sector": "energie_utilities",
                    "url": "https://example.com/job2",
                },
            ]
            for job in mock_jobs:
                pain = self._create_pain_from_job(job)
                pains.append(pain)
            return pains

        # Real implementation with Serper API
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                for keyword in PAIN_SIGNALS["job_offers"][:3]:  # Limit to 3 keywords
                    url = "https://google.serper.dev/search"
                    payload = {
                        "q": f"{keyword} offre emploi France",
                        "num": 5,
                    }
                    headers = {
                        "X-API-KEY": serper_key,
                        "Content-Type": "application/json",
                    }
                    async with session.post(url, json=payload, headers=headers, timeout=10) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            for result in data.get("organic", [])[:3]:
                                job = {
                                    "company": self._extract_company(result.get("title", "")),
                                    "title": result.get("title", ""),
                                    "sector": "unknown",
                                    "url": result.get("link", ""),
                                }
                                pain = self._create_pain_from_job(job)
                                pains.append(pain)
                        await asyncio.sleep(1)  # Rate limiting
        except Exception as exc:
            log.warning("Job scan error: %s", exc)

        return pains

    async def scan_news(self) -> List[Pain]:
        """
        Scan news for cyberattack incidents, ransomware, OT breaches.
        """
        pains = []
        serper_key = os.getenv("SERPER_API_KEY", "")

        if not serper_key:
            # Mock data
            mock_news = [
                {
                    "company": "Michelin",
                    "title": "Cyberattaque sur l'usine de production",
                    "sector": "manufacturing",
                    "url": "https://example.com/news1",
                },
            ]
            for news in mock_news:
                pain = self._create_pain_from_news(news)
                pains.append(pain)
            return pains

        # Real implementation
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                for keyword in PAIN_SIGNALS["news_triggers"][:3]:
                    url = "https://google.serper.dev/news"
                    payload = {
                        "q": keyword,
                        "num": 5,
                        "tbs": "qdr:m",  # Last month
                    }
                    headers = {
                        "X-API-KEY": serper_key,
                        "Content-Type": "application/json",
                    }
                    async with session.post(url, json=payload, headers=headers, timeout=10) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            for result in data.get("news", [])[:3]:
                                news = {
                                    "company": self._extract_company(result.get("title", "")),
                                    "title": result.get("title", ""),
                                    "sector": "unknown",
                                    "url": result.get("link", ""),
                                }
                                pain = self._create_pain_from_news(news)
                                pains.append(pain)
                        await asyncio.sleep(1)
        except Exception as exc:
            log.warning("News scan error: %s", exc)

        return pains

    async def scan_linkedin(self) -> List[Pain]:
        """
        Scan LinkedIn for RSSI changes, new DSI positions, cybersecurity job posts.
        """
        pains = []
        # LinkedIn API requires OAuth - using mock data for now
        log.info("LinkedIn scan: using mock data (requires OAuth implementation)")

        mock_signals = [
            {
                "company": "Airbus",
                "signal": "Nouveau RSSI OT recruté",
                "sector": "manufacturing",
            },
        ]

        for signal in mock_signals:
            pain = self._create_pain_from_linkedin(signal)
            pains.append(pain)

        return pains

    async def scan_regulatory(self) -> List[Pain]:
        """
        Scan regulatory deadlines: NIS2, IEC 62443, ISO 27001 renewals.
        """
        pains = []
        log.info("Regulatory scan: checking known deadlines")

        # Known regulatory deadlines
        deadlines = [
            {
                "event": "NIS2 Compliance Deadline",
                "date": "2024-10-17",
                "impact": "Entities essentielles must comply",
                "sectors": ["energie_utilities", "transport_logistique"],
            },
        ]

        for deadline in deadlines:
            for sector in deadline["sectors"]:
                pain = Pain(
                    pain_id=self._generate_id(f"regulatory_{deadline['event']}_{sector}"),
                    sector=sector,
                    company="[Multiple entities]",
                    decision_maker=None,
                    signal_source="regulatory",
                    signal_text=f"{deadline['event']} - {deadline['impact']}",
                    budget_estimate=20000.0,
                    score=self._calculate_score({
                        "budget_estime_gte_1000": True,
                        "decideur_identifie_contactable": False,
                        "signal_recent_30j": True,
                        "secteur_prioritaire": sector in SECTEURS_PRIORITAIRES,
                        "douleur_discrete_peu_concurrence": True,
                        "connexion_linkedin_commune": False,
                    }, sector),
                    detected_at=datetime.now().isoformat(),
                    urgency="high",
                    metadata={"deadline": deadline["date"], "event": deadline["event"]},
                )
                pains.append(pain)

        return pains

    # ── Pain Creation ─────────────────────────────────────────────────────────
    def _create_pain_from_job(self, job: Dict) -> Pain:
        """Create a Pain from a job posting."""
        company = job.get("company", "Unknown")
        sector = job.get("sector", "unknown")

        return Pain(
            pain_id=self._generate_id(f"job_{company}_{job.get('title', '')}"),
            sector=sector,
            company=company,
            decision_maker=None,
            signal_source="job_offer",
            signal_text=job.get("title", ""),
            budget_estimate=15000.0,  # Minimum viable audit
            score=self._calculate_score({
                "budget_estime_gte_1000": True,
                "decideur_identifie_contactable": False,
                "signal_recent_30j": True,
                "secteur_prioritaire": sector in SECTEURS_PRIORITAIRES,
                "douleur_discrete_peu_concurrence": True,
                "connexion_linkedin_commune": False,
            }, sector),
            detected_at=datetime.now().isoformat(),
            urgency="medium",
            metadata={"url": job.get("url", "")},
        )

    def _create_pain_from_news(self, news: Dict) -> Pain:
        """Create a Pain from a news article."""
        company = news.get("company", "Unknown")
        sector = news.get("sector", "unknown")

        return Pain(
            pain_id=self._generate_id(f"news_{company}_{news.get('title', '')}"),
            sector=sector,
            company=company,
            decision_maker=None,
            signal_source="news",
            signal_text=news.get("title", ""),
            budget_estimate=40000.0,  # Post-incident budget is higher
            score=self._calculate_score({
                "budget_estime_gte_1000": True,
                "decideur_identifie_contactable": False,
                "signal_recent_30j": True,
                "secteur_prioritaire": sector in SECTEURS_PRIORITAIRES,
                "douleur_discrete_peu_concurrence": False,  # News = public = competition
                "connexion_linkedin_commune": False,
            }, sector),
            detected_at=datetime.now().isoformat(),
            urgency="critical",
            metadata={"url": news.get("url", "")},
        )

    def _create_pain_from_linkedin(self, signal: Dict) -> Pain:
        """Create a Pain from a LinkedIn signal."""
        company = signal.get("company", "Unknown")
        sector = signal.get("sector", "unknown")

        return Pain(
            pain_id=self._generate_id(f"linkedin_{company}_{signal.get('signal', '')}"),
            sector=sector,
            company=company,
            decision_maker=None,
            signal_source="linkedin",
            signal_text=signal.get("signal", ""),
            budget_estimate=15000.0,
            score=self._calculate_score({
                "budget_estime_gte_1000": True,
                "decideur_identifie_contactable": True,  # LinkedIn = contactable
                "signal_recent_30j": True,
                "secteur_prioritaire": sector in SECTEURS_PRIORITAIRES,
                "douleur_discrete_peu_concurrence": True,
                "connexion_linkedin_commune": False,
            }, sector),
            detected_at=datetime.now().isoformat(),
            urgency="high",
            metadata={"source": "linkedin"},
        )

    # ── Scoring ───────────────────────────────────────────────────────────────
    def _calculate_score(self, factors: Dict[str, bool], sector: str) -> float:
        """
        Calculate pain score based on SCORING_GRID.
        Returns 0-100 score.
        """
        score = 0.0

        if factors.get("budget_estime_gte_1000"):
            score += SCORING_GRID["budget_estime_gte_1000"]
        if factors.get("decideur_identifie_contactable"):
            score += SCORING_GRID["decideur_identifie_contactable"]
        if factors.get("signal_recent_30j"):
            score += SCORING_GRID["signal_recent_30j"]
        if factors.get("secteur_prioritaire"):
            score += SCORING_GRID["secteur_prioritaire"]
        if factors.get("douleur_discrete_peu_concurrence"):
            score += SCORING_GRID["douleur_discrete_peu_concurrence"]
        if factors.get("connexion_linkedin_commune"):
            score += SCORING_GRID["connexion_linkedin_commune"]

        # Apply sector multiplier
        sector_multiplier = SECTEURS_PRIORITAIRES.get(sector, 1.0)
        score *= sector_multiplier

        return min(score, 100.0)

    # ── Utilities ─────────────────────────────────────────────────────────────
    def _generate_id(self, text: str) -> str:
        """Generate unique pain ID."""
        return hashlib.sha256(text.encode()).hexdigest()[:16]

    def _extract_company(self, text: str) -> str:
        """Extract company name from text (simple heuristic)."""
        # Try to find common company patterns
        words = text.split()
        for word in words:
            if len(word) > 3 and word[0].isupper():
                return word
        return "Unknown"

    # ── Query ─────────────────────────────────────────────────────────────────
    async def get_high_score_pains(self, min_score: float = 70) -> List[Pain]:
        """Get pains with score >= min_score."""
        return [p for p in self.pains if p.score >= min_score]

    async def get_pains_by_sector(self, sector: str) -> List[Pain]:
        """Get pains filtered by sector."""
        return [p for p in self.pains if p.sector == sector]

    async def get_recent_pains(self, days: int = 30) -> List[Pain]:
        """Get pains detected in the last N days."""
        cutoff = datetime.now() - timedelta(days=days)
        return [
            p for p in self.pains
            if datetime.fromisoformat(p.detected_at) >= cutoff
        ]

    def get_stats(self) -> Dict:
        """Get pain detection statistics."""
        if not self.pains:
            return {
                "total": 0,
                "avg_score": 0,
                "by_sector": {},
                "by_source": {},
                "high_priority": 0,
            }

        by_sector = {}
        by_source = {}
        high_priority = 0

        for pain in self.pains:
            by_sector[pain.sector] = by_sector.get(pain.sector, 0) + 1
            by_source[pain.signal_source] = by_source.get(pain.signal_source, 0) + 1
            if pain.score >= 80:
                high_priority += 1

        return {
            "total": len(self.pains),
            "avg_score": sum(p.score for p in self.pains) / len(self.pains),
            "by_sector": by_sector,
            "by_source": by_source,
            "high_priority": high_priority,
        }


# ── CLI Test ──────────────────────────────────────────────────────────────────
async def main():
    """Test Pain Detector."""
    print("🔍 NAYA Pain Detector — Test Module\n")

    detector = PainDetector()

    # Scan all sources
    pains = await detector.scan_all_sources()

    print(f"\n✅ Detected {len(pains)} pains (score ≥70)")

    for pain in pains[:5]:
        print(f"\n📊 Pain: {pain.company} ({pain.sector})")
        print(f"   Score: {pain.score:.1f}/100")
        print(f"   Source: {pain.signal_source}")
        print(f"   Signal: {pain.signal_text[:80]}...")
        print(f"   Budget estimate: {pain.budget_estimate:.0f} EUR")
        print(f"   Urgency: {pain.urgency}")

    # Stats
    stats = detector.get_stats()
    print(f"\n📈 Statistics:")
    print(f"   Total pains: {stats['total']}")
    print(f"   Avg score: {stats['avg_score']:.1f}")
    print(f"   High priority (≥80): {stats['high_priority']}")
    print(f"   By sector: {stats['by_sector']}")
    print(f"   By source: {stats['by_source']}")


if __name__ == "__main__":
    asyncio.run(main())
