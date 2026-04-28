"""NAYA V19 - Contract Provider - Fournit les contrats systeme."""
import logging, json
from typing import Dict, Optional
from pathlib import Path
log = logging.getLogger("NAYA.CONTRACT")

class ContractProvider:
    CONTRACTS_DIR = Path("contracts")

    def get_existence_contract(self) -> Optional[str]:
        f = self.CONTRACTS_DIR / "NAYA_EXISTANCE_CONTRACT.txt"
        if f.exists():
            return f.read_text(encoding="utf-8", errors="replace")
        return None

    def verify_contract_integrity(self) -> Dict:
        contract = self.get_existence_contract()
        if not contract:
            return {"valid": False, "reason": "Contract file missing"}
        has_naya = "NAYA" in contract
        has_reapers = "REAPERS" in contract
        has_founder = "fondatrice" in contract.lower()
        return {
            "valid": has_naya and has_reapers and has_founder,
            "naya_referenced": has_naya,
            "reapers_referenced": has_reapers,
            "founder_referenced": has_founder,
            "length": len(contract)
        }
