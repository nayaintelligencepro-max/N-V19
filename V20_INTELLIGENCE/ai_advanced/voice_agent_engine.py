"""
NAYA V20 — Voice Agent Engine
══════════════════════════════════════════════════════════════════════════════
Template-based cold call script generator and call log tracker.

DOCTRINE:
  The phone is the fastest closing instrument.  A well-structured 3-minute
  cold call with a personalised OT-pain hook converts at 12–18%.
  This engine generates scripts, logs every attempt and learns the best
  day/hour combination per sector from outcome data.

OUTPUT:
  CallScript — ready-to-read structured script with hook, qualification
               questions, objection responses and CTA.
  call_logs  — outcome data used to optimise future timing.
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

log = logging.getLogger("NAYA.VOICE_AGENT")

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_FILE = ROOT / "data" / "cache" / "voice_agent_engine.json"

POSITIVE_OUTCOMES = ("connected", "meeting_booked")
DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


@dataclass
class CallScript:
    """A personalized cold call script for an OT prospect."""

    script_id: str
    prospect_name: str
    company: str
    sector: str
    opening_hook: str
    qualification_questions: List[str]
    objection_responses: Dict[str, str]
    cta: str
    estimated_duration_s: int


@dataclass
class CallLog:
    """A record of a single call attempt."""

    log_id: str
    script_id: str
    outcome: str       # connected | voicemail | no_answer | meeting_booked | not_interested
    duration_s: int
    notes: str
    called_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class VoiceAgentEngine:
    """
    Generates personalised cold call scripts and tracks call outcomes to
    continuously optimise best-time-to-call per sector.

    Thread-safe singleton.  Persists to DATA_FILE.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._data_file = DATA_FILE
        self._scripts: Dict[str, Dict] = {}
        self._call_logs: List[Dict] = []
        self._load()

    # ──────────────────────────────────────────────────────────────────────
    # Persistence
    # ──────────────────────────────────────────────────────────────────────

    def _load(self) -> None:
        if self._data_file.exists():
            try:
                with open(self._data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._scripts = data.get("scripts", {})
                    self._call_logs = data.get("call_logs", [])
            except Exception:
                pass

    def _save(self) -> None:
        self._data_file.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            with open(self._data_file, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "scripts": self._scripts,
                        "call_logs": self._call_logs,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    },
                    f,
                    indent=2,
                    ensure_ascii=False,
                )

    # ──────────────────────────────────────────────────────────────────────
    # Business methods
    # ──────────────────────────────────────────────────────────────────────

    def create_call_script(
        self,
        prospect_name: str,
        company: str,
        sector: str,
        pain_context: str,
        offer_summary: str,
    ) -> CallScript:
        """
        Generate a personalised cold call script for an OT prospect.

        Args:
            prospect_name: First or full name of the contact.
            company: Prospect's company name.
            sector: Industry sector (e.g. "transport", "energie").
            pain_context: Short description of the detected pain signal.
            offer_summary: Brief description of the offer to propose.

        Returns:
            CallScript with hook, questions, objection answers and CTA.
        """
        script_id = _sha256(prospect_name + company)[:10]

        opening_hook = (
            f"Bonjour {prospect_name}, je vous contacte suite à des signaux "
            f"concernant la cybersécurité OT chez {company}. "
            f"Nous avons aidé des acteurs similaires en {sector} "
            f"à résoudre {pain_context[:50]}."
        )
        qualification_questions = [
            f"Avez-vous un responsable cybersécurité OT dédié chez {company}?",
            "Avez-vous déjà réalisé un audit IEC 62443 ?",
            "Quel est votre horizon de décision pour ce type de projet?",
        ]
        objection_responses = {
            "pas le budget": (
                "Nos audits express à 5k€ s'autofinancent en évitant un seul incident."
            ),
            "déjà un prestataire": (
                "Nous complétons l'existant avec une expertise OT spécialisée."
            ),
            "pas prioritaire": (
                f"Avec NIS2 en vigueur, {company} risque une amende si une attaque "
                "survient sans audit préalable."
            ),
        }
        cta = (
            f"Proposons 20 minutes pour valider si {offer_summary} "
            "correspond à vos enjeux."
        )

        script = CallScript(
            script_id=script_id,
            prospect_name=prospect_name,
            company=company,
            sector=sector,
            opening_hook=opening_hook,
            qualification_questions=qualification_questions,
            objection_responses=objection_responses,
            cta=cta,
            estimated_duration_s=180,
        )

        with self._lock:
            self._scripts[script_id] = asdict(script)
        self._save()
        return script

    def log_call_attempt(
        self,
        script_id: str,
        outcome: str,
        duration_s: int,
        notes: str = "",
    ) -> str:
        """
        Record the outcome of a call attempt.

        Args:
            script_id: ID of the script used for this call.
            outcome: Result label (e.g. "connected", "voicemail", "meeting_booked").
            duration_s: Call duration in seconds.
            notes: Optional free-text notes.

        Returns:
            log_id — unique identifier for this log entry.
        """
        log_id = _sha256(script_id + str(time.time()))[:12]
        call_log = CallLog(
            log_id=log_id,
            script_id=script_id,
            outcome=outcome,
            duration_s=duration_s,
            notes=notes,
        )
        with self._lock:
            self._call_logs.append(asdict(call_log))
        self._save()
        return log_id

    def get_best_call_times(self, sector: str) -> Dict:
        """
        Analyse historical call outcomes for a sector to find optimal call windows.

        Args:
            sector: Industry sector to analyse.

        Returns:
            Dict with best_day (name), best_hour (int 0-23), sample_size (int).
            Defaults to Tuesday at 10:00 if no data available.
        """
        with self._lock:
            logs = list(self._call_logs)

        # Filter to positive outcomes for scripts in this sector
        sector_script_ids = {
            sid
            for sid, s in self._scripts.items()
            if s.get("sector", "") == sector
        }
        successful = [
            lg for lg in logs
            if lg["outcome"] in POSITIVE_OUTCOMES
            and lg["script_id"] in sector_script_ids
        ]

        if not successful:
            return {"best_day": "Tuesday", "best_hour": 10, "sample_size": 0}

        day_counts: Dict[int, int] = {}
        hour_counts: Dict[int, int] = {}

        for lg in successful:
            try:
                dt = datetime.fromisoformat(lg["called_at"])
                day_counts[dt.weekday()] = day_counts.get(dt.weekday(), 0) + 1
                hour_counts[dt.hour] = hour_counts.get(dt.hour, 0) + 1
            except ValueError:
                continue

        best_day_idx = max(day_counts, key=lambda d: day_counts[d])
        best_hour = max(hour_counts, key=lambda h: hour_counts[h])

        return {
            "best_day": DAY_NAMES[best_day_idx],
            "best_hour": best_hour,
            "sample_size": len(successful),
        }

    def get_stats(self) -> Dict:
        """
        Return high-level statistics for dashboard display.

        Returns:
            Dict with total_scripts, total_calls, connection_rate.
        """
        with self._lock:
            total_scripts = len(self._scripts)
            total_calls = len(self._call_logs)
            connected = sum(
                1 for lg in self._call_logs if lg["outcome"] in POSITIVE_OUTCOMES
            )
        connection_rate = connected / total_calls if total_calls > 0 else 0.0
        return {
            "total_scripts": total_scripts,
            "total_calls": total_calls,
            "connection_rate": round(connection_rate, 4),
        }


# ──────────────────────────────────────────────────────────────────────────────
# Singleton
# ──────────────────────────────────────────────────────────────────────────────

_voice_engine: Optional[VoiceAgentEngine] = None


def get_voice_agent_engine() -> VoiceAgentEngine:
    """Return the process-wide singleton VoiceAgentEngine instance."""
    global _voice_engine
    if _voice_engine is None:
        _voice_engine = VoiceAgentEngine()
    return _voice_engine
