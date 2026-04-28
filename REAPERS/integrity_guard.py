"""NAYA V19 - REAPERS Integrity Guard - Verification d integrite systeme."""
import hashlib, time, logging, os
from typing import Dict, List
from pathlib import Path
log = logging.getLogger("NAYA.REAPERS.INTEGRITY")

class IntegrityGuard:
    """Alias souverain pour ReapersIntegrityGuard."""

    def __init__(self, targets=None):
        self._guard = ReapersIntegrityGuard()
        self._targets = targets or {}

    def create_baseline(self):
        return self._guard._init_baselines()

    def check_integrity(self):
        result = self._guard.verify_all()
        # result["results"] maps filename → "OK" | "MODIFIED" | "MISSING"
        return {k: (v == "OK") for k, v in result.get("results", {}).items()}


class ReapersIntegrityGuard:
    """Verifie l integrite des fichiers critiques du systeme."""

    CRITICAL_FILES = [
        "main.py", "CONSTITUTION/invariants.py", "CONSTITUTION/governance_rules.py",
        "contracts/NAYA_EXISTANCE_CONTRACT.txt", "SECRETS/secrets_loader.py",
    ]

    def __init__(self):
        self._baselines: Dict[str, str] = {}
        self._violations: List[Dict] = []
        self._init_baselines()

    def _init_baselines(self) -> None:
        for f in self.CRITICAL_FILES:
            path = Path(f)
            if path.exists():
                content = path.read_bytes()
                self._baselines[f] = hashlib.sha256(content).hexdigest()

    def verify_all(self) -> Dict:
        results = {}
        violations = []
        for f, expected_hash in self._baselines.items():
            path = Path(f)
            if not path.exists():
                results[f] = "MISSING"
                violations.append({"file": f, "issue": "missing"})
                continue
            current = hashlib.sha256(path.read_bytes()).hexdigest()
            if current != expected_hash:
                results[f] = "MODIFIED"
                violations.append({"file": f, "issue": "modified"})
            else:
                results[f] = "OK"
        if violations:
            self._violations.extend(violations)
            log.warning(f"[INTEGRITY] {len(violations)} violations detectees!")
        return {"files_checked": len(self._baselines), "violations": len(violations), "results": results}

    def update_baseline(self, filepath: str) -> bool:
        path = Path(filepath)
        if path.exists():
            self._baselines[filepath] = hashlib.sha256(path.read_bytes()).hexdigest()
            return True
        return False

    def get_stats(self) -> Dict:
        return {
            "monitored_files": len(self._baselines),
            "total_violations": len(self._violations)
        }
