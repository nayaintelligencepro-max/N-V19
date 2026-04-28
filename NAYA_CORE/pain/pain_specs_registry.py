"""
NAYA V19.3 — PAIN SPECS REGISTRY
Enregistre les 32 specs qui remplacent les 39 anciens pain_engine.py / pain_hunt_engine.py.
"""
from pathlib import Path
from typing import Dict, List
from .generic_pain_engine import PainSpec, PainMode, pain_registry, PainEngineRegistry

# ═══════════════════════════════════════════════════════════════════
# SPECS — Remplace tous les anciens fichiers dupliqués
# ═══════════════════════════════════════════════════════════════════

SPECS: List[PainSpec] = [
    # TIER-based (PROJECT_01_CASH_RAPIDE) — remplace 6 pain_engine.py
    PainSpec(pain_id="P1_PREMIUM", name="PREMIUM", project="PROJECT_01_CASH_RAPIDE",
             mode=PainMode.TIER, floor_price=1000, target_price=5000,
             description="Services premium 1000-5000 EUR",
             offer_types=["audit", "diagnostic", "chatbot_ia", "saas", "conseil_strategique"]),
    PainSpec(pain_id="P2_PREMIUM_PLUS", name="PREMIUM_PLUS", project="PROJECT_01_CASH_RAPIDE",
             mode=PainMode.TIER, floor_price=5000, target_price=15000,
             description="Services premium plus 5-15k EUR"),
    PainSpec(pain_id="P3_EXECUTIVE", name="EXECUTIVE", project="PROJECT_01_CASH_RAPIDE",
             mode=PainMode.TIER, floor_price=15000, target_price=40000,
             description="Executive services 15-40k EUR"),
    PainSpec(pain_id="P4_ENTERPRISE", name="ENTERPRISE", project="PROJECT_01_CASH_RAPIDE",
             mode=PainMode.TIER, floor_price=40000, target_price=100000,
             description="Enterprise solutions 40-100k EUR"),
    PainSpec(pain_id="P5_STRATEGIC", name="STRATEGIC", project="PROJECT_01_CASH_RAPIDE",
             mode=PainMode.TIER, floor_price=100000, target_price=250000,
             description="Strategic deals 100-250k EUR"),
    PainSpec(pain_id="P6_HIGH_STAKES", name="HIGH_STAKES", project="PROJECT_01_CASH_RAPIDE",
             mode=PainMode.TIER, floor_price=250000, target_price=1000000,
             description="High stakes deals 250k-1M EUR"),

    # THEMATIC — Google XR
    PainSpec(pain_id="PAIN_03_INDUSTRIAL_SIMULATION", name="IndustrialSimulation",
             project="PROJECT_02_GOOGLE_XR", mode=PainMode.THEMATIC, sector="xr_industrial",
             description="Industrial XR simulation gap"),
    PainSpec(pain_id="PAIN_04_DATA_VISUALIZATION", name="DataVisualizationXR",
             project="PROJECT_02_GOOGLE_XR", mode=PainMode.THEMATIC, sector="xr_data",
             description="XR data visualization needs"),
    PainSpec(pain_id="PAIN_05_CUSTOM_XR_PLATFORM", name="CustomXRPlatform",
             project="PROJECT_02_GOOGLE_XR", mode=PainMode.THEMATIC, sector="xr_custom",
             description="Custom XR platform demand"),
    PainSpec(pain_id="PAIN_URGENT_01_ENTERPRISE_XR", name="EnterpriseXRUrgent",
             project="PROJECT_02_GOOGLE_XR", mode=PainMode.THEMATIC, sector="xr_enterprise",
             description="Urgent enterprise XR deployment"),
    PainSpec(pain_id="PAIN_URGENT_02_TRAINING_XR", name="TrainingXRUrgent",
             project="PROJECT_02_GOOGLE_XR", mode=PainMode.THEMATIC, sector="xr_training",
             description="Urgent XR training infrastructure"),

    # THEMATIC — Naya Botanica
    PainSpec(pain_id="PAIN_01_SKIN_REPAIR", name="SkinRepair",
             project="PROJECT_03_NAYA_BOTANICA", mode=PainMode.THEMATIC, sector="cosmetics",
             description="Advanced skin repair demand"),
    PainSpec(pain_id="PAIN_02_HYPERPIGMENTATION", name="Hyperpigmentation",
             project="PROJECT_03_NAYA_BOTANICA", mode=PainMode.THEMATIC, sector="cosmetics",
             description="Hyperpigmentation solutions gap"),
    PainSpec(pain_id="PAIN_03_FIRMING_BODY", name="BodyFirming",
             project="PROJECT_03_NAYA_BOTANICA", mode=PainMode.THEMATIC, sector="cosmetics",
             description="Body firming market gap"),

    # THEMATIC — Tiny House
    PainSpec(pain_id="PAIN_01_OFF_GRID_LIVING", name="OffGridLiving",
             project="PROJECT_04_TINY_HOUSE", mode=PainMode.THEMATIC, sector="housing",
             description="Off-grid living solutions"),
    PainSpec(pain_id="PAIN_02_MOBILE_WORKFORCE", name="MobileWorkforce",
             project="PROJECT_04_TINY_HOUSE", mode=PainMode.THEMATIC, sector="housing",
             description="Mobile workforce housing"),
    PainSpec(pain_id="PAIN_03_DISASTER_HOUSING", name="DisasterHousing",
             project="PROJECT_04_TINY_HOUSE", mode=PainMode.THEMATIC, sector="housing",
             description="Disaster emergency housing"),

    # THEMATIC — Marchés Oubliés
    PainSpec(pain_id="PAIN_01_ACCESS_TO_SERVICES", name="AccessToServices",
             project="PROJECT_05_MARCHES_OUBLIES", mode=PainMode.THEMATIC, sector="underserved",
             description="Underserved market access"),
    PainSpec(pain_id="PAIN_02_STRUCTURED_OFFER_ABSENCE", name="StructuredOfferAbsence",
             project="PROJECT_05_MARCHES_OUBLIES", mode=PainMode.THEMATIC, sector="underserved",
             description="Absence of structured offers"),
    PainSpec(pain_id="PAIN_03_UNDERVALUED_URBAN_POTENTIAL", name="UndervaluedUrbanPotential",
             project="PROJECT_05_MARCHES_OUBLIES", mode=PainMode.THEMATIC, sector="underserved",
             description="Undervalued urban potential"),

    # THEMATIC — Acquisition Immobilière
    PainSpec(pain_id="PAIN_01_UNDERVALUED_PROPERTY", name="UndervaluedProperty",
             project="PROJECT_06_ACQUISITION_IMMOBILIERE", mode=PainMode.THEMATIC, sector="realestate",
             description="Undervalued property detection"),
    PainSpec(pain_id="PAIN_02_LIQUIDITY_NEED_SELLER", name="LiquidityNeedSeller",
             project="PROJECT_06_ACQUISITION_IMMOBILIERE", mode=PainMode.THEMATIC, sector="realestate",
             description="Seller liquidity pressure"),
    PainSpec(pain_id="PAIN_03_COMPLEX_ESTIMATION", name="ComplexEstimation",
             project="PROJECT_06_ACQUISITION_IMMOBILIERE", mode=PainMode.THEMATIC, sector="realestate",
             description="Complex property estimation"),

    # THEMATIC — Naya Paye (fintech Polynésie)
    PainSpec(pain_id="PAIN_01_NO_MODERN_BANKING", name="NoModernBanking",
             project="PROJECT_07_NAYA_PAYE", mode=PainMode.THEMATIC, sector="fintech",
             description="No modern banking (Revolut-like) in Polynesia",
             regulatory_complexity=0.7,
             default_signal={"population": 280000, "market_size": 50_000_000}),
    PainSpec(pain_id="PAIN_02_BUSINESS_PAYMENT_FRICTION", name="BusinessPaymentFriction",
             project="PROJECT_07_NAYA_PAYE", mode=PainMode.THEMATIC, sector="fintech",
             description="B2B payment friction", regulatory_complexity=0.6),
    PainSpec(pain_id="PAIN_03_CROSS_BORDER_TRANSFERS", name="CrossBorderTransfers",
             project="PROJECT_07_NAYA_PAYE", mode=PainMode.THEMATIC, sector="fintech",
             description="Cross-border transfer complexity", regulatory_complexity=0.8),

    # pain_hunt_engine (projets 004-009)
    PainSpec(pain_id="MAIN_PROJECT_004", name="SupplyChain", project="PROJECT_004_SUPPLY_CHAIN",
             mode=PainMode.THEMATIC, sector="supply_chain",
             description="Supply chain optimization"),
    PainSpec(pain_id="MAIN_PROJECT_005", name="HRScaling", project="PROJECT_005_HR_SCALING",
             mode=PainMode.THEMATIC, sector="hr",
             description="HR scaling challenges"),
    PainSpec(pain_id="MAIN_PROJECT_006", name="MarketExpansion", project="PROJECT_006_MARKET_EXPANSION",
             mode=PainMode.THEMATIC, sector="growth",
             description="Market expansion execution"),
    PainSpec(pain_id="MAIN_PROJECT_007", name="Fintech", project="PROJECT_007_FINTECH_SOLUTIONS",
             mode=PainMode.THEMATIC, sector="fintech",
             description="Fintech solutions gaps"),
    PainSpec(pain_id="MAIN_PROJECT_008", name="DataAnalytics", project="PROJECT_008_DATA_ANALYTICS",
             mode=PainMode.THEMATIC, sector="data",
             description="Data analytics infrastructure"),
    PainSpec(pain_id="MAIN_PROJECT_009", name="Sustainability", project="PROJECT_009_SUSTAINABILITY",
             mode=PainMode.THEMATIC, sector="esg",
             description="Sustainability compliance"),
]


def register_all_specs(persistence_dir: Path = None) -> PainEngineRegistry:
    """
    Enregistre les 32 specs dans le registry global.
    Appelé au boot par NAYA_CORE (voir __init__.py).
    """
    base = persistence_dir or Path("data/pain_state")
    base.mkdir(parents=True, exist_ok=True)
    for spec in SPECS:
        pain_registry.register(spec, persistence_dir=base)
    return pain_registry


def get_by_project(project: str) -> List[PainSpec]:
    return [s for s in SPECS if s.project == project]


def get_by_id(pain_id: str) -> PainSpec:
    for s in SPECS:
        if s.pain_id == pain_id:
            return s
    raise KeyError(f"PainSpec {pain_id} not found")


__all__ = ["SPECS", "register_all_specs", "get_by_project", "get_by_id"]
