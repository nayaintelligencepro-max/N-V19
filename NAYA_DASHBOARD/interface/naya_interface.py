"""
NAYA Dashboard — Interface Bridge V10
Point de contact unique et souverain entre le Dashboard et le systeme NAYA.
Toute interaction humaine transite par ce module.
Aucune logique metier — pont pur, lecture et delegation uniquement.
"""
import logging
from typing import Dict, Any, Optional

log = logging.getLogger("NAYA.DASHBOARD.interface")

__all__ = ["NayaInterface"]


class NayaInterface:
    """Interface unifiee dashboard -> systeme NAYA V19"""

    def __init__(self, system=None) -> None:
        self._system = system
        self._call_count = 0

    def get_status(self) -> Dict[str, Any]:
        self._call_count += 1
        if self._system and hasattr(self._system, "get_status"):
            try:
                return self._system.get_status()
            except Exception as e:
                log.warning(f"[INTERFACE] get_status error: {e}")
        return {"status": "unavailable", "system_connected": False}

    def snapshot(self) -> Dict[str, Any]:
        st = self.get_status()
        return {
            "status": st.get("status", "unknown"),
            "version": st.get("version", "10.0.0"),
            "uptime": st.get("uptime", "00h 00m 00s"),
            "components": st.get("components", 0),
            "ready": st.get("ready", False),
            "calls_to_interface": self._call_count,
        }

    def is_ready(self) -> bool:
        if self._system and hasattr(self._system, "is_ready"):
            return self._system.is_ready()
        return False

    def get_pipeline(self) -> Dict[str, Any]:
        try:
            from NAYA_CORE.cash_engine_real import get_cash_engine
            return get_cash_engine().get_pipeline_summary()
        except Exception as e:
            log.debug(f"[INTERFACE] get_pipeline: {e}")
            return {"active_deals": 0, "pipeline_total_eur": 0}

    def get_revenue_status(self) -> Dict[str, Any]:
        try:
            if self._system and hasattr(self._system, "_revenue_engine") and self._system._revenue_engine:
                return self._system._revenue_engine.get_stats()
        except Exception as e:
            log.debug(f"[INTERFACE] get_revenue_status: {e}")
        return {"status": "unavailable"}

    def get_portfolio(self) -> Dict[str, Any]:
        try:
            from NAYA_CORE.portfolio_manager import get_portfolio
            pm = get_portfolio(db=self._get_db())
            return {
                "kpis": pm.get_portfolio_kpis(),
                "projects": {
                    pid: {
                        "name": s.name, "status": s.status,
                        "revenue_total": s.total_revenue, "mrr": s.mrr,
                        "pipeline": {"signals": s.signals, "won": s.won},
                    }
                    for pid, s in pm.get_all_snapshots().items()
                },
            }
        except Exception as e:
            log.debug(f"[INTERFACE] get_portfolio: {e}")
            return {"kpis": {}, "projects": {}}

    def get_brain_status(self) -> Dict[str, Any]:
        try:
            if self._system and hasattr(self._system, "_brain") and self._system._brain:
                return self._system._brain.get_stats()
        except Exception as e:
            log.debug(f"[INTERFACE] get_brain_status: {e}")
        return {"available": False}

    def think(self, prompt: str, task_type: str = "fast") -> Dict[str, Any]:
        try:
            if self._system and hasattr(self._system, "_brain") and self._system._brain:
                if self._system._brain.available:
                    from NAYA_CORE.execution.naya_brain import TaskType
                    tt = TaskType.FAST
                    result = self._system._brain.think(prompt, tt)
                    return {"text": result.text, "provider": result.provider, "latency_ms": result.latency_ms}
        except Exception as e:
            log.warning(f"[INTERFACE] think error: {e}")
        return {"text": "", "error": "Brain non disponible"}

    def get_security_status(self) -> Dict[str, Any]:
        try:
            reapers = self._get_comp("reapers")
            if reapers:
                return {
                    "status": "active",
                    "targets_monitored": len(getattr(reapers, "targets", {})),
                }
        except Exception as e:
            log.debug(f"[INTERFACE] get_security_status: {e}")
        return {"status": "unavailable"}

    def get_scheduler_status(self) -> Dict[str, Any]:
        try:
            if self._system and hasattr(self._system, "_scheduler") and self._system._scheduler:
                return self._system._scheduler.get_status()
        except Exception as e:
            log.debug(f"[INTERFACE] get_scheduler_status: {e}")
        return {"status": "unavailable"}

    def get_tori_status(self) -> Dict[str, Any]:
        if not self._system:
            return {}
        return {
            "event_stream":    self._system._comp.get("event_stream_server", "inactive"),
            "command_gateway": self._system._comp.get("command_gateway_server", "inactive"),
            "observation_bus": self._system._comp.get("observation_bus_server", "inactive"),
        }

    def trigger_hunt(self) -> Dict[str, Any]:
        try:
            from NAYA_CORE.naya_sovereign_engine import get_sovereign
            result = get_sovereign().trigger_now()
            return result.to_dict() if hasattr(result, "to_dict") else {"triggered": True}
        except Exception as e:
            return {"triggered": False, "error": str(e)[:60]}

    def trigger_revenue_scan(self) -> Dict[str, Any]:
        try:
            if self._system and hasattr(self._system, "_revenue_engine") and self._system._revenue_engine:
                return self._system._revenue_engine.run_cycle()
        except Exception as e:
            return {"error": str(e)[:60]}
        return {"error": "Revenue engine non disponible"}

    def _get_db(self):
        if self._system and hasattr(self._system, "_db"):
            return self._system._db
        return None

    def _get_comp(self, key: str):
        if self._system and hasattr(self._system, "_comp"):
            return self._system._comp.get(key)
        return None
