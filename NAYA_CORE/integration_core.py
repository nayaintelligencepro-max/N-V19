"""
NAYA V19 INTEGRATION CORE
Modules intégrés directement dans NAYA_CORE.
Backward compatible avec tous les modules existants.
"""
import logging
from typing import Dict, Optional

log = logging.getLogger("NAYA.V19.INTEGRATION")


class NAYAIntegration:
    """
    V19 Integration layer — gère tous les composants d'intégration NAYA.
    Directement intégré dans NAYA_CORE_MAIN.
    """

    def __init__(self):
        self.telemetry = None
        self.resilience_patterns = {}
        self.ml_engine = None
        self.event_bus = None
        self.celery_app = None
        self._initialized = False

    def initialize(self) -> Dict:
        """Initialize all integration components within NAYA system."""
        results = {}

        # 1. TELEMETRY
        try:
            from NAYA_TELEMETRY.telemetry_core import NAYATelemetryCore
            self.telemetry = NAYATelemetryCore(service_name="naya-v19")
            telemetry_status = self.telemetry.initialize()
            results['telemetry'] = telemetry_status
            log.info(f"✅ Telemetry: {telemetry_status}")
        except ImportError:
            log.warning("⚠️ OpenTelemetry not available, using fallback")
            results['telemetry'] = {"initialized": False, "reason": "OpenTelemetry not installed"}

        # 2. RESILIENCE
        try:
            from RESILIENCE.resilience_patterns import ResilientFunction, CircuitBreaker
            self.resilience_patterns = {
                'ResilientFunction': ResilientFunction,
                'CircuitBreaker': CircuitBreaker,
            }
            results['resilience'] = {"initialized": True, "patterns": list(self.resilience_patterns.keys())}
            log.info(f"✅ Resilience: {len(self.resilience_patterns)} patterns loaded")
        except ImportError as e:
            log.warning(f"⚠️ Resilience patterns not available: {e}")
            results['resilience'] = {"initialized": False}

        # 3. ML ENGINE
        try:
            from ML_ENGINE.ml_revenue_engine import OfferOptimizer
            self.ml_engine = OfferOptimizer()
            results['ml_engine'] = {"initialized": True, "type": "OfferOptimizer"}
            log.info("✅ ML Engine: Ready")
        except ImportError as e:
            log.warning(f"⚠️ ML Engine not available: {e}")
            results['ml_engine'] = {"initialized": False}

        # 4. EVENT STREAMING
        try:
            from EVENT_STREAMING.event_bus import EventBus
            self.event_bus = EventBus()
            event_bus_status = self.event_bus.initialize()
            results['event_bus'] = event_bus_status
            log.info(f"✅ Event Bus: {event_bus_status}")
        except ImportError as e:
            log.warning(f"⚠️ Event Bus not available: {e}")
            results['event_bus'] = {"initialized": False}

        # 5. CELERY/ASYNC
        try:
            from ASYNC.celery_tasks import NAYACeleryApp
            self.celery_app = NAYACeleryApp()
            celery_status = self.celery_app.initialize()
            results['celery'] = celery_status
            log.info(f"✅ Celery: {celery_status}")
        except ImportError as e:
            log.warning(f"⚠️ Celery not available: {e}")
            results['celery'] = {"initialized": False}

        self._initialized = True
        results['overall'] = True

        return results

    def get_status(self) -> Dict:
        """Get integration status."""
        return {
            "initialized": self._initialized,
            "telemetry": self.telemetry.get_status() if self.telemetry else None,
            "resilience": len(self.resilience_patterns),
            "ml_engine": bool(self.ml_engine),
            "event_bus": self.event_bus.get_status() if self.event_bus else None,
        }

    def trace_operation(self, operation_name: str, func):
        """Wrap function with telemetry if available."""
        if self.telemetry:
            return self.telemetry.trace_function(operation_name)(func)
        return func

    def make_resilient(self, circuit_breaker=True, retry=3):
        """Make function resilient."""
        if self.resilience_patterns.get('ResilientFunction'):
            from RESILIENCE.resilience_patterns import ResilientFunction
            return ResilientFunction(
                circuit_breaker=circuit_breaker,
                retry_attempts=retry
            )
        return lambda f: f

    def optimize_offer(self, lead_data: dict):
        """Generate ML-optimized offer."""
        if self.ml_engine:
            return self.ml_engine.optimize_offer(lead_data)
        return self._static_offer_generation(lead_data)

    def _static_offer_generation(self, lead_data: dict):
        """Fallback offer generation."""
        lead_score = lead_data.get('lead_score', 50)
        if lead_score >= 80:
            return {'type': 'premium', 'price': 80000}
        elif lead_score >= 60:
            return {'type': 'security', 'price': 40000}
        else:
            return {'type': 'audit', 'price': 15000}

    def publish_event(self, event_type, source, data):
        """Publish event if event bus available."""
        if self.event_bus:
            from EVENT_STREAMING.event_bus import Event, EventType
            try:
                et = EventType[event_type.upper()] if isinstance(event_type, str) else event_type
                event = Event(
                    event_type=et,
                    timestamp=None,
                    source_service=source,
                    data=data,
                )
                return self.event_bus.publish(event)
            except Exception as e:
                log.warning(f"Event publish failed: {e}")
                return False
        return False

    def submit_async_task(self, task_type: str, *args, **kwargs):
        """Submit async task if Celery available."""
        if self.celery_app:
            return self.celery_app.submit_task(task_type, *args, **kwargs)
        return None


# Global singleton
_integration: Optional[NAYAIntegration] = None


def get_integration() -> NAYAIntegration:
    """Get or create V19 integration instance."""
    global _integration
    if _integration is None:
        _integration = NAYAIntegration()
    return _integration


# Backward-compatibility alias (do NOT expose old names in new code)
def get_v19_integration() -> NAYAIntegration:
    """Alias for get_integration()."""
    return get_integration()
