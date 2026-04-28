"""
NAYA SUPREME — HUNTING AGENTS
══════════════════════════════════════════════════════════════════════════════════
4 agents autonomes de chasse intégrés nativement dans NAYA SUPREME.

Agent 1: PainHunterB2B     — Douleurs B2B/B2A/Gouvernemental (3 catégories)
Agent 2: MegaProjectHunter — Projets innovants 15M-40M€ (GAFAM/infras)
Agent 3: ForgottenMarketConqueror — Marchés oubliés (conquête blue ocean)
Agent 4: StrategicBusinessCreator — Stratège business (blueprints complets)
══════════════════════════════════════════════════════════════════════════════════
"""

from .pain_hunter_b2b import PainHunterB2B, HuntCategory, HuntedPain
from .mega_project_hunter import MegaProjectHunter, MegaProject, TechDomain
from .forgotten_market_conqueror import ForgottenMarketConqueror, ForgottenMarket
from .strategic_business_creator import StrategicBusinessCreator, BusinessBlueprint
from .sourcing_procurement_agent import SourcingProcurementAgent
from .hunter_integration import HuntingAgentsIntegration

__all__ = [
    "PainHunterB2B", "HuntCategory", "HuntedPain",
    "MegaProjectHunter", "MegaProject", "TechDomain",
    "ForgottenMarketConqueror", "ForgottenMarket",
    "StrategicBusinessCreator", "BusinessBlueprint",
    "SourcingProcurementAgent",
    "HuntingAgentsIntegration",
]
