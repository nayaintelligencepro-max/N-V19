"""
NAYA V20 — Blockchain Proof of Audit
══════════════════════════════════════════════════════════════════════════════
Polygon L2-compatible audit proof system using SHA-256 simulation.

DOCTRINE:
  Industrial clients increasingly demand tamper-proof evidence of conducted
  audits for insurance, regulatory and board-level reporting purposes.
  A blockchain-anchored audit certificate:
    - Cannot be backdated
    - Cannot be falsified after issuance
    - Can be verified by any third party without NAYA's involvement
    - Adds €2k–€5k to every audit engagement as a premium add-on

PRODUCTION NOTE:
  In production, submit content_hash to Polygon Amoy testnet (free) or
  Polygon PoS mainnet via web3.py + INFURA.
  Replace `tx_hash = _sha256(...)` with actual transaction hash from
  `web3.eth.send_raw_transaction(...)`.
  This simulation is binary-compatible with the production interface.
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

log = logging.getLogger("NAYA.BLOCKCHAIN_PROOF")

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_FILE = ROOT / "data" / "cache" / "blockchain_proof_of_audit.json"


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


@dataclass
class AuditProof:
    """Blockchain-anchored proof of a completed audit."""

    proof_id: str
    audit_id: str
    company: str
    audit_type: str
    auditor: str
    content_hash: str          # SHA-256 of audit content
    merkle_root: str           # SHA-256(content_hash + block_timestamp)
    block_timestamp: str
    chain_id: str = "polygon_amoy_testnet"
    tx_hash: str = ""          # Simulated: SHA-256(content_hash + block_timestamp)
    is_verified: bool = True
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class BlockchainProofOfAudit:
    """
    Issues and verifies blockchain-style audit proofs.

    Thread-safe singleton.  Persists all proofs to DATA_FILE.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._data_file = DATA_FILE
        self._proofs: Dict[str, Dict] = {}
        self._load()

    # ──────────────────────────────────────────────────────────────────────
    # Persistence
    # ──────────────────────────────────────────────────────────────────────

    def _load(self) -> None:
        if self._data_file.exists():
            try:
                with open(self._data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._proofs = data.get("proofs", {})
            except Exception:
                pass

    def _save(self) -> None:
        self._data_file.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            with open(self._data_file, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "proofs": self._proofs,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    },
                    f,
                    indent=2,
                    ensure_ascii=False,
                )

    # ──────────────────────────────────────────────────────────────────────
    # Business methods
    # ──────────────────────────────────────────────────────────────────────

    def register_audit(
        self,
        audit_id: str,
        company: str,
        audit_type: str,
        auditor: str,
        scope: str,
        result_summary: str,
    ) -> AuditProof:
        """
        Register a completed audit and issue a blockchain-anchored proof.

        Args:
            audit_id: Internal audit identifier.
            company: Audited company name.
            audit_type: Audit type label (e.g. "IEC 62443", "NIS2 Gap Analysis").
            auditor: Auditor name or identifier.
            scope: Short description of what was audited.
            result_summary: High-level summary of findings.

        Returns:
            AuditProof with hashes, timestamp and simulated tx_hash.
        """
        proof_id = _sha256(audit_id + company + str(time.time()))[:16]
        content_hash = _sha256(
            json.dumps(
                {
                    "audit_id": audit_id,
                    "company": company,
                    "scope": scope,
                    "result_summary": result_summary,
                },
                sort_keys=True,
            )
        )
        block_timestamp = datetime.now(timezone.utc).isoformat()
        merkle_root = _sha256(content_hash + block_timestamp)
        tx_hash = _sha256(content_hash + block_timestamp)

        proof = AuditProof(
            proof_id=proof_id,
            audit_id=audit_id,
            company=company,
            audit_type=audit_type,
            auditor=auditor,
            content_hash=content_hash,
            merkle_root=merkle_root,
            block_timestamp=block_timestamp,
            tx_hash=tx_hash,
            is_verified=True,
        )

        with self._lock:
            self._proofs[proof_id] = asdict(proof)
        self._save()
        return proof

    def verify_proof(self, proof_id: str) -> Dict:
        """
        Re-verify a stored audit proof's hash integrity.

        Args:
            proof_id: Target proof identifier.

        Returns:
            Dict with verified (bool), proof_id, company, audit_type,
            block_timestamp, tx_hash.
        """
        with self._lock:
            data = self._proofs.get(proof_id)
        if not data:
            return {"verified": False, "error": f"Proof '{proof_id}' not found."}

        # Recompute expected tx_hash from stored content_hash and block_timestamp
        expected_tx = _sha256(data["content_hash"] + data["block_timestamp"])
        verified = expected_tx == data["tx_hash"]

        return {
            "verified": verified,
            "proof_id": proof_id,
            "company": data["company"],
            "audit_type": data["audit_type"],
            "block_timestamp": data["block_timestamp"],
            "tx_hash": data["tx_hash"],
        }

    def get_proof_by_company(self, company: str) -> List[AuditProof]:
        """
        Return all audit proofs issued for a given company.

        Args:
            company: Company name to filter by.

        Returns:
            List of AuditProof objects.
        """
        with self._lock:
            matches = [p for p in self._proofs.values() if p["company"] == company]
        return [AuditProof(**p) for p in matches]

    def export_certificate(self, proof_id: str) -> str:
        """
        Export a human-readable certificate for a stored proof.

        Args:
            proof_id: Target proof identifier.

        Returns:
            Formatted certificate text.

        Raises:
            ValueError: If proof_id is not found.
        """
        with self._lock:
            data = self._proofs.get(proof_id)
        if not data:
            raise ValueError(f"Proof '{proof_id}' not found.")

        lines = [
            "╔══════════════════════════════════════════════════════════╗",
            "║       CERTIFICAT D'AUDIT — NAYA BLOCKCHAIN PROOF         ║",
            "╠══════════════════════════════════════════════════════════╣",
            f"║  Proof ID        : {proof_id:<38} ║",
            f"║  Audit ID        : {data['audit_id']:<38} ║",
            f"║  Entreprise      : {data['company']:<38} ║",
            f"║  Type d'audit    : {data['audit_type']:<38} ║",
            f"║  Auditeur        : {data['auditor']:<38} ║",
            f"║  Horodatage bloc : {data['block_timestamp'][:38]:<38} ║",
            f"║  Réseau          : {data['chain_id']:<38} ║",
            f"║  TX Hash         : {data['tx_hash'][:38]:<38} ║",
            f"║  Vérifié         : {'OUI' if data['is_verified'] else 'NON':<38} ║",
            "╚══════════════════════════════════════════════════════════╝",
        ]
        return "\n".join(lines)

    def get_stats(self) -> Dict:
        """
        Return aggregate statistics for the dashboard.

        Returns:
            Dict with total_proofs, verified_proofs, companies_certified.
        """
        with self._lock:
            proofs = list(self._proofs.values())
        total = len(proofs)
        verified = sum(1 for p in proofs if p.get("is_verified"))
        companies = len({p["company"] for p in proofs})
        return {
            "total_proofs": total,
            "verified_proofs": verified,
            "companies_certified": companies,
        }


# ──────────────────────────────────────────────────────────────────────────────
# Singleton
# ──────────────────────────────────────────────────────────────────────────────

_blockchain: Optional[BlockchainProofOfAudit] = None


def get_blockchain_proof_of_audit() -> BlockchainProofOfAudit:
    """Return the process-wide singleton BlockchainProofOfAudit instance."""
    global _blockchain
    if _blockchain is None:
        _blockchain = BlockchainProofOfAudit()
    return _blockchain
