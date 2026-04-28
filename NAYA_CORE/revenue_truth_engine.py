"""Revenue Truth Engine.

Sépare strictement:
- Encaissements vérifiés (preuve de paiement)
- Ventes simulées / test / non confirmées
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parent.parent
VALIDATION_LEDGER = ROOT / "data" / "validation" / "real_sales_ledger.json"
REAL_LEDGER = ROOT / "data" / "real_sales" / "real_sales_ledger.json"
CASH_PIPELINE = ROOT / "data" / "cache" / "cash_pipeline.json"


@dataclass
class RevenueTruthReport:
    generated_at: str
    verified_revenue_eur: float
    verified_sales_count: int
    unverified_revenue_eur: float
    unverified_sales_count: int
    simulated_or_test_count: int
    notes: List[str]


class RevenueTruthEngine:
    def _read_json(self, path: Path, default: Any) -> Any:
        try:
            if path.exists():
                return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
        return default

    def build_report(self) -> RevenueTruthReport:
        validation_sales: List[Dict[str, Any]] = self._read_json(VALIDATION_LEDGER, [])
        real_sales: List[Dict[str, Any]] = self._read_json(REAL_LEDGER, [])
        pipeline: Dict[str, Any] = self._read_json(CASH_PIPELINE, {})

        verified = []
        unverified = []
        simulated = []

        # Validation ledger: ne compter que payment_confirmed/sale_completed non test
        for s in validation_sales:
            status = (s.get("status") or "").lower()
            validator = (s.get("validated_by") or "").lower()
            amount = float(s.get("amount_eur") or 0)
            if status in {"payment_confirmed", "sale_completed"} and not any(x in validator for x in ["test", "auto", "api test"]):
                verified.append(amount)
            elif status in {"payment_confirmed", "sale_completed"}:
                simulated.append(amount)
            elif status in {"payment_link_sent", "pending"}:
                unverified.append(amount)

        # real ledger vide => rien à ajouter, sinon considéré vérifié
        for s in real_sales:
            amount = float(s.get("amount_eur") or 0)
            verified.append(amount)

        # cash pipeline won_total est considéré non prouvé sans trace paiement
        won_total = float(pipeline.get("won_total") or 0)
        won_count = int(pipeline.get("won_count") or 0)
        if won_total > 0:
            unverified.append(won_total)

        notes = [
            "Verified = preuve paiement non marquée test/auto.",
            "Unverified = lien envoyé/pending/ou won pipeline sans preuve paiement.",
            "Simulated/Test = marquage validateur contenant test/auto.",
        ]
        if won_total > 0 and won_count > 0:
            notes.append(f"cash_pipeline indique {won_count} won ({won_total:,.0f} EUR) sans canal de paiement prouvé.")

        return RevenueTruthReport(
            generated_at=datetime.now(timezone.utc).isoformat(),
            verified_revenue_eur=round(sum(verified), 2),
            verified_sales_count=len(verified),
            unverified_revenue_eur=round(sum(unverified), 2),
            unverified_sales_count=len(unverified),
            simulated_or_test_count=len(simulated),
            notes=notes,
        )


revenue_truth_engine = RevenueTruthEngine()
