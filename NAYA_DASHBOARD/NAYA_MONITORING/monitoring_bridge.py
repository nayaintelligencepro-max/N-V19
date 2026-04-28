
from NAYA_INTERFACE.bus.state_stream import state_stream
from NAYA_DASHBOARD.NAYA_MONITORING.metrics_collector import collect_metrics
from NAYA_DASHBOARD.NAYA_MONITORING.performance_tracker import track
from NAYA_DASHBOARD.NAYA_MONITORING.alerts_engine import evaluate

def _tick():
    metrics = collect_metrics()
    track(metrics)
    alerts = evaluate(metrics)
    state_stream.update_state("monitoring", {
        "metrics": metrics,
        "alerts": alerts
    })

# simple timer hook (called externally)
def monitoring_tick():
    _tick()


class MonitoringBridge:
    """
    Pont entre le monitoring dashboard et le state stream.
    Orchestre les collectes périodiques de métriques.
    """

    def __init__(self):
        from NAYA_DASHBOARD.NAYA_MONITORING.metrics_collector import MetricsCollector
        from NAYA_DASHBOARD.NAYA_MONITORING.performance_tracker import PerformanceTracker
        from NAYA_DASHBOARD.NAYA_MONITORING.alerts_engine import AlertsEngine
        self.collector = MetricsCollector()
        self.tracker = PerformanceTracker()
        self.alerts = AlertsEngine()
        self._tick_count = 0

    def tick(self) -> dict:
        """Exécute un cycle de monitoring : collect → track → evaluate → publish."""
        self._tick_count += 1
        try:
            metrics = self.collector.collect()
            self.tracker.track(metrics)
            active_alerts = self.alerts.evaluate(metrics)
            state = {"metrics": metrics, "alerts": active_alerts, "tick": self._tick_count}
            try:
                state_stream.update_state("monitoring", state)
            except Exception:
                pass  # state_stream optionnel
            return state
        except Exception as e:
            return {"error": str(e), "tick": self._tick_count}

    def get_status(self) -> dict:
        return {
            "ticks": self._tick_count,
            "degraded": self.tracker.is_degraded(),
            "alert_history_count": self.alerts.get_count() if hasattr(self.alerts, "get_count") else 0,
            "latest_metrics": self.collector.get_latest(),
        }
