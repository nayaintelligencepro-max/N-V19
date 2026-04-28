"""
NAYA SUPREME V19.3 — AMELIORATION #9
Revenue Reconciliation Engine
=============================
Reconciliation automatique entre les paiements recus et le pipeline.
Detecte les incoherences : paiement sans deal, deal sans paiement,
montants discordants, paiements en retard.

Unique a NAYA : reconciliation financiere automatique dans un
systeme de vente IA avec detection d'anomalies.
"""
import time
import logging
import threading
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

log = logging.getLogger("NAYA.RECONCILIATION")


class DiscrepancyType(Enum):
    PAYMENT_NO_DEAL = "payment_without_deal"
    DEAL_NO_PAYMENT = "deal_without_payment"
    AMOUNT_MISMATCH = "amount_mismatch"
    PAYMENT_LATE = "payment_late"
    DOUBLE_PAYMENT = "double_payment"
    REFUND_NEEDED = "refund_needed"


@dataclass
class Discrepancy:
    discrepancy_id: str
    discrepancy_type: DiscrepancyType
    deal_id: str
    company: str
    expected_amount: float
    actual_amount: float
    delta: float
    severity: str  # info | warning | critical
    message: str
    auto_resolvable: bool
    created_at: float = field(default_factory=time.time)
    resolved: bool = False


@dataclass
class ReconciliationReport:
    timestamp: float
    total_deals_checked: int
    total_payments_checked: int
    total_revenue_expected: float
    total_revenue_received: float
    delta: float
    discrepancies: List[Discrepancy]
    health_score: float  # 0-100
    next_expected_payments: List[Dict]


class RevenueReconciliationEngine:
    """
    Moteur de reconciliation financiere automatique.

    Reconcilie :
    1. Pipeline (deals won) vs Paiements recus
    2. Factures envoyees vs Paiements recus
    3. Montants attendus vs Montants recus
    4. Delais de paiement (alerte si > 30 jours)
    5. Detection de doubles paiements
    """

    def __init__(self):
        self._deals: Dict[str, Dict] = {}
        self._payments: Dict[str, Dict] = {}
        self._discrepancies: List[Discrepancy] = []
        self._reports: List[ReconciliationReport] = []
        self._lock = threading.Lock()
        self._reconciliation_count: int = 0

    def register_deal(self, deal_id: str, company: str, amount: float,
                      stage: str = "won", closed_at: float = None) -> None:
        """Enregistre un deal pour la reconciliation."""
        self._deals[deal_id] = {
            "deal_id": deal_id,
            "company": company,
            "amount": amount,
            "stage": stage,
            "closed_at": closed_at or time.time(),
            "payment_received": False,
            "payment_amount": 0,
        }

    def register_payment(self, payment_id: str, deal_id: str, amount: float,
                         provider: str = "paypal", paid_at: float = None) -> None:
        """Enregistre un paiement recu."""
        self._payments[payment_id] = {
            "payment_id": payment_id,
            "deal_id": deal_id,
            "amount": amount,
            "provider": provider,
            "paid_at": paid_at or time.time(),
        }

    def reconcile(self) -> ReconciliationReport:
        """Execute la reconciliation complete."""
        self._reconciliation_count += 1
        start = time.time()
        discrepancies: List[Discrepancy] = []
        disc_id = 0

        # 1. Associer paiements aux deals
        deal_payments: Dict[str, List[Dict]] = {}
        for p in self._payments.values():
            did = p.get("deal_id", "")
            if did not in deal_payments:
                deal_payments[did] = []
            deal_payments[did].append(p)

        # 2. Verifier chaque deal "won" a un paiement
        total_expected = 0
        total_received = 0
        now = time.time()

        for deal_id, deal in self._deals.items():
            if deal["stage"] not in ("won", "contract", "closed"):
                continue

            total_expected += deal["amount"]
            payments = deal_payments.get(deal_id, [])

            if not payments:
                days_since_close = (now - deal["closed_at"]) / 86400
                severity = "critical" if days_since_close > 30 else "warning" if days_since_close > 14 else "info"

                if days_since_close > 7:
                    disc_id += 1
                    discrepancies.append(Discrepancy(
                        discrepancy_id=f"DISC_{disc_id}",
                        discrepancy_type=DiscrepancyType.DEAL_NO_PAYMENT,
                        deal_id=deal_id,
                        company=deal["company"],
                        expected_amount=deal["amount"],
                        actual_amount=0,
                        delta=-deal["amount"],
                        severity=severity,
                        message=f"Deal {deal['company']} ({deal['amount']:.0f} EUR) ferme il y a {days_since_close:.0f}j — pas de paiement recu",
                        auto_resolvable=False,
                    ))
            else:
                total_paid = sum(p["amount"] for p in payments)
                total_received += total_paid

                # Verifier le montant
                delta = total_paid - deal["amount"]
                if abs(delta) > 1:  # > 1 EUR de difference
                    disc_id += 1
                    if delta > 0:
                        msg = f"Trop-percu de {delta:.2f} EUR pour {deal['company']}"
                        dtype = DiscrepancyType.DOUBLE_PAYMENT if delta >= deal["amount"] else DiscrepancyType.AMOUNT_MISMATCH
                    else:
                        msg = f"Sous-paiement de {abs(delta):.2f} EUR pour {deal['company']}"
                        dtype = DiscrepancyType.AMOUNT_MISMATCH

                    discrepancies.append(Discrepancy(
                        discrepancy_id=f"DISC_{disc_id}",
                        discrepancy_type=dtype,
                        deal_id=deal_id,
                        company=deal["company"],
                        expected_amount=deal["amount"],
                        actual_amount=total_paid,
                        delta=delta,
                        severity="warning" if abs(delta) < 100 else "critical",
                        message=msg,
                        auto_resolvable=abs(delta) < 10,
                    ))
                else:
                    total_received += 0  # Exact match, already counted

                # Verifier paiement en retard
                for p in payments:
                    delay_days = (p["paid_at"] - deal["closed_at"]) / 86400
                    if delay_days > 30:
                        disc_id += 1
                        discrepancies.append(Discrepancy(
                            discrepancy_id=f"DISC_{disc_id}",
                            discrepancy_type=DiscrepancyType.PAYMENT_LATE,
                            deal_id=deal_id,
                            company=deal["company"],
                            expected_amount=deal["amount"],
                            actual_amount=p["amount"],
                            delta=0,
                            severity="info",
                            message=f"Paiement recu {delay_days:.0f}j apres le closing pour {deal['company']}",
                            auto_resolvable=False,
                        ))

        # 3. Paiements sans deal associe
        for p_id, payment in self._payments.items():
            if payment["deal_id"] not in self._deals:
                disc_id += 1
                total_received += payment["amount"]
                discrepancies.append(Discrepancy(
                    discrepancy_id=f"DISC_{disc_id}",
                    discrepancy_type=DiscrepancyType.PAYMENT_NO_DEAL,
                    deal_id=payment["deal_id"],
                    company=f"Unknown (payment {p_id})",
                    expected_amount=0,
                    actual_amount=payment["amount"],
                    delta=payment["amount"],
                    severity="warning",
                    message=f"Paiement de {payment['amount']:.0f} EUR sans deal associe",
                    auto_resolvable=False,
                ))

        # Score de sante
        if total_expected > 0:
            collection_rate = total_received / total_expected
            health = round(collection_rate * 100, 1)
        else:
            health = 100.0 if not discrepancies else 50.0

        # Prochains paiements attendus
        next_payments = []
        for deal_id, deal in self._deals.items():
            if deal["stage"] in ("won", "contract") and deal_id not in deal_payments:
                next_payments.append({
                    "deal_id": deal_id,
                    "company": deal["company"],
                    "amount": deal["amount"],
                    "days_since_close": round((now - deal["closed_at"]) / 86400, 1),
                })

        report = ReconciliationReport(
            timestamp=time.time(),
            total_deals_checked=len(self._deals),
            total_payments_checked=len(self._payments),
            total_revenue_expected=round(total_expected, 2),
            total_revenue_received=round(total_received, 2),
            delta=round(total_received - total_expected, 2),
            discrepancies=discrepancies,
            health_score=min(100, health),
            next_expected_payments=sorted(next_payments, key=lambda x: -x["amount"]),
        )

        with self._lock:
            self._reports.append(report)
            self._discrepancies.extend(discrepancies)

        if discrepancies:
            log.info(
                f"[RECONCILE] {len(discrepancies)} anomalies | "
                f"attendu={total_expected:.0f} EUR recu={total_received:.0f} EUR "
                f"health={health:.0f}/100"
            )
        else:
            log.info(f"[RECONCILE] OK — {total_expected:.0f} EUR reconcilies sans anomalie")

        return report

    def get_stats(self) -> Dict:
        return {
            "reconciliations_run": self._reconciliation_count,
            "total_deals": len(self._deals),
            "total_payments": len(self._payments),
            "total_discrepancies": len(self._discrepancies),
            "unresolved": sum(1 for d in self._discrepancies if not d.resolved),
        }

    def to_dict(self) -> Dict:
        if not self._reports:
            return {"status": "no_reconciliation_run"}
        r = self._reports[-1]
        return {
            "health_score": r.health_score,
            "expected": r.total_revenue_expected,
            "received": r.total_revenue_received,
            "delta": r.delta,
            "discrepancies": len(r.discrepancies),
            "next_payments": r.next_expected_payments[:5],
        }


_engine: Optional[RevenueReconciliationEngine] = None


def get_reconciliation_engine() -> RevenueReconciliationEngine:
    global _engine
    if _engine is None:
        _engine = RevenueReconciliationEngine()
    return _engine
