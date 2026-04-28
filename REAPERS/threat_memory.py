"""NAYA V19 - Threat Memory - Memoire des menaces detectees."""
import time, logging, json
from typing import Dict, List
from pathlib import Path
log = logging.getLogger("NAYA.REAPERS.THREATS")

THREATS_FILE = Path("data/cache/threat_memory.json")

class ThreatMemory:
    """Memorise les menaces passees pour mieux les anticiper."""

    def __init__(self):
        self._threats: List[Dict] = []
        self._patterns: Dict[str, int] = {}
        self._load()

    def record(self, threat_type: str, source: str = "unknown",
               severity: float = 0.5, details: str = "") -> Dict:
        """Alias for record_threat — backward compatibility."""
        return self.record_threat(threat_type=threat_type, source=source,
                                  severity=severity, details=details)

    def record_threat(self, threat_type: str, source: str, severity: float,
                      details: str = "") -> Dict:
        threat = {
            "type": threat_type, "source": source, "severity": severity,
            "details": details, "ts": time.time(), "mitigated": False
        }
        self._threats.append(threat)
        self._patterns[threat_type] = self._patterns.get(threat_type, 0) + 1
        if len(self._threats) > 2000:
            self._threats = self._threats[-1000:]
        self._save()
        log.warning(f"[THREATS] {threat_type} from {source} (sev={severity})")
        return threat

    def is_known_threat(self, threat_type: str) -> bool:
        return threat_type in self._patterns

    def get_threat_frequency(self, threat_type: str) -> int:
        return self._patterns.get(threat_type, 0)

    def get_top_threats(self, n: int = 5) -> List[Dict]:
        return sorted(
            [{"type": t, "count": c} for t, c in self._patterns.items()],
            key=lambda x: x["count"], reverse=True
        )[:n]

    def anticipate(self) -> List[Dict]:
        """Anticipe les menaces probables basees sur l historique."""
        high_freq = [t for t, c in self._patterns.items() if c >= 3]
        return [{"threat": t, "frequency": self._patterns[t],
                 "recommendation": "Renforcer les defenses"} for t in high_freq]

    def _save(self):
        try:
            THREATS_FILE.parent.mkdir(parents=True, exist_ok=True)
            THREATS_FILE.write_text(json.dumps({
                "threats": self._threats[-500:], "patterns": self._patterns
            }, default=str))
        except Exception:
            pass

    def _load(self):
        try:
            if THREATS_FILE.exists():
                data = json.loads(THREATS_FILE.read_text())
                self._threats = data.get("threats", [])
                self._patterns = data.get("patterns", {})
        except Exception:
            pass

    def get_stats(self) -> Dict:
        return {
            "total_threats": len(self._threats),
            "unique_types": len(self._patterns),
            "top_threats": self.get_top_threats(3)
        }
