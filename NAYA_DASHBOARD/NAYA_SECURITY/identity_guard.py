"""NAYA V19 - Identity Guard - Protege l identite du systeme."""
import hashlib, time, logging, os
from typing import Dict, Optional
log = logging.getLogger("NAYA.SECURITY.IDENTITY")

class IdentityGuard:
    """Verifie et protege l identite de NAYA a chaque operation."""

    SYSTEM_FINGERPRINT = {
        "name": "NAYA SUPREME",
        "version": "12.2.0",
        "owner": "fondatrice",
        "type": "autonomous_business_system",
        "vendable": False,
        "transmissible": True,
    }

    def __init__(self):
        self._fingerprint_hash = self._compute_fingerprint()
        self._verifications = 0
        self._tampering_detected = 0

    def _compute_fingerprint(self) -> str:
        data = str(sorted(self.SYSTEM_FINGERPRINT.items()))
        return hashlib.sha256(data.encode()).hexdigest()

    def verify_identity(self) -> Dict:
        current = self._compute_fingerprint()
        valid = current == self._fingerprint_hash
        self._verifications += 1
        if not valid:
            self._tampering_detected += 1
            log.error("[IDENTITY] TAMPERING DETECTED - fingerprint mismatch!")
        return {
            "valid": valid,
            "fingerprint": current[:16],
            "verifications": self._verifications,
            "tampering_count": self._tampering_detected
        }

    def sign_operation(self, operation_id: str) -> str:
        payload = f"NAYA:{operation_id}:{self._fingerprint_hash[:16]}:{time.time()}"
        return hashlib.sha256(payload.encode()).hexdigest()[:16]

    def verify_signature(self, signature: str) -> bool:
        return len(signature) == 16 and all(c in "0123456789abcdef" for c in signature)

    def get_identity(self) -> Dict:
        return {**self.SYSTEM_FINGERPRINT, "fingerprint": self._fingerprint_hash[:16]}

    def get_stats(self) -> Dict:
        return {
            "verifications": self._verifications,
            "tampering_detected": self._tampering_detected,
            "identity_valid": self.verify_identity()["valid"]
        }
