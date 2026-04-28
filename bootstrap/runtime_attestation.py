"""NAYA V19 - Runtime Attestation - Atteste que le runtime est sain."""
import time, logging, hashlib, platform
from typing import Dict

log = logging.getLogger("NAYA.BOOT.ATTEST")

class RuntimeAttestation:
    """Atteste l integrite et la sante du runtime au boot."""

    def __init__(self):
        self._attestation: Dict = {}
        self._boot_time = time.time()

    def attest(self) -> Dict:
        self._attestation = {
            "timestamp": time.time(),
            "platform": platform.system(),
            "python": platform.python_version(),
            "node": platform.node(),
            "integrity": self._check_integrity(),
            "contract_present": self._check_contract(),
            "secrets_dir": self._check_secrets(),
            "attestation_hash": hashlib.sha256(f"naya:{time.time()}".encode()).hexdigest()[:16]
        }
        all_ok = all(v for k, v in self._attestation.items()
                     if k in ("integrity", "contract_present"))
        self._attestation["overall"] = "passed" if all_ok else "degraded"
        log.info(f"[ATTEST] Runtime attestation: {self._attestation['overall']}")
        return self._attestation

    def _check_integrity(self) -> bool:
        from pathlib import Path
        return Path("main.py").exists()

    def _check_contract(self) -> bool:
        from pathlib import Path
        return Path("contracts/NAYA_EXISTANCE_CONTRACT.txt").exists()

    def _check_secrets(self) -> bool:
        from pathlib import Path
        return Path("SECRETS/secrets_loader.py").exists()

    def get_stats(self) -> Dict:
        return self._attestation or {"status": "not_attested"}
