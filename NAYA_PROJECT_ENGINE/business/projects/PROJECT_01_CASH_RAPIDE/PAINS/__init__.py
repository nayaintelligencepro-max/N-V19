"""PROJECT_01 — Cash Rapide PAINs Registry."""
try:
    from NAYA_PROJECT_ENGINE.business.projects.PROJECT_01_CASH_RAPIDE.PAINS.P1_PREMIUM import P1_SERVICES, get_p1_offer
    from NAYA_PROJECT_ENGINE.business.projects.PROJECT_01_CASH_RAPIDE.PAINS.P2_PREMIUM_PLUS import P2_SERVICES, get_p2_offer
    from NAYA_PROJECT_ENGINE.business.projects.PROJECT_01_CASH_RAPIDE.PAINS.P3_EXECUTIVE import P3_SERVICES, get_p3_offer
    PALIER_SERVICES = {"P1": P1_SERVICES, "P2": P2_SERVICES, "P3": P3_SERVICES}
    __all__ = ["PALIER_SERVICES", "get_p1_offer", "get_p2_offer", "get_p3_offer"]
except ImportError:
    __all__ = []
