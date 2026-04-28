"""
NAYA V19 — Revenue Engine
Le moteur qui transforme les opportunites en argent reel.
"""
# Import safe - ne pas crasher si un sous-module manque
def _safe(fn):
    try:
        return fn()
    except Exception:
        return None

# Exports principaux
try:
    from .unified_revenue_engine import UnifiedRevenueEngine
except Exception:
    UnifiedRevenueEngine = None

try:
    from .outreach_engine import OutreachEngine
except Exception:
    OutreachEngine = None

try:
    from .payment_engine import PaymentEngine
except Exception:
    PaymentEngine = None

try:
    from .pipeline_tracker import PipelineTracker
except Exception:
    PipelineTracker = None

try:
    from .offer_generator import OfferGenerator
except Exception:
    OfferGenerator = None

try:
    from .payment_tracker import PaymentTracker
except Exception:
    PaymentTracker = None

__all__ = ["UnifiedRevenueEngine", "OutreachEngine", "PaymentEngine",
           "PipelineTracker", "OfferGenerator", "PaymentTracker"]

try:
    from .deblock_engine import DeblockEngine, get_deblock
except Exception:
    DeblockEngine = None; get_deblock = None

try:
    from .revenue_tracker import RevenueTracker, get_tracker
except Exception:
    RevenueTracker = None; get_tracker = None
