"""
NAYA V19 - Stealth Operations Engine
Mode furtif reel: masque l origine geographique, anonymise les interactions,
efface les traces apres chaque operation.
"""
import logging, time, hashlib, uuid, os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

log = logging.getLogger("NAYA.STEALTH")

@dataclass
class StealthSession:
    session_id: str
    persona_name: str
    persona_email: str
    origin_masked: bool = True
    traces: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    cleaned: bool = False

class StealthOperationsEngine:
    """Operations furtives - confidentialite geographique et operationnelle."""

    PERSONAS = [
        {"name": "Alexandre Duval", "domain": "consulting-digital.fr", "role": "Consultant Senior"},
        {"name": "Marie Laurent", "domain": "tech-advisory.eu", "role": "Directrice Innovation"},
        {"name": "Thomas Bernard", "domain": "strategie-business.com", "role": "Partner"},
        {"name": "Sophie Martin", "domain": "performance-group.io", "role": "CEO"},
        {"name": "Pierre Leroy", "domain": "digital-solutions.pro", "role": "Managing Director"},
    ]

    def __init__(self):
        self._sessions: Dict[str, StealthSession] = {}
        self._persona_rotation = 0
        self._total_ops = 0
        self._total_cleaned = 0

    def create_stealth_session(self, operation_type: str = "outreach") -> StealthSession:
        """Cree une session furtive avec persona et masquage."""
        persona = self._get_next_persona()
        session_id = f"STEALTH_{uuid.uuid4().hex[:10].upper()}"

        session = StealthSession(
            session_id=session_id,
            persona_name=persona["name"],
            persona_email=f"{persona['name'].lower().replace(' ', '.')}@{persona['domain']}",
            origin_masked=True
        )
        self._sessions[session_id] = session
        self._total_ops += 1
        log.debug(f"[STEALTH] Session {session_id} creee: {persona['name']}")
        return session

    def mask_origin(self, metadata: Dict) -> Dict:
        """Masque l origine geographique dans les metadata."""
        masked = metadata.copy()
        FIELDS_TO_MASK = ["ip", "location", "city", "country", "timezone",
                          "latitude", "longitude", "region", "postal_code"]
        for field in FIELDS_TO_MASK:
            if field in masked:
                masked[field] = "[MASKED]"
        masked.pop("x-forwarded-for", None)
        masked.pop("x-real-ip", None)
        # Replace with neutral location
        masked["apparent_location"] = "Paris, France"
        masked["apparent_timezone"] = "Europe/Paris"
        return masked

    def anonymize_interaction(self, interaction: Dict, session_id: str = None) -> Dict:
        """Anonymise une interaction avec un prospect."""
        session = self._sessions.get(session_id) if session_id else None
        anon = interaction.copy()

        # Remplacer les identifiants systeme
        anon.pop("system_id", None)
        anon.pop("internal_ref", None)
        anon.pop("naya_id", None)

        # Injecter la persona
        if session:
            anon["sender_name"] = session.persona_name
            anon["sender_email"] = session.persona_email
            session.traces.append(f"interaction_{time.time()}")

        return anon

    def clean_traces(self, session_id: str) -> Dict:
        """Efface toutes les traces d une session apres operation."""
        session = self._sessions.get(session_id)
        if not session:
            return {"cleaned": False, "reason": "session not found"}

        traces_count = len(session.traces)
        session.traces.clear()
        session.cleaned = True
        self._total_cleaned += 1

        log.info(f"[STEALTH] Session {session_id}: {traces_count} traces effacees")
        return {
            "cleaned": True,
            "session_id": session_id,
            "traces_removed": traces_count,
            "timestamp": time.time()
        }

    def clean_all_completed(self) -> int:
        """Nettoie toutes les sessions terminees."""
        cleaned = 0
        for sid, session in list(self._sessions.items()):
            age_h = (time.time() - session.created_at) / 3600
            if age_h > 24 or session.cleaned:
                self.clean_traces(sid)
                del self._sessions[sid]
                cleaned += 1
        return cleaned

    def _get_next_persona(self) -> Dict:
        persona = self.PERSONAS[self._persona_rotation % len(self.PERSONAS)]
        self._persona_rotation += 1
        return persona

    def generate_signature(self, session_id: str) -> Dict:
        """Genere une signature professionnelle pour la persona active."""
        session = self._sessions.get(session_id)
        if not session:
            return {}
        persona = None
        for p in self.PERSONAS:
            if p["name"] == session.persona_name:
                persona = p
                break
        if not persona:
            return {}
        return {
            "name": persona["name"],
            "role": persona["role"],
            "email": session.persona_email,
            "phone": "+33 1 XX XX XX XX",
            "company": persona["domain"].split(".")[0].replace("-", " ").title()
        }

    def get_stats(self) -> Dict:
        active = sum(1 for s in self._sessions.values() if not s.cleaned)
        return {
            "total_operations": self._total_ops,
            "active_sessions": active,
            "total_cleaned": self._total_cleaned,
            "personas_available": len(self.PERSONAS)
        }

_stealth = None
def get_stealth_engine():
    global _stealth
    if _stealth is None:
        _stealth = StealthOperationsEngine()
    return _stealth
