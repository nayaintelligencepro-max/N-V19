"""
NAYA V20 — AR OT Assessment
══════════════════════════════════════════════════════════════════════════════
HoloLens 2 compatible AR-assisted OT equipment assessment.

DOCTRINE:
  Traditional OT asset inventories take 2–3 days and require multiple site
  visits.  With AR-assisted scanning, a technician walks through a plant
  floor and NAYA identifies every PLC, HMI and historian in real time —
  matching against known vulnerability databases.

  Assessment time: 4 hours per plant (vs. 2–3 days traditional)
  Revenue model: €2,500 per equipment scan session + full audit upsell

  HoloLens 2 integration: frame data is sent from the device to this engine
  via a local REST API; vulnerability overlays are returned for display.

EQUIPMENT DATABASE:
  Siemens, Schneider, Rockwell, ABB, Honeywell
  (default vulnerabilities from public ICS-CERT advisories)
══════════════════════════════════════════════════════════════════════════════
"""
import hashlib
import json
import logging
import threading
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

log = logging.getLogger("NAYA.AR_OT_ASSESSMENT")

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_FILE = ROOT / "data" / "cache" / "ar_ot_assessment.json"

KNOWN_OT_EQUIPMENT: Dict[str, Dict] = {
    "Siemens": {
        "products": ["S7-300", "S7-400", "S7-1200", "S7-1500", "WinCC"],
        "default_vulns": ["Default credentials", "Unencrypted Profinet"],
    },
    "Schneider": {
        "products": ["Modicon M340", "Modicon M580", "EcoStruxure"],
        "default_vulns": ["CVE-2022-24323", "Unencrypted Modbus"],
    },
    "Rockwell": {
        "products": ["CompactLogix", "ControlLogix", "FactoryTalk"],
        "default_vulns": ["EtherNet/IP vulnerabilities", "Legacy firmware"],
    },
    "ABB": {
        "products": ["AC500", "Symphony Plus"],
        "default_vulns": ["Default SSH keys", "Outdated firmware"],
    },
    "Honeywell": {
        "products": ["Experion", "Uniformance"],
        "default_vulns": ["CVE-2021-38397", "Unencrypted historian"],
    },
}


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


@dataclass
class EquipmentDetection:
    """A single piece of OT equipment identified in an AR scan frame."""

    equipment_id: str
    vendor: str
    product: str
    firmware_hint: str
    location_hint: str
    vulnerabilities: List[str]
    risk_level: str              # HIGH | MEDIUM | LOW


@dataclass
class ARSession:
    """An active AR scanning session at an industrial site."""

    session_id: str
    company: str
    site_name: str
    technician_name: str
    status: str                  # ACTIVE | COMPLETED
    equipment_detected: List[EquipmentDetection] = field(default_factory=list)
    vulnerabilities_found: int = 0
    started_at: str = ""
    estimated_value_eur: float = 0.0

    def __post_init__(self) -> None:
        if not self.started_at:
            self.started_at = datetime.now(timezone.utc).isoformat()


@dataclass
class ARReport:
    """Final assessment report generated from a completed AR session."""

    report_id: str
    session_id: str
    company: str
    equipment_count: int
    critical_vulns: int
    total_vulnerabilities: int
    risk_score: int              # 0-100
    summary: str
    recommendations: List[str]
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AROTAssessment:
    """
    Manages AR scanning sessions, ingests frame data from HoloLens 2 devices,
    and generates real-time and final OT vulnerability reports.

    Thread-safe singleton.  Persists all sessions to DATA_FILE.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._data_file = DATA_FILE
        self._sessions: Dict[str, Dict] = {}
        self._load()

    # ──────────────────────────────────────────────────────────────────────
    # Persistence
    # ──────────────────────────────────────────────────────────────────────

    def _load(self) -> None:
        if self._data_file.exists():
            try:
                with open(self._data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._sessions = data.get("sessions", {})
            except Exception:
                pass

    def _save(self) -> None:
        self._data_file.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            with open(self._data_file, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "sessions": self._sessions,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    },
                    f,
                    indent=2,
                    ensure_ascii=False,
                )

    # ──────────────────────────────────────────────────────────────────────
    # Equipment matching
    # ──────────────────────────────────────────────────────────────────────

    def _match_vendor(self, label: str) -> Optional[str]:
        """Return the matching vendor name if a vendor key appears in label."""
        label_lower = label.lower()
        for vendor in KNOWN_OT_EQUIPMENT:
            if vendor.lower() in label_lower:
                return vendor
        return None

    def _match_product(self, vendor: str, label: str) -> str:
        """Return the most specific product name found in label, else return label."""
        for product in KNOWN_OT_EQUIPMENT[vendor]["products"]:
            if product.lower() in label.lower():
                return product
        return label

    # ──────────────────────────────────────────────────────────────────────
    # Report helper
    # ──────────────────────────────────────────────────────────────────────

    def _generate_report(self, session: ARSession) -> ARReport:
        """
        Build an ARReport from the current session state.

        Args:
            session: The ARSession to report on.

        Returns:
            ARReport with risk score, summary and recommendations.
        """
        report_id = _sha256(session.session_id + str(time.time()))[:12]
        eq_count = len(session.equipment_detected)
        total_vulns = session.vulnerabilities_found
        risk_score = min(100, total_vulns * 10)

        critical_vulns = sum(
            1 for eq in session.equipment_detected if eq.risk_level == "HIGH"
        )

        summary = (
            f"Scan AR site {session.site_name} ({session.company}): "
            f"{eq_count} équipements détectés, {total_vulns} vulnérabilités, "
            f"score de risque {risk_score}/100."
        )

        recommendations = [
            "Segmenter les équipements à risque élevé du réseau corporate.",
            "Changer les credentials par défaut sur tous les équipements identifiés.",
            "Planifier un audit IEC 62443 complet du site.",
        ]
        if critical_vulns > 0:
            recommendations.insert(
                0,
                f"PRIORITÉ: {critical_vulns} équipement(s) HIGH — action corrective immédiate."
            )

        return ARReport(
            report_id=report_id,
            session_id=session.session_id,
            company=session.company,
            equipment_count=eq_count,
            critical_vulns=critical_vulns,
            total_vulnerabilities=total_vulns,
            risk_score=risk_score,
            summary=summary,
            recommendations=recommendations,
        )

    # ──────────────────────────────────────────────────────────────────────
    # Business methods
    # ──────────────────────────────────────────────────────────────────────

    def create_session(
        self,
        session_id: str,
        company: str,
        site_name: str,
        technician_name: str,
    ) -> ARSession:
        """
        Open a new AR scanning session.

        Args:
            session_id: Unique session identifier (e.g. device + timestamp hash).
            company: Client company name.
            site_name: Industrial site name or identifier.
            technician_name: Name of the technician conducting the scan.

        Returns:
            New ARSession with ACTIVE status.
        """
        session = ARSession(
            session_id=session_id,
            company=company,
            site_name=site_name,
            technician_name=technician_name,
            status="ACTIVE",
        )
        with self._lock:
            self._sessions[session_id] = {
                **asdict(session),
                "equipment_detected": [],
            }
        self._save()
        return session

    def ingest_ar_frame(
        self, session_id: str, frame_data: Dict
    ) -> List[EquipmentDetection]:
        """
        Process a single AR camera frame and extract equipment detections.

        Args:
            session_id: Target session identifier.
            frame_data: Dict with keys:
                        - equipment_labels: List[str] — labels seen in the frame
                        - location: str — location hint (e.g. "Bay A / Rack 3")

        Returns:
            List of EquipmentDetection objects found in this frame.

        Raises:
            ValueError: If session_id is not found.
        """
        with self._lock:
            session_data = self._sessions.get(session_id)
        if not session_data:
            raise ValueError(f"Session '{session_id}' not found.")

        location = frame_data.get("location", "unknown")
        labels = frame_data.get("equipment_labels", [])
        detections: List[EquipmentDetection] = []

        for label in labels:
            vendor = self._match_vendor(label)
            if not vendor:
                continue

            product = self._match_product(vendor, label)
            vulns = list(KNOWN_OT_EQUIPMENT[vendor]["default_vulns"])
            risk_level = "HIGH" if len(vulns) >= 2 else ("MEDIUM" if len(vulns) == 1 else "LOW")

            eq_id = _sha256(session_id + label + location)[:12]
            detection = EquipmentDetection(
                equipment_id=eq_id,
                vendor=vendor,
                product=product,
                firmware_hint="unknown",
                location_hint=location,
                vulnerabilities=vulns,
                risk_level=risk_level,
            )
            detections.append(detection)

        # Update session
        with self._lock:
            for det in detections:
                self._sessions[session_id]["equipment_detected"].append(asdict(det))
            total_vulns = sum(
                len(eq["vulnerabilities"])
                for eq in self._sessions[session_id]["equipment_detected"]
            )
            self._sessions[session_id]["vulnerabilities_found"] = total_vulns
            eq_count = len(self._sessions[session_id]["equipment_detected"])
            self._sessions[session_id]["estimated_value_eur"] = eq_count * 2_500

        self._save()
        return detections

    def generate_live_report(self, session_id: str) -> ARReport:
        """
        Generate a non-finalising live snapshot report from the current session.

        Args:
            session_id: Target session identifier.

        Returns:
            ARReport reflecting current scan state.
        """
        with self._lock:
            session_data = self._sessions.get(session_id)
        if not session_data:
            raise ValueError(f"Session '{session_id}' not found.")
        session = self._session_from_data(session_data)
        return self._generate_report(session)

    def finalize_session(self, session_id: str) -> ARReport:
        """
        Mark a session as completed and return the final report.

        Args:
            session_id: Target session identifier.

        Returns:
            Final ARReport.
        """
        with self._lock:
            if session_id not in self._sessions:
                raise ValueError(f"Session '{session_id}' not found.")
            self._sessions[session_id]["status"] = "COMPLETED"
            session_data = self._sessions[session_id]
        self._save()
        session = self._session_from_data(session_data)
        return self._generate_report(session)

    @staticmethod
    def _session_from_data(data: Dict) -> ARSession:
        """Reconstruct an ARSession from its dict representation."""
        raw_eq = data.get("equipment_detected", [])
        equipment = [EquipmentDetection(**eq) for eq in raw_eq]
        return ARSession(
            session_id=data["session_id"],
            company=data["company"],
            site_name=data["site_name"],
            technician_name=data["technician_name"],
            status=data["status"],
            equipment_detected=equipment,
            vulnerabilities_found=data.get("vulnerabilities_found", 0),
            started_at=data.get("started_at", ""),
            estimated_value_eur=data.get("estimated_value_eur", 0.0),
        )

    def get_stats(self) -> Dict:
        """
        Return aggregate statistics for the dashboard.

        Returns:
            Dict with total_sessions, completed_sessions, total_equipment_scanned.
        """
        with self._lock:
            sessions = list(self._sessions.values())
        total = len(sessions)
        completed = sum(1 for s in sessions if s["status"] == "COMPLETED")
        total_eq = sum(len(s.get("equipment_detected", [])) for s in sessions)
        return {
            "total_sessions": total,
            "completed_sessions": completed,
            "total_equipment_scanned": total_eq,
        }


# ──────────────────────────────────────────────────────────────────────────────
# Singleton
# ──────────────────────────────────────────────────────────────────────────────

_ar_assessment: Optional[AROTAssessment] = None


def get_ar_ot_assessment() -> AROTAssessment:
    """Return the process-wide singleton AROTAssessment instance."""
    global _ar_assessment
    if _ar_assessment is None:
        _ar_assessment = AROTAssessment()
    return _ar_assessment
