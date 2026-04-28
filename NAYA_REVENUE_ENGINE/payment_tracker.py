"""
NAYA V19 - Payment Tracker
Suivi automatique des paiements recus, relance si impaye, reconciliation.
"""
import time, logging, json, uuid, threading
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum

log = logging.getLogger("NAYA.PAYMENT.TRACKER")
PAYMENTS_FILE = Path("data/cache/payments_ledger.json")

class PaymentStatus(Enum):
    PENDING = "pending"
    PARTIAL = "partial"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

@dataclass
class PaymentRecord:
    payment_id: str
    opportunity_id: str
    prospect_name: str
    amount_eur: float
    amount_paid: float = 0.0
    status: PaymentStatus = PaymentStatus.PENDING
    payment_method: str = "paypal"
    invoice_date: float = field(default_factory=time.time)
    due_date: float = 0.0
    paid_date: Optional[float] = None
    reminders_sent: int = 0
    max_reminders: int = 3
    notes: str = ""

class PaymentTracker:
    """Suivi complet du cycle de paiement: facturation -> encaissement -> relance."""

    PAYMENT_METHODS = {
        "paypal": {"url_template": "https://www.paypal.me/Myking987/{amount}"},
        "deblock": {"url_template": "https://deblock.com/a-ftp860"},
    }
    OVERDUE_DAYS = 7
    REMINDER_INTERVAL_DAYS = 3

    def __init__(self):
        self._payments: Dict[str, PaymentRecord] = {}
        self._lock = threading.RLock()
        self._total_invoiced = 0.0
        self._total_collected = 0.0
        self._load()

    def create_invoice(self, opp_id: str, prospect: str, amount: float,
                       method: str = "paypal", due_days: int = 7) -> PaymentRecord:
        """Cree une facture/demande de paiement."""
        pid = f"PAY_{uuid.uuid4().hex[:8].upper()}"
        record = PaymentRecord(
            payment_id=pid,
            opportunity_id=opp_id,
            prospect_name=prospect,
            amount_eur=amount,
            payment_method=method,
            due_date=time.time() + (due_days * 86400)
        )
        with self._lock:
            self._payments[pid] = record
            self._total_invoiced += amount
        self._save()
        log.info(f"[PAYMENT] Facture {pid}: {amount}EUR -> {prospect} via {method}")
        return record

    def record_payment(self, payment_id: str, amount_received: float) -> Dict:
        """Enregistre un paiement recu."""
        with self._lock:
            rec = self._payments.get(payment_id)
            if not rec:
                return {"error": "payment_not_found"}
            rec.amount_paid += amount_received
            if rec.amount_paid >= rec.amount_eur:
                rec.status = PaymentStatus.PAID
                rec.paid_date = time.time()
                self._total_collected += amount_received
                log.info(f"[PAYMENT] {payment_id} PAYE: {rec.amount_eur}EUR")
            else:
                rec.status = PaymentStatus.PARTIAL
                self._total_collected += amount_received
                log.info(f"[PAYMENT] {payment_id} partiel: {rec.amount_paid}/{rec.amount_eur}EUR")
        self._save()
        return {"status": rec.status.value, "paid": rec.amount_paid, "total": rec.amount_eur}

    def check_overdue(self) -> List[PaymentRecord]:
        """Identifie les paiements en retard."""
        now = time.time()
        overdue = []
        with self._lock:
            for rec in self._payments.values():
                if rec.status == PaymentStatus.PENDING and now > rec.due_date:
                    rec.status = PaymentStatus.OVERDUE
                    overdue.append(rec)
        if overdue:
            self._save()
            log.warning(f"[PAYMENT] {len(overdue)} paiements en retard")
        return overdue

    def generate_reminder(self, payment_id: str) -> Optional[Dict]:
        """Genere un message de relance pour un paiement en retard."""
        with self._lock:
            rec = self._payments.get(payment_id)
            if not rec or rec.status == PaymentStatus.PAID:
                return None
            if rec.reminders_sent >= rec.max_reminders:
                return {"action": "escalate", "reason": f"Max relances atteint ({rec.max_reminders})"}

            rec.reminders_sent += 1
            days_overdue = int((time.time() - rec.due_date) / 86400)

            payment_link = self.PAYMENT_METHODS.get(rec.payment_method, {}).get(
                "url_template", ""
            ).format(amount=rec.amount_eur)

            if rec.reminders_sent == 1:
                tone = "courtois"
                message = (f"Bonjour {rec.prospect_name}, nous vous rappelons que le paiement de "
                          f"{rec.amount_eur}EUR est en attente. Lien: {payment_link}")
            elif rec.reminders_sent == 2:
                tone = "ferme"
                message = (f"Bonjour {rec.prospect_name}, votre paiement de {rec.amount_eur}EUR "
                          f"est en retard de {days_overdue} jours. Merci de regulariser: {payment_link}")
            else:
                tone = "final"
                message = (f"{rec.prospect_name}, derniere relance pour le paiement de "
                          f"{rec.amount_eur}EUR ({days_overdue}j de retard). {payment_link}")

        self._save()
        return {
            "payment_id": payment_id,
            "reminder_number": rec.reminders_sent,
            "tone": tone,
            "message": message,
            "payment_link": payment_link,
            "days_overdue": days_overdue
        }

    def get_payment_link(self, amount: float, method: str = "paypal") -> str:
        template = self.PAYMENT_METHODS.get(method, {}).get("url_template", "")
        return template.format(amount=amount)

    def reconcile(self) -> Dict:
        """Reconciliation globale: compare facture vs encaisse."""
        with self._lock:
            total_invoiced = sum(r.amount_eur for r in self._payments.values())
            total_paid = sum(r.amount_paid for r in self._payments.values())
            by_status = {}
            for r in self._payments.values():
                by_status[r.status.value] = by_status.get(r.status.value, 0) + 1
        return {
            "total_invoiced": total_invoiced,
            "total_collected": total_paid,
            "outstanding": total_invoiced - total_paid,
            "collection_rate": total_paid / total_invoiced if total_invoiced > 0 else 0,
            "by_status": by_status,
            "total_records": len(self._payments)
        }

    def _save(self):
        try:
            PAYMENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
            with self._lock:
                data = {}
                for pid, rec in self._payments.items():
                    data[pid] = {
                        "payment_id": rec.payment_id, "opportunity_id": rec.opportunity_id,
                        "prospect_name": rec.prospect_name, "amount_eur": rec.amount_eur,
                        "amount_paid": rec.amount_paid, "status": rec.status.value,
                        "payment_method": rec.payment_method, "invoice_date": rec.invoice_date,
                        "due_date": rec.due_date, "paid_date": rec.paid_date,
                        "reminders_sent": rec.reminders_sent, "notes": rec.notes
                    }
            PAYMENTS_FILE.write_text(json.dumps(data, indent=2))
        except Exception as e:
            log.debug(f"[PAYMENT] Save: {e}")

    def _load(self):
        try:
            if PAYMENTS_FILE.exists():
                data = json.loads(PAYMENTS_FILE.read_text())
                for pid, d in data.items():
                    self._payments[pid] = PaymentRecord(
                        payment_id=d["payment_id"], opportunity_id=d["opportunity_id"],
                        prospect_name=d["prospect_name"], amount_eur=d["amount_eur"],
                        amount_paid=d.get("amount_paid", 0), payment_method=d.get("payment_method", "paypal"),
                        status=PaymentStatus(d.get("status", "pending")),
                        invoice_date=d.get("invoice_date", 0), due_date=d.get("due_date", 0),
                        paid_date=d.get("paid_date"), reminders_sent=d.get("reminders_sent", 0)
                    )
                    self._total_invoiced += d["amount_eur"]
                    self._total_collected += d.get("amount_paid", 0)
                log.info(f"[PAYMENT] {len(self._payments)} records charges")
        except Exception as e:
            log.debug(f"[PAYMENT] Load: {e}")

    def get_stats(self) -> Dict:
        return self.reconcile()

_tracker = None
_tracker_lock = threading.Lock()
def get_payment_tracker():
    global _tracker
    if _tracker is None:
        with _tracker_lock:
            if _tracker is None:
                _tracker = PaymentTracker()
    return _tracker
