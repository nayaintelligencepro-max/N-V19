"""
NAYA SUPREME — STRATEGIC BUSINESS CREATOR
══════════════════════════════════════════════════════════════════════════════════
Agent stratégique autonome — analyse macro, crée des business models complets,
orchestre l'exécution de bout en bout.

DOCTRINE:
  Ne pas subir le marché. Le CRÉER.
  Chaque douleur détectée = un business potentiel.
  Chaque marché oublié = un empire possible.
  Chaque projet méga = un levier de cashflow.

RÔLE:
  Ce module est le STRATÈGE. Il prend les outputs des 3 autres agents
  (PainHunterB2B, MegaProjectHunter, ForgottenMarketConqueror)
  et les transforme en business models exécutables avec:
  - Business Model Canvas complet
  - Financial projections 12-36 mois
  - Go-to-Market strategy
  - Pricing strategy (via BUSINESS_ENGINES.strategic_pricing_engine)
  - Risk matrix
  - Execution roadmap

INTÉGRATION:
  → Consomme: HUNTING_AGENTS.pain_hunter_b2b
  → Consomme: HUNTING_AGENTS.mega_project_hunter
  → Consomme: HUNTING_AGENTS.forgotten_market_conqueror
  → Utilise: BUSINESS_ENGINES (pricing, model_builder, discretion)
  → Utilise: NAYA_CORE (autonomous_engine, scheduler, cash_engine_real)
  → Persiste: PERSISTENCE (database)
══════════════════════════════════════════════════════════════════════════════════
"""

import os, time, uuid, json, logging, threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime, timedelta, timezone
from pathlib import Path

log = logging.getLogger("NAYA.HUNTER.STRATEGIC_CREATOR")

def _gs(key: str, default: str = "") -> str:
    try:
        from SECRETS.secrets_loader import get_secret
        return get_secret(key, default) or default
    except Exception:
        return os.environ.get(key, default)


# ══════════════════════════════════════════════════════════════════════════════
# ENUMS
# ══════════════════════════════════════════════════════════════════════════════

class BusinessPhase(Enum):
    IDEATION        = "ideation"
    VALIDATION      = "validation"
    MODEL_COMPLETE  = "model_complete"
    EXECUTION_PLAN  = "execution_plan"
    LAUNCHING       = "launching"
    SCALING         = "scaling"
    PROFITABLE      = "profitable"
    EMPIRE          = "empire"

class RevenueModel(Enum):
    ONE_TIME_SERVICE  = "one_time_service"
    RECURRING_SAAS    = "recurring_saas"
    COMMISSION        = "commission"
    LICENSING         = "licensing"
    FREEMIUM          = "freemium"
    MARKETPLACE       = "marketplace"
    CONSULTING_RETAINER = "consulting_retainer"
    PROJECT_BASED     = "project_based"
    HYBRID            = "hybrid"

class RiskLevel(Enum):
    LOW    = "low"
    MEDIUM = "medium"
    HIGH   = "high"
    CRITICAL = "critical"

class SourceType(Enum):
    PAIN_HUNTER       = "pain_hunter_b2b"
    MEGA_PROJECT      = "mega_project_hunter"
    FORGOTTEN_MARKET  = "forgotten_market_conqueror"
    MANUAL            = "manual"
    NAYA_CORE         = "naya_core"


# ══════════════════════════════════════════════════════════════════════════════
# DATA MODELS
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class FinancialProjection:
    """Projection financière sur 12-36 mois."""
    month: int = 0
    revenue: float = 0.0
    costs: float = 0.0
    profit: float = 0.0
    customers: int = 0
    mrr: float = 0.0              # Monthly Recurring Revenue
    churn_rate: float = 0.05      # 5% par défaut
    cac: float = 0.0              # Customer Acquisition Cost
    ltv: float = 0.0              # Lifetime Value
    burn_rate: float = 0.0
    runway_months: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "month": self.month, "revenue": self.revenue,
            "costs": self.costs, "profit": self.profit,
            "customers": self.customers, "mrr": self.mrr,
            "churn_rate": self.churn_rate, "cac": self.cac,
            "ltv": self.ltv,
        }

@dataclass
class RiskItem:
    """Risque identifié avec mitigation."""
    name: str = ""
    level: RiskLevel = RiskLevel.MEDIUM
    probability: float = 0.0   # 0-1
    impact: float = 0.0        # 0-1
    mitigation: str = ""
    
    @property
    def risk_score(self) -> float:
        return round(self.probability * self.impact * 100, 2)
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name, "level": self.level.value,
            "probability": self.probability, "impact": self.impact,
            "score": self.risk_score, "mitigation": self.mitigation,
        }

@dataclass
class GoToMarketPlan:
    """Plan go-to-market structuré."""
    channels: List[str] = field(default_factory=list)
    primary_channel: str = ""
    acquisition_strategy: str = ""
    content_strategy: str = ""
    partnership_strategy: str = ""
    launch_milestones: List[Dict] = field(default_factory=list)
    kpis: List[str] = field(default_factory=list)
    budget_allocation: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "channels": self.channels,
            "primary_channel": self.primary_channel,
            "acquisition_strategy": self.acquisition_strategy,
            "content_strategy": self.content_strategy,
            "partnerships": self.partnership_strategy,
            "milestones": self.launch_milestones,
            "kpis": self.kpis,
            "budget": self.budget_allocation,
        }

@dataclass
class BusinessBlueprint:
    """Business model complet — le produit final du Strategic Creator."""
    id: str = field(default_factory=lambda: f"BIZ_{uuid.uuid4().hex[:8].upper()}")
    
    # Meta
    name: str = ""
    tagline: str = ""
    description: str = ""
    phase: BusinessPhase = BusinessPhase.IDEATION
    source_type: SourceType = SourceType.MANUAL
    source_id: str = ""          # ID de la douleur/projet/marché source
    created_at: float = field(default_factory=time.time)
    
    # Business Model Canvas
    value_proposition: str = ""
    customer_segments: List[str] = field(default_factory=list)
    channels: List[str] = field(default_factory=list)
    revenue_streams: List[str] = field(default_factory=list)
    revenue_model: RevenueModel = RevenueModel.HYBRID
    key_resources: List[str] = field(default_factory=list)
    key_activities: List[str] = field(default_factory=list)
    key_partners: List[str] = field(default_factory=list)
    cost_structure: Dict = field(default_factory=dict)
    
    # Financials
    initial_investment: float = 0.0
    monthly_burn: float = 0.0
    break_even_month: int = 0
    year1_revenue: float = 0.0
    year2_revenue: float = 0.0
    year3_revenue: float = 0.0
    target_margin: float = 0.0
    projections: List[FinancialProjection] = field(default_factory=list)
    
    # Pricing
    pricing_strategy: str = ""
    price_points: List[Dict] = field(default_factory=list)
    
    # GTM
    gtm_plan: Optional[GoToMarketPlan] = None
    
    # Risks
    risks: List[RiskItem] = field(default_factory=list)
    
    # Execution
    execution_roadmap: List[Dict] = field(default_factory=list)
    team_needed: List[Dict] = field(default_factory=list)
    tech_requirements: List[str] = field(default_factory=list)
    
    # Scoring
    viability_score: float = 0.0      # 0-100
    scalability_score: float = 0.0    # 0-100
    profitability_score: float = 0.0  # 0-100
    execution_score: float = 0.0      # 0-100
    overall_score: float = 0.0
    
    def compute_scores(self) -> float:
        # Viabilité
        self.viability_score = min(100, (
            (min(self.year1_revenue / 500000, 1.0)) * 30 +
            (self.target_margin) * 30 +
            (min(len(self.customer_segments) / 3, 1.0)) * 20 +
            (1 - min(max(r.risk_score for r in self.risks) / 100, 1.0) if self.risks else 0.5) * 20
        ))
        
        # Scalabilité
        revenue_growth = self.year3_revenue / max(self.year1_revenue, 1)
        self.scalability_score = min(100, (
            min(revenue_growth / 10, 1.0) * 40 +
            (1 if self.revenue_model in (RevenueModel.RECURRING_SAAS, RevenueModel.MARKETPLACE) else 0.5) * 30 +
            (min(len(self.key_partners) / 3, 1.0)) * 30
        ))
        
        # Profitabilité
        if self.initial_investment > 0:
            roi_3y = (self.year1_revenue + self.year2_revenue + self.year3_revenue) * self.target_margin / self.initial_investment
        else:
            roi_3y = 5
        self.profitability_score = min(100, roi_3y * 20)
        
        # Exécution
        self.execution_score = min(100, (
            (1 - min(self.initial_investment / 500000, 1.0)) * 30 +
            (1 - min(self.break_even_month / 18, 1.0)) * 30 +
            min(len(self.execution_roadmap) / 6, 1.0) * 20 +
            (1 if self.gtm_plan else 0) * 20
        ))
        
        self.overall_score = round(
            self.viability_score * 0.30 +
            self.scalability_score * 0.25 +
            self.profitability_score * 0.25 +
            self.execution_score * 0.20,
            2
        )
        return self.overall_score
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id, "name": self.name, "tagline": self.tagline,
            "description": self.description, "phase": self.phase.value,
            "source": {"type": self.source_type.value, "id": self.source_id},
            "canvas": {
                "value_proposition": self.value_proposition,
                "customer_segments": self.customer_segments,
                "channels": self.channels,
                "revenue_streams": self.revenue_streams,
                "revenue_model": self.revenue_model.value,
                "key_resources": self.key_resources,
                "key_activities": self.key_activities,
                "key_partners": self.key_partners,
                "cost_structure": self.cost_structure,
            },
            "financials": {
                "initial_investment": self.initial_investment,
                "monthly_burn": self.monthly_burn,
                "break_even_month": self.break_even_month,
                "year1_revenue": self.year1_revenue,
                "year2_revenue": self.year2_revenue,
                "year3_revenue": self.year3_revenue,
                "target_margin": self.target_margin,
                "projections_count": len(self.projections),
            },
            "pricing": {
                "strategy": self.pricing_strategy,
                "price_points": self.price_points,
            },
            "gtm": self.gtm_plan.to_dict() if self.gtm_plan else None,
            "risks": [r.to_dict() for r in self.risks],
            "execution": {
                "roadmap_steps": len(self.execution_roadmap),
                "team_size": len(self.team_needed),
                "tech_requirements": self.tech_requirements,
            },
            "scoring": {
                "viability": self.viability_score,
                "scalability": self.scalability_score,
                "profitability": self.profitability_score,
                "execution": self.execution_score,
                "overall": self.overall_score,
            },
        }


# ══════════════════════════════════════════════════════════════════════════════
# BLUEPRINT BUILDER — Transforme les opportunités en business complets
# ══════════════════════════════════════════════════════════════════════════════

class BlueprintBuilder:
    """Construit des BusinessBlueprints complets à partir des données des autres agents."""
    
    def from_pain(self, pain_data: Dict) -> BusinessBlueprint:
        """Construit un business depuis une douleur détectée."""
        pain = pain_data.get("pain", {})
        offer = pain_data.get("offer", {})
        target = pain_data.get("target", {})
        classification = pain_data.get("classification", {})
        
        category = classification.get("category", "cash_rapide")
        deal_value = classification.get("deal_value", 50000)
        
        bp = BusinessBlueprint(
            name=f"Service: {pain.get('category', 'B2B')}",
            tagline=offer.get("title", "Service premium B2B"),
            description=pain.get("description", ""),
            source_type=SourceType.PAIN_HUNTER,
            source_id=pain_data.get("id", ""),
            value_proposition=f"Résolution de {pain.get('category', 'problème')} — "
                             f"ROI {offer.get('roi_ratio', 2)}x garanti",
            customer_segments=[target.get("sector", "B2B"), target.get("type", "PME")],
            revenue_model=self._select_revenue_model(category),
            initial_investment=deal_value * 0.1,
            target_margin=0.65,
        )
        
        # Financials basés sur la catégorie
        if category == "cash_rapide":
            bp.year1_revenue = deal_value * 12
            bp.year2_revenue = deal_value * 24
            bp.year3_revenue = deal_value * 36
            bp.break_even_month = 1
            bp.monthly_burn = deal_value * 0.15
        elif category == "moyen_terme":
            bp.year1_revenue = deal_value * 6
            bp.year2_revenue = deal_value * 12
            bp.year3_revenue = deal_value * 24
            bp.break_even_month = 3
            bp.monthly_burn = deal_value * 0.2
        else:
            bp.year1_revenue = deal_value * 4
            bp.year2_revenue = deal_value * 8
            bp.year3_revenue = deal_value * 16
            bp.break_even_month = 6
            bp.monthly_burn = deal_value * 0.25
        
        bp.projections = self._generate_projections(bp, 24)
        bp.risks = self._standard_risks("service")
        bp.gtm_plan = self._build_gtm(bp, ["LinkedIn", "cold email", "réseau"])
        bp.execution_roadmap = self._build_roadmap_service(classification.get("delivery_days", 7))
        bp.pricing_strategy = "Value-based: prix = 30% de l'impact financier du problème"
        bp.price_points = [{"tier": "Standard", "price": deal_value, "description": "Livraison complète"}]
        
        bp.phase = BusinessPhase.MODEL_COMPLETE
        bp.compute_scores()
        return bp
    
    def from_mega_project(self, project_data: Dict) -> BusinessBlueprint:
        """Construit un business depuis un mega project."""
        value = project_data.get("value", {})
        build = project_data.get("build", {})
        acquirers = project_data.get("acquirers", {})
        
        bp = BusinessBlueprint(
            name=project_data.get("name", "InnoProject"),
            tagline=f"Tech innovation — {project_data.get('domain', 'AI')}",
            description=project_data.get("description", ""),
            source_type=SourceType.MEGA_PROJECT,
            source_id=project_data.get("id", ""),
            value_proposition=f"Solution innovante dans {project_data.get('domain', 'tech')} "
                             f"ciblant un marché de {value.get('tam', 0)/1e9:.0f}Mds€",
            customer_segments=[acquirers.get("type", "GAFAM")],
            revenue_model=RevenueModel.LICENSING,
            initial_investment=build.get("cost", 500000),
            target_margin=0.80,
        )
        
        sale_min = value.get("min", 15_000_000)
        bp.year1_revenue = sale_min * 0.1   # Premiers contrats
        bp.year2_revenue = sale_min * 0.3
        bp.year3_revenue = sale_min          # Vente/acquisition
        bp.break_even_month = build.get("months", 12)
        bp.monthly_burn = build.get("cost", 500000) / max(build.get("months", 12), 1)
        
        bp.projections = self._generate_projections(bp, 36)
        bp.risks = self._standard_risks("tech_startup")
        bp.gtm_plan = self._build_gtm(bp, ["Corp Dev direct", "conferences", "VC intros"])
        bp.execution_roadmap = self._build_roadmap_tech(build.get("months", 12))
        bp.pricing_strategy = "Acquisition-based: valeur = multiple de revenue/tech asset"
        bp.price_points = [
            {"tier": "License", "price": sale_min * 0.05, "description": "Annual license"},
            {"tier": "Acquisition", "price": sale_min, "description": "Full acquisition"},
        ]
        
        bp.phase = BusinessPhase.VALIDATION
        bp.compute_scores()
        return bp
    
    def from_forgotten_market(self, market_data: Dict) -> BusinessBlueprint:
        """Construit un business depuis un marché oublié."""
        size = market_data.get("market_size", {})
        strategy = market_data.get("strategy", {})
        offer = market_data.get("offer", {})
        
        bp = BusinessBlueprint(
            name=market_data.get("name", "Nouveau Marché"),
            tagline=f"Conquête: {market_data.get('name', 'marché')}",
            description=market_data.get("description", ""),
            source_type=SourceType.FORGOTTEN_MARKET,
            source_id=market_data.get("id", ""),
            value_proposition=f"Premier service dédié pour un marché de "
                             f"{size.get('population', 0):,} clients potentiels",
            customer_segments=[market_data.get("geography", "France")],
            channels=offer.get("channels", []),
            revenue_model=self._model_from_frequency(size.get("frequency", "monthly")),
            initial_investment=strategy.get("launch_cost", 30000),
            target_margin=strategy.get("margin", 0.65),
        )
        
        monthly_rev = strategy.get("monthly_revenue", 50000)
        bp.year1_revenue = monthly_rev * 12
        bp.year2_revenue = monthly_rev * 24
        bp.year3_revenue = monthly_rev * 36
        bp.break_even_month = max(1, int(bp.initial_investment / max(monthly_rev * bp.target_margin, 1)))
        bp.monthly_burn = monthly_rev * 0.2
        
        bp.projections = self._generate_projections(bp, 24)
        bp.risks = self._standard_risks("market_entry")
        bp.gtm_plan = self._build_gtm(bp, offer.get("channels", []))
        bp.execution_roadmap = self._build_roadmap_market(strategy.get("launch_days", 30))
        bp.pricing_strategy = f"Market-based: {size.get('avg_ticket', 0)}€ moyen/client"
        bp.price_points = [{"tier": "Standard", "price": size.get("avg_ticket", 100)}]
        
        bp.phase = BusinessPhase.MODEL_COMPLETE
        bp.compute_scores()
        return bp
    
    # ── Helpers ──────────────────────────────────────────────────────────────
    
    def _select_revenue_model(self, category: str) -> RevenueModel:
        if category == "cash_rapide": return RevenueModel.ONE_TIME_SERVICE
        elif category == "moyen_terme": return RevenueModel.PROJECT_BASED
        return RevenueModel.CONSULTING_RETAINER
    
    def _model_from_frequency(self, freq: str) -> RevenueModel:
        if freq == "monthly": return RevenueModel.RECURRING_SAAS
        elif freq == "annual": return RevenueModel.RECURRING_SAAS
        return RevenueModel.ONE_TIME_SERVICE
    
    def _generate_projections(self, bp: BusinessBlueprint, months: int) -> List[FinancialProjection]:
        projs = []
        for m in range(1, months + 1):
            growth = 1 + (0.15 * min(m / 6, 1))  # 15% growth cap at month 6
            rev = (bp.year1_revenue / 12) * growth ** (m / 12)
            cost = bp.monthly_burn * (1 + 0.05 * (m / 12))
            projs.append(FinancialProjection(
                month=m, revenue=round(rev, 2), costs=round(cost, 2),
                profit=round(rev - cost, 2),
                customers=int(rev / max(bp.price_points[0]["price"] if bp.price_points else 100, 1)),
                mrr=round(rev, 2) if bp.revenue_model in (RevenueModel.RECURRING_SAAS,) else 0,
            ))
        return projs
    
    def _standard_risks(self, business_type: str) -> List[RiskItem]:
        base_risks = [
            RiskItem("Concurrence inattendue", RiskLevel.MEDIUM, 0.3, 0.5,
                     "Moat via exécution rapide + relation client"),
            RiskItem("Acquisition clients plus lente que prévu", RiskLevel.HIGH, 0.4, 0.6,
                     "Diversifier canaux + réduire CAC"),
            RiskItem("Réglementation", RiskLevel.LOW, 0.15, 0.7,
                     "Veille juridique + conformité proactive"),
        ]
        if business_type == "tech_startup":
            base_risks.append(RiskItem("Retard technique", RiskLevel.HIGH, 0.5, 0.5,
                                       "MVP first + itérations rapides"))
        elif business_type == "market_entry":
            base_risks.append(RiskItem("Adoption lente du marché", RiskLevel.MEDIUM, 0.35, 0.5,
                                       "Education market + early adopters"))
        return base_risks
    
    def _build_gtm(self, bp: BusinessBlueprint, channels: List[str]) -> GoToMarketPlan:
        return GoToMarketPlan(
            channels=channels,
            primary_channel=channels[0] if channels else "direct",
            acquisition_strategy="Outbound ciblé + inbound content",
            content_strategy="Thought leadership + case studies + ROI calculators",
            partnership_strategy="Fédérations sectorielles + intégrateurs",
            launch_milestones=[
                {"week": 1, "action": "Setup canaux + premiers contenus"},
                {"week": 2, "action": "Premiers contacts + cold outreach"},
                {"week": 4, "action": "Premier client signé (objectif)"},
                {"week": 8, "action": "Process stabilisé + premiers témoignages"},
                {"week": 12, "action": "Scaling acquisition"},
            ],
            kpis=["CAC", "LTV", "Conversion rate", "MRR", "Churn", "NPS"],
            budget_allocation={
                "content": 0.20, "ads": 0.30, "sales": 0.35,
                "partnerships": 0.10, "tools": 0.05,
            },
        )
    
    def _build_roadmap_service(self, delivery_days: int) -> List[Dict]:
        return [
            {"phase": "Setup", "duration": "1-3j", "actions": ["Qualification prospect", "Scoping", "Contrat"]},
            {"phase": "Delivery", "duration": f"{delivery_days}j", "actions": ["Exécution service", "Livrables"]},
            {"phase": "Follow-up", "duration": "7j", "actions": ["Satisfaction", "Upsell", "Témoignage"]},
            {"phase": "Scale", "duration": "30j", "actions": ["Process documenté", "Recruter si besoin", "Automatiser"]},
        ]
    
    def _build_roadmap_tech(self, build_months: int) -> List[Dict]:
        return [
            {"phase": "Research", "duration": f"{build_months//4}m", "actions": ["Market validation", "Tech feasibility"]},
            {"phase": "MVP", "duration": f"{build_months//3}m", "actions": ["Core product", "Alpha users"]},
            {"phase": "Beta", "duration": f"{build_months//3}m", "actions": ["Beta launch", "Iterate", "Metrics"]},
            {"phase": "Launch", "duration": f"{build_months//4}m", "actions": ["GA launch", "First revenues"]},
            {"phase": "Scale", "duration": "6m", "actions": ["Growth", "Fundraise/Sell"]},
        ]
    
    def _build_roadmap_market(self, launch_days: int) -> List[Dict]:
        return [
            {"phase": "Prep", "duration": f"{launch_days//3}j", "actions": ["Offre finalisée", "Canaux prêts"]},
            {"phase": "Launch", "duration": f"{launch_days//3}j", "actions": ["Premiers clients", "Feedback loop"]},
            {"phase": "Optimize", "duration": f"{launch_days//3}j", "actions": ["Ajuster offre/prix", "Automatiser"]},
            {"phase": "Dominate", "duration": "90j", "actions": ["Prendre position #1", "Barrières à l'entrée"]},
        ]


# ══════════════════════════════════════════════════════════════════════════════
# MAIN ENGINE
# ══════════════════════════════════════════════════════════════════════════════

class StrategicBusinessCreator:
    """Agent stratégique — transforme opportunités en business exécutables."""
    VERSION = "1.0.0"
    
    def __init__(self):
        self._builder = BlueprintBuilder()
        self._blueprints: List[BusinessBlueprint] = []
        self._cycle_count = 0
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()
        
        # Agents sources
        self._pain_hunter = None
        self._mega_hunter = None
        self._market_conqueror = None
        
        # NAYA integrations
        self._db = None
        self._discretion = None
        self._event_stream = None
        self._pricing_engine = None
        
        log.info("[StrategicBusinessCreator] Initialisé — V%s", self.VERSION)
    
    def set_pain_hunter(self, hunter): self._pain_hunter = hunter
    def set_mega_hunter(self, hunter): self._mega_hunter = hunter
    def set_market_conqueror(self, conqueror): self._market_conqueror = conqueror
    def set_database(self, db): self._db = db
    def set_discretion(self, protocol): self._discretion = protocol
    def set_event_stream(self, stream): self._event_stream = stream
    def set_pricing_engine(self, engine): self._pricing_engine = engine
    
    def strategic_cycle(self) -> Dict:
        """
        Cycle stratégique complet:
        1. Collecte les top opportunités de chaque agent
        2. Construit des business models pour chacune
        3. Score, classe et persiste
        """
        cycle_id = f"STRAT_{uuid.uuid4().hex[:6].upper()}"
        self._cycle_count += 1
        
        log.info(f"[{cycle_id}] Cycle stratégique #{self._cycle_count}")
        
        result = {
            "cycle_id": cycle_id,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "blueprints_created": 0,
            "from_pains": 0,
            "from_mega_projects": 0,
            "from_forgotten_markets": 0,
            "total_year1_revenue": 0.0,
            "top_blueprints": [],
        }
        
        new_blueprints = []
        
        # ── Depuis PainHunterB2B ────────────────────────────────────────
        if self._pain_hunter:
            try:
                top_pains = self._pain_hunter.get_top_opportunities(5)
                for pain_data in top_pains:
                    bp = self._builder.from_pain(pain_data)
                    new_blueprints.append(bp)
                    result["from_pains"] += 1
            except Exception as e:
                log.debug(f"[Strategy] Pain source error: {e}")
        
        # ── Depuis MegaProjectHunter ────────────────────────────────────
        if self._mega_hunter:
            try:
                top_projects = self._mega_hunter.get_top_projects(3)
                for proj_data in top_projects:
                    bp = self._builder.from_mega_project(proj_data)
                    new_blueprints.append(bp)
                    result["from_mega_projects"] += 1
            except Exception as e:
                log.debug(f"[Strategy] Mega source error: {e}")
        
        # ── Depuis ForgottenMarketConqueror ──────────────────────────────
        if self._market_conqueror:
            try:
                top_markets = self._market_conqueror.get_top_markets(5)
                for mkt_data in top_markets:
                    bp = self._builder.from_forgotten_market(mkt_data)
                    new_blueprints.append(bp)
                    result["from_forgotten_markets"] += 1
            except Exception as e:
                log.debug(f"[Strategy] Market source error: {e}")
        
        # ── Enrichir avec pricing engine si disponible ──────────────────
        if self._pricing_engine:
            for bp in new_blueprints:
                try:
                    if hasattr(self._pricing_engine, "optimize_price"):
                        optimized = self._pricing_engine.optimize_price({
                            "value": bp.year1_revenue / 12,
                            "cost": bp.monthly_burn,
                            "market": bp.customer_segments,
                        })
                        if optimized:
                            bp.pricing_strategy += f" | Optimisé: {optimized}"
                except Exception:
                    pass
        
        # ── Score final et persist ──────────────────────────────────────
        for bp in new_blueprints:
            bp.compute_scores()
            result["total_year1_revenue"] += bp.year1_revenue
            
            with self._lock:
                self._blueprints.append(bp)
            
            self._persist_blueprint(bp)
            self._stream_event("BUSINESS_BLUEPRINT_CREATED", {
                "id": bp.id, "name": bp.name,
                "source": bp.source_type.value,
                "year1_revenue": bp.year1_revenue,
                "overall_score": bp.overall_score,
            })
        
        # Garder les 200 derniers
        with self._lock:
            if len(self._blueprints) > 200:
                self._blueprints = sorted(
                    self._blueprints, key=lambda b: b.overall_score, reverse=True
                )[:200]
        
        result["blueprints_created"] = len(new_blueprints)
        
        # Top 5
        sorted_bps = sorted(new_blueprints, key=lambda b: b.overall_score, reverse=True)
        result["top_blueprints"] = [b.to_dict() for b in sorted_bps[:5]]
        result["completed_at"] = datetime.now(timezone.utc).isoformat()
        
        log.info(
            f"[{cycle_id}] Terminé — {result['blueprints_created']} blueprints, "
            f"Y1 Revenue: {result['total_year1_revenue']:,.0f}€"
        )
        return result
    
    def _persist_blueprint(self, bp: BusinessBlueprint):
        if not self._db: return
        try:
            data = bp.to_dict()
            if self._discretion: data = self._discretion.mask(data)
            self._db.log_event("BUSINESS_BLUEPRINT", data, "HUNTING_AGENTS.strategic_creator", "HIGH")
        except Exception as e:
            log.debug(f"[Persist] {e}")
    
    def _stream_event(self, event_type: str, data: Dict):
        if self._event_stream and hasattr(self._event_stream, "broadcast"):
            try:
                self._event_stream.broadcast({
                    "type": event_type, "source": "STRATEGIC_CREATOR", "data": data,
                })
            except Exception: pass
    
    # ── Autonomous ───────────────────────────────────────────────────────────
    
    def start_autonomous(self, interval_seconds: int = 7200):
        """Toutes les 2h par défaut."""
        if self._running: return
        self._running = True
        self._thread = threading.Thread(
            target=self._auto_loop, args=(interval_seconds,),
            daemon=True, name="StrategicCreator-Auto",
        )
        self._thread.start()
    
    def stop_autonomous(self):
        self._running = False
        if self._thread: self._thread.join(timeout=5)
    
    def _auto_loop(self, interval: int):
        while self._running:
            try: self.strategic_cycle()
            except Exception as e: log.error(f"[StrategicCreator] {e}")
            time.sleep(interval)
    
    # ── Query Methods ────────────────────────────────────────────────────────
    
    def get_top_blueprints(self, n: int = 10) -> List[Dict]:
        with self._lock:
            s = sorted(self._blueprints, key=lambda b: b.overall_score, reverse=True)
            return [b.to_dict() for b in s[:n]]
    
    def get_cash_businesses(self) -> List[Dict]:
        """Business à lancer MAINTENANT (break-even < 3 mois)."""
        with self._lock:
            cash = [b for b in self._blueprints if b.break_even_month <= 3]
            cash.sort(key=lambda b: b.profitability_score, reverse=True)
            return [b.to_dict() for b in cash]
    
    def get_empire_candidates(self) -> List[Dict]:
        """Business à potentiel d'empire (scalability > 70)."""
        with self._lock:
            emp = [b for b in self._blueprints if b.scalability_score > 70]
            emp.sort(key=lambda b: b.scalability_score, reverse=True)
            return [b.to_dict() for b in emp]
    
    def get_stats(self) -> Dict:
        with self._lock:
            total_y1 = sum(b.year1_revenue for b in self._blueprints)
            by_source = {}
            for b in self._blueprints:
                src = b.source_type.value
                by_source[src] = by_source.get(src, 0) + 1
            return {
                "version": self.VERSION,
                "total_cycles": self._cycle_count,
                "total_blueprints": len(self._blueprints),
                "total_year1_revenue_potential": total_y1,
                "by_source": by_source,
                "autonomous_running": self._running,
            }
    
    def to_dict(self) -> Dict:
        return self.get_stats()
