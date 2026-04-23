"""
NAYA V19 - Channel Project Bridge
Connecte chaque business/projet a ses canaux dedies.
Chaque business cree a son propre plan de canaux.
"""
import logging, time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

log = logging.getLogger("NAYA.CHANNEL.BRIDGE")

@dataclass
class ChannelPlan:
    project_id: str
    project_name: str
    channels: List[Dict[str, Any]] = field(default_factory=list)
    storytelling_angle: str = ""
    target_audience: str = ""
    credibility_strategy: str = ""
    content_calendar: List[Dict] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

CHANNEL_TEMPLATES = {
    "e-commerce": {
        "channels": [
            {"name": "instagram", "priority": 1, "content_type": "visual_product"},
            {"name": "tiktok", "priority": 2, "content_type": "short_video"},
            {"name": "facebook", "priority": 3, "content_type": "ads_community"},
            {"name": "seo_blog", "priority": 4, "content_type": "articles"},
        ],
        "storytelling": "Transformation client - avant/apres avec le produit",
        "credibility": "Temoignages clients + certifications + transparence ingredients"
    },
    "service_b2b": {
        "channels": [
            {"name": "linkedin", "priority": 1, "content_type": "thought_leadership"},
            {"name": "email", "priority": 2, "content_type": "outreach_direct"},
            {"name": "webinar", "priority": 3, "content_type": "education"},
        ],
        "storytelling": "Expertise sectorielle - ROI concret mesurable",
        "credibility": "Etudes de cas + chiffres + temoignages decideurs"
    },
    "saas": {
        "channels": [
            {"name": "linkedin", "priority": 1, "content_type": "product_launch"},
            {"name": "product_hunt", "priority": 2, "content_type": "launch"},
            {"name": "content_marketing", "priority": 3, "content_type": "seo"},
            {"name": "youtube", "priority": 4, "content_type": "demo_tutorial"},
        ],
        "storytelling": "Probleme -> Solution -> Resultat en X minutes",
        "credibility": "Demo live + essai gratuit + metriques utilisateurs"
    },
    "immobilier": {
        "channels": [
            {"name": "portails_immo", "priority": 1, "content_type": "listings"},
            {"name": "facebook_local", "priority": 2, "content_type": "community"},
            {"name": "instagram", "priority": 3, "content_type": "visual_property"},
        ],
        "storytelling": "Investissement intelligent - rentabilite demontree",
        "credibility": "Historique transactions + ROI reel + partenaires locaux"
    },
    "fintech": {
        "channels": [
            {"name": "linkedin", "priority": 1, "content_type": "trust_building"},
            {"name": "press_release", "priority": 2, "content_type": "credibility"},
            {"name": "community", "priority": 3, "content_type": "support"},
        ],
        "storytelling": "Liberte financiere - simplicite vs complexite bancaire",
        "credibility": "Licences reglementaires + securite + transparence"
    }
}

class ChannelProjectBridge:
    """Connecte chaque projet a ses canaux optimaux."""

    PROJECT_CHANNEL_MAP = {
        "PROJECT_01_CASH_RAPIDE": "service_b2b",
        "PROJECT_02_GOOGLE_XR": "service_b2b",
        "PROJECT_03_NAYA_BOTANICA": "e-commerce",
        "PROJECT_04_TINY_HOUSE": "e-commerce",
        "PROJECT_05_MARCHES_OUBLIES": "service_b2b",
        "PROJECT_06_ACQUISITION_IMMOBILIERE": "immobilier",
        "PROJECT_07_NAYA_PAYE": "fintech",
    }

    def __init__(self):
        self._plans: Dict[str, ChannelPlan] = {}

    def create_channel_plan(self, project_id: str, project_name: str,
                            business_type: str = None) -> ChannelPlan:
        btype = business_type or self.PROJECT_CHANNEL_MAP.get(project_id, "service_b2b")
        template = CHANNEL_TEMPLATES.get(btype, CHANNEL_TEMPLATES["service_b2b"])

        plan = ChannelPlan(
            project_id=project_id,
            project_name=project_name,
            channels=template["channels"],
            storytelling_angle=template["storytelling"],
            credibility_strategy=template["credibility"],
            target_audience=self._infer_audience(btype)
        )
        self._plans[project_id] = plan
        log.info(f"[CHANNEL-BRIDGE] Plan cree pour {project_id}: {len(plan.channels)} canaux")
        return plan

    def get_plan(self, project_id: str) -> Optional[ChannelPlan]:
        return self._plans.get(project_id)

    def add_channel(self, project_id: str, channel_name: str,
                    content_type: str, priority: int = 5) -> bool:
        plan = self._plans.get(project_id)
        if not plan:
            return False
        plan.channels.append({
            "name": channel_name, "priority": priority,
            "content_type": content_type
        })
        plan.channels.sort(key=lambda c: c["priority"])
        return True

    def generate_content_calendar(self, project_id: str, weeks: int = 4) -> List[Dict]:
        plan = self._plans.get(project_id)
        if not plan:
            return []
        calendar = []
        for week in range(1, weeks + 1):
            for ch in plan.channels[:3]:
                calendar.append({
                    "week": week,
                    "channel": ch["name"],
                    "content_type": ch["content_type"],
                    "storytelling": plan.storytelling_angle,
                    "status": "planned"
                })
        plan.content_calendar = calendar
        return calendar

    def _infer_audience(self, business_type: str) -> str:
        AUDIENCES = {
            "e-commerce": "Consommateurs 25-55 ans, sensibles qualite et naturalite",
            "service_b2b": "Decideurs PME/ETI, directeurs operations/IT, 35-55 ans",
            "saas": "Startups et PME tech, early adopters, CTO/CEO",
            "immobilier": "Investisseurs, primo-accedants, expatries",
            "fintech": "Particuliers et TPE/PME, 25-45 ans, mobile-first",
        }
        return AUDIENCES.get(business_type, "Professionnels et decideurs")

    def get_all_plans(self) -> Dict[str, ChannelPlan]:
        return self._plans.copy()

    def get_stats(self) -> Dict:
        return {
            "total_plans": len(self._plans),
            "total_channels": sum(len(p.channels) for p in self._plans.values()),
            "projects": list(self._plans.keys())
        }

_bridge = None
def get_channel_bridge():
    global _bridge
    if _bridge is None:
        _bridge = ChannelProjectBridge()
    return _bridge
