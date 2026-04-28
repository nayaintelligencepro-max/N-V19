"""
NAYA SUPREME V19.3 — AMELIORATION #8
Auto-Escalation Engine
======================
Escalade intelligente vers la fondatrice Stephanie quand un deal
necessite une intervention humaine.

Unique a NAYA : systeme d'escalade intelligent qui sait QUAND
demander l'aide humaine et priorise les escalades par ROI potentiel.
"""
import time
import logging
import threading
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

log = logging.getLogger("NAYA.ESCALATION")


class EscalationLevel(Enum):
    INFO = "info"           # Notification simple
    ATTENTION = "attention"  # A traiter dans la journee
    URGENT = "urgent"        # A traiter dans l'heure
    CRITICAL = "critical"    # Action immediate requise


class EscalationReason(Enum):
    DEAL_COOLING = "deal_cooling"
    HIGH_VALUE_DEAL = "high_value_deal"
    OBJECTION_COMPLEX = "objection_complex"
    MEETING_REQUESTED = "meeting_requested"
    CONTRACT_READY = "contract_ready"
    PAYMENT_ISSUE = "payment_issue"
    LEGAL_QUESTION = "legal_question"
    VIP_PROSPECT = "vip_prospect"
    SYSTEM_ANOMALY = "system_anomaly"


@dataclass
class EscalationTicket:
    ticket_id: str
    level: EscalationLevel
    reason: EscalationReason
    deal_id: str
    company: str
    amount: float
    summary: str
    recommended_action: str
    context: Dict = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    acknowledged: bool = False
    resolved: bool = False
    resolved_at: float = 0
    resolution_notes: str = ""


class AutoEscalationEngine:
    """
    Moteur d'escalade intelligent qui decide automatiquement
    quand alerter la fondatrice et avec quel niveau de priorite.

    Regles d'escalade :
    1. Deal > 10k EUR en phase negotiation → ATTENTION
    2. Deal > 20k EUR n'importe quel stage → URGENT
    3. Meeting request du prospect → URGENT
    4. Contrat pret a signer → CRITICAL
    5. Paiement echoue → CRITICAL
    6. Objection juridique → ATTENTION
    7. Deal cooling + high value → URGENT
    8. VIP prospect (CEO, CTO, CISO) → ATTENTION
    """

    ESCALATION_RULES = [
        {
            "name": "contract_ready",
            "condition": lambda ctx: ctx.get("stage") == "contract" and ctx.get("amount", 0) >= 1000,
            "level": EscalationLevel.CRITICAL,
            "reason": EscalationReason.CONTRACT_READY,
            "action": "Contrat pret — valider et envoyer pour signature",
        },
        {
            "name": "payment_issue",
            "condition": lambda ctx: ctx.get("payment_failed", False),
            "level": EscalationLevel.CRITICAL,
            "reason": EscalationReason.PAYMENT_ISSUE,
            "action": "Paiement echoue — contacter le client pour resoudre",
        },
        {
            "name": "mega_deal",
            "condition": lambda ctx: ctx.get("amount", 0) >= 20000,
            "level": EscalationLevel.URGENT,
            "reason": EscalationReason.HIGH_VALUE_DEAL,
            "action": "Deal > 20k EUR — attention personnelle requise",
        },
        {
            "name": "meeting_requested",
            "condition": lambda ctx: ctx.get("meeting_requested", False),
            "level": EscalationLevel.URGENT,
            "reason": EscalationReason.MEETING_REQUESTED,
            "action": "Le prospect demande un meeting — repondre rapidement",
        },
        {
            "name": "high_value_negotiation",
            "condition": lambda ctx: (
                ctx.get("stage") == "negotiation" and ctx.get("amount", 0) >= 10000
            ),
            "level": EscalationLevel.ATTENTION,
            "reason": EscalationReason.HIGH_VALUE_DEAL,
            "action": "Deal 10k+ en negotiation — suivi rapproche necessaire",
        },
        {
            "name": "cooling_high_value",
            "condition": lambda ctx: (
                ctx.get("temperature", "warm") in ("cooling", "cold")
                and ctx.get("amount", 0) >= 5000
            ),
            "level": EscalationLevel.URGENT,
            "reason": EscalationReason.DEAL_COOLING,
            "action": "Deal haute valeur refroidit — intervention directe recommandee",
        },
        {
            "name": "legal_question",
            "condition": lambda ctx: ctx.get("has_legal_question", False),
            "level": EscalationLevel.ATTENTION,
            "reason": EscalationReason.LEGAL_QUESTION,
            "action": "Question juridique du prospect — reponse expert necessaire",
        },
        {
            "name": "vip_prospect",
            "condition": lambda ctx: ctx.get("title", "").upper() in ("CEO", "CTO", "CISO", "CFO", "COO"),
            "level": EscalationLevel.ATTENTION,
            "reason": EscalationReason.VIP_PROSPECT,
            "action": "Prospect VIP (C-level) — approche personnalisee requise",
        },
    ]

    def __init__(self):
        self._tickets: List[EscalationTicket] = []
        self._lock = threading.Lock()
        self._total_escalations: int = 0
        self._resolved_count: int = 0

    def evaluate(self, deal_id: str, company: str, amount: float,
                 context: Dict = None) -> List[EscalationTicket]:
        """
        Evalue si un deal necessite une escalade.
        Retourne la liste des tickets d'escalade crees.
        """
        ctx = context or {}
        ctx.setdefault("amount", amount)
        tickets: List[EscalationTicket] = []

        for rule in self.ESCALATION_RULES:
            try:
                if rule["condition"](ctx):
                    ticket_id = f"ESC_{int(time.time())}_{self._total_escalations}"
                    ticket = EscalationTicket(
                        ticket_id=ticket_id,
                        level=rule["level"],
                        reason=rule["reason"],
                        deal_id=deal_id,
                        company=company,
                        amount=amount,
                        summary=f"[{rule['level'].value.upper()}] {company} ({amount:.0f} EUR) — {rule['name']}",
                        recommended_action=rule["action"],
                        context=ctx,
                    )
                    tickets.append(ticket)
                    self._total_escalations += 1

                    log.info(
                        f"[ESCALATION] {ticket.level.value.upper()} — {company} "
                        f"({amount:.0f} EUR): {rule['action']}"
                    )
            except Exception as e:
                log.debug(f"[ESCALATION] Rule {rule['name']} error: {e}")

        with self._lock:
            self._tickets.extend(tickets)
            if len(self._tickets) > 1000:
                self._tickets = self._tickets[-500:]

        return tickets

    def acknowledge(self, ticket_id: str) -> bool:
        """Marque un ticket comme vu."""
        with self._lock:
            for ticket in self._tickets:
                if ticket.ticket_id == ticket_id:
                    ticket.acknowledged = True
                    return True
        return False

    def resolve(self, ticket_id: str, notes: str = "") -> bool:
        """Resout un ticket d'escalade."""
        with self._lock:
            for ticket in self._tickets:
                if ticket.ticket_id == ticket_id:
                    ticket.resolved = True
                    ticket.resolved_at = time.time()
                    ticket.resolution_notes = notes
                    self._resolved_count += 1
                    return True
        return False

    def get_pending(self, level: EscalationLevel = None) -> List[Dict]:
        """Retourne les tickets non resolus."""
        with self._lock:
            pending = [t for t in self._tickets if not t.resolved]
            if level:
                pending = [t for t in pending if t.level == level]
        return [
            {
                "ticket_id": t.ticket_id,
                "level": t.level.value,
                "company": t.company,
                "amount": t.amount,
                "summary": t.summary,
                "action": t.recommended_action,
                "age_hours": round((time.time() - t.created_at) / 3600, 1),
            }
            for t in sorted(pending, key=lambda x: (
                ["critical", "urgent", "attention", "info"].index(x.level.value)
            ))
        ]

    def format_telegram_alert(self, ticket: EscalationTicket) -> str:
        """Formate un ticket pour envoi Telegram."""
        emoji = {"critical": "🚨", "urgent": "⚠️", "attention": "📌", "info": "ℹ️"}
        e = emoji.get(ticket.level.value, "📌")
        return (
            f"{e} *ESCALADE {ticket.level.value.upper()}*\n\n"
            f"🏢 {ticket.company}\n"
            f"💰 {ticket.amount:,.0f} EUR\n"
            f"📋 {ticket.reason.value}\n\n"
            f"👉 *Action:* {ticket.recommended_action}\n"
            f"🔗 Deal ID: `{ticket.deal_id}`"
        )

    def get_stats(self) -> Dict:
        pending = sum(1 for t in self._tickets if not t.resolved)
        return {
            "total_escalations": self._total_escalations,
            "pending": pending,
            "resolved": self._resolved_count,
            "critical_pending": sum(
                1 for t in self._tickets
                if not t.resolved and t.level == EscalationLevel.CRITICAL
            ),
        }


_engine: Optional[AutoEscalationEngine] = None


def get_escalation_engine() -> AutoEscalationEngine:
    global _engine
    if _engine is None:
        _engine = AutoEscalationEngine()
    return _engine
