"""
NAYA V20 — Digital Twin Engine
══════════════════════════════════════════════════════════════════════════════
Creates and maintains behavioural digital twins of each prospect.

DOCTRINE:
  A digital twin accumulates every interaction with a prospect to build a
  predictive behavioural model.  After 5–10 interactions NAYA knows:
    - Which channel the contact actually responds on
    - Which day/hour maximises open rates
    - Whether to write formally or technically
    - How likely the next message is to get a reply

This replaces expensive CRM enrichment and is 100% on-device.
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

log = logging.getLogger("NAYA.DIGITAL_TWIN")

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_FILE = ROOT / "data" / "cache" / "digital_twin_engine.json"

_DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
_TECHNICAL_SECTORS = ("ot", "cybersecurite", "cybersécurité", "it", "scada")


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


@dataclass
class ProspectTwin:
    """Behavioural model of a single prospect."""

    prospect_id: str
    company: str
    contact_name: str
    role: str
    sector: str
    interaction_history: List[Dict] = field(default_factory=list)
    estimated_budget_eur: float = 0.0
    preferred_channel: str = "email"
    best_contact_day: int = 1           # 0=Mon … 6=Sun
    best_contact_hour: int = 10         # 0-23
    communication_style: str = "formal"
    response_rate: float = 0.0
    last_signal_at: str = ""
    twin_confidence: float = 0.0        # 0-1


class DigitalTwinEngine:
    """
    Maintains a registry of ProspectTwin objects, updating them as new
    interaction events arrive.

    Thread-safe singleton.  Persists all twins to DATA_FILE.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._data_file = DATA_FILE
        self._twins: Dict[str, Dict] = {}
        self._load()

    # ──────────────────────────────────────────────────────────────────────
    # Persistence
    # ──────────────────────────────────────────────────────────────────────

    def _load(self) -> None:
        if self._data_file.exists():
            try:
                with open(self._data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._twins = data.get("twins", {})
            except Exception:
                pass

    def _save(self) -> None:
        self._data_file.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            with open(self._data_file, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "twins": self._twins,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    },
                    f,
                    indent=2,
                    ensure_ascii=False,
                )

    # ──────────────────────────────────────────────────────────────────────
    # Business methods
    # ──────────────────────────────────────────────────────────────────────

    def create_twin(
        self,
        prospect_id: str,
        company: str,
        contact_name: str,
        role: str,
        sector: str,
    ) -> ProspectTwin:
        """
        Create a new digital twin (idempotent — returns existing if already created).

        Args:
            prospect_id: Unique identifier for this prospect.
            company: Prospect's company name.
            contact_name: Contact full name.
            role: Job title.
            sector: Industry sector.

        Returns:
            ProspectTwin (new or existing).
        """
        with self._lock:
            if prospect_id not in self._twins:
                twin = ProspectTwin(
                    prospect_id=prospect_id,
                    company=company,
                    contact_name=contact_name,
                    role=role,
                    sector=sector,
                )
                self._twins[prospect_id] = asdict(twin)
        self._save()
        return ProspectTwin(**self._twins[prospect_id])

    def update_behavior(
        self,
        prospect_id: str,
        event_type: str,
        channel: str,
        responded: bool,
        response_sentiment: str = "neutral",
    ) -> None:
        """
        Record an interaction event and update the twin's behavioural model.

        Args:
            prospect_id: Target twin identifier.
            event_type: Interaction label (e.g. "email_sent", "linkedin_message").
            channel: Communication channel used ("email", "linkedin", "phone").
            responded: True if the prospect replied/engaged.
            response_sentiment: Sentiment of the response ("positive", "neutral", "negative").
        """
        with self._lock:
            if prospect_id not in self._twins:
                return
            twin_data = self._twins[prospect_id]
            now = datetime.now(timezone.utc).isoformat()

            twin_data["interaction_history"].append({
                "event_type": event_type,
                "channel": channel,
                "responded": responded,
                "sentiment": response_sentiment,
                "timestamp": now,
            })

            history = twin_data["interaction_history"]
            total = len(history)
            responded_events = [h for h in history if h["responded"]]
            responded_count = len(responded_events)

            # Preferred channel — most common channel where responded=True
            if responded_events:
                channel_counts: Dict[str, int] = {}
                for h in responded_events:
                    channel_counts[h["channel"]] = channel_counts.get(h["channel"], 0) + 1
                twin_data["preferred_channel"] = max(channel_counts, key=lambda c: channel_counts[c])

            # Best contact day and hour from responded interactions
            if responded_events:
                day_counts: Dict[int, int] = {}
                hour_counts: Dict[int, int] = {}
                for h in responded_events:
                    try:
                        dt = datetime.fromisoformat(h["timestamp"])
                        day_counts[dt.weekday()] = day_counts.get(dt.weekday(), 0) + 1
                        hour_counts[dt.hour] = hour_counts.get(dt.hour, 0) + 1
                    except ValueError:
                        continue
                if day_counts:
                    twin_data["best_contact_day"] = max(day_counts, key=lambda d: day_counts[d])
                if hour_counts:
                    twin_data["best_contact_hour"] = max(hour_counts, key=lambda h: hour_counts[h])

            # Response rate
            twin_data["response_rate"] = responded_count / total if total > 0 else 0.0

            # Confidence grows with interactions, caps at 1.0 after 10
            twin_data["twin_confidence"] = min(1.0, total / 10)

            # Communication style
            sector_lower = twin_data.get("sector", "").lower()
            if "technical" in event_type or sector_lower in _TECHNICAL_SECTORS:
                twin_data["communication_style"] = "technical"
            else:
                twin_data["communication_style"] = "formal"

            twin_data["last_signal_at"] = now

    def get_optimal_contact_window(self, prospect_id: str) -> Dict:
        """
        Return the optimal day, hour and channel for the next contact attempt.

        Args:
            prospect_id: Target twin identifier.

        Returns:
            Dict with day (int), day_name (str), hour (int),
            channel (str), confidence (float).
        """
        with self._lock:
            twin_data = self._twins.get(prospect_id)
        if not twin_data:
            return {
                "day": 1, "day_name": "Tue", "hour": 10,
                "channel": "email", "confidence": 0.0,
            }
        day = twin_data["best_contact_day"]
        return {
            "day": day,
            "day_name": _DAY_NAMES[day],
            "hour": twin_data["best_contact_hour"],
            "channel": twin_data["preferred_channel"],
            "confidence": twin_data["twin_confidence"],
        }

    def get_twin(self, prospect_id: str) -> Optional[ProspectTwin]:
        """
        Retrieve a stored twin.

        Args:
            prospect_id: Twin identifier.

        Returns:
            ProspectTwin or None if not found.
        """
        with self._lock:
            data = self._twins.get(prospect_id)
        return ProspectTwin(**data) if data else None

    def get_stats(self) -> Dict:
        """
        Return aggregate statistics for the dashboard.

        Returns:
            Dict with total_twins, avg_confidence, avg_response_rate.
        """
        with self._lock:
            twins = list(self._twins.values())
        total = len(twins)
        avg_conf = sum(t["twin_confidence"] for t in twins) / total if total else 0.0
        avg_rr = sum(t["response_rate"] for t in twins) / total if total else 0.0
        return {
            "total_twins": total,
            "avg_confidence": round(avg_conf, 4),
            "avg_response_rate": round(avg_rr, 4),
        }


# ──────────────────────────────────────────────────────────────────────────────
# Singleton
# ──────────────────────────────────────────────────────────────────────────────

_twin_engine: Optional[DigitalTwinEngine] = None


def get_digital_twin_engine() -> DigitalTwinEngine:
    """Return the process-wide singleton DigitalTwinEngine instance."""
    global _twin_engine
    if _twin_engine is None:
        _twin_engine = DigitalTwinEngine()
    return _twin_engine
