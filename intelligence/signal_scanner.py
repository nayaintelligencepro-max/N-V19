#!/usr/bin/env python3
"""
NAYA SUPREME V19 — Signal Scanner
Multi-source scanner for weak signals: news, jobs, LinkedIn, regulatory.
Signal types: pain, opportunity, threat, trend.
Urgency scoring 0-100.
"""

import asyncio
import hashlib
import json
import logging
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

log = logging.getLogger("NAYA.SignalScanner")


# ── Signal Types ──────────────────────────────────────────────────────────────
class SignalType(str, Enum):
    PAIN = "pain"
    OPPORTUNITY = "opportunity"
    THREAT = "threat"
    TREND = "trend"


class UrgencyLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ── Data Model ────────────────────────────────────────────────────────────────
@dataclass
class Signal:
    """Weak signal detected from market sources."""
    signal_id: str
    signal_type: SignalType
    source: str  # news, jobs, linkedin, regulatory, social
    title: str
    content: str
    company: Optional[str]
    sector: Optional[str]
    url: Optional[str]
    urgency_score: float  # 0-100
    urgency_level: UrgencyLevel
    detected_at: str
    expires_at: Optional[str]  # For time-sensitive signals
    metadata: Dict = None

    def to_dict(self) -> Dict:
        data = asdict(self)
        data["signal_type"] = self.signal_type.value
        data["urgency_level"] = self.urgency_level.value
        return data


# ── Signal Scanner Engine ─────────────────────────────────────────────────────
class SignalScanner:
    """
    Multi-source weak signal scanner for market intelligence.
    Sources: Serper (news/jobs), LinkedIn, regulatory calendars, social media.
    Real-time urgency scoring.
    """

    def __init__(self, storage_path: str = "data/intelligence/signals.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.signals: List[Signal] = []
        self._load_signals()
        log.info("✅ SignalScanner initialized")

    # ── Storage ───────────────────────────────────────────────────────────────
    def _load_signals(self) -> None:
        """Load signals from storage."""
        if self.storage_path.exists():
            try:
                data = json.loads(self.storage_path.read_text())
                self.signals = []
                for item in data:
                    item["signal_type"] = SignalType(item["signal_type"])
                    item["urgency_level"] = UrgencyLevel(item["urgency_level"])
                    self.signals.append(Signal(**item))
                log.info("Loaded %d signals from storage", len(self.signals))
            except Exception as exc:
                log.warning("Failed to load signals: %s", exc)
                self.signals = []
        else:
            self.signals = []

    def _save_signals(self) -> None:
        """Save signals to storage."""
        try:
            data = [s.to_dict() for s in self.signals]
            self.storage_path.write_text(json.dumps(data, indent=2, default=str))
        except Exception as exc:
            log.warning("Failed to save signals: %s", exc)

    # ── Main Scan ─────────────────────────────────────────────────────────────
    async def scan_all_sources(self) -> List[Signal]:
        """
        Scan all sources in parallel and return all detected signals.
        """
        log.info("📡 Scanning all signal sources...")

        results = await asyncio.gather(
            self.scan_news_signals(),
            self.scan_job_signals(),
            self.scan_linkedin_signals(),
            self.scan_regulatory_signals(),
            return_exceptions=True,
        )

        # Flatten and deduplicate
        all_signals = []
        seen_ids = set()

        for result in results:
            if isinstance(result, list):
                for signal in result:
                    if signal.signal_id not in seen_ids:
                        all_signals.append(signal)
                        seen_ids.add(signal.signal_id)
            elif isinstance(result, Exception):
                log.warning("Scan error: %s", result)

        # Save all signals
        self.signals.extend(all_signals)
        self._prune_old_signals()
        self._save_signals()

        log.info("✅ Detected %d new signals", len(all_signals))
        return all_signals

    # ── News Signals ──────────────────────────────────────────────────────────
    async def scan_news_signals(self) -> List[Signal]:
        """Scan news for cyber incidents, attacks, regulatory changes."""
        signals = []
        serper_key = os.getenv("SERPER_API_KEY", "")

        keywords = [
            "cyberattaque industrielle",
            "ransomware usine",
            "faille SCADA",
            "NIS2 compliance",
            "IEC 62443",
        ]

        if not serper_key:
            log.warning("SERPER_API_KEY not set, using mock data")
            # Mock signals
            mock_news = [
                {
                    "title": "Cyberattaque majeure sur une usine Michelin",
                    "content": "L'usine de production a été paralysée pendant 48h",
                    "company": "Michelin",
                    "sector": "manufacturing",
                    "url": "https://example.com/news1",
                },
                {
                    "title": "NIS2: Les entités essentielles ont 6 mois pour se conformer",
                    "content": "Deadline octobre 2024 pour la conformité NIS2",
                    "company": None,
                    "sector": "all",
                    "url": "https://example.com/news2",
                },
            ]
            for news in mock_news:
                signal = self._create_news_signal(news)
                signals.append(signal)
            return signals

        # Real implementation
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                for keyword in keywords[:3]:  # Limit to avoid rate limiting
                    url = "https://google.serper.dev/news"
                    payload = {
                        "q": keyword,
                        "num": 5,
                        "tbs": "qdr:w",  # Last week
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
                                    "title": result.get("title", ""),
                                    "content": result.get("snippet", ""),
                                    "company": self._extract_company(result.get("title", "")),
                                    "sector": "unknown",
                                    "url": result.get("link", ""),
                                }
                                signal = self._create_news_signal(news)
                                signals.append(signal)
                        await asyncio.sleep(1)  # Rate limiting
        except Exception as exc:
            log.warning("News scan error: %s", exc)

        return signals

    # ── Job Signals ───────────────────────────────────────────────────────────
    async def scan_job_signals(self) -> List[Signal]:
        """Scan job postings for RSSI OT, security positions."""
        signals = []
        serper_key = os.getenv("SERPER_API_KEY", "")

        keywords = [
            "RSSI OT recrutement",
            "IEC 62443 engineer",
            "SCADA security manager",
        ]

        if not serper_key:
            # Mock signals
            mock_jobs = [
                {
                    "title": "SNCF recrute un RSSI OT ferroviaire",
                    "content": "Poste permanent, base Paris",
                    "company": "SNCF",
                    "sector": "transport_logistique",
                    "url": "https://example.com/job1",
                },
            ]
            for job in mock_jobs:
                signal = self._create_job_signal(job)
                signals.append(signal)
            return signals

        # Real implementation
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                for keyword in keywords[:2]:
                    url = "https://google.serper.dev/search"
                    payload = {
                        "q": f"{keyword} offre emploi",
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
                                    "title": result.get("title", ""),
                                    "content": result.get("snippet", ""),
                                    "company": self._extract_company(result.get("title", "")),
                                    "sector": "unknown",
                                    "url": result.get("link", ""),
                                }
                                signal = self._create_job_signal(job)
                                signals.append(signal)
                        await asyncio.sleep(1)
        except Exception as exc:
            log.warning("Job scan error: %s", exc)

        return signals

    # ── LinkedIn Signals ──────────────────────────────────────────────────────
    async def scan_linkedin_signals(self) -> List[Signal]:
        """Scan LinkedIn for executive changes, company updates."""
        signals = []
        log.info("LinkedIn scan: using mock data (requires OAuth)")

        # Mock signals
        mock_linkedin = [
            {
                "title": "Airbus nomme un nouveau RSSI",
                "content": "Jean Dupont rejoint Airbus comme Directeur Cybersécurité",
                "company": "Airbus",
                "sector": "manufacturing",
                "url": "https://linkedin.com/posts/...",
            },
        ]

        for item in mock_linkedin:
            signal = Signal(
                signal_id=self._generate_id(f"linkedin_{item['title']}"),
                signal_type=SignalType.OPPORTUNITY,
                source="linkedin",
                title=item["title"],
                content=item["content"],
                company=item["company"],
                sector=item["sector"],
                url=item["url"],
                urgency_score=self._calculate_urgency({
                    "is_executive_change": True,
                    "is_security_role": True,
                    "is_recent": True,
                }),
                urgency_level=self._score_to_urgency_level(75),
                detected_at=datetime.now().isoformat(),
                expires_at=(datetime.now() + timedelta(days=30)).isoformat(),
                metadata={"source": "linkedin"},
            )
            signals.append(signal)

        return signals

    # ── Regulatory Signals ────────────────────────────────────────────────────
    async def scan_regulatory_signals(self) -> List[Signal]:
        """Scan regulatory calendars for deadlines and compliance requirements."""
        signals = []
        log.info("Regulatory scan: checking known deadlines")

        # Known deadlines (would be loaded from a calendar API in production)
        deadlines = [
            {
                "title": "NIS2 Compliance Deadline",
                "date": "2024-10-17",
                "content": "All essential entities must be NIS2 compliant by this date",
                "sectors": ["energie_utilities", "transport_logistique", "manufacturing"],
            },
            {
                "title": "ISO 27001:2022 Migration Deadline",
                "date": "2025-10-31",
                "content": "ISO 27001:2013 certificates expire, migration to 2022 required",
                "sectors": ["all"],
            },
        ]

        for deadline in deadlines:
            deadline_date = datetime.fromisoformat(deadline["date"])
            days_until = (deadline_date - datetime.now()).days

            if days_until > 0 and days_until < 180:  # Within 6 months
                urgency = min(100, 100 - (days_until / 180 * 100))

                signal = Signal(
                    signal_id=self._generate_id(f"regulatory_{deadline['title']}"),
                    signal_type=SignalType.THREAT if days_until < 90 else SignalType.OPPORTUNITY,
                    source="regulatory",
                    title=deadline["title"],
                    content=f"{deadline['content']} ({days_until} days remaining)",
                    company=None,
                    sector=",".join(deadline["sectors"]),
                    url=None,
                    urgency_score=urgency,
                    urgency_level=self._score_to_urgency_level(urgency),
                    detected_at=datetime.now().isoformat(),
                    expires_at=deadline["date"],
                    metadata={
                        "days_until_deadline": days_until,
                        "affected_sectors": deadline["sectors"],
                    },
                )
                signals.append(signal)

        return signals

    # ── Signal Creation ───────────────────────────────────────────────────────
    def _create_news_signal(self, news: Dict) -> Signal:
        """Create signal from news article."""
        # Determine signal type based on content
        content_lower = (news.get("title", "") + " " + news.get("content", "")).lower()

        if any(word in content_lower for word in ["attaque", "ransomware", "breach", "faille"]):
            signal_type = SignalType.THREAT
            urgency_factors = {
                "is_cyber_incident": True,
                "is_recent": True,
                "has_company": news.get("company") is not None,
            }
        elif any(word in content_lower for word in ["deadline", "conformité", "compliance"]):
            signal_type = SignalType.OPPORTUNITY
            urgency_factors = {
                "is_regulatory": True,
                "is_recent": True,
            }
        else:
            signal_type = SignalType.TREND
            urgency_factors = {"is_recent": True}

        urgency_score = self._calculate_urgency(urgency_factors)

        return Signal(
            signal_id=self._generate_id(f"news_{news.get('title', '')}"),
            signal_type=signal_type,
            source="news",
            title=news.get("title", ""),
            content=news.get("content", ""),
            company=news.get("company"),
            sector=news.get("sector"),
            url=news.get("url"),
            urgency_score=urgency_score,
            urgency_level=self._score_to_urgency_level(urgency_score),
            detected_at=datetime.now().isoformat(),
            expires_at=(datetime.now() + timedelta(days=14)).isoformat(),
            metadata={"source": "news"},
        )

    def _create_job_signal(self, job: Dict) -> Signal:
        """Create signal from job posting."""
        urgency_score = self._calculate_urgency({
            "is_security_role": True,
            "has_company": job.get("company") is not None,
            "is_recent": True,
        })

        return Signal(
            signal_id=self._generate_id(f"job_{job.get('title', '')}"),
            signal_type=SignalType.PAIN,  # Job posting = pain exists
            source="jobs",
            title=job.get("title", ""),
            content=job.get("content", ""),
            company=job.get("company"),
            sector=job.get("sector"),
            url=job.get("url"),
            urgency_score=urgency_score,
            urgency_level=self._score_to_urgency_level(urgency_score),
            detected_at=datetime.now().isoformat(),
            expires_at=(datetime.now() + timedelta(days=30)).isoformat(),
            metadata={"source": "jobs"},
        )

    # ── Scoring ───────────────────────────────────────────────────────────────
    def _calculate_urgency(self, factors: Dict[str, bool]) -> float:
        """Calculate urgency score 0-100 based on factors."""
        score = 50.0  # Base score

        if factors.get("is_cyber_incident"):
            score += 30
        if factors.get("is_recent"):
            score += 15
        if factors.get("has_company"):
            score += 10
        if factors.get("is_executive_change"):
            score += 20
        if factors.get("is_security_role"):
            score += 15
        if factors.get("is_regulatory"):
            score += 25

        return min(score, 100.0)

    def _score_to_urgency_level(self, score: float) -> UrgencyLevel:
        """Convert urgency score to urgency level."""
        if score >= 80:
            return UrgencyLevel.CRITICAL
        elif score >= 60:
            return UrgencyLevel.HIGH
        elif score >= 40:
            return UrgencyLevel.MEDIUM
        else:
            return UrgencyLevel.LOW

    # ── Utilities ─────────────────────────────────────────────────────────────
    def _generate_id(self, text: str) -> str:
        """Generate unique signal ID."""
        return hashlib.sha256(text.encode()).hexdigest()[:16]

    def _extract_company(self, text: str) -> Optional[str]:
        """Extract company name from text."""
        words = text.split()
        for word in words:
            if len(word) > 3 and word[0].isupper() and not word.isupper():
                return word
        return None

    def _prune_old_signals(self, days: int = 90) -> None:
        """Remove signals older than N days."""
        cutoff = datetime.now() - timedelta(days=days)
        original_count = len(self.signals)
        self.signals = [
            s for s in self.signals
            if datetime.fromisoformat(s.detected_at) >= cutoff
        ]
        pruned = original_count - len(self.signals)
        if pruned > 0:
            log.info("Pruned %d old signals", pruned)

    # ── Query ─────────────────────────────────────────────────────────────────
    async def get_signals_by_type(self, signal_type: SignalType) -> List[Signal]:
        """Get signals filtered by type."""
        return [s for s in self.signals if s.signal_type == signal_type]

    async def get_signals_by_urgency(self, min_urgency: UrgencyLevel) -> List[Signal]:
        """Get signals with urgency >= min_urgency."""
        urgency_order = {
            UrgencyLevel.LOW: 0,
            UrgencyLevel.MEDIUM: 1,
            UrgencyLevel.HIGH: 2,
            UrgencyLevel.CRITICAL: 3,
        }
        min_level = urgency_order[min_urgency]
        return [s for s in self.signals if urgency_order[s.urgency_level] >= min_level]

    async def get_signals_by_company(self, company: str) -> List[Signal]:
        """Get signals for a specific company."""
        return [s for s in self.signals if s.company == company]

    def get_stats(self) -> Dict:
        """Get signal statistics."""
        if not self.signals:
            return {
                "total": 0,
                "by_type": {},
                "by_urgency": {},
                "by_source": {},
            }

        by_type = {}
        by_urgency = {}
        by_source = {}

        for signal in self.signals:
            by_type[signal.signal_type.value] = by_type.get(signal.signal_type.value, 0) + 1
            by_urgency[signal.urgency_level.value] = by_urgency.get(signal.urgency_level.value, 0) + 1
            by_source[signal.source] = by_source.get(signal.source, 0) + 1

        return {
            "total": len(self.signals),
            "by_type": by_type,
            "by_urgency": by_urgency,
            "by_source": by_source,
            "avg_urgency_score": sum(s.urgency_score for s in self.signals) / len(self.signals),
        }


# ── CLI Test ──────────────────────────────────────────────────────────────────
async def main():
    """Test Signal Scanner."""
    print("📡 NAYA Signal Scanner — Test Module\n")

    scanner = SignalScanner()

    # Scan all sources
    signals = await scanner.scan_all_sources()

    print(f"\n✅ Detected {len(signals)} signals")

    # Show samples
    for signal in signals[:5]:
        print(f"\n📊 Signal: {signal.title}")
        print(f"   Type: {signal.signal_type.value}")
        print(f"   Source: {signal.source}")
        print(f"   Urgency: {signal.urgency_level.value} ({signal.urgency_score:.1f}/100)")
        if signal.company:
            print(f"   Company: {signal.company}")
        print(f"   Content: {signal.content[:80]}...")

    # Stats
    stats = scanner.get_stats()
    print(f"\n📈 Statistics:")
    print(f"   Total signals: {stats['total']}")
    print(f"   Avg urgency: {stats['avg_urgency_score']:.1f}")
    print(f"   By type: {stats['by_type']}")
    print(f"   By urgency: {stats['by_urgency']}")
    print(f"   By source: {stats['by_source']}")


if __name__ == "__main__":
    asyncio.run(main())
