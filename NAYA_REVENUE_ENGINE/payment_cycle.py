"""
NAYA V19 - Payment Cycle Manager
Suivi automatique des paiements, relances automatiques si impayes,
reconciliation et reporting.
"""
import os, time, logging, uuid, json, threading
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

log = logging.getLogger("NAYA.PAYMENT.CYCLE")

class PaymentStatus(Enum):
    PENDING = "pending"
    SENT = "sent"          # Lien de paiement envoye
    PARTIAL = "partial"     # Paiement partiel recu
    PAID = "paid"           # Paye integralement
    OVERDUE = "overdue"     # En retard
    DISPUTED = "disputed"   # Litige
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

@dataclass
class PaymentRecord:
    payment_id: str
    prospect_id: str
    prospect_name: str
    amount_eur: float
    amount_paid: float = 0.0
    status: PaymentStatus = PaymentStatus.PENDING
    payment_method: str = "paypal"  # paypal, deblock, bank_transfer
    payment_link: str = ""
    invoice_ref: str = ""
    due_date: float = 0.0
    created_at: float = field(default_factory=time.time)
    paid_at: Optional[float] = None
    reminders_sent: int = 0
    max_reminders: int = 3
    notes: str = ""

PAYMENT_FILE = Path("data/cache/payments.json")

class PaymentCycleManager:
    """Gere le cycle complet de paiement: creation -> suivi -> relance -> reconciliation."""

    PAYPAL_ME = os.environ.get("PAYPAL_ME_URL", "https://www.paypal.me/Myking987")
    DEBLOCK_URL = os.environ.get("DEBLOCK_ME_URL", "https://deblock.com/a-ftp860")
    REMINDER_INTERVALS_H = [24, 72, 168]  # 1 jour, 3 jours, 7 jours

    def __init__(self):
        self._payments: Dict[str, PaymentRecord] = {}
        self._lock = threading.RLock()
        self._total_invoiced = 0.0
        self._total_collected = 0.0
        self._total_outstanding = 0.0
        self._load()

    def create_payment(self, prospect_id: str, prospect_name: str,
                       amount: float, method: str = "paypal",
                       due_days: int = 3) -> PaymentRecord:
        """Cree un nouveau paiement a suivre."""
        pid = f"PAY_{uuid.uuid4().hex[:8].upper()}"
        link = self.PAYPAL_ME if method == "paypal" else self.DEBLOCK_URL
        record = PaymentRecord(
            payment_id=pid,
            prospect_id=prospect_id,
            prospect_name=prospect_name,
            amount_eur=amount,
            payment_method=method,
            payment_link=f"{link}/{amount}",
            invoice_ref=f"INV-{pid}",
            due_date=time.time() + (due_days * 86400)
        )
        with self._lock:
            self._payments[pid] = record
            self._total_invoiced += amount
            self._total_outstanding += amount
        self._save()
        log.info(f"[PAYMENT] Cree: {pid} | {amount}EUR | {prospect_name} | {method}")
        return record

    def record_payment(self, payment_id: str, amount_received: float) -> Dict:
        """Enregistre un paiement recu (partiel ou complet)."""
        with self._lock:
            record = self._payments.get(payment_id)
            if not record:
                return {"error": "payment_not_found"}
            record.amount_paid += amount_received
            self._total_collected += amount_received
            self._total_outstanding -= amount_received
            if record.amount_paid >= record.amount_eur:
                record.status = PaymentStatus.PAID
                record.paid_at = time.time()
                log.info(f"[PAYMENT] PAYE: {payment_id} | {record.amount_eur}EUR")
            else:
                record.status = PaymentStatus.PARTIAL
                log.info(f"[PAYMENT] Partiel: {payment_id} | {record.amount_paid}/{record.amount_eur}EUR")
        self._save()
        return {"status": record.status.value, "paid": record.amount_paid, "remaining": record.amount_eur - record.amount_paid}

    def check_overdue(self) -> List[PaymentRecord]:
        """Identifie les paiements en retard."""
        overdue = []
        now = time.time()
        with self._lock:
            for record in self._payments.values():
                if record.status in (PaymentStatus.PENDING, PaymentStatus.SENT, PaymentStatus.PARTIAL):
                    if now > record.due_date:
                        record.status = PaymentStatus.OVERDUE
                        overdue.append(record)
        if overdue:
            self._save()
        return overdue

    def generate_reminder(self, payment_id: str) -> Optional[Dict]:
        """Genere un rappel de paiement si applicable."""
        with self._lock:
            record = self._payments.get(payment_id)
            if not record:
                return None
            if record.status == PaymentStatus.PAID:
                return None
            if record.reminders_sent >= record.max_reminders:
                return {"action": "escalate", "message": "Max relances atteint - action manuelle requise"}
            record.reminders_sent += 1
            remaining = record.amount_eur - record.amount_paid
            reminder = {
                "to": record.prospect_name,
                "subject": f"Rappel: Facture {record.invoice_ref} - {remaining:.0f} EUR",
                "body": (
                    f"Bonjour {record.prospect_name},\n\n"
                    f"Nous vous rappelons que la facture {record.invoice_ref} "
                    f"d un montant de {remaining:.0f} EUR est en attente de reglement.\n\n"
                    f"Lien de paiement: {record.payment_link}\n\n"
                    f"Merci de votre confiance.\n"
                    f"Cordialement"
                ),
                "payment_link": record.payment_link,
                "reminder_number": record.reminders_sent,
                "amount_due": remaining
            }
        self._save()
        log.info(f"[PAYMENT] Relance #{record.reminders_sent} pour {payment_id}")
        return reminder

    def get_reconciliation_report(self) -> Dict:
        """Rapport de reconciliation financiere."""
        with self._lock:
            by_status = {}
            by_method = {}
            for r in self._payments.values():
                by_status[r.status.value] = by_status.get(r.status.value, 0) + 1
                by_method[r.payment_method] = by_method.get(r.payment_method, 0) + r.amount_paid
            return {
                "total_invoiced": self._total_invoiced,
                "total_collected": self._total_collected,
                "total_outstanding": self._total_outstanding,
                "collection_rate": self._total_collected / self._total_invoiced if self._total_invoiced > 0 else 0,
                "by_status": by_status,
                "by_method": by_method,
                "overdue_count": sum(1 for r in self._payments.values() if r.status == PaymentStatus.OVERDUE),
                "total_payments": len(self._payments)
            }

    def _save(self):
        try:
            PAYMENT_FILE.parent.mkdir(parents=True, exist_ok=True)
            data = {}
            with self._lock:
                for pid, r in self._payments.items():
                    data[pid] = {
                        "payment_id": r.payment_id, "prospect_id": r.prospect_id,
                        "prospect_name": r.prospect_name, "amount_eur": r.amount_eur,
                        "amount_paid": r.amount_paid, "status": r.status.value,
                        "method": r.payment_method, "created_at": r.created_at,
                        "paid_at": r.paid_at, "reminders": r.reminders_sent
                    }
            PAYMENT_FILE.write_text(json.dumps(data, indent=2))
        except Exception as e:
            log.debug(f"[PAYMENT] Save: {e}")

    def _load(self):
        try:
            if PAYMENT_FILE.exists():
                data = json.loads(PAYMENT_FILE.read_text())
                for pid, d in data.items():
                    self._payments[pid] = PaymentRecord(
                        payment_id=d["payment_id"], prospect_id=d["prospect_id"],
                        prospect_name=d["prospect_name"], amount_eur=d["amount_eur"],
                        amount_paid=d.get("amount_paid", 0),
                        status=PaymentStatus(d.get("status", "pending")),
                        payment_method=d.get("method", "paypal"),
                        created_at=d.get("created_at", 0),
                        paid_at=d.get("paid_at"), reminders_sent=d.get("reminders", 0)
                    )
                    self._total_invoiced += d["amount_eur"]
                    self._total_collected += d.get("amount_paid", 0)
                    self._total_outstanding += d["amount_eur"] - d.get("amount_paid", 0)
                log.info(f"[PAYMENT] {len(self._payments)} paiements charges")
        except Exception as e:
            log.debug(f"[PAYMENT] Load: {e}")

    def get_stats(self) -> Dict:
        return self.get_reconciliation_report()

_mgr = None
_mgr_lock = threading.Lock()
def get_payment_cycle():
    global _mgr
    if _mgr is None:
        with _mgr_lock:
            if _mgr is None:
                _mgr = PaymentCycleManager()
    return _mgr
