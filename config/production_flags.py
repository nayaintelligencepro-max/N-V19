"""
NAYA V19.3 — Production feature flags.

Single source of truth for ENABLE_* flags. Every agent / pipeline / integration
reads from here instead of hardcoding a boolean.

Usage:
    from config.production_flags import flags
    if flags.outreach_email:
        send_email(...)

Override any flag via env var (ENABLE_OUTREACH_EMAIL=true|false). Master switch
NAYA_PRODUCTION_MODE=true turns every optional flag ON by default.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field, fields
from typing import Any, Dict


def _b(name: str, default: bool) -> bool:
    """Parse boolean env var with production override."""
    raw = os.environ.get(name, "")
    if raw:
        return raw.strip().lower() in {"1", "true", "yes", "on", "y"}
    if _PRODUCTION_MODE and default is False:
        return False  # still respect explicit False defaults
    if _PRODUCTION_MODE:
        return True
    return default


_PRODUCTION_MODE: bool = os.environ.get("NAYA_PRODUCTION_MODE", "").strip().lower() in {
    "1", "true", "yes", "on", "y"
}


@dataclass(frozen=True)
class ProductionFlags:
    """Feature flags for NAYA V19.3.

    Defaults are **dev-safe** (most False). When NAYA_PRODUCTION_MODE=true,
    optional flags flip ON automatically. Any explicit env var still wins.
    """

    # Master switch
    production_mode: bool = field(default_factory=lambda: _PRODUCTION_MODE)

    # Core platform
    vector_memory: bool = field(default_factory=lambda: _b("ENABLE_VECTOR_MEMORY", True))
    self_healing: bool = field(default_factory=lambda: _b("ENABLE_SELF_HEALING", True))
    feedback_loop: bool = field(default_factory=lambda: _b("ENABLE_FEEDBACK_LOOP", True))
    metrics: bool = field(default_factory=lambda: _b("ENABLE_METRICS", True))

    # Revenue pipelines
    subscriptions: bool = field(default_factory=lambda: _b("ENABLE_SUBSCRIPTIONS", True))
    lightning_payments: bool = field(default_factory=lambda: _b("ENABLE_LIGHTNING_PAYMENTS", False))
    contract_generator: bool = field(default_factory=lambda: _b("ENABLE_CONTRACT_GENERATOR", True))

    # Outreach channels
    outreach_email: bool = field(default_factory=lambda: _b("ENABLE_OUTREACH_EMAIL", False))
    outreach_whatsapp: bool = field(default_factory=lambda: _b("ENABLE_OUTREACH_WHATSAPP", False))
    outreach_telegram: bool = field(default_factory=lambda: _b("ENABLE_OUTREACH_TELEGRAM", False))
    outreach_linkedin: bool = field(default_factory=lambda: _b("ENABLE_OUTREACH_LINKEDIN", False))

    # Agents
    pain_hunt_autonomous: bool = field(default_factory=lambda: _b("ENABLE_PAIN_HUNT_AUTONOMOUS", False))
    guardian_autoscan: bool = field(default_factory=lambda: _b("ENABLE_GUARDIAN_AUTOSCAN", True))
    guardian_autorepair: bool = field(default_factory=lambda: _b("ENABLE_GUARDIAN_AUTOREPAIR", True))
    parallel_pipeline: bool = field(default_factory=lambda: _b("ENABLE_PARALLEL_PIPELINE", True))
    revenue_tracker: bool = field(default_factory=lambda: _b("ENABLE_REVENUE_TRACKER", True))

    # Sales validation gates (defensive — must be opted-in, not flipped by prod mode)
    pre_deploy_gate_strict: bool = field(
        default_factory=lambda: os.environ.get("NAYA_PRE_DEPLOY_GATE_STRICT", "true").lower() == "true"
    )

    def as_dict(self) -> Dict[str, Any]:
        return {f.name: getattr(self, f.name) for f in fields(self)}

    def summary(self) -> str:
        on = sum(1 for f in fields(self) if getattr(self, f.name))
        total = len(fields(self))
        return f"ProductionFlags: {on}/{total} enabled (production_mode={self.production_mode})"


flags = ProductionFlags()


def refresh() -> ProductionFlags:
    """Re-read flags from env (useful in tests / after dotenv reload)."""
    global flags, _PRODUCTION_MODE
    _PRODUCTION_MODE = os.environ.get("NAYA_PRODUCTION_MODE", "").strip().lower() in {
        "1", "true", "yes", "on", "y"
    }
    flags = ProductionFlags()
    return flags


if __name__ == "__main__":
    print(flags.summary())
    for name, val in flags.as_dict().items():
        print(f"  {name:30s} = {val}")
