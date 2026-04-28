"""NAYA V19 - Interface Signature Validator."""
import hashlib, hmac, os, time
from typing import Dict, Optional

class InterfaceSignatureValidator:
    """Valide les signatures des messages entrants sur l interface."""

    def __init__(self):
        self._secret = os.getenv("NAYA_SECRET_KEY", "naya_default_key")
        self._validated = 0
        self._rejected = 0

    def sign(self, payload: str) -> str:
        return hmac.new(self._secret.encode(), payload.encode(), hashlib.sha256).hexdigest()[:24]

    def validate(self, payload: str, signature: str) -> bool:
        expected = self.sign(payload)
        valid = hmac.compare_digest(expected, signature)
        if valid:
            self._validated += 1
        else:
            self._rejected += 1
        return valid

    def create_signed_envelope(self, data: Dict) -> Dict:
        import json
        payload_str = json.dumps(data, sort_keys=True)
        return {"data": data, "signature": self.sign(payload_str), "ts": time.time()}

    def get_stats(self) -> Dict:
        return {"validated": self._validated, "rejected": self._rejected}
