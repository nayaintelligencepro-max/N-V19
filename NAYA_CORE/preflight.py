"""Préflight système NAYA.

Valide avant exécution: secrets, filesystem, dépendances minimales, et mode runtime.
"""

from __future__ import annotations

import importlib
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List

from SECRETS import validate_all_keys, validate_production_secrets


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str


def _check_write_paths() -> CheckResult:
    base = Path("data")
    try:
        base.mkdir(parents=True, exist_ok=True)
        probe = base / ".preflight_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return CheckResult("filesystem", True, "data/ writable")
    except Exception as exc:
        return CheckResult("filesystem", False, f"write failed: {type(exc).__name__}: {exc}")


def _check_dependencies() -> CheckResult:
    required = ["fastapi", "uvicorn", "pydantic", "sqlalchemy"]
    missing = []
    for mod in required:
        try:
            importlib.import_module(mod)
        except Exception:
            missing.append(mod)
    if missing:
        return CheckResult("dependencies", False, f"missing: {', '.join(missing)}")
    return CheckResult("dependencies", True, "core dependencies available")


def _check_secrets() -> CheckResult:
    report = validate_all_keys(strict=False)
    loaded = report.get("loaded_critical", 0)
    total = report.get("total_critical", 0)
    weak = validate_production_secrets(raise_on_weak=False)
    env = os.getenv("ENVIRONMENT", "development").lower()

    if env == "production" and weak:
        return CheckResult("secrets", False, f"weak secrets: {', '.join(weak)}")

    if loaded == 0:
        return CheckResult("secrets", False, f"0/{total} critical secrets")

    return CheckResult("secrets", True, f"{loaded}/{total} critical secrets configured")


def run_preflight() -> Dict[str, object]:
    """Exécute tous les checks de préflight."""
    checks: List[CheckResult] = [
        _check_write_paths(),
        _check_dependencies(),
        _check_secrets(),
    ]

    ok = all(c.ok for c in checks)
    return {
        "ok": ok,
        "environment": os.getenv("ENVIRONMENT", "development"),
        "checks": [asdict(c) for c in checks],
    }
