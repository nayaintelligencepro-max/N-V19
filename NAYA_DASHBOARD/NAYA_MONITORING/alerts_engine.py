"""NAYA V19 - Alerts Engine - Moteur d alertes pour le monitoring."""
import time, logging, threading
from typing import Dict, List, Callable, Optional
log = logging.getLogger("NAYA.ALERTS")

class AlertSeverity:
    INFO = "info"; WARNING = "warning"; CRITICAL = "critical"

class AlertsEngine:
    """Genere et dispatche des alertes systeme vers TORI et Telegram."""

    def __init__(self):
        self._alerts: List[Dict] = []
        self._handlers: List[Callable] = []
        self._muted: set = set()
        self._total_fired = 0

    def on_alert(self, handler: Callable) -> None:
        self._handlers.append(handler)

    def fire(self, source: str, message: str, severity: str = "info", data: Dict = None) -> Dict:
        if source in self._muted:
            return {"muted": True}
        alert = {
            "source": source, "message": message, "severity": severity,
            "data": data or {}, "ts": time.time(), "acknowledged": False
        }
        self._alerts.append(alert)
        self._total_fired += 1
        if len(self._alerts) > 1000:
            self._alerts = self._alerts[-500:]
        for handler in self._handlers:
            try:
                handler(alert)
            except Exception as e:
                log.error(f"[ALERTS] Handler error: {e}")
        if severity == "critical":
            log.error(f"[ALERT] CRITICAL: {source} - {message}")
        return alert

    def acknowledge(self, index: int) -> bool:
        if 0 <= index < len(self._alerts):
            self._alerts[index]["acknowledged"] = True
            return True
        return False

    def mute(self, source: str) -> None:
        self._muted.add(source)

    def unmute(self, source: str) -> None:
        self._muted.discard(source)

    def get_unacknowledged(self, severity: str = None) -> List[Dict]:
        alerts = [a for a in self._alerts if not a["acknowledged"]]
        if severity:
            alerts = [a for a in alerts if a["severity"] == severity]
        return alerts[-50:]

    def get_stats(self) -> Dict:
        return {
            "total_fired": self._total_fired,
            "unacknowledged": sum(1 for a in self._alerts if not a["acknowledged"]),
            "critical": sum(1 for a in self._alerts if a["severity"] == "critical"),
            "muted_sources": len(self._muted)
        }

    def get_count(self) -> int:
        """Retourne le nombre total d'alertes déclenchées."""
        return self._total_fired


# Module-level singleton and convenience function
_alerts = AlertsEngine()


def evaluate(metrics: Dict) -> List[Dict]:
    """Évalue les métriques système et retourne les alertes actives."""
    THRESHOLDS = {
        "cpu_percent":    {"warning": 80.0, "critical": 90.0},
        "memory_percent": {"warning": 80.0, "critical": 90.0},
        "disk_percent":   {"warning": 85.0, "critical": 95.0},
    }
    active = []
    for key, value in metrics.items():
        if not isinstance(value, (int, float)):
            continue
        thres = THRESHOLDS.get(key)
        if thres:
            if value >= thres["critical"]:
                alert = _alerts.fire(
                    source=key,
                    message=f"{key} critique: {value:.1f}% (seuil: {thres['critical']}%)",
                    severity="critical",
                    data={"value": value, "threshold": thres["critical"]},
                )
                if alert:
                    active.append(alert)
            elif value >= thres["warning"]:
                alert = _alerts.fire(
                    source=key,
                    message=f"{key} élevé: {value:.1f}% (seuil: {thres['warning']}%)",
                    severity="warning",
                    data={"value": value, "threshold": thres["warning"]},
                )
                if alert:
                    active.append(alert)
        elif value < 0:
            alert = _alerts.fire(
                source=key,
                message=f"Valeur anormale: {key}={value}",
                severity="warning",
                data={"value": value},
            )
            if alert:
                active.append(alert)
    return active
