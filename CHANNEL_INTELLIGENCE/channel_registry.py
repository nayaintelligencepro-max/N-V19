"""
NAYA — Channel Registry
Registre complet des canaux d'acquisition et de distribution.
"""
from dataclasses import dataclass, field
from typing import Dict, List
from enum import Enum

class ChannelType(Enum):
    OUTBOUND = "outbound"     # On va chercher les clients
    INBOUND = "inbound"       # Les clients viennent à nous
    PARTNERSHIP = "partnership"  # Via partenaires
    REFERRAL = "referral"     # Via clients existants
    PAID = "paid"             # Publicité payante

@dataclass
class Channel:
    id: str; name: str; type: ChannelType
    cost_per_lead: float; conversion_rate: float
    avg_deal_size: float; time_to_close_days: int
    scalability: float  # 0-1
    requires_skill: str
    best_for: List[str] = field(default_factory=list)

    @property
    def roi_score(self):
        revenue = self.avg_deal_size * self.conversion_rate
        return (revenue - self.cost_per_lead) / max(self.cost_per_lead, 1)

CHANNEL_CATALOG = [
    Channel("C01","LinkedIn Outreach","outbound",50,0.08,8000,21,0.7,"Copywriting",
            ["B2B","Consultants","SaaS"]),
    Channel("C02","Email Cold Outreach","outbound",10,0.04,5000,30,0.9,"Ciblage",
            ["E-com","PME","Agences"]),
    Channel("C03","Partenariat Comptables","partnership",200,0.25,12000,14,0.6,"Relations",
            ["Finance","PME","Fiscalité"]),
    Channel("C04","SEO Local","inbound",300,0.15,3000,45,0.8,"SEO",
            ["Local","Services","Restaurants"]),
    Channel("C05","Référencement Clients","referral",0,0.40,15000,7,0.5,"Satisfaction",
            ["Tous secteurs"]),
    Channel("C06","Google Ads","paid",150,0.06,4000,14,1.0,"PPC",
            ["E-com","Services locaux"]),
    Channel("C07","Visite physique terrain","outbound",30,0.20,5000,3,0.4,"Vente directe",
            ["Restaurants","Retail","BTP"]),
    Channel("C08","Webinaire gratuit","inbound",80,0.12,6000,30,0.8,"Expertise",
            ["Coaches","Consultants","SaaS"]),
]

class ChannelRegistry:
    def __init__(self): self._channels = {c.id: c for c in CHANNEL_CATALOG}

    def best_for_vertical(self, vertical: str, budget: float = 1000) -> List[Channel]:
        eligible = [c for c in self._channels.values()
                   if any(v.lower() in " ".join(c.best_for).lower() for v in [vertical])
                   and c.cost_per_lead <= budget]
        return sorted(eligible, key=lambda c: c.roi_score, reverse=True)

    def fastest_to_revenue(self, n: int = 3) -> List[Channel]:
        return sorted(self._channels.values(), 
                     key=lambda c: c.time_to_close_days)[:n]

    def zero_budget_channels(self) -> List[Channel]:
        return [c for c in self._channels.values() if c.cost_per_lead <= 50]
