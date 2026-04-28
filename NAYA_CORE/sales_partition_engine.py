"""Sales Partition Engine.

Sépare les enregistrements de ventes en 3 catégories:
- real_verified: paiement confirmé non test
- test_or_simulated: entrées de test/simulation
- pending_or_unverified: lien envoyé/pending/non confirmé
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "validation" / "real_sales_ledger.json"
OUT_DIR = ROOT / "data" / "validation"
REAL_OUT = OUT_DIR / "real_sales_verified_only.json"
TEST_OUT = OUT_DIR / "real_sales_test_or_simulated.json"
PENDING_OUT = OUT_DIR / "real_sales_pending_or_unverified.json"


@dataclass
class PartitionReport:
    timestamp: str
    source_entries: int
    real_verified_count: int
    real_verified_eur: float
    test_count: int
    test_eur: float
    pending_count: int
    pending_eur: float


class SalesPartitionEngine:
    @staticmethod
    def _read(path: Path, default: Any) -> Any:
        try:
            if path.exists():
                return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
        return default

    @staticmethod
    def _write(path: Path, data: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def _is_test_like(entry: Dict[str, Any]) -> bool:
        validator = str(entry.get("validated_by") or "").lower()
        notes = str(entry.get("validation_notes") or "").lower()
        company = str(entry.get("company") or "").lower()
        email = str(entry.get("contact_email") or "").lower()
        offer = str(entry.get("offer_title") or "").lower()

        test_markers = ["test", "auto", "api test", "cli", "simulation", "dummy", "example"]
        haystack = " | ".join([validator, notes, company, email, offer])
        return any(m in haystack for m in test_markers)

    def partition(self) -> PartitionReport:
        rows: List[Dict[str, Any]] = self._read(SRC, [])
        real_verified: List[Dict[str, Any]] = []
        tests: List[Dict[str, Any]] = []
        pending: List[Dict[str, Any]] = []

        for r in rows:
            status = str(r.get("status") or "").lower()
            amount = float(r.get("amount_eur") or 0)
            if self._is_test_like(r):
                r["partition_tag"] = "test_or_simulated"
                tests.append(r)
                continue

            if status in {"payment_confirmed", "sale_completed"}:
                r["partition_tag"] = "real_verified"
                real_verified.append(r)
            else:
                r["partition_tag"] = "pending_or_unverified"
                pending.append(r)

        self._write(REAL_OUT, real_verified)
        self._write(TEST_OUT, tests)
        self._write(PENDING_OUT, pending)

        return PartitionReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
            source_entries=len(rows),
            real_verified_count=len(real_verified),
            real_verified_eur=round(sum(float(x.get("amount_eur") or 0) for x in real_verified), 2),
            test_count=len(tests),
            test_eur=round(sum(float(x.get("amount_eur") or 0) for x in tests), 2),
            pending_count=len(pending),
            pending_eur=round(sum(float(x.get("amount_eur") or 0) for x in pending), 2),
        )


sales_partition_engine = SalesPartitionEngine()
