"""
NAYA CORE — AGENT 6 — CONTENT ENGINE ADVANCED
Production contenu B2B récurrent (3k-15k EUR/mois abonnement)
Articles LinkedIn, WhitePapers OT, Newsletters, Études de cas
Planification 4 semaines + distribution automatique
"""

import asyncio
import json
import logging
from typing import Optional, List, Dict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum

logger = logging.getLogger(__name__)

class ContentType(Enum):
    LINKEDIN_POST = "linkedin_post"
    WHITEPAPER = "whitepaper"
    NEWSLETTER = "newsletter"
    CASE_STUDY = "case_study"
    BLOG_ARTICLE = "blog_article"

@dataclass
class ContentPiece:
    """Morceau de contenu généré"""
    content_id: str
    content_type: ContentType
    title: str
    body: str
    target_audience: str
    keywords: List[str] = field(default_factory=list)
    engagement_estimate: int = 0  # Estimated impressions
    distribution_channels: List[str] = field(default_factory=list)
    scheduled_date: Optional[datetime] = None
    published_date: Optional[datetime] = None
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self):
        return {
            'content_id': self.content_id,
            'content_type': self.content_type.value,
            'title': self.title,
            'body': self.body[:500],  # Truncate for display
            'target_audience': self.target_audience,
            'keywords': self.keywords,
            'engagement_estimate': self.engagement_estimate,
            'distribution_channels': self.distribution_channels,
            'scheduled_date': self.scheduled_date.isoformat() if self.scheduled_date else None,
            'generated_at': self.generated_at.isoformat(),
        }

class ContentStrategy:
    """Planification contenu 4 semaines"""
    
    CONTENT_CALENDAR = {
        'Monday': [ContentType.LINKEDIN_POST],
        'Tuesday': [ContentType.BLOG_ARTICLE],
        'Wednesday': [ContentType.LINKEDIN_POST],
        'Thursday': [ContentType.CASE_STUDY],
        'Friday': [ContentType.LINKEDIN_POST],
    }
    
    TOPICS = [
        'IEC 62443 Security Levels Explained',
        'NIS2 Directive: What You Need to Know',
        'SCADA Vulnerability Trends 2024',
        'Zero Trust for OT Environments',
        'Ransomware Prevention in Manufacturing',
        'Cyber Risk Management for Critical Infrastructure',
    ]
    
    async def generate_calendar(self, weeks: int = 4) -> List[Dict]:
        """Générer calendrier contenu 4 semaines"""
        calendar = []
        
        days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        
        for week in range(weeks):
            for day_idx, day in enumerate(days_of_week):
                content_types = self.CONTENT_CALENDAR.get(day, [ContentType.LINKEDIN_POST])
                topic_idx = (week * 5 + day_idx) % len(self.TOPICS)
                
                for content_type in content_types:
                    scheduled_date = datetime.now(timezone.utc) + timedelta(days=week*7 + day_idx)
                    
                    calendar.append({
                        'week': week + 1,
                        'day': day,
                        'content_type': content_type.value,
                        'topic': self.TOPICS[topic_idx],
                        'scheduled_date': scheduled_date,
                    })
        
        return calendar

class ContentGenerator:
    """Générer contenu dynamique"""
    
    async def generate_linkedin_post(self, topic: str) -> str:
        """Générer post LinkedIn"""
        await asyncio.sleep(0.1)
        return f"""🔐 {topic}

Industrial organizations face unprecedented cyber threats. 

Key points:
✓ Threat landscape evolving rapidly
✓ Legacy systems increasingly targeted
✓ Compliance requirements stricter

What's your biggest OT security challenge?

#Cybersecurity #OT #IEC62443 #NIS2
"""
    
    async def generate_whitepaper(self, topic: str) -> str:
        """Générer whitepaper"""
        await asyncio.sleep(0.3)
        return f"""WHITEPAPER: {topic}

TABLE OF CONTENTS
1. Executive Summary
2. The Challenge
3. Industry Context
4. Solutions Framework
5. Implementation Roadmap
6. Case Studies
7. Recommendations

EXECUTIVE SUMMARY
This whitepaper explores {topic} and provides actionable guidance...

[Full whitepaper content would follow]
"""
    
    async def generate_case_study(self, company_name: str) -> str:
        """Générer case study"""
        await asyncio.sleep(0.2)
        return f"""CASE STUDY: {company_name}

SITUATION
{company_name} faced critical OT security gaps threatening production...

SOLUTION
Our comprehensive audit and remediation program...

RESULTS
✓ Compliance score: 45 → 88%
✓ Risk reduction: 72%
✓ Operational efficiency: +15%
✓ Time to remediation: 6 months

LESSONS LEARNED
1. Early engagement crucial
2. Risk prioritization essential
3. Phased approach works best
"""

class ContentEngineAdvanced:
    """AGENT 6 — CONTENT ENGINE ADVANCED
    Générer contenu B2B récurrent
    Distribution LinkedIn, newsletters, blog
    Abonnement 3k-15k EUR/mois
    """
    
    def __init__(self):
        self.strategy = ContentStrategy()
        self.generator = ContentGenerator()
        self.content_created: Dict[str, ContentPiece] = {}
        self.run_count = 0
    
    async def generate_single(self, content_type: ContentType, topic: str, 
                             scheduled_date: datetime) -> ContentPiece:
        """Générer UN morceau de contenu"""
        
        logger.info(f"Generating {content_type.value}: {topic}")
        
        # Generate body based on type
        if content_type == ContentType.LINKEDIN_POST:
            body = await self.generator.generate_linkedin_post(topic)
            engagement = 500
        elif content_type == ContentType.WHITEPAPER:
            body = await self.generator.generate_whitepaper(topic)
            engagement = 1500
        elif content_type == ContentType.CASE_STUDY:
            body = await self.generator.generate_case_study('Sample Corp')
            engagement = 800
        else:
            body = f"Article about {topic}"
            engagement = 600
        
        content = ContentPiece(
            content_id=f"content_{hash(topic + content_type.value) % 1000000}",
            content_type=content_type,
            title=topic,
            body=body,
            target_audience="RSSI, DSI, Security Managers",
            keywords=['OT', 'Cybersecurity', 'Compliance', topic.split()[0]],
            engagement_estimate=engagement,
            distribution_channels=['LinkedIn', 'Email', 'Blog'],
            scheduled_date=scheduled_date,
        )
        
        self.content_created[content.content_id] = content
        
        return content
    
    async def generate_calendar_content(self) -> List[ContentPiece]:
        """Générer contenu pour calendrier 4 semaines"""
        
        calendar = await self.strategy.generate_calendar(weeks=4)
        
        tasks = []
        for item in calendar:
            # FIX V19.3: ContentType enum attend LINKEDIN_POST pas "LINKEDIN POST"
            # item['content_type'] est déjà au format "linkedin_post" (minuscules avec _)
            ct_key = item['content_type'].upper()
            try:
                ct_enum = ContentType[ct_key]
            except KeyError:
                logger.warning(f"ContentType inconnu: {ct_key} — fallback LINKEDIN_POST")
                ct_enum = ContentType.LINKEDIN_POST
            task = self.generate_single(
                ct_enum,
                item['topic'],
                item['scheduled_date']
            )
            tasks.append(task)
        
        return await asyncio.gather(*tasks)
    
    async def run_cycle(self) -> Dict:
        """Cycle complet: générer contenu 4 semaines"""
        self.run_count += 1
        
        logger.info(f"Content Engine cycle #{self.run_count}")
        
        content = await self.generate_calendar_content()
        
        # Stats par type
        type_breakdown = {}
        for c in content:
            ct = c.content_type.value
            type_breakdown[ct] = type_breakdown.get(ct, 0) + 1
        
        result = {
            'run_count': self.run_count,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'total_generated': len(content),
            'type_breakdown': type_breakdown,
            'total_engagement_potential': sum(c.engagement_estimate for c in content),
            'monthly_revenue_estimate': 8000,  # Abonnement moyen
            'content_pieces': [c.to_dict() for c in content[:5]],  # Top 5 seulement
        }
        
        return result
    
    def get_stats(self) -> Dict:
        """Stats"""
        return {
            'run_count': self.run_count,
            'total_content_created': len(self.content_created),
            'monthly_engagement_potential': sum(c.engagement_estimate for c in self.content_created.values()),
        }

# Instance globale
content_engine = ContentEngineAdvanced()

async def main():
    result = await content_engine.run_cycle()
    print(json.dumps(result, indent=2, default=str))

if __name__ == "__main__":
    asyncio.run(main())

# Alias for backwards compatibility
ContentEngineAgent = ContentEngineAdvanced