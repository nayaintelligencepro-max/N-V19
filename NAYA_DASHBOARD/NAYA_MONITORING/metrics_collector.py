"""NAYA V19 - Metrics Collector - Collecte les metriques systeme."""
import time, logging, threading
from typing import Dict, List

log = logging.getLogger("NAYA.METRICS")

# Try importing psutil for real system metrics
try:
    import psutil
    _PSUTIL = True
except ImportError:
    _PSUTIL = False


class MetricsCollector:
    def __init__(self):
        self._metrics: Dict[str, List] = {}
        self._lock = threading.Lock()

    def record(self, name: str, value: float) -> None:
        with self._lock:
            if name not in self._metrics:
                self._metrics[name] = []
            self._metrics[name].append({"value": value, "ts": time.time()})
            if len(self._metrics[name]) > 1000:
                self._metrics[name] = self._metrics[name][-500:]

    def get_metric(self, name: str, last_n: int = 10) -> List:
        with self._lock:
            return self._metrics.get(name, [])[-last_n:]

    def get_average(self, name: str, last_n: int = 10) -> float:
        data = self.get_metric(name, last_n)
        if not data:
            return 0
        return sum(d["value"] for d in data) / len(data)

    def get_all_names(self) -> List[str]:
        return list(self._metrics.keys())

    def get_stats(self) -> Dict:
        return {
            "metrics_tracked": len(self._metrics),
            "total_points": sum(len(v) for v in self._metrics.values())
        }

    def collect(self) -> Dict:
        """Collecte et retourne un snapshot de toutes les métriques système."""
        return collect_metrics()

    def get_latest(self) -> Dict:
        """Retourne la dernière valeur de chaque métrique."""
        return get_latest()


_collector = MetricsCollector()


def _get_cpu_percent() -> float:
    if _PSUTIL:
        try:
            return psutil.cpu_percent(interval=0.1)
        except Exception:
            pass
    # Fallback: estimé à partir de /proc/stat si disponible
    try:
        import os
        if os.path.exists("/proc/stat"):
            with open("/proc/stat") as f:
                line = f.readline()
            vals = list(map(int, line.split()[1:]))
            idle = vals[3]
            total = sum(vals)
            time.sleep(0.05)
            with open("/proc/stat") as f:
                line2 = f.readline()
            vals2 = list(map(int, line2.split()[1:]))
            idle2 = vals2[3]
            total2 = sum(vals2)
            dt = total2 - total
            di = idle2 - idle
            return round((1 - di / max(dt, 1)) * 100, 1) if dt > 0 else 0.0
    except Exception:
        pass
    return 0.0


def _get_memory_percent() -> float:
    if _PSUTIL:
        try:
            return psutil.virtual_memory().percent
        except Exception:
            pass
    try:
        with open("/proc/meminfo") as f:
            lines = f.readlines()
        info = {}
        for line in lines[:5]:
            k, v = line.split(":")
            info[k.strip()] = int(v.strip().split()[0])
        total = info.get("MemTotal", 0)
        avail = info.get("MemAvailable", info.get("MemFree", total))
        if total > 0:
            return round((total - avail) / total * 100, 1)
    except Exception:
        pass
    return 0.0


def _get_disk_percent() -> float:
    if _PSUTIL:
        try:
            return psutil.disk_usage("/").percent
        except Exception:
            pass
    try:
        import os
        st = os.statvfs("/")
        total = st.f_blocks * st.f_frsize
        free = st.f_bfree * st.f_frsize
        if total > 0:
            return round((total - free) / total * 100, 1)
    except Exception:
        pass
    return 0.0


def collect_metrics() -> Dict:
    """Retourne un snapshot complet des métriques système."""
    cpu = _get_cpu_percent()
    mem = _get_memory_percent()
    disk = _get_disk_percent()
    ts = time.time()
    # Persiste dans le collecteur singleton pour historique
    _collector.record("cpu_percent", cpu)
    _collector.record("memory_percent", mem)
    _collector.record("disk_percent", disk)
    return {
        "cpu_percent": cpu,
        "memory_percent": mem,
        "disk_percent": disk,
        "timestamp": ts,
        "stats": _collector.get_stats(),
    }


def get_latest() -> Dict:
    """Retourne les dernières valeurs de chaque métrique."""
    return {name: _collector.get_metric(name, 1) for name in _collector.get_all_names()}

