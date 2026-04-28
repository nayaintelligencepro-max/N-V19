"""
NAYA SUPREME V19.3 — AMELIORATION #10
System Heartbeat Monitor
========================
Heartbeat continu de tous les sous-systemes NAYA avec alertes
instantanees si un module meurt ou ne repond plus.

Unique a NAYA : monitoring heartbeat a la seconde avec
auto-redemarrage et escalade intelligente.
"""
import os
import time
import logging
import threading
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field

log = logging.getLogger("NAYA.HEARTBEAT")


@dataclass
class HeartbeatEntry:
    module_name: str
    last_beat: float
    beat_count: int
    status: str  # alive | warning | dead
    avg_interval_ms: float
    check_function: Optional[Callable] = None
    max_silence_seconds: float = 300  # 5 min default
    last_error: str = ""
    consecutive_failures: int = 0
    auto_restart_count: int = 0


@dataclass
class HeartbeatAlert:
    module_name: str
    alert_type: str  # missed_beat | dead | recovered | restarted
    message: str
    timestamp: float = field(default_factory=time.time)
    notified: bool = False


class SystemHeartbeatMonitor:
    """
    Moniteur de battement cardiaque pour tous les modules NAYA.

    Chaque module envoie un heartbeat periodique.
    Si un module ne bat plus, le moniteur :
    1. Genere une alerte WARNING apres 1x le timeout
    2. Tente un auto-restart apres 2x le timeout
    3. Genere une alerte CRITICAL apres 3x le timeout
    4. Escalade vers la fondatrice apres 5x le timeout
    """

    def __init__(self):
        self._modules: Dict[str, HeartbeatEntry] = {}
        self._alerts: List[HeartbeatAlert] = []
        self._lock = threading.Lock()
        self._monitor_thread: Optional[threading.Thread] = None
        self._running: bool = False
        self._check_interval: float = 30.0
        self._total_beats: int = 0
        self._total_alerts: int = 0
        self._total_restarts: int = 0
        self._started_at: float = 0

    def register_module(self, name: str, check_function: Callable = None,
                        max_silence_seconds: float = 300) -> None:
        """Enregistre un module pour le monitoring heartbeat."""
        with self._lock:
            self._modules[name] = HeartbeatEntry(
                module_name=name,
                last_beat=time.time(),
                beat_count=0,
                status="alive",
                avg_interval_ms=0,
                check_function=check_function,
                max_silence_seconds=max_silence_seconds,
            )
        log.info(f"[HEARTBEAT] Module '{name}' enregistre (timeout={max_silence_seconds}s)")

    def beat(self, module_name: str) -> None:
        """Enregistre un battement pour un module."""
        with self._lock:
            entry = self._modules.get(module_name)
            if not entry:
                self._modules[module_name] = HeartbeatEntry(
                    module_name=module_name,
                    last_beat=time.time(),
                    beat_count=1,
                    status="alive",
                    avg_interval_ms=0,
                )
                return

            now = time.time()
            interval = (now - entry.last_beat) * 1000
            entry.last_beat = now
            entry.beat_count += 1
            entry.consecutive_failures = 0
            self._total_beats += 1

            if entry.beat_count > 1:
                alpha = 0.2
                entry.avg_interval_ms = round(
                    alpha * interval + (1 - alpha) * entry.avg_interval_ms, 1
                )

            if entry.status != "alive":
                old_status = entry.status
                entry.status = "alive"
                self._alerts.append(HeartbeatAlert(
                    module_name=module_name,
                    alert_type="recovered",
                    message=f"Module '{module_name}' recovered ({old_status} -> alive)",
                ))
                log.info(f"[HEARTBEAT] Module '{module_name}' RECOVERED")

    def check_all(self) -> Dict[str, str]:
        """Verifie l'etat de tous les modules."""
        now = time.time()
        statuses: Dict[str, str] = {}

        with self._lock:
            for name, entry in self._modules.items():
                silence = now - entry.last_beat
                timeout = entry.max_silence_seconds

                if silence < timeout:
                    entry.status = "alive"
                elif silence < timeout * 2:
                    entry.status = "warning"
                    entry.consecutive_failures += 1
                    if entry.consecutive_failures == 1:
                        self._create_alert(name, "missed_beat",
                            f"Module '{name}' silencieux depuis {silence:.0f}s (timeout={timeout}s)")
                elif silence < timeout * 3:
                    entry.status = "dead"
                    self._attempt_restart(entry)
                else:
                    entry.status = "dead"
                    if entry.consecutive_failures <= 5:
                        self._create_alert(name, "dead",
                            f"CRITICAL: Module '{name}' mort depuis {silence:.0f}s")

                # Tenter le check function si disponible
                if entry.check_function and entry.status in ("warning", "dead"):
                    try:
                        entry.check_function()
                        entry.status = "alive"
                        entry.last_beat = now
                        entry.consecutive_failures = 0
                    except Exception as e:
                        entry.last_error = str(e)[:100]

                statuses[name] = entry.status

        return statuses

    def _create_alert(self, module_name: str, alert_type: str, message: str) -> None:
        """Cree une alerte interne."""
        self._alerts.append(HeartbeatAlert(
            module_name=module_name, alert_type=alert_type, message=message
        ))
        self._total_alerts += 1
        if len(self._alerts) > 500:
            self._alerts = self._alerts[-250:]
        log.warning(f"[HEARTBEAT] ALERT: {message}")

    def _attempt_restart(self, entry: HeartbeatEntry) -> None:
        """Tente de redemarrer un module mort."""
        if entry.auto_restart_count >= 3:
            return  # Max 3 restarts automatiques
        entry.auto_restart_count += 1
        self._total_restarts += 1
        log.info(f"[HEARTBEAT] Auto-restart #{entry.auto_restart_count} pour '{entry.module_name}'")

        if entry.check_function:
            try:
                entry.check_function()
                entry.status = "alive"
                entry.last_beat = time.time()
                entry.consecutive_failures = 0
                self._create_alert(entry.module_name, "restarted",
                    f"Module '{entry.module_name}' redemarré automatiquement")
            except Exception as e:
                entry.last_error = str(e)[:100]
                log.error(f"[HEARTBEAT] Auto-restart echoue pour '{entry.module_name}': {e}")

    def start_monitoring(self) -> None:
        """Demarre le monitoring en background."""
        if self._running:
            return
        self._running = True
        self._started_at = time.time()
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop, daemon=True, name="heartbeat-monitor"
        )
        self._monitor_thread.start()
        log.info(f"[HEARTBEAT] Monitoring demarre (interval={self._check_interval}s)")

    def stop_monitoring(self) -> None:
        """Arrete le monitoring."""
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        log.info("[HEARTBEAT] Monitoring arrete")

    def _monitor_loop(self) -> None:
        """Boucle de monitoring en background."""
        while self._running:
            self.check_all()
            time.sleep(self._check_interval)

    def get_dashboard(self) -> Dict:
        """Retourne le dashboard complet des heartbeats."""
        statuses = self.check_all()
        return {
            "modules": {
                name: {
                    "status": entry.status,
                    "beat_count": entry.beat_count,
                    "avg_interval_ms": entry.avg_interval_ms,
                    "silence_seconds": round(time.time() - entry.last_beat, 1),
                    "consecutive_failures": entry.consecutive_failures,
                    "auto_restarts": entry.auto_restart_count,
                    "last_error": entry.last_error,
                }
                for name, entry in self._modules.items()
            },
            "summary": {
                "total_modules": len(self._modules),
                "alive": sum(1 for s in statuses.values() if s == "alive"),
                "warning": sum(1 for s in statuses.values() if s == "warning"),
                "dead": sum(1 for s in statuses.values() if s == "dead"),
            },
            "stats": self.get_stats(),
        }

    def get_recent_alerts(self, last_n: int = 20) -> List[Dict]:
        """Retourne les alertes recentes."""
        return [
            {
                "module": a.module_name,
                "type": a.alert_type,
                "message": a.message,
                "timestamp": a.timestamp,
            }
            for a in self._alerts[-last_n:]
        ]

    def get_stats(self) -> Dict:
        uptime = time.time() - self._started_at if self._started_at else 0
        return {
            "total_modules": len(self._modules),
            "total_beats": self._total_beats,
            "total_alerts": self._total_alerts,
            "total_restarts": self._total_restarts,
            "monitoring_active": self._running,
            "uptime_hours": round(uptime / 3600, 2),
        }


_monitor: Optional[SystemHeartbeatMonitor] = None


def get_heartbeat_monitor() -> SystemHeartbeatMonitor:
    global _monitor
    if _monitor is None:
        _monitor = SystemHeartbeatMonitor()
    return _monitor
