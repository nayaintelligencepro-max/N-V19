"""
NAYA — Publication Orchestrator
Orchestre la publication multi-canal pour maximiser la portée.
"""
from typing import Dict, List
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

@dataclass
class PublicationPlan:
    content: str; channels: List[str]
    schedule: List[datetime]; frequency: str
    estimated_reach: int; estimated_leads: int

class PublicationOrchestrator:
    """Coordonne la publication de contenu sur tous les canaux."""

    OPTIMAL_TIMES = {
        "linkedin": [(8,30), (12,0), (17,30)],
        "email": [(7,0), (10,0), (14,0)],
        "instagram": [(9,0), (12,30), (19,0)],
    }

    def create_plan(self, content: str, channels: List[str], 
                   start: datetime = None, weeks: int = 4) -> PublicationPlan:
        start = start or datetime.now(timezone.utc)
        schedule = []
        for week in range(weeks):
            for channel in channels:
                times = self.OPTIMAL_TIMES.get(channel.lower(), [(9,0)])
                for h, m in times[:2]:
                    d = start + timedelta(weeks=week, hours=h, minutes=m)
                    schedule.append(d)
        reach = len(channels) * len(schedule) * 150
        leads = int(reach * 0.02)
        return PublicationPlan(content, channels, schedule[:20], "weekly", reach, leads)

    def orchestrate(self, plans: List[PublicationPlan]) -> Dict:
        total_reach = sum(p.estimated_reach for p in plans)
        total_leads = sum(p.estimated_leads for p in plans)
        return {"total_publications": sum(len(p.schedule) for p in plans),
                "estimated_reach": total_reach, "estimated_leads": total_leads,
                "channels": list(set(c for p in plans for c in p.channels))}
