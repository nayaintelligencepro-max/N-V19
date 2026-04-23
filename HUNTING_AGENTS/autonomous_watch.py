"""
NAYA V19 - Autonomous Watch Engine
Veille permanente sur sources ciblees: appels d offres publics,
marches gouvernementaux, annonces restructuration, opportunites haute valeur.
"""
import time, logging, threading, json, hashlib
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path

log = logging.getLogger("NAYA.WATCH")

@dataclass
class WatchAlert:
    alert_id: str
    source_type: str  # public_tender, restructuration, market_gap, government, corporate
    title: str
    description: str
    estimated_value_eur: float
    urgency: float
    sector: str
    geography: str
    detected_at: float = field(default_factory=time.time)
    processed: bool = False
    forwarded_to_hunt: bool = False

class AutonomousWatchEngine:
    """Veille autonome permanente - detecte opportunites haute valeur."""

    WATCH_SOURCES = {
        "public_tenders": {
            "description": "Appels d offres publics et marches gouvernementaux",
            "keywords": ["appel offre", "marche public", "consultation", "DSP"],
            "min_value": 10000, "check_interval_min": 30
        },
        "restructuration": {
            "description": "Entreprises en restructuration ou transformation",
            "keywords": ["restructuration", "transformation digitale", "plan social", "fusion"],
            "min_value": 50000, "check_interval_min": 60
        },
        "market_gaps": {
            "description": "Lacunes marche identifiees",
            "keywords": ["pas de solution", "manque", "besoin non couvert", "sous-desservi"],
            "min_value": 5000, "check_interval_min": 120
        },
        "corporate_pain": {
            "description": "Douleurs corporate exprimees publiquement",
            "keywords": ["perte", "cout", "inefficace", "probleme", "plainte"],
            "min_value": 5000, "check_interval_min": 45
        },
        "regional_specific": {
            "description": "Opportunites specifiques Polynesie francaise",
            "keywords": ["polynesie", "tahiti", "papeete", "pacifique", "outre-mer"],
            "min_value": 2000, "check_interval_min": 60
        }
    }

    def __init__(self):
        self._alerts: List[WatchAlert] = []
        self._lock = threading.RLock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._total_detected = 0
        self._callbacks: List = []

    def on_alert(self, callback) -> None:
        self._callbacks.append(callback)

    def analyze_content(self, content: str, source_type: str = "general",
                       geography: str = "") -> List[WatchAlert]:
        """Analyse un contenu et detecte les opportunites."""
        alerts = []
        content_lower = content.lower()

        for src_name, src_config in self.WATCH_SOURCES.items():
            score = 0
            matched_keywords = []
            for kw in src_config["keywords"]:
                if kw.lower() in content_lower:
                    score += 1
                    matched_keywords.append(kw)

            if score >= 2:  # Au moins 2 keywords matches
                value = self._estimate_value(content, src_config["min_value"])
                urgency = min(1.0, score * 0.25)

                alert = WatchAlert(
                    alert_id=f"WATCH_{hashlib.md5(f'{content[:50]}{time.time()}'.encode()).hexdigest()[:8].upper()}",
                    source_type=src_name,
                    title=f"Opportunite {src_name}: {', '.join(matched_keywords[:3])}",
                    description=content[:500],
                    estimated_value_eur=value,
                    urgency=urgency,
                    sector=self._detect_sector(content),
                    geography=geography or self._detect_geography(content)
                )
                alerts.append(alert)
                with self._lock:
                    self._alerts.append(alert)
                    self._total_detected += 1
                for cb in self._callbacks:
                    try:
                        cb(alert)
                    except Exception as e:
                        log.error(f"[WATCH] Callback: {e}")

        return alerts

    def _estimate_value(self, content: str, min_value: float) -> float:
        """Estime la valeur de l opportunite depuis le contenu."""
        import re
        numbers = re.findall(r'(\d[\d\s]*(?:\.\d+)?)\s*(?:euros?|EUR|k|K|million)', content)
        if numbers:
            try:
                val = float(numbers[0].replace(' ', ''))
                if 'million' in content.lower():
                    val *= 1_000_000
                elif 'k' in content.lower():
                    val *= 1000
                return max(min_value, val)
            except ValueError:
                pass
        return min_value

    def _detect_sector(self, content: str) -> str:
        SECTOR_KW = {
            "sante": ["hopital", "clinique", "medical", "sante"],
            "tech": ["logiciel", "saas", "digital", "tech"],
            "immobilier": ["immobilier", "construction", "batiment"],
            "finance": ["banque", "finance", "assurance"],
            "gouvernement": ["mairie", "prefecture", "ministere", "gouvernement"],
            "energie": ["energie", "solaire", "renouvelable"],
            "education": ["ecole", "formation", "universite"],
        }
        cl = content.lower()
        for sector, kws in SECTOR_KW.items():
            if any(k in cl for k in kws):
                return sector
        return "general"

    def _detect_geography(self, content: str) -> str:
        cl = content.lower()
        if any(k in cl for k in ["polynesie", "tahiti", "papeete"]):
            return "polynesie_francaise"
        if any(k in cl for k in ["france", "paris", "lyon"]):
            return "france"
        return "international"

    def get_unprocessed(self) -> List[WatchAlert]:
        with self._lock:
            return [a for a in self._alerts if not a.processed]

    def mark_processed(self, alert_id: str) -> None:
        with self._lock:
            for a in self._alerts:
                if a.alert_id == alert_id:
                    a.processed = True
                    break

    def get_stats(self) -> Dict:
        with self._lock:
            by_source = {}
            for a in self._alerts:
                by_source[a.source_type] = by_source.get(a.source_type, 0) + 1
            return {
                "total_detected": self._total_detected,
                "unprocessed": sum(1 for a in self._alerts if not a.processed),
                "by_source": by_source,
                "running": self._running
            }

_watch = None
_watch_lock = threading.Lock()
def get_watch_engine() -> AutonomousWatchEngine:
    global _watch
    if _watch is None:
        with _watch_lock:
            if _watch is None:
                _watch = AutonomousWatchEngine()
    return _watch
