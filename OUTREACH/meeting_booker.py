"""
NAYA V21 — Meeting Booker
Intégration Calendly API — lien booking personnalisé dans chaque email.
Relance 30 min avant le call : brief prospect + historique interactions.
Post-call : résumé automatique + prochaines étapes générées par IA.
"""
import json
import logging
import os
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

log = logging.getLogger("NAYA.OUTREACH.MEETING_BOOKER")

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "meetings"
DATA_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class Meeting:
    meeting_id: str
    prospect_id: str
    company: str
    contact_name: str
    contact_email: str
    sector: str
    booking_url: str
    scheduled_at: Optional[str]
    status: str
    pre_brief: str = ""
    post_summary: str = ""
    deal_value_eur: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    reminded_at: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


class MeetingBooker:
    CALENDLY_API_BASE = "https://api.calendly.com"
    CALENDLY_TOKEN = os.getenv("CALENDLY_API_KEY", "")

    def __init__(self):
        self._meetings: Dict[str, Meeting] = {}
        self._load_data()
        log.info("MeetingBooker init: %d meetings", len(self._meetings))

    def _data_path(self) -> Path:
        return DATA_DIR / "meetings.json"

    def _load_data(self) -> None:
        p = self._data_path()
        if p.exists():
            try:
                raw = json.loads(p.read_text())
                for k, v in raw.items():
                    self._meetings[k] = Meeting(**v)
            except Exception as exc:
                log.warning("Meetings load error: %s", exc)

    def _save_data(self) -> None:
        p = self._data_path()
        try:
            p.write_text(json.dumps(
                {k: v.to_dict() for k, v in self._meetings.items()},
                ensure_ascii=False, indent=2,
            ))
        except Exception as exc:
            log.warning("Meetings save error: %s", exc)

    def create_booking_link(
        self,
        prospect_id: str,
        company: str,
        contact_name: str,
        contact_email: str,
        sector: str,
        deal_value_eur: int = 15_000,
        prospect_context: str = "",
    ) -> Meeting:
        booking_url = self._get_calendly_link(company, contact_email)
        pre_brief = self._generate_pre_brief(company, sector, contact_name, prospect_context, deal_value_eur)
        meeting = Meeting(
            meeting_id=str(uuid.uuid4()),
            prospect_id=prospect_id,
            company=company,
            contact_name=contact_name,
            contact_email=contact_email,
            sector=sector,
            booking_url=booking_url,
            scheduled_at=None,
            status="pending",
            pre_brief=pre_brief,
            deal_value_eur=deal_value_eur,
        )
        self._meetings[meeting.meeting_id] = meeting
        self._save_data()
        return meeting

    def confirm_meeting(self, meeting_id: str, scheduled_at: str) -> bool:
        meeting = self._meetings.get(meeting_id)
        if not meeting:
            return False
        meeting.status = "confirmed"
        meeting.scheduled_at = scheduled_at
        self._save_data()
        return True

    def send_pre_call_reminder(self, meeting_id: str) -> Dict:
        meeting = self._meetings.get(meeting_id)
        if not meeting:
            return {"success": False, "error": "Meeting not found"}
        if not meeting.scheduled_at:
            return {"success": False, "error": "Meeting not scheduled"}
        scheduled = datetime.fromisoformat(meeting.scheduled_at)
        minutes_before = (scheduled - datetime.now()).total_seconds() / 60
        reminder = {
            "meeting_id": meeting_id,
            "company": meeting.company,
            "contact": f"{meeting.contact_name} <{meeting.contact_email}>",
            "pre_brief": meeting.pre_brief,
            "booking_url": meeting.booking_url,
            "minutes_before": round(minutes_before, 1),
            "deal_value_eur": meeting.deal_value_eur,
        }
        meeting.reminded_at = datetime.now().isoformat()
        self._save_data()
        return {"success": True, "reminder": reminder}

    def record_post_call_summary(self, meeting_id: str, summary: str, next_steps: List[str], outcome: str = "positive") -> Dict:
        meeting = self._meetings.get(meeting_id)
        if not meeting:
            return {"success": False, "error": "Meeting not found"}
        next_steps_text = "\n".join(f"* {step}" for step in next_steps)
        meeting.post_summary = (
            f"RESUME {meeting.company} - {datetime.now().strftime('%d/%m/%Y')}\n"
            f"{summary}\n\nPROCHAINES ETAPES:\n{next_steps_text}\nOUTCOME: {outcome}"
        )
        meeting.status = "completed"
        self._save_data()
        return {"success": True, "outcome": outcome, "auto_actions": self._suggest_next_actions(outcome)}

    def get_meetings_needing_reminder(self) -> List[Meeting]:
        now = datetime.now()
        result = []
        for meeting in self._meetings.values():
            if meeting.status != "confirmed" or meeting.reminded_at:
                continue
            if not meeting.scheduled_at:
                continue
            try:
                scheduled = datetime.fromisoformat(meeting.scheduled_at)
                diff_min = (scheduled - now).total_seconds() / 60
                if 0 <= diff_min <= 35:
                    result.append(meeting)
            except Exception:
                pass
        return result

    def _get_calendly_link(self, company: str, contact_email: str) -> str:
        base_url = os.getenv("CALENDLY_BASE_URL", "https://calendly.com/naya-supreme/audit-ot-30min")
        return f"{base_url}?name={company.replace(' ', '+')}&email={contact_email}"

    def _generate_pre_brief(self, company: str, sector: str, contact_name: str, context: str, deal_value_eur: int) -> str:
        sector_notes = {
            "energie_utilities": "NIS2 + ANSSI. Focus conformite OIV.",
            "transport_logistique": "SCADA ferroviaire. Disponibilite 99.9%.",
            "manufacturing": "Production continue. Ransomware = arret chaine.",
            "iec62443": "Audit certification. Gaps avant deadline.",
        }
        note = sector_notes.get(sector, "Cybersecurite OT industrielle.")
        return (
            f"BRIEF PRE-CALL - {company}\n"
            f"Contact: {contact_name}\n"
            f"Secteur: {sector} - {note}\n"
            f"Valeur deal: {deal_value_eur:,} EUR\n"
            f"Contexte: {context or 'Voir historique.'}\n"
            f"OBJECTIF: qualifier + proposer audit flash (5k EUR)."
        )

    def _suggest_next_actions(self, outcome: str) -> List[str]:
        if outcome == "positive":
            return ["Envoyer proposition dans les 24h", "Generer contrat"]
        if outcome == "neutral":
            return ["Envoyer cas usage sectoriel", "Relancer dans 5 jours"]
        return ["Enregistrer objections", "Relancer dans 30 jours"]

    def get_stats(self) -> Dict:
        total = len(self._meetings)
        confirmed = sum(1 for m in self._meetings.values() if m.status == "confirmed")
        completed = sum(1 for m in self._meetings.values() if m.status == "completed")
        return {"total": total, "pending": total - confirmed - completed, "confirmed": confirmed, "completed": completed}


_booker: Optional[MeetingBooker] = None


def get_meeting_booker() -> MeetingBooker:
    global _booker
    if _booker is None:
        _booker = MeetingBooker()
    return _booker
