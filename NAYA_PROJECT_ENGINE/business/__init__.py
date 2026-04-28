"""Business package exports."""

from .adaptive_business_hunt_engine import (
    AdaptiveBusinessHuntEngine,
    adaptive_business_hunt_engine,
)
from .universal_pain_engine import UniversalPainEngine, universal_pain_engine
from .zero_waste_recycler import ZeroWasteAssetRecycler, zero_waste_recycler

__all__ = [
    "AdaptiveBusinessHuntEngine",
    "adaptive_business_hunt_engine",
    "UniversalPainEngine",
    "universal_pain_engine",
    "ZeroWasteAssetRecycler",
    "zero_waste_recycler",
]

"""NAYA — Business Projects Registry v5.1 (ENHANCED)
Manages ALL 9 projects: 6 business projects + 3 services (Alibaba, Samsung, SAP Ariba)
"""
from typing import Dict, Any, List
import logging

log = logging.getLogger("NAYA.BUSINESS")

try:
    # ══════════════════════════════════════════════════════════════
    # 6 BUSINESS PROJECTS (Fixed: Now includes PROJECT_02!)
    # ══════════════════════════════════════════════════════════════
    from NAYA_PROJECT_ENGINE.business.projects.PROJECT_01_CASH_RAPIDE import CashRapideProject, PROJECT_STATE as P1
    from NAYA_PROJECT_ENGINE.business.projects.PROJECT_02_GOOGLE_XR import GoogleXRProject, PROJECT_STATE as P2  # FIXED: Added P2!
    from NAYA_PROJECT_ENGINE.business.projects.PROJECT_03_NAYA_BOTANICA import NayaBotanicaProject, PROJECT_STATE as P3
    from NAYA_PROJECT_ENGINE.business.projects.PROJECT_04_TINY_HOUSE import TinyHouseProject, PROJECT_STATE as P4
    from NAYA_PROJECT_ENGINE.business.projects.PROJECT_05_MARCHES_OUBLIES import MarchesOubliesProject, PROJECT_STATE as P5
    from NAYA_PROJECT_ENGINE.business.projects.PROJECT_06_ACQUISITION_IMMOBILIERE import AcquisitionImmobiliereProject, PROJECT_STATE as P6

    ALL_PROJECTS = [P1, P2, P3, P4, P5, P6]  # FIXED: Now includes P2!
    log.info("✅ Loaded 6 business projects (PROJECT_01 through PROJECT_06)")

    # ══════════════════════════════════════════════════════════════
    # 3 SERVICES/PROJECTS (PROJECT_07, 08, 09 - NEWLY INTEGRATED!)
    # ══════════════════════════════════════════════════════════════
    try:
        from NAYA_PROJECT_ENGINE.business.first_project_queu import (
            run_alibaba, run_samsung, run_sap_ariba, SERVICE_QUEUE
        )
        
        # Create service references (these are PROJECT_07, 08, 09)
        SERVICES = {
            "SERVICE_1_ALIBABA": run_alibaba,      # PROJECT_07
            "SERVICE_2_SAMSUNG": run_samsung,      # PROJECT_08
            "SERVICE_3_SAP_ARIBA": run_sap_ariba,  # PROJECT_09
        }
        
        log.info("✅ Loaded 3 services (SERVICE_1_ALIBABA, SERVICE_2_SAMSUNG, SERVICE_3_SAP_ARIBA)")
        
    except ImportError as e:
        log.warning(f"⚠️  Services not available: {e}")
        SERVICES = {}
        SERVICE_QUEUE = []

    # ══════════════════════════════════════════════════════════════
    # UTILITY FUNCTIONS
    # ══════════════════════════════════════════════════════════════

    def get_active_projects() -> List[Any]:
        """Get all active projects (both business + services)."""
        return [p for p in ALL_PROJECTS if getattr(p, 'active', False)]

    def get_project_by_id(project_id: str) -> Any:
        """Get project by ID."""
        return next((p for p in ALL_PROJECTS if getattr(p, 'id', '') == project_id), None)

    def get_all_projects_including_services() -> Dict[str, Any]:
        """Get ALL 9 projects: business projects + services."""
        return {
            "business_projects": ALL_PROJECTS,
            "services": SERVICES,
            "service_queue": SERVICE_QUEUE,
            "total_count": len(ALL_PROJECTS) + len(SERVICES),
        }

    def get_service(service_name: str) -> Any:
        """Get a specific service by name."""
        return SERVICES.get(service_name, None)

    __all__ = [
        "ALL_PROJECTS", 
        "SERVICES", 
        "SERVICE_QUEUE",
        "get_active_projects", 
        "get_project_by_id",
        "get_all_projects_including_services",
        "get_service",
    ]

    log.info(f"🎯 Business Module Ready: {len(ALL_PROJECTS)} projects + {len(SERVICES)} services = 9 total")

except ImportError as e:
    log.error(f"❌ Failed to load business projects: {e}")
    ALL_PROJECTS = []
    SERVICES = {}
    SERVICE_QUEUE = []
    __all__ = ["ALL_PROJECTS", "SERVICES"]
