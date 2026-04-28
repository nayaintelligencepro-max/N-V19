"""NAYA V19 - Contract Validator - Valide le contrat d existence."""
import logging, hashlib
from typing import Dict, Optional
from pathlib import Path

log = logging.getLogger("NAYA.KERNEL.CONTRACT")

class ContractValidator:
    """Valide que le contrat d existence est intact et respecte."""

    CONTRACT_PATH = Path("contracts/NAYA_EXISTANCE_CONTRACT.txt")
    REQUIRED_ELEMENTS = [
        "NAYA", "REAPERS", "fondatrice", "souverain",
        "confidentialite", "loyaute", "fidelite",
        "non destinee a la vente", "business"
    ]

    def validate(self) -> Dict:
        if not self.CONTRACT_PATH.exists():
            return {"valid": False, "reason": "Contract file missing"}

        try:
            content = self.CONTRACT_PATH.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return {"valid": False, "reason": str(e)}

        content_lower = content.lower()
        missing = [elem for elem in self.REQUIRED_ELEMENTS
                   if elem.lower() not in content_lower]

        integrity_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

        return {
            "valid": len(missing) == 0,
            "missing_elements": missing,
            "integrity_hash": integrity_hash,
            "length": len(content),
            "all_elements_present": len(missing) == 0
        }

    def get_contract_summary(self) -> Dict:
        result = self.validate()
        result["path"] = str(self.CONTRACT_PATH)
        return result
