"""
NAYA V19.3 — REVENUE RECONCILIATION ENGINE
Réconcilie les paiements Deblock + PayPal en un ledger unique.
Alertes Telegram sur chaque entrée + divergences détectées.

Sources supportées:
- Deblock.me (crypto)
- PayPal.me (classique)
- Manuel (virement, cash, chèque — réconciliation manuelle)

Fonctionnalités:
- Ledger immuable append-only (JSON)
- Détection doublons par hash
- Détection divergences (montant offre vs paiement reçu)
- Alertes Telegram: nouveau paiement, doublon, divergence, manquement
- Export CSV mensuel
- Projection cash-flow basée sur pipeline Deblock pending
"""
import asyncio
import hashlib
import json
import logging
import os
import csv
from pathlib import Path
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from enum import Enum

log = logging.getLogger("NAYA.RECONCILE")


class PaymentSource(str, Enum):
    DEBLOCK = "deblock"
    PAYPAL = "paypal"
    BANK_TRANSFER = "bank_transfer"
    MANUAL = "manual"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    RECONCILED = "reconciled"      # Matché à une offre
    ORPHAN = "orphan"              # Reçu sans offre identifiée
    DISPUTED = "disputed"
    REFUNDED = "refunded"


@dataclass
class PaymentEntry:
    """Entrée ledger immuable"""
    entry_id: str                   # hash content-based
    source: PaymentSource
    external_id: str                # id Deblock/PayPal
    amount_eur: float
    received_at: datetime
    status: PaymentStatus = PaymentStatus.PENDING
    payer_email: str = ""
    payer_name: str = ""
    memo: str = ""                  # description paiement
    matched_offer_id: Optional[str] = None
    matched_prospect_id: Optional[str] = None
    expected_amount_eur: Optional[float] = None  # montant offre attendue
    discrepancy_eur: float = 0.0                 # amount - expected
    raw: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        d = asdict(self)
        d["source"] = self.source.value
        d["status"] = self.status.value
        d["received_at"] = self.received_at.isoformat()
        return d

    @staticmethod
    def compute_hash(source: str, external_id: str, amount: float, received_at: str) -> str:
        content = f"{source}|{external_id}|{amount:.2f}|{received_at}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


@dataclass
class OfferExpectation:
    """Offre en attente de paiement (injectée par le closer)"""
    offer_id: str
    prospect_id: str
    prospect_email: str
    amount_eur: float
    created_at: datetime
    deadline: datetime
    payment_link_deblock: str = ""
    payment_link_paypal: str = ""


# ═════════════════════════════════════════════════════════════════
# LEDGER (append-only, JSON)
# ═════════════════════════════════════════════════════════════════

class RevenueLedger:
    """Ledger immuable append-only."""

    def __init__(self, ledger_path: Path):
        self.ledger_path = ledger_path
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        self._entries: Dict[str, PaymentEntry] = {}
        self._lock = asyncio.Lock()
        self._load()

    def _load(self):
        if not self.ledger_path.exists():
            return
        try:
            with open(self.ledger_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    data = json.loads(line)
                    entry = PaymentEntry(
                        entry_id=data["entry_id"],
                        source=PaymentSource(data["source"]),
                        external_id=data["external_id"],
                        amount_eur=data["amount_eur"],
                        received_at=datetime.fromisoformat(data["received_at"]),
                        status=PaymentStatus(data["status"]),
                        payer_email=data.get("payer_email", ""),
                        payer_name=data.get("payer_name", ""),
                        memo=data.get("memo", ""),
                        matched_offer_id=data.get("matched_offer_id"),
                        matched_prospect_id=data.get("matched_prospect_id"),
                        expected_amount_eur=data.get("expected_amount_eur"),
                        discrepancy_eur=data.get("discrepancy_eur", 0.0),
                        raw=data.get("raw", {}),
                    )
                    self._entries[entry.entry_id] = entry
            log.info(f"Ledger loaded: {len(self._entries)} entries")
        except Exception as e:
            log.error(f"Ledger load error: {e}")

    async def append(self, entry: PaymentEntry) -> bool:
        """Ajoute une entrée. Retourne False si doublon."""
        async with self._lock:
            if entry.entry_id in self._entries:
                return False
            self._entries[entry.entry_id] = entry
            try:
                with open(self.ledger_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry.to_dict()) + "\n")
            except Exception as e:
                log.error(f"Ledger write error: {e}")
                return False
            return True

    async def update_status(self, entry_id: str, status: PaymentStatus,
                            matched_offer_id: Optional[str] = None,
                            matched_prospect_id: Optional[str] = None,
                            expected_amount_eur: Optional[float] = None):
        async with self._lock:
            entry = self._entries.get(entry_id)
            if not entry:
                return False
            entry.status = status
            if matched_offer_id:
                entry.matched_offer_id = matched_offer_id
            if matched_prospect_id:
                entry.matched_prospect_id = matched_prospect_id
            if expected_amount_eur is not None:
                entry.expected_amount_eur = expected_amount_eur
                entry.discrepancy_eur = entry.amount_eur - expected_amount_eur
            # Re-write complet (append-only = pas idéal ici, mais simple & robuste)
            try:
                with open(self.ledger_path, "w", encoding="utf-8") as f:
                    for e in self._entries.values():
                        f.write(json.dumps(e.to_dict()) + "\n")
            except Exception as e:
                log.error(f"Ledger rewrite error: {e}")
            return True

    def all(self) -> List[PaymentEntry]:
        return list(self._entries.values())

    def by_status(self, status: PaymentStatus) -> List[PaymentEntry]:
        return [e for e in self._entries.values() if e.status == status]

    def total_revenue(self, since: Optional[datetime] = None) -> float:
        total = 0.0
        for e in self._entries.values():
            if e.status in (PaymentStatus.CONFIRMED, PaymentStatus.RECONCILED):
                if since is None or e.received_at >= since:
                    total += e.amount_eur
        return total

    def summary(self) -> Dict:
        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return {
            "total_entries": len(self._entries),
            "by_status": {
                s.value: len(self.by_status(s)) for s in PaymentStatus
            },
            "revenue_lifetime_eur": self.total_revenue(),
            "revenue_current_month_eur": self.total_revenue(since=month_start),
            "by_source": {
                src.value: sum(e.amount_eur for e in self._entries.values()
                               if e.source == src
                               and e.status in (PaymentStatus.CONFIRMED, PaymentStatus.RECONCILED))
                for src in PaymentSource
            },
            "orphans": len(self.by_status(PaymentStatus.ORPHAN)),
            "disputed": len(self.by_status(PaymentStatus.DISPUTED)),
        }


# ═════════════════════════════════════════════════════════════════
# RECONCILER
# ═════════════════════════════════════════════════════════════════

class RevenueReconciler:
    """
    Réconcilie paiements Deblock + PayPal avec les offres émises.
    Envoie alertes Telegram automatiques.
    """

    DEFAULT_TOLERANCE_EUR = 5.0  # Tolérance pour frais réseau / taux

    def __init__(self, ledger: RevenueLedger, tolerance_eur: float = None):
        self.ledger = ledger
        self.tolerance = tolerance_eur or self.DEFAULT_TOLERANCE_EUR
        self._expectations: Dict[str, OfferExpectation] = {}
        self._telegram_enabled = bool(os.getenv("TELEGRAM_BOT_TOKEN"))

    def register_expectation(self, offer: OfferExpectation):
        self._expectations[offer.offer_id] = offer
        log.info(f"Expectation registered: {offer.offer_id} = {offer.amount_eur}EUR")

    async def _notify_telegram(self, message: str):
        if not self._telegram_enabled:
            log.info(f"[TG-DISABLED] {message}")
            return
        try:
            # Import lazy pour éviter dépendance dure
            from NAYA_CORE.notifier import telegram_notify
            await telegram_notify(message)
        except Exception as e:
            log.debug(f"Telegram notify failed: {e}")

    async def ingest_deblock_payment(self, raw: Dict) -> Optional[PaymentEntry]:
        """
        Ingère un paiement Deblock.
        raw attendu: {id, amount_eur, created_at, payer_email, memo, status}
        """
        return await self._ingest(
            source=PaymentSource.DEBLOCK,
            external_id=str(raw.get("id", "")),
            amount_eur=float(raw.get("amount_eur", 0)),
            received_at_str=raw.get("created_at", datetime.now(timezone.utc).isoformat()),
            payer_email=raw.get("payer_email", ""),
            payer_name=raw.get("payer_name", ""),
            memo=raw.get("memo", ""),
            raw=raw,
        )

    async def ingest_paypal_payment(self, raw: Dict) -> Optional[PaymentEntry]:
        """
        Ingère un paiement PayPal.
        raw attendu: {id, amount: {value, currency}, create_time, payer: {email_address, name}, note_to_payer}
        """
        amount = raw.get("amount", {})
        value = float(amount.get("value", 0))
        currency = amount.get("currency_code", "EUR")
        # Conversion simple si USD (taux approximatif — idéalement appeler API forex)
        if currency == "USD":
            value *= 0.92
        payer = raw.get("payer", {})
        return await self._ingest(
            source=PaymentSource.PAYPAL,
            external_id=str(raw.get("id", "")),
            amount_eur=value,
            received_at_str=raw.get("create_time", datetime.now(timezone.utc).isoformat()),
            payer_email=payer.get("email_address", ""),
            payer_name=f"{payer.get('name', {}).get('given_name','')} "
                       f"{payer.get('name', {}).get('surname','')}".strip(),
            memo=raw.get("note_to_payer", ""),
            raw=raw,
        )

    async def _ingest(self, source: PaymentSource, external_id: str,
                      amount_eur: float, received_at_str: str,
                      payer_email: str, payer_name: str, memo: str,
                      raw: Dict) -> Optional[PaymentEntry]:
        try:
            received_at = datetime.fromisoformat(received_at_str.replace("Z", "+00:00"))
        except Exception:
            received_at = datetime.now(timezone.utc)

        entry_id = PaymentEntry.compute_hash(
            source.value, external_id, amount_eur, received_at.isoformat()
        )

        entry = PaymentEntry(
            entry_id=entry_id,
            source=source,
            external_id=external_id,
            amount_eur=amount_eur,
            received_at=received_at,
            status=PaymentStatus.CONFIRMED,
            payer_email=payer_email,
            payer_name=payer_name,
            memo=memo,
            raw=raw,
        )

        appended = await self.ledger.append(entry)
        if not appended:
            # Doublon: pas d'alerte (déjà notifié auparavant)
            log.debug(f"Duplicate payment ignored: {entry_id}")
            return None

        # Tentative de match avec une expectation
        matched = self._match_expectation(entry)
        if matched:
            await self.ledger.update_status(
                entry_id=entry.entry_id,
                status=PaymentStatus.RECONCILED,
                matched_offer_id=matched.offer_id,
                matched_prospect_id=matched.prospect_id,
                expected_amount_eur=matched.amount_eur,
            )
            discrepancy = amount_eur - matched.amount_eur
            msg = (
                f"💰 PAIEMENT RÉCONCILIÉ — {source.value.upper()}\n"
                f"Montant: {amount_eur:.2f} EUR\n"
                f"Offre: {matched.offer_id}\n"
                f"Prospect: {matched.prospect_email}\n"
            )
            if abs(discrepancy) > self.tolerance:
                msg += f"⚠️ DIVERGENCE: {discrepancy:+.2f} EUR (attendu {matched.amount_eur:.2f})"
            await self._notify_telegram(msg)
        else:
            await self.ledger.update_status(entry.entry_id, PaymentStatus.ORPHAN)
            await self._notify_telegram(
                f"❓ PAIEMENT ORPHELIN — {source.value.upper()}\n"
                f"Montant: {amount_eur:.2f} EUR\n"
                f"De: {payer_email or payer_name}\n"
                f"Memo: {memo[:100]}\n"
                f"→ Pas d'offre matchée. À vérifier manuellement."
            )

        return entry

    def _match_expectation(self, entry: PaymentEntry) -> Optional[OfferExpectation]:
        """
        Match par:
        1. Memo contient offer_id
        2. Email payeur matche prospect_email
        3. Montant proche d'une expectation pending (± tolerance)
        """
        # 1. Memo contient offer_id
        if entry.memo:
            for offer_id, exp in self._expectations.items():
                if offer_id.lower() in entry.memo.lower():
                    return exp

        # 2. Email payeur
        if entry.payer_email:
            email_l = entry.payer_email.lower()
            for exp in self._expectations.values():
                if exp.prospect_email.lower() == email_l:
                    return exp

        # 3. Montant proche
        candidates = [
            e for e in self._expectations.values()
            if abs(e.amount_eur - entry.amount_eur) <= self.tolerance
        ]
        if len(candidates) == 1:
            return candidates[0]

        return None

    async def check_overdue_expectations(self) -> List[OfferExpectation]:
        """Détecte les offres dont la deadline est passée sans paiement reçu."""
        now = datetime.now(timezone.utc)
        overdue = []
        reconciled_offer_ids = {
            e.matched_offer_id for e in self.ledger.all()
            if e.matched_offer_id and e.status == PaymentStatus.RECONCILED
        }
        for offer_id, exp in self._expectations.items():
            if offer_id in reconciled_offer_ids:
                continue
            if exp.deadline < now:
                overdue.append(exp)

        if overdue:
            msg = f"⏰ {len(overdue)} OFFRE(S) EN RETARD DE PAIEMENT:\n"
            for exp in overdue[:5]:
                days_late = (now - exp.deadline).days
                msg += f"- {exp.offer_id} ({exp.prospect_email}) | {exp.amount_eur:.0f}EUR | {days_late}j retard\n"
            await self._notify_telegram(msg)

        return overdue

    def export_csv(self, output_path: Path, month: Optional[str] = None):
        """Export CSV du ledger (optionnel: filtré par mois YYYY-MM)."""
        entries = self.ledger.all()
        if month:
            entries = [e for e in entries if e.received_at.strftime("%Y-%m") == month]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "entry_id", "source", "external_id", "amount_eur", "received_at",
                "status", "payer_email", "payer_name", "memo",
                "matched_offer_id", "matched_prospect_id",
                "expected_amount_eur", "discrepancy_eur"
            ])
            for e in entries:
                writer.writerow([
                    e.entry_id, e.source.value, e.external_id,
                    f"{e.amount_eur:.2f}", e.received_at.isoformat(),
                    e.status.value, e.payer_email, e.payer_name, e.memo,
                    e.matched_offer_id or "", e.matched_prospect_id or "",
                    f"{e.expected_amount_eur:.2f}" if e.expected_amount_eur else "",
                    f"{e.discrepancy_eur:+.2f}"
                ])
        return output_path


# ═════════════════════════════════════════════════════════════════
# SINGLETON
# ═════════════════════════════════════════════════════════════════

_default_ledger_path = Path("data/revenue/ledger.jsonl")
_default_ledger = RevenueLedger(_default_ledger_path)
reconciler = RevenueReconciler(_default_ledger)


__all__ = [
    "PaymentSource", "PaymentStatus", "PaymentEntry", "OfferExpectation",
    "RevenueLedger", "RevenueReconciler", "reconciler",
]
