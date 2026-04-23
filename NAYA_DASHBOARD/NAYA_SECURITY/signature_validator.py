"""NAYA V19 - Signature Validator - Valide les signatures des requetes."""
import hashlib, hmac, time, logging, os
from typing import Dict, Optional

log = logging.getLogger("NAYA.SECURITY.SIG")

class SignatureValidator:
    """Valide les signatures HMAC des requetes entrantes."""

    def __init__(self):
        self._secret = os.getenv("NAYA_SECRET_KEY", "naya_default_secret_change_in_production")
        self._validated = 0
        self._rejected = 0

    def sign(self, payload: str) -> str:
        return hmac.new(self._secret.encode(), payload.encode(), hashlib.sha256).hexdigest()[:32]

    def validate(self, payload: str, signature: str) -> bool:
        expected = self.sign(payload)
        valid = hmac.compare_digest(expected, signature)
        if valid:
            self._validated += 1
        else:
            self._rejected += 1
            log.warning("[SIG] Invalid signature rejected")
        return valid

    def sign_request(self, data: Dict) -> Dict:
        """Signe une requete sortante."""
        import json
        payload = json.dumps(data, sort_keys=True)
        sig = self.sign(payload)
        return {"data": data, "signature": sig, "timestamp": time.time()}

    def validate_request(self, signed_request: Dict) -> Dict:
        import json
        data = signed_request.get("data", {})
        sig = signed_request.get("signature", "")
        payload = json.dumps(data, sort_keys=True)
        valid = self.validate(payload, sig)
        # Check timestamp freshness (5 min max)
        ts = signed_request.get("timestamp", 0)
        fresh = (time.time() - ts) < 300
        return {"valid": valid and fresh, "signature_ok": valid, "fresh": fresh}

    def get_stats(self) -> Dict:
        return {"validated": self._validated, "rejected": self._rejected}
