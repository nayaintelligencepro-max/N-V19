"""
NAYA SUPREME V14 — Revenue Engine V14 (backward-compat alias)
Fichier manquant corrigé : référencé dans tests, bootstrap, system_connector.
Délègue à unified_revenue_engine.py (le vrai moteur).
"""
import logging
from typing import Optional

log = logging.getLogger("NAYA.REVENUE.V14")

_engine: Optional[object] = None
_lock = __import__('threading').Lock()


def get_revenue_engine_v10():
    """
    Factory singleton — backward-compatible avec tous les imports existants.
    Retourne l'UnifiedRevenueEngine (le vrai moteur V14).
    """
    global _engine
    if _engine is None:
        with _lock:
            if _engine is None:
                try:
                    from NAYA_REVENUE_ENGINE.unified_revenue_engine import UnifiedRevenueEngine
                    _engine = UnifiedRevenueEngine()
                    log.info("✅ RevenueEngine V14 initialisé via unified_revenue_engine")
                except Exception as e:
                    log.warning("⚠️ UnifiedRevenueEngine unavailable: %s — using stub", e)
                    _engine = _RevenueEngineStub()
    return _engine


class _RevenueEngineStub:
    """Stub minimal si unified_revenue_engine ne peut pas charger."""
    version = "14.0.0-stub"

    def run_pipeline(self, *a, **kw):
        return {"status": "stub", "message": "Revenue engine stub — configure API keys"}

    def get_status(self):
        return {"status": "stub", "version": self.version}

    def hunt(self, *a, **kw):
        return []
