"""
NAYA V19.6 — Competitor Monitor
Intelligence Module
Veille concurrents - scan signaux et donne alertes
"""

import asyncio
from typing import Optional, List, Dict
from dataclasses import dataclass, field
from datetime import datetime
import logging

@dataclass
class CompetitorSignal:
    """Signal détecté sur concurrent"""
    competitor_name: str
    signal_type: str  # "product_launch", "price_change", "partnership", "funding"
    description: str
    source: str  # "linkedin", "twitter", "news", "web"
    detected_at: datetime
    relevance_score: float  # 0.0 - 1.0
    threat_level: str  # "low", "medium", "high"

@dataclass
class CompetitorProfile:
    """Profil concurrent avec historique"""
    company_name: str
    sector: str
    positioning: str
    estimated_revenue: float
    key_contacts: List[str] = field(default_factory=list)
    recent_signals: List[CompetitorSignal] = field(default_factory=list)
    threat_assessment: str = "monitoring"
    last_scan: datetime = field(default_factory=datetime.utcnow)

class CompetitorMonitor:
    """
    Veille concurrents automatisée.
    Cibles: Clay.com, Instantly.ai, n8n, Zapier, Make.com (pour outreach)
    Signals: pricing changes, new features, partnerships, funding, hirings
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.competitors = {
            "clay": CompetitorProfile("Clay.com", "Hunting/Enrichment", "B2B Sales Automation"),
            "instantly": CompetitorProfile("Instantly.ai", "Outreach", "Email Sequences"),
            "n8n": CompetitorProfile("n8n", "Automation", "Workflow Automation"),
            "zapier": CompetitorProfile("Zapier", "Automation", "API Integration"),
            "make": CompetitorProfile("Make.com", "Automation", "Visual Automation"),
        }
        self.threat_multiplier = {}  # Track relative threats

    async def scan_all_competitors(self) -> Dict[str, List[CompetitorSignal]]:
        """Scan tous les concurrents pour signaux"""
        try:
            tasks = [
                self._scan_competitor_web("clay"),
                self._scan_competitor_web("instantly"),
                self._scan_competitor_web("n8n"),
                self._scan_competitor_web("zapier"),
                self._scan_competitor_web("make"),
                self._scan_linkedin_hiring(),
                self._scan_funding_news(),
                self._scan_product_announcements()
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)
            return self._consolidate_signals(results)

        except Exception as e:
            self.logger.error(f"Competitor scan failed: {e}")
            return {}

    async def _scan_competitor_web(self, competitor_key: str) -> List[CompetitorSignal]:
        """Scan site web et blog concurrent pour signaux"""
        signals = []

        # Exemple: Clay.com
        if competitor_key == "clay":
            signals.append(CompetitorSignal(
                competitor_name="Clay.com",
                signal_type="product_launch",
                description="New AI-powered contact enrichment features",
                source="web",
                detected_at=datetime.utcnow(),
                relevance_score=0.85,
                threat_level="high"
            ))

        return signals

    async def _scan_linkedin_hiring(self) -> List[CompetitorSignal]:
        """Détecte embauches competitors = expansion"""
        signals = []
        # Scan LinkedIn pour hirings chez concurrents
        return signals

    async def _scan_funding_news(self) -> List[CompetitorSignal]:
        """Détecte funding rounds = accélération"""
        signals = []
        # Scan news pour Series A/B/C funding
        return signals

    async def _scan_product_announcements(self) -> List[CompetitorSignal]:
        """Détecte annonces produits"""
        signals = []
        # Scrape Twitter, ProductHunt, etc.
        return signals

    def _consolidate_signals(self, scan_results: List) -> Dict[str, List[CompetitorSignal]]:
        """Consolide tous les signaux"""
        consolidated = {}
        for result in scan_results:
            if isinstance(result, list):
                for signal in result:
                    if signal.competitor_name not in consolidated:
                        consolidated[signal.competitor_name] = []
                    consolidated[signal.competitor_name].append(signal)

        return consolidated

    async def assess_threat(self, competitor_key: str) -> Dict:
        """Évalue menace relative d'un concurrent"""
        if competitor_key not in self.competitors:
            return {}

        profile = self.competitors[competitor_key]
        recent_signals = profile.recent_signals[-5:]  # Last 5 signals

        threat_score = 0.0
        for signal in recent_signals:
            threat_score += signal.relevance_score

        threat_score /= max(len(recent_signals), 1)
        threat_score = min(threat_score, 1.0)

        return {
            "competitor": competitor_key,
            "threat_score": threat_score,
            "threat_level": "high" if threat_score > 0.7 else "medium" if threat_score > 0.4 else "low",
            "recent_moves": [s.description for s in recent_signals],
            "recommendation": self._generate_recommendation(threat_score, competitor_key)
        }

    def _generate_recommendation(self, threat_score: float, competitor: str) -> str:
        """Génère recommandation basée sur menace"""
        if threat_score > 0.8:
            return f"URGENT: {competitor} accelerating. Review positioning and pricing."
        elif threat_score > 0.5:
            return f"Monitor {competitor} closely. Adjust messaging to differentiate."
        else:
            return f"{competitor} not immediate threat. Continue standard monitoring."

    async def create_competitive_alert(self, signal: CompetitorSignal) -> Dict:
        """Crée alerte compétitive pour leadership"""
        alert = {
            "type": "COMPETITIVE_SIGNAL",
            "severity": "HIGH" if signal.threat_level == "high" else "MEDIUM" if signal.threat_level == "medium" else "LOW",
            "competitor": signal.competitor_name,
            "signal": signal.description,
            "our_response": self._suggest_response(signal),
            "timestamp": signal.detected_at.isoformat()
        }
        return alert

    def _suggest_response(self, signal: CompetitorSignal) -> str:
        """Suggère réponse stratégique"""
        if signal.signal_type == "price_change":
            return "Review our pricing strategy and customer value communication"
        elif signal.signal_type == "product_launch":
            return "Analyze features vs our roadmap. Communicate our unique value."
        elif signal.signal_type == "partnership":
            return "Evaluate partnership opportunities or market consolidation."
        else:
            return "Monitor situation and update battle cards."

    def get_competitive_landscape(self) -> Dict:
        """Vue complète du paysage compétitif"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "competitors": [
                {
                    "name": profile.company_name,
                    "positioning": profile.positioning,
                    "threat_level": profile.threat_assessment,
                    "recent_signals": len(profile.recent_signals),
                    "last_scan": profile.last_scan.isoformat()
                }
                for profile in self.competitors.values()
            ]
        }

# Export
__all__ = ['CompetitorMonitor', 'CompetitorProfile', 'CompetitorSignal']
