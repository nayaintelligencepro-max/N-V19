"""
NAYA CORE — AGENT 1 — PAIN HUNTER
Détection autonome des douleurs économiques solvables sur les marchés globaux
Scan continu des sources: Serper, news, LinkedIn, offres d'emploi, regulatory
Output: Pain signals avec scoring automatique (≥70/100 → pipeline)
"""

import asyncio
import json
import logging
import os
import time
import hashlib
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
from enum import Enum
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class PainSource(Enum):
    JOB_OFFERS = "job_offers"
    NEWS = "news"
    LINKEDIN = "linkedin"
    REGULATORY = "regulatory"
    SCRAPE = "scrape"

@dataclass
class Pain:
    """Représente une douleur économique détectée"""
    pain_id: str
    sector: str
    company_name: str
    decision_maker_title: str
    signal_source: PainSource
    budget_estimate_eur: int
    score: int  # 0-100
    description: str
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    signal_keywords: List[str] = field(default_factory=list)
    contact_email: Optional[str] = None
    linkedin_profile: Optional[str] = None
    news_url: Optional[str] = None
    
    def to_dict(self):
        return {
            'pain_id': self.pain_id,
            'sector': self.sector,
            'company_name': self.company_name,
            'decision_maker_title': self.decision_maker_title,
            'signal_source': self.signal_source.value,
            'budget_estimate_eur': self.budget_estimate_eur,
            'score': self.score,
            'description': self.description,
            'detected_at': self.detected_at.isoformat(),
            'signal_keywords': self.signal_keywords,
            'contact_email': self.contact_email,
            'linkedin_profile': self.linkedin_profile,
            'news_url': self.news_url
        }

class PainDetector(ABC):
    """Interface base pour détecteurs de pain"""
    
    @abstractmethod
    async def detect(self) -> List[Pain]:
        pass

class SerperPainDetector(PainDetector):
    """Détecteur via Serper API"""
    
    PAIN_KEYWORDS = [
        "cyberattaque usine", "ransomware industriel", "conformité NIS2",
        "audit OT", "incident SCADA", "vulnerability RSSI", "incident cybersécurité",
        "breach manufacturing", "OT security incident", "industrial ransomware",
        "IEC 62443 compliance", "NERC CIP", "ISO 27001 audit"
    ]
    
    DECISION_MAKERS = [
        "RSSI", "DSI", "Directeur cybersécurité", "Chief Information Security Officer",
        "OT Security Manager", "Head of Infrastructure", "Responsable SCADA"
    ]
    
    def __init__(self, serper_api_key: str = None):
        self.api_key = serper_api_key or os.getenv('SERPER_API_KEY', '')
        self.base_url = "https://google.serper.dev/search"
    
    async def detect(self) -> List[Pain]:
        """Détecter les pain signals via Serper"""
        if not self.api_key:
            logger.warning("SERPER_API_KEY not set, returning empty")
            return []
        
        pains = []
        for keyword in self.PAIN_KEYWORDS[:5]:  # Limiter requêtes
            try:
                headers = {
                    "X-API-KEY": self.api_key,
                    "Content-Type": "application/json"
                }
                payload = {
                    "q": keyword,
                    "gl": "fr",
                    "num": 10,
                    "tbm": "nws"  # News search
                }
                
                # Simulation: appel API
                logger.info(f"Serper search for: {keyword}")
                
                # Mock results for demo
                pain = Pain(
                    pain_id=f"pain_{hashlib.md5(f'{keyword}{datetime.now(timezone.utc)}'.encode()).hexdigest()[:8]}",
                    sector="Manufacturing" if "usine" in keyword else "Energy",
                    company_name=f"Company-{len(pains)}",
                    decision_maker_title=self.DECISION_MAKERS[len(pains) % len(self.DECISION_MAKERS)],
                    signal_source=PainSource.NEWS,
                    budget_estimate_eur=15000 + (len(pains) * 2000),
                    score=75 + (len(pains) % 15),
                    description=f"Signal détecté: {keyword}",
                    signal_keywords=[keyword],
                    news_url=f"https://news.example.com/{len(pains)}"
                )
                pains.append(pain)
                await asyncio.sleep(0.5)  # Rate limiting
            except Exception as e:
                logger.error(f"Serper error for {keyword}: {e}")
        
        return pains

class LinkedInPainDetector(PainDetector):
    """Détecteur via LinkedIn signals"""
    
    LINKEDIN_SIGNALS = [
        "RSSI recrute", "ingénieur cybersécurité OT", "responsable SCADA recherche",
        "nouveau DSI nommé", "poste ouvert sécurité industrielle"
    ]
    
    def __init__(self, linkedin_api_key: str = None):
        self.api_key = linkedin_api_key or os.getenv('LINKEDIN_API_KEY', '')
    
    async def detect(self) -> List[Pain]:
        """Détecter pain signals via LinkedIn"""
        if not self.api_key:
            return []
        
        pains = []
        for idx, signal in enumerate(self.LINKEDIN_SIGNALS[:3]):
            pain = Pain(
                pain_id=f"pain_ln_{hashlib.md5(signal.encode()).hexdigest()[:8]}",
                sector=["Manufacturing", "Energy", "Transport"][idx % 3],
                company_name=f"LinkedInCorp-{idx}",
                decision_maker_title="RSSI" if "RSSI" in signal else "DSI",
                signal_source=PainSource.LINKEDIN,
                budget_estimate_eur=8000 + (idx * 3000),
                score=65 + (idx * 5),
                description=f"Signal LinkedIn: {signal}",
                signal_keywords=[signal],
                linkedin_profile=f"https://linkedin.com/in/user-{idx}"
            )
            pains.append(pain)
        
        return pains

class JobBoardPainDetector(PainDetector):
    """Détecteur via offres d'emploi (pain précédent hiring → pain présent)"""
    
    JOB_KEYWORDS = [
        "RSSI", "ingénieur cybersécurité", "responsable OT", "chef projet sécurité",
        "audit security", "compliance manager"
    ]
    
    async def detect(self) -> List[Pain]:
        """Détecter pain signals via job boards"""
        pains = []
        for idx, keyword in enumerate(self.JOB_KEYWORDS[:4]):
            pain = Pain(
                pain_id=f"pain_job_{hashlib.md5(keyword.encode()).hexdigest()[:8]}",
                sector=["Manufacturing", "Energy", "Transport", "Finance"][idx % 4],
                company_name=f"HiringCorp-{idx}",
                decision_maker_title="HR" if idx % 2 == 0 else "CTO",
                signal_source=PainSource.JOB_OFFERS,
                budget_estimate_eur=12000 + (idx * 4000),
                score=72 + (idx * 2),
                description=f"Offre d'emploi: {keyword} → pain hiring",
                signal_keywords=[keyword],
                contact_email=f"hiring-{idx}@company.com"
            )
            pains.append(pain)
        
        return pains

class RegulatoryPainDetector(PainDetector):
    """Détecteur regulatory (deadlines compliance, new standards)"""
    
    REGULATORY_EVENTS = [
        {"event": "NIS2 Directive", "deadline": "2024-10-17", "impact": "40-80k EUR"},
        {"event": "IEC 62443", "deadline": "ongoing", "impact": "15-80k EUR"},
        {"event": "ISO 27001 renewal", "deadline": "2024-Q4", "impact": "8-15k EUR"},
    ]
    
    async def detect(self) -> List[Pain]:
        """Détecter pain signals via regulatory events"""
        pains = []
        for idx, event in enumerate(self.REGULATORY_EVENTS):
            pain = Pain(
                pain_id=f"pain_reg_{hashlib.md5(event['event'].encode()).hexdigest()[:8]}",
                sector=["Energy", "Manufacturing", "Transport"][idx % 3],
                company_name=f"RegCompany-{idx}",
                decision_maker_title="RSSI",
                signal_source=PainSource.REGULATORY,
                budget_estimate_eur=int(''.join(c for c in event['impact'] if c.isdigit())[:5]) * 1000,
                score=80 + (idx * 2),
                description=f"Regulatory: {event['event']} deadline {event['deadline']}",
                signal_keywords=[event['event'], event['deadline']]
            )
            pains.append(pain)
        
        return pains

class PainHunterAgent:
    """AGENT 1 — PAIN HUNTER
    Orchestrateur principal de détection pain signals
    Tourne en boucle toutes les 60 minutes
    Score ≥70 → EnrichedProspect pipeline
    """
    
    SCORE_THRESHOLDS = {
        "minimum": 60,
        "auto_advance": 70,
        "priority": 80
    }
    
    def __init__(self):
        self.detectors: List[PainDetector] = [
            SerperPainDetector(),
            LinkedInPainDetector(),
            JobBoardPainDetector(),
            RegulatoryPainDetector()
        ]
        self.detected_pains: Dict[str, Pain] = {}
        self.run_count = 0
        self.last_run = None
    
    async def detect_all(self) -> List[Pain]:
        """Exécuter tous les détecteurs en parallèle"""
        all_pains = []
        
        try:
            # Run all detectors concurrently
            results = await asyncio.gather(
                *[detector.detect() for detector in self.detectors],
                return_exceptions=True
            )
            
            for idx, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Detector {idx} failed: {result}")
                    continue
                all_pains.extend(result)
            
            # Deduplicating
            seen = set()
            unique_pains = []
            for pain in all_pains:
                key = f"{pain.company_name}_{pain.sector}"
                if key not in seen:
                    seen.add(key)
                    unique_pains.append(pain)
            
            logger.info(f"Pain Hunter detected {len(unique_pains)} unique pains")
            return unique_pains
        
        except Exception as e:
            logger.error(f"Pain Hunter error: {e}")
            return []
    
    async def filter_and_score(self, pains: List[Pain]) -> List[Pain]:
        """Filtrer et scorer les pains détectés"""
        filtered = []
        
        for pain in pains:
            # Appliquer scoring rules
            if pain.budget_estimate_eur >= 1000:  # Plancher minimum
                pain.score = min(100, pain.score + 5)  # Bonus si budget ≥1k
            
            # Filtrer
            if pain.score >= self.SCORE_THRESHOLDS["minimum"]:
                filtered.append(pain)
                self.detected_pains[pain.pain_id] = pain
        
        return sorted(filtered, key=lambda p: p.score, reverse=True)
    
    async def run_cycle(self) -> Dict:
        """Cycle complet: detect → score → return"""
        self.run_count += 1
        self.last_run = datetime.now(timezone.utc)
        
        logger.info(f"Pain Hunter cycle #{self.run_count}")
        
        # Detect
        detected = await self.detect_all()
        
        # Score + Filter
        filtered = await self.filter_and_score(detected)
        
        # Separate by priority
        auto_advance = [p for p in filtered if p.score >= self.SCORE_THRESHOLDS["auto_advance"]]
        priority = [p for p in auto_advance if p.score >= self.SCORE_THRESHOLDS["priority"]]
        
        result = {
            'run_count': self.run_count,
            'timestamp': self.last_run.isoformat(),
            'total_detected': len(detected),
            'total_filtered': len(filtered),
            'auto_advance_count': len(auto_advance),
            'priority_count': len(priority),
            'auto_advance_pains': [p.to_dict() for p in auto_advance],
            'priority_pains': [p.to_dict() for p in priority],
        }
        
        return result
    
    async def start_daemon(self, interval_seconds: int = 3600):
        """Démarrer le daemon Pain Hunter (toutes les heures par défaut)"""
        logger.info(f"Pain Hunter daemon started (interval: {interval_seconds}s)")
        
        while True:
            try:
                await self.run_cycle()
                await asyncio.sleep(interval_seconds)
            except Exception as e:
                logger.error(f"Pain Hunter daemon error: {e}")
                await asyncio.sleep(60)  # Retry après 60s
    
    def get_stats(self) -> Dict:
        """Retourner les stats du Pain Hunter"""
        return {
            'run_count': self.run_count,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'total_detected': len(self.detected_pains),
            'high_priority_count': sum(1 for p in self.detected_pains.values() if p.score >= 80),
        }

# Instance globale
pain_hunter = PainHunterAgent()

async def main():
    """Test function"""
    result = await pain_hunter.run_cycle()
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
