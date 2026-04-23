"""
NAYA — Multi Channel Manager v5.0
=====================================
Gère les campagnes sur 8+ canaux avec narrative cohérente.
"""
import hashlib, logging
from typing import Dict, List, Any, Optional
from enum import Enum
from datetime import datetime, timezone

log = logging.getLogger("NAYA.CHANNELS")

class ChannelType(Enum):
    LINKEDIN       = "linkedin"
    TWITTER        = "twitter"
    INSTAGRAM      = "instagram"
    EMAIL          = "email"
    BLOG           = "blog"
    PRESS_RELEASE  = "press_release"
    SALES_OUTREACH = "sales_outreach"
    GOOGLE_ADS     = "google_ads"
    FACEBOOK_ADS   = "facebook_ads"
    EVENTS         = "events"

class StorytellingMode(Enum):
    GROWTH_STORY   = "growth_story"
    CRISIS_TRIUMPH = "crisis_triumph"
    INNOVATION     = "innovation"
    SERVICE_EXCEL  = "service_excellence"
    VISION_MISSION = "vision_mission"

CHANNEL_SPECS = {
    ChannelType.TWITTER:        {"max_chars": 280,  "tone": "punchy",       "reach": 5000,  "engagement": 0.03},
    ChannelType.LINKEDIN:       {"max_chars": 3000, "tone": "professional", "reach": 8000,  "engagement": 0.06},
    ChannelType.INSTAGRAM:      {"max_chars": 2200, "tone": "visual",       "reach": 6000,  "engagement": 0.08},
    ChannelType.EMAIL:          {"max_chars": 2000, "tone": "personal",     "reach": 3000,  "engagement": 0.22},
    ChannelType.BLOG:           {"max_chars": 8000, "tone": "thought_lead", "reach": 2000,  "engagement": 0.04},
    ChannelType.PRESS_RELEASE:  {"max_chars": 1500, "tone": "news",         "reach": 50000, "engagement": 0.02},
    ChannelType.SALES_OUTREACH: {"max_chars": 500,  "tone": "direct",       "reach": 50,    "engagement": 0.15},
    ChannelType.GOOGLE_ADS:     {"max_chars": 90,   "tone": "urgent",       "reach": 20000, "engagement": 0.05},
    ChannelType.FACEBOOK_ADS:   {"max_chars": 300,  "tone": "emotional",    "reach": 15000, "engagement": 0.04},
    ChannelType.EVENTS:         {"max_chars": 300,  "tone": "engaging",     "reach": 500,   "engagement": 0.20},
}

class MultiChannelManager:
    """Gestionnaire multi-canal — narrative cohérente sur tous canaux."""

    def __init__(self):
        self.campaigns: List[Dict] = []
        self.published_count = 0
        self.total_reach = 0

    def create_campaign(self, brand_name: str, core_message: str, target_audience: str,
                        mode: StorytellingMode = StorytellingMode.GROWTH_STORY,
                        channels: Optional[List[ChannelType]] = None) -> Dict:
        if channels is None:
            channels = [ChannelType.LINKEDIN, ChannelType.TWITTER, ChannelType.EMAIL,
                        ChannelType.BLOG, ChannelType.PRESS_RELEASE, ChannelType.INSTAGRAM,
                        ChannelType.SALES_OUTREACH, ChannelType.GOOGLE_ADS]

        campaign_id = f"CAMP-{hashlib.md5(f'{brand_name}{core_message}'.encode()).hexdigest()[:8]}"
        channel_contents = []

        for ch in channels:
            spec = CHANNEL_SPECS.get(ch, {"max_chars": 500, "tone": "neutral", "reach": 1000, "engagement": 0.03})
            body = self._adapt_body(core_message, ch, mode, target_audience, spec["max_chars"])
            channel_contents.append({
                "channel": ch.value, "tone": spec["tone"], "body": body[:spec["max_chars"]],
                "cta": self._cta(ch, brand_name), "estimated_reach": spec["reach"],
                "engagement_rate": spec["engagement"], "published": False,
            })

        total_reach = sum(c["estimated_reach"] for c in channel_contents)
        campaign = {"campaign_id": campaign_id, "brand": brand_name,
                    "core_message": core_message, "mode": mode.value,
                    "target_audience": target_audience, "channels": channel_contents,
                    "total_reach": total_reach, "status": "READY",
                    "created_at": datetime.now(timezone.utc).isoformat()}
        self.campaigns.append(campaign)
        return campaign

    def _adapt_body(self, message: str, channel: ChannelType, mode: StorytellingMode,
                    audience: str, max_chars: int) -> str:
        templates = {
            StorytellingMode.GROWTH_STORY:   f"De 0 à une vraie traction: {message}. Pour {audience}.",
            StorytellingMode.INNOVATION:      f"Comment nous résolvons {message} pour {audience}.",
            StorytellingMode.SERVICE_EXCEL:   f"47 clients comme vous ont obtenu: {message}.",
            StorytellingMode.VISION_MISSION:  f"Notre mission: {message} — pour chaque {audience}.",
            StorytellingMode.CRISIS_TRIUMPH:  f"Situation difficile → Apprentissage → {message}.",
        }
        base = templates.get(mode, message)
        if channel == ChannelType.TWITTER: return base[:250] + " #naya #business"
        if channel == ChannelType.LINKEDIN:
            return f"{base}\n\n1. Approche systématique\n2. Résultats mesurables\n3. Impact durable\n\nVotre avis ?"
        return base

    def _cta(self, channel: ChannelType, brand: str) -> str:
        ctas = {
            ChannelType.TWITTER: "RT si utile !",
            ChannelType.LINKEDIN: "Connectons-nous",
            ChannelType.EMAIL: "Répondez à cet email",
            ChannelType.SALES_OUTREACH: "20 minutes cette semaine ?",
            ChannelType.GOOGLE_ADS: "Découvrir maintenant",
        }
        return ctas.get(channel, f"Contactez {brand}")

    def get_stats(self) -> Dict:
        return {"campaigns": len(self.campaigns), "published": self.published_count,
                "total_reach": self.total_reach, "channels_available": len(ChannelType)}


_MANAGER: Optional[MultiChannelManager] = None

def get_channel_manager() -> MultiChannelManager:
    global _MANAGER
    if _MANAGER is None: _MANAGER = MultiChannelManager()
    return _MANAGER
