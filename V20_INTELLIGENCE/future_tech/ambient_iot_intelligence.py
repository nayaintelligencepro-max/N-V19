"""
NAYA V20 — Ambient IoT Intelligence
══════════════════════════════════════════════════════════════════════════════
Real-time IoT anomaly detection triggering automatic OT audit proposals.

DOCTRINE:
  Industrial IoT sensors broadcast early warning signals of OT system stress.
  A temperature sensor spike on a cooling unit, an abnormal power draw on a
  PLC, or a network latency anomaly on a historian node — each is a buying
  signal for an emergency OT audit.

  When an anomaly fires NAYA automatically:
    1. Classifies severity (MEDIUM / HIGH / CRITICAL)
    2. Drafts an audit proposal with commercial framing
    3. Sends a CRITICAL Telegram alert for immediate human review

  This converts raw telemetry into qualified sales opportunities in < 1 second.
══════════════════════════════════════════════════════════════════════════════
"""
import hashlib
import json
import logging
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

log = logging.getLogger("NAYA.AMBIENT_IOT")

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_FILE = ROOT / "data" / "cache" / "ambient_iot_intelligence.json"


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


@dataclass
class IoTAnomaly:
    """An anomalous sensor reading with associated audit proposal."""

    anomaly_id: str
    device_id: str
    device_type: str
    company: str
    sector: str
    metric: str
    value: float
    threshold: float
    deviation_pct: float
    severity: str                   # CRITICAL | HIGH | MEDIUM
    audit_proposal_text: str
    detected_at: str
    proposal_generated_at: str


class AmbientIoTIntelligence:
    """
    Ingests IoT sensor events, detects anomalies and generates automatic
    OT audit proposals.

    Thread-safe singleton.  Persists anomalies to DATA_FILE.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._data_file = DATA_FILE
        self._anomalies: List[Dict] = []
        self._load()

    # ──────────────────────────────────────────────────────────────────────
    # Persistence
    # ──────────────────────────────────────────────────────────────────────

    def _load(self) -> None:
        if self._data_file.exists():
            try:
                with open(self._data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._anomalies = data.get("anomalies", [])
            except Exception:
                pass

    def _save(self) -> None:
        self._data_file.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            with open(self._data_file, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "anomalies": self._anomalies,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    },
                    f,
                    indent=2,
                    ensure_ascii=False,
                )

    # ──────────────────────────────────────────────────────────────────────
    # Business methods
    # ──────────────────────────────────────────────────────────────────────

    def ingest_sensor_event(
        self,
        device_id: str,
        device_type: str,
        company: str,
        sector: str,
        metric: str,
        value: float,
        threshold: float,
        unit: str = "",
    ) -> Optional[IoTAnomaly]:
        """
        Ingest a sensor reading and detect if it represents an anomaly.

        Args:
            device_id: Unique device identifier.
            device_type: Device type label (e.g. "SCADA", "PLC", "historian").
            company: Company owning the device.
            sector: Industry sector.
            metric: Metric name (e.g. "cpu_load", "temperature_c").
            value: Current sensor reading.
            threshold: Normal operating threshold; anomaly if value > threshold.
            unit: Optional unit label for display (e.g. "°C", "%").

        Returns:
            IoTAnomaly if value exceeds threshold, None otherwise.
        """
        if value <= threshold:
            return None

        deviation_pct = (
            abs((value - threshold) / threshold * 100) if threshold != 0 else 100.0
        )

        if deviation_pct > 50:
            severity = "CRITICAL"
        elif deviation_pct > 20:
            severity = "HIGH"
        else:
            severity = "MEDIUM"

        anomaly_id = _sha256(device_id + metric + str(value))[:12]
        now = datetime.now(timezone.utc).isoformat()

        audit_proposal_text = (
            f"Anomalie détectée sur {device_type} [{device_id}] chez {company}. "
            f"Métrique {metric}: {value}{unit} (seuil: {threshold}{unit}, "
            f"déviation: {deviation_pct:.1f}%). "
            f"Recommandation: audit OT immédiat pour {sector}."
        )

        anomaly = IoTAnomaly(
            anomaly_id=anomaly_id,
            device_id=device_id,
            device_type=device_type,
            company=company,
            sector=sector,
            metric=metric,
            value=value,
            threshold=threshold,
            deviation_pct=round(deviation_pct, 2),
            severity=severity,
            audit_proposal_text=audit_proposal_text,
            detected_at=now,
            proposal_generated_at=now,
        )

        with self._lock:
            self._anomalies.append(asdict(anomaly))
        self._save()

        if severity == "CRITICAL":
            self._send_critical_alert(anomaly)

        return anomaly

    def get_active_anomalies(self, company: Optional[str] = None) -> List[IoTAnomaly]:
        """
        Return stored anomalies, optionally filtered by company.

        Args:
            company: If provided, only return anomalies for this company.

        Returns:
            List of IoTAnomaly objects sorted by deviation_pct descending.
        """
        with self._lock:
            raw = list(self._anomalies)
        if company:
            raw = [a for a in raw if a["company"] == company]
        raw.sort(key=lambda a: a["deviation_pct"], reverse=True)
        return [IoTAnomaly(**a) for a in raw]

    def generate_audit_proposal(self, anomaly_id: str) -> str:
        """
        Return the pre-generated audit proposal text for a stored anomaly.

        Args:
            anomaly_id: Target anomaly identifier.

        Returns:
            Audit proposal text string.

        Raises:
            ValueError: If anomaly_id is not found.
        """
        with self._lock:
            matches = [a for a in self._anomalies if a["anomaly_id"] == anomaly_id]
        if not matches:
            raise ValueError(f"Anomaly '{anomaly_id}' not found.")
        return matches[0]["audit_proposal_text"]

    def get_stats(self) -> Dict:
        """
        Return aggregate statistics for the dashboard.

        Returns:
            Dict with total_anomalies, critical_count, companies_affected.
        """
        with self._lock:
            anomalies = list(self._anomalies)
        total = len(anomalies)
        critical = sum(1 for a in anomalies if a["severity"] == "CRITICAL")
        companies = len({a["company"] for a in anomalies})
        return {
            "total_anomalies": total,
            "critical_count": critical,
            "companies_affected": companies,
        }

    def _send_critical_alert(self, anomaly: IoTAnomaly) -> None:
        """Send a Telegram alert for CRITICAL anomalies."""
        msg = (
            f"🔥 AMBIENT IOT — ANOMALIE CRITIQUE\n"
            f"├── Device  : {anomaly.device_id} ({anomaly.device_type})\n"
            f"├── Société : {anomaly.company} [{anomaly.sector}]\n"
            f"├── Métrique: {anomaly.metric} = {anomaly.value} (seuil {anomaly.threshold})\n"
            f"├── Déviation: {anomaly.deviation_pct:.1f}%\n"
            f"└── Proposition: {anomaly.audit_proposal_text[:100]}…"
        )
        try:
            from NAYA_CORE.integrations.telegram_notifier import get_notifier
            get_notifier().send(msg)
        except Exception as exc:
            log.warning("AmbientIoTIntelligence: Telegram alert failed: %s", exc)


# ──────────────────────────────────────────────────────────────────────────────
# Singleton
# ──────────────────────────────────────────────────────────────────────────────

_iot: Optional[AmbientIoTIntelligence] = None


def get_ambient_iot_intelligence() -> AmbientIoTIntelligence:
    """Return the process-wide singleton AmbientIoTIntelligence instance."""
    global _iot
    if _iot is None:
        _iot = AmbientIoTIntelligence()
    return _iot
