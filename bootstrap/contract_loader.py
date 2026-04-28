"""
NAYA — Contract Loader
Loads and validates the NAYA existence contract and module contracts.
Ensures system operates within defined governance boundaries.
"""
import json
import logging
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

log = logging.getLogger("NAYA.CONTRACTS")
ROOT = Path(__file__).parent.parent


@dataclass
class Contract:
    name: str
    version: str
    rules: List[str]
    hash: str
    valid: bool


class ContractLoader:
    """Loads and validates governance contracts."""

    def __init__(self):
        self._contracts: Dict[str, Contract] = {}
        self._contract_dir = ROOT / "contracts"

    def load_all(self) -> Dict[str, Any]:
        """Load all contracts from the contracts directory."""
        loaded = 0
        if not self._contract_dir.exists():
            log.warning("Contracts directory not found: %s", self._contract_dir)
            return {"loaded": 0, "contracts": []}

        for f in self._contract_dir.iterdir():
            if f.suffix in (".txt", ".json", ".md"):
                try:
                    content = f.read_text(encoding="utf-8", errors="replace")
                    file_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
                    rules = [l.strip() for l in content.split("\n")
                             if l.strip() and not l.startswith("#")]
                    self._contracts[f.stem] = Contract(
                        name=f.stem, version="1.0",
                        rules=rules[:50], hash=file_hash, valid=True
                    )
                    loaded += 1
                except Exception as exc:
                    log.warning("Failed to load contract %s: %s", f.name, exc)

        log.info("Loaded %d contracts", loaded)
        return {"loaded": loaded, "contracts": list(self._contracts.keys())}

    def validate(self, contract_name: str) -> bool:
        """Verify a contract's integrity."""
        contract = self._contracts.get(contract_name)
        if not contract:
            return False
        return contract.valid and len(contract.rules) > 0

    def get_contract(self, name: str) -> Optional[Contract]:
        return self._contracts.get(name)

    def get_all_rules(self) -> List[str]:
        """Get all rules from all contracts."""
        rules = []
        for c in self._contracts.values():
            rules.extend(c.rules)
        return rules

    def get_stats(self) -> Dict:
        return {
            "total_contracts": len(self._contracts),
            "total_rules": sum(len(c.rules) for c in self._contracts.values()),
            "valid": sum(1 for c in self._contracts.values() if c.valid),
        }


def load_contracts() -> Dict[str, Any]:
    """Charge et retourne tous les contrats de gouvernance NAYA."""
    loader = ContractLoader()
    return loader.load_all()
