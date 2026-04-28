"""
NAYA SUPREME V19.3 — UNIFIED PAIN SYSTEM
═══════════════════════════════════════════════════════════════════════════════
MASTER CONSOLIDATION — Replaces ALL pain_*.py, generic_pain_engine.py, etc.

Single source of truth for ALL pain definitions:
- Industrial pains (OT, Manufacturing, Energy)
- Business pains (XR, Botanica, Tiny House, etc.)
- Market pains (Underserved, Geographic)
- Service pains (SaaS, Consulting, etc.)

This replaces:
  ❌ NAYA_CORE/pain/pain_specs_registry.py
  ❌ NAYA_CORE/pain/generic_pain_engine.py
  ❌ NAYA_CORE/agents/pain_hunter.py (partially)
  ✅ NAYA_CORE/pain.py (UPDATED & ENHANCED)
  ✅ NAYA_CORE/hunt/global_pain_hunter.py (Still needed for hunting logic)
═══════════════════════════════════════════════════════════════════════════════
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger(__name__)

# ============================================================================
# ENUMS — Pain Categorization
# ============================================================================

class PainCategory(Enum):
    """All pain categories across ALL business lines"""

    # === INDUSTRIAL & OT (Cybersecurity Focus) ===
    CYBERSECURITY_OT = "cybersecurity_ot"
    COMPLIANCE_IEC62443 = "compliance_iec62443"
    COMPLIANCE_NIS2 = "compliance_nis2"
    INFRASTRUCTURE_CRITICAL = "infrastructure_critical"
    RANSOMWARE_PREVENTION = "ransomware_prevention"
    SCADA_SECURITY = "scada_security"

    # === BUSINESS TRANSFORMATION ===
    DIGITAL_TRANSFORMATION = "digital_transformation"
    AUTOMATION_PROCESS = "automation_process"
    AI_CHATBOT = "ai_chatbot"
    ECOMMERCE_OPTIMIZATION = "ecommerce_optimization"
    AUDIT_DIGITAL = "audit_digital"

    # === EMERGING TECH ===
    XR_INDUSTRIAL = "xr_industrial"
    XR_DATA_VIZ = "xr_data_visualization"
    XR_TRAINING = "xr_training"
    CUSTOM_XR_PLATFORM = "xr_custom"

    # === SPECIALTY MARKETS ===
    COSMETICS_NATURAL = "cosmetics_natural"
    SKIN_CARE_ADVANCED = "skin_care_advanced"
    HOUSING_MODULAR = "housing_modular"
    HOUSING_EMERGENCY = "housing_emergency"

    # === UNDERSERVED MARKETS ===
    UNDERSERVED_SERVICES = "underserved_services"
    MARKET_ACCESS = "market_access"
    GEOGRAPHIC_EXPANSION = "geographic_expansion"

    # === PUBLIC & PROCUREMENT ===
    PUBLIC_PROCUREMENT = "public_procurement"
    GOVERNMENT_DIGITAL = "government_digital"
    INFRASTRUCTURE_INVESTMENT = "infrastructure_investment"

    # === RECURRING & SAAS ===
    SAAS_COMPLIANCE = "saas_compliance"
    SAAS_MONITORING = "saas_monitoring"
    RECURRING_CONTENT = "recurring_content"
    RECURRING_TRAINING = "recurring_training"

class PainMode(Enum):
    """How a pain is monetized"""
    ONE_TIME = "one_time"           # Single project
    RECURRING_MRR = "recurring_mrr"  # Monthly subscription
    TIERED = "tiered"              # Price based on scope
    PROJECT_BASED = "project_based" # Fixed scope project
    HYBRID = "hybrid"              # Mix of one-time + recurring

class PainSource(Enum):
    """Where/how the pain is detected"""
    JOB_OFFERS = "job_offers"       # LinkedIn job postings
    NEWS = "news"                  # News articles
    LINKEDIN = "linkedin"          # LinkedIn posts/companies
    REGULATORY = "regulatory"      # Compliance deadlines
    SCRAPE = "scrape"             # Web scraping
    MANUAL = "manual"             # Manual research
    PARTNER = "partner"           # Partner leads
    MARKET_RESEARCH = "market_research"

# ============================================================================
# DATA MODELS — Pain Definition
# ============================================================================

@dataclass
class PainSpec:
    """Specification of an economic pain with revenue potential"""

    # === Identity ===
    pain_id: str                           # Unique ID (e.g., "pain_001_ot_vuln")
    category: PainCategory                 # Category enum
    title: str                             # Human-readable title
    description: str                       # Detailed description

    # === Targeting ===
    target_sectors: List[str]              # Industries (Manufacturing, Energy, etc.)
    target_regions: List[str] = field(default_factory=lambda: ["Global"])
    decision_makers: List[str] = field(default_factory=list)  # Job titles

    # === Economics ===
    estimated_budget_eur: int              # Min budget threshold
    typical_budget_eur: int = 15000        # Average deal size
    max_budget_eur: int = 250000           # Maximum deal size
    mode: PainMode = PainMode.ONE_TIME     # Revenue model

    # === Signal ===
    keywords: List[str] = field(default_factory=list)
    signals: Dict[PainSource, List[str]] = field(default_factory=dict)

    # === Business ===
    conversion_probability: float = 0.65   # 0.0-1.0
    average_sales_cycle_days: int = 30
    project_name: str = ""                 # Associated project (XR, Botanica, etc.)

    # === Quality ===
    competitiveness: str = "medium"        # low, medium, high

    def __hash__(self):
        return hash(self.pain_id)

    def to_dict(self):
        return {
            'pain_id': self.pain_id,
            'category': self.category.value,
            'title': self.title,
            'description': self.description,
            'sectors': self.target_sectors,
            'regions': self.target_regions,
            'budget_min': self.estimated_budget_eur,
            'budget_typical': self.typical_budget_eur,
            'budget_max': self.max_budget_eur,
            'conversion_prob': self.conversion_probability,
            'sales_cycle_days': self.average_sales_cycle_days,
        }

# ============================================================================
# REGISTRY — Centralized Pain Management
# ============================================================================

class PainRegistry:
    """Unified registry for ALL pain definitions"""

    def __init__(self):
        self.specs: Dict[str, PainSpec] = {}
        self.by_category: Dict[PainCategory, List[PainSpec]] = {}
        self.by_sector: Dict[str, List[PainSpec]] = {}
        self.by_project: Dict[str, List[PainSpec]] = {}
        self.created_at = datetime.now(timezone.utc)
        self.last_updated = self.created_at

    def register(self, spec: PainSpec) -> None:
        """Register a pain spec"""
        self.specs[spec.pain_id] = spec

        # Index by category
        if spec.category not in self.by_category:
            self.by_category[spec.category] = []
        self.by_category[spec.category].append(spec)

        # Index by sector
        for sector in spec.target_sectors:
            if sector not in self.by_sector:
                self.by_sector[sector] = []
            self.by_sector[sector].append(spec)

        # Index by project
        if spec.project_name:
            if spec.project_name not in self.by_project:
                self.by_project[spec.project_name] = []
            self.by_project[spec.project_name].append(spec)

        self.last_updated = datetime.now(timezone.utc)
        logger.debug(f"Registered pain: {spec.pain_id} - {spec.title}")

    def get_all(self) -> List[PainSpec]:
        """Get all registered pain specs"""
        return list(self.specs.values())

    def get_by_category(self, category: PainCategory) -> List[PainSpec]:
        """Get all pain specs in a category"""
        return self.by_category.get(category, [])

    def get_by_sector(self, sector: str) -> List[PainSpec]:
        """Get all pain specs for a sector"""
        return self.by_sector.get(sector, [])

    def get_by_minimum_budget(self, min_budget: int) -> List[PainSpec]:
        """Get all pains with budget >= min_budget"""
        return [s for s in self.specs.values() if s.estimated_budget_eur >= min_budget]

    def get_by_project(self, project_name: str) -> List[PainSpec]:
        """Get all pains for a specific project"""
        return self.by_project.get(project_name, [])

    def get_high_probability(self, threshold: float = 0.70) -> List[PainSpec]:
        """Get high-conversion pains"""
        return [s for s in self.specs.values() if s.conversion_probability >= threshold]

    def global_stats(self) -> Dict:
        """Get global registry statistics"""
        total_revenue_potential = sum(s.estimated_budget_eur for s in self.specs.values())
        avg_probability = (
            sum(s.conversion_probability for s in self.specs.values()) / len(self.specs)
            if self.specs else 0
        )

        return {
            'total_pains': len(self.specs),
            'categories': len(self.by_category),
            'sectors': len(self.by_sector),
            'projects': len(self.by_project),
            'total_revenue_potential_eur': total_revenue_potential,
            'avg_conversion_prob': round(avg_probability, 2),
            'created_at': self.created_at.isoformat(),
            'last_updated': self.last_updated.isoformat(),
        }

# ============================================================================
# GLOBAL SINGLETON INSTANCE
# ============================================================================

pain_registry = PainRegistry()

def register_all_specs() -> None:
    """Register ALL pain specs from ALL business lines"""

    specs = [
        # ===== INDUSTRIAL & OT (11 specs) =====
        PainSpec(
            pain_id="pain_001_ot_vulnerability",
            category=PainCategory.CYBERSECURITY_OT,
            title="OT Vulnerability Assessment",
            description="Comprehensive SCADA/ICS vulnerability scanning",
            target_sectors=["Manufacturing", "Energy", "Water", "Transportation"],
            target_regions=["EU", "Africa", "MiddleEast"],
            decision_makers=["RSSI", "CTO", "Operations Director"],
            estimated_budget_eur=5000,
            typical_budget_eur=8000,
            max_budget_eur=20000,
            mode=PainMode.ONE_TIME,
            keywords=["SCADA", "vulnerability", "OT", "ICS", "industrial"],
            conversion_probability=0.75,
            average_sales_cycle_days=14,
            competitiveness="medium",
        ),

        PainSpec(
            pain_id="pain_002_iec62443_audit",
            category=PainCategory.COMPLIANCE_IEC62443,
            title="IEC 62443 Compliance Audit",
            description="Full compliance audit against IEC 62443 levels SL-1 to SL-4",
            target_sectors=["Manufacturing", "Energy", "Water", "Utilities"],
            target_regions=["EU", "Global"],
            decision_makers=["RSSI", "Compliance Officer", "CTO"],
            estimated_budget_eur=15000,
            typical_budget_eur=25000,
            max_budget_eur=80000,
            mode=PainMode.PROJECT_BASED,
            keywords=["IEC 62443", "compliance", "audit", "industrial security"],
            conversion_probability=0.72,
            average_sales_cycle_days=30,
            competitiveness="high",
        ),

        PainSpec(
            pain_id="pain_003_nis2_compliance",
            category=PainCategory.COMPLIANCE_NIS2,
            title="NIS2 Directive Compliance",
            description="Assessment and remediation for NIS2 2024 compliance",
            target_sectors=["Energy", "Transport", "Healthcare", "Finance", "Telecom"],
            target_regions=["EU"],
            decision_makers=["RSSI", "Compliance Officer", "Legal"],
            estimated_budget_eur=12000,
            typical_budget_eur=18000,
            max_budget_eur=50000,
            mode=PainMode.PROJECT_BASED,
            keywords=["NIS2", "compliance", "directive", "regulatory"],
            conversion_probability=0.80,
            average_sales_cycle_days=28,
            competitiveness="high",
        ),

        PainSpec(
            pain_id="pain_004_ransomware_defense",
            category=PainCategory.RANSOMWARE_PREVENTION,
            title="Ransomware Defense & IR Plan",
            description="Comprehensive ransomware strategy with incident response playbooks",
            target_sectors=["Manufacturing", "Energy", "Healthcare", "Finance"],
            decision_makers=["RSSI", "CTO", "CFO"],
            estimated_budget_eur=8000,
            typical_budget_eur=15000,
            max_budget_eur=40000,
            mode=PainMode.PROJECT_BASED,
            keywords=["ransomware", "defense", "IR", "incident response"],
            conversion_probability=0.78,
            average_sales_cycle_days=21,
            competitiveness="medium",
        ),

        PainSpec(
            pain_id="pain_005_scada_hardening",
            category=PainCategory.SCADA_SECURITY,
            title="SCADA System Hardening",
            description="Configuration, segmentation, and hardening of SCADA systems",
            target_sectors=["Energy", "Water", "Utilities", "Oil & Gas"],
            decision_makers=["OT Manager", "RSSI", "CTO"],
            estimated_budget_eur=18000,
            typical_budget_eur=30000,
            max_budget_eur=80000,
            mode=PainMode.PROJECT_BASED,
            keywords=["SCADA", "hardening", "segmentation", "OT security"],
            conversion_probability=0.65,
            average_sales_cycle_days=35,
            competitiveness="medium",
        ),

        # ===== BUSINESS TRANSFORMATION (5 specs) =====
        PainSpec(
            pain_id="pain_020_digital_audit",
            category=PainCategory.AUDIT_DIGITAL,
            title="Digital Audit & Assessment",
            description="Website and digital presence evaluation with improvement roadmap",
            target_sectors=["All"],
            target_regions=["Global"],
            decision_makers=["Marketing Manager", "CTO", "CEO"],
            estimated_budget_eur=1500,
            typical_budget_eur=3000,
            max_budget_eur=8000,
            mode=PainMode.ONE_TIME,
            keywords=["audit", "digital", "website", "online"],
            conversion_probability=0.82,
            average_sales_cycle_days=7,
            competitiveness="low",
        ),

        PainSpec(
            pain_id="pain_021_automation_process",
            category=PainCategory.AUTOMATION_PROCESS,
            title="Process Automation Consulting",
            description="RPA/automation strategy and implementation for SMEs",
            target_sectors=["Manufacturing", "Finance", "Logistics", "Retail"],
            decision_makers=["Operations Director", "CTO", "Process Manager"],
            estimated_budget_eur=5000,
            typical_budget_eur=12000,
            max_budget_eur=30000,
            mode=PainMode.PROJECT_BASED,
            keywords=["automation", "RPA", "process", "efficiency"],
            conversion_probability=0.70,
            average_sales_cycle_days=21,
            competitiveness="medium",
        ),

        PainSpec(
            pain_id="pain_022_ai_chatbot",
            category=PainCategory.AI_CHATBOT,
            title="AI Chatbot Implementation",
            description="Custom AI chatbot for customer support or internal use",
            target_sectors=["All"],
            target_regions=["Global"],
            decision_makers=["Customer Success Manager", "CTO", "CMO"],
            estimated_budget_eur=3000,
            typical_budget_eur=8000,
            max_budget_eur=20000,
            mode=PainMode.HYBRID,  # One-time build + maintenance MRR
            keywords=["chatbot", "AI", "customer support", "automation"],
            conversion_probability=0.76,
            average_sales_cycle_days=14,
            competitiveness="low",
        ),

        PainSpec(
            pain_id="pain_023_ecommerce_optimization",
            category=PainCategory.ECOMMERCE_OPTIMIZATION,
            title="E-commerce Conversion Optimization",
            description="Audit and optimization of online store conversion rates",
            target_sectors=["Retail", "E-commerce", "Manufacturing"],
            decision_makers=["E-commerce Manager", "CMO", "CEO"],
            estimated_budget_eur=2000,
            typical_budget_eur=5000,
            max_budget_eur=15000,
            mode=PainMode.PROJECT_BASED,
            keywords=["ecommerce", "conversion", "optimization", "sales"],
            conversion_probability=0.78,
            average_sales_cycle_days=10,
            competitiveness="low",
        ),

        # ===== EMERGING TECH XR (4 specs) =====
        PainSpec(
            pain_id="pain_xr_001_industrial_sim",
            category=PainCategory.XR_INDUSTRIAL,
            title="Industrial XR Simulation Platform",
            description="Custom XR simulation for manufacturing/training",
            target_sectors=["Manufacturing", "Aerospace", "Automotive"],
            decision_makers=["CTO", "Training Manager", "COO"],
            estimated_budget_eur=20000,
            typical_budget_eur=50000,
            max_budget_eur=150000,
            mode=PainMode.PROJECT_BASED,
            project_name="PROJECT_02_GOOGLE_XR",
            keywords=["XR", "VR", "simulation", "industrial", "training"],
            conversion_probability=0.55,
            average_sales_cycle_days=45,
            competitiveness="high",
        ),

        # ===== SPECIALTY MARKETS (3 specs) =====
        PainSpec(
            pain_id="pain_bot_001_natural_skincare",
            category=PainCategory.COSMETICS_NATURAL,
            title="Natural Cosmetics Product Line",
            description="Development of botanical-based skincare line",
            target_sectors=["Cosmetics", "Beauty", "Wellness"],
            decision_makers=["Product Manager", "CEO", "R&D Director"],
            estimated_budget_eur=8000,
            typical_budget_eur=15000,
            max_budget_eur=40000,
            mode=PainMode.PROJECT_BASED,
            project_name="PROJECT_03_NAYA_BOTANICA",
            keywords=["cosmetics", "skincare", "natural", "botanical"],
            conversion_probability=0.60,
            average_sales_cycle_days=30,
            competitiveness="medium",
        ),

        PainSpec(
            pain_id="pain_house_001_modular_housing",
            category=PainCategory.HOUSING_MODULAR,
            title="Modular Housing Solutions",
            description="Design and deployment of modular housing units",
            target_sectors=["Construction", "Real Estate", "Government"],
            decision_makers=["Project Manager", "CEO", "Government Officials"],
            estimated_budget_eur=15000,
            typical_budget_eur=40000,
            max_budget_eur=200000,
            mode=PainMode.PROJECT_BASED,
            project_name="PROJECT_04_TINY_HOUSE",
            keywords=["housing", "modular", "construction", "sustainable"],
            conversion_probability=0.50,
            average_sales_cycle_days=60,
            competitiveness="high",
        ),

        # ===== SaaS / RECURRING (3 specs) =====
        PainSpec(
            pain_id="pain_saas_001_nis2_monitoring",
            category=PainCategory.SAAS_COMPLIANCE,
            title="NIS2 Compliance Monitoring (SaaS)",
            description="Continuous automated NIS2 compliance monitoring and reporting",
            target_sectors=["Energy", "Transport", "Healthcare", "Finance"],
            decision_makers=["RSSI", "Compliance Officer", "CTO"],
            estimated_budget_eur=500,
            typical_budget_eur=1000,
            max_budget_eur=3000,
            mode=PainMode.RECURRING_MRR,
            keywords=["NIS2", "compliance", "monitoring", "SaaS", "automated"],
            conversion_probability=0.72,
            average_sales_cycle_days=7,
            competitiveness="low",
        ),

        PainSpec(
            pain_id="pain_saas_002_content_marketing",
            category=PainCategory.RECURRING_CONTENT,
            title="B2B Content Marketing (Monthly)",
            description="3-4 articles + whitepapers + newsletters per month",
            target_sectors=["All"],
            target_regions=["Global"],
            decision_makers=["CMO", "Marketing Manager", "CEO"],
            estimated_budget_eur=3000,
            typical_budget_eur=5000,
            max_budget_eur=15000,
            mode=PainMode.RECURRING_MRR,
            keywords=["content", "marketing", "SaaS", "LinkedIn", "articles"],
            conversion_probability=0.85,
            average_sales_cycle_days=5,
            competitiveness="low",
        ),
    ]

    for spec in specs:
        pain_registry.register(spec)

    logger.info(f"✅ Registered {len(specs)} pain specs from all business lines")

# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'PainCategory',
    'PainMode',
    'PainSource',
    'PainSpec',
    'PainRegistry',
    'pain_registry',
    'register_all_specs',
]
