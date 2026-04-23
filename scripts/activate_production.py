#!/usr/bin/env python3
"""
NAYA V19.3 — Activate Production Mode

Loads .env, validates all critical API keys, enables every ENABLE_* flag
(via config/production_flags.py), and prints a GO / NO-GO checklist.

Usage:
    python scripts/activate_production.py              # dry-run (print status)
    python scripts/activate_production.py --apply      # write enriched .env
    python scripts/activate_production.py --strict     # fail on any missing key
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT / ".env"


# Patterns that indicate a "real" (non-placeholder) value per family.
REAL_VALUE_PATTERNS: Dict[str, re.Pattern] = {
    "OPENAI_API_KEY":           re.compile(r"^sk-(proj-|svcacct-|[A-Za-z0-9])[A-Za-z0-9_-]{20,}"),
    "ANTHROPIC_API_KEY":        re.compile(r"^sk-ant-(api03-|admin-)?[A-Za-z0-9_-]{20,}"),
    "GROQ_API_KEY":             re.compile(r"^gsk_[A-Za-z0-9]{20,}"),
    "DEEPSEEK_API_KEY":         re.compile(r"^sk-[a-f0-9]{32}"),
    "GEMINI_API_KEY":           re.compile(r"^(AQ\.|AI)[A-Za-z0-9_-]{20,}"),
    "HUGGINGFACE_API_KEY":      re.compile(r"^hf_[A-Za-z0-9]{30,}"),
    "SENDGRID_API_KEY":         re.compile(r"^SG\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}"),
    "SERPER_API_KEY":           re.compile(r"^[a-f0-9]{40}$"),
    "SUPABASE_URL":             re.compile(r"^https://[a-z0-9]+\.supabase\.co$"),
    "SUPABASE_ANON_KEY":        re.compile(r"^eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$"),
    "SUPABASE_SERVICE_KEY":     re.compile(r"^eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$"),
    "TELEGRAM_BOT_TOKEN":       re.compile(r"^\d{8,}:AA[A-Za-z0-9_-]{30,}$"),
    "TELEGRAM_CHAT_ID":         re.compile(r"^-?\d+$"),
    "STRIPE_SECRET_KEY":        re.compile(r"^sk_(live|test)_[A-Za-z0-9]{20,}"),
    "STRIPE_PUBLISHABLE_KEY":   re.compile(r"^pk_(live|test)_[A-Za-z0-9]{20,}"),
    "SHOPIFY_ACCESS_TOKEN":     re.compile(r"^shpat_[a-f0-9]{30,}$"),
    "NOTION_TOKEN":             re.compile(r"^ntn_[A-Za-z0-9]{30,}"),
    "N8N_API_KEY":              re.compile(r"^eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$"),
    "GOOGLE_OAUTH_CLIENT_ID":   re.compile(r"^\d+-[a-z0-9]+\.apps\.googleusercontent\.com$"),
    "GOOGLE_OAUTH_CLIENT_SECRET": re.compile(r"^GOCSPX-[A-Za-z0-9_-]{20,}$"),
    "RENDER_API_KEY":           re.compile(r"^rnd_[A-Za-z0-9]{20,}"),
    "VERCEL_TOKEN":             re.compile(r"^vcp_[A-Za-z0-9]{20,}"),
    "DOCKER_TOKEN":             re.compile(r"^dckr_pat_[A-Za-z0-9_-]{15,}"),
    "TIKTOK_ACCESS_TOKEN":      re.compile(r"^[A-Za-z0-9_-]{20,}$"),
    "PAYPAL_ME_URL":            re.compile(r"^https://(www\.)?paypal\.me/.+"),
    "WHATSAPP_LINK":            re.compile(r"^https://wa\.me/.+"),
}

# Pipelines that REQUIRE at least one key from each set to be real.
REQUIREMENTS: Dict[str, List[List[str]]] = {
    "LLM (≥1 required)": [
        ["ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GROQ_API_KEY", "DEEPSEEK_API_KEY", "GEMINI_API_KEY", "HUGGINGFACE_API_KEY"],
    ],
    "Hunt (Serper)": [["SERPER_API_KEY"]],
    "Email outreach": [["SENDGRID_API_KEY"]],
    "Telegram notif": [["TELEGRAM_BOT_TOKEN"], ["TELEGRAM_CHAT_ID"]],
    "WhatsApp outreach": [["WHATSAPP_LINK"]],
    "Payment collection": [["PAYPAL_ME_URL", "STRIPE_SECRET_KEY", "DEBLOCK_ME_URL"]],
    "Persistence (Supabase)": [["SUPABASE_URL", "SUPABASE_ANON_KEY"]],
}

# Every ENABLE_* flag we'll flip to true in --apply mode.
ENABLE_FLAGS: List[str] = [
    "NAYA_PRODUCTION_MODE",
    "ENABLE_VECTOR_MEMORY",
    "ENABLE_SELF_HEALING",
    "ENABLE_FEEDBACK_LOOP",
    "ENABLE_METRICS",
    "ENABLE_SUBSCRIPTIONS",
    "ENABLE_CONTRACT_GENERATOR",
    "ENABLE_OUTREACH_EMAIL",
    "ENABLE_OUTREACH_WHATSAPP",
    "ENABLE_OUTREACH_TELEGRAM",
    "ENABLE_PAIN_HUNT_AUTONOMOUS",
    "ENABLE_GUARDIAN_AUTOSCAN",
    "ENABLE_GUARDIAN_AUTOREPAIR",
    "ENABLE_PARALLEL_PIPELINE",
    "ENABLE_REVENUE_TRACKER",
]


def load_env(path: Path) -> Dict[str, str]:
    if not path.exists():
        return {}
    env: Dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def is_real_value(key: str, value: str) -> bool:
    if not value:
        return False
    placeholder_markers = {
        "your_", "placeholder", "example", "change_this", "xxxx", "change_me",
        "here", "_here", "youru", "YOUR_", "YOURUSERNAME",
    }
    v_low = value.lower()
    if any(m in v_low for m in placeholder_markers):
        return False
    pattern = REAL_VALUE_PATTERNS.get(key)
    if pattern is None:
        # Fallback: non-empty & not obviously placeholder
        return len(value) >= 8
    return bool(pattern.match(value))


def audit(env: Dict[str, str]) -> Tuple[List[str], List[str], Dict[str, bool]]:
    """Return (ok_msgs, missing_msgs, per_key_status)."""
    ok: List[str] = []
    missing: List[str] = []
    per_key: Dict[str, bool] = {}

    for pipeline, groups in REQUIREMENTS.items():
        pipeline_ok = True
        for group in groups:
            group_ok = False
            for key in group:
                val = env.get(key, "")
                good = is_real_value(key, val)
                per_key[key] = good
                if good:
                    group_ok = True
            if not group_ok:
                pipeline_ok = False
                missing.append(f"{pipeline}: needs at least one of {group}")
        if pipeline_ok:
            ok.append(f"{pipeline}: OK")

    return ok, missing, per_key


def apply_flags(env: Dict[str, str]) -> Dict[str, str]:
    new = dict(env)
    for f in ENABLE_FLAGS:
        new[f] = "true"
    return new


def write_env(path: Path, env: Dict[str, str]) -> None:
    # Preserve ordering: write categories in a predictable order.
    sorted_keys = sorted(env.keys())
    lines = [
        "# ==================== NAYA V19.3 — PRODUCTION .env ====================",
        "# Auto-updated by scripts/activate_production.py",
        "# DO NOT COMMIT.",
        "",
    ]
    for k in sorted_keys:
        val = env[k]
        if " " in val or any(c in val for c in ['#', '$', '"', "'"]):
            val = f'"{val}"'
        lines.append(f"{k}={val}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="NAYA production activation")
    parser.add_argument("--apply", action="store_true", help="Write ENABLE_* flags to .env")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on any missing required key")
    args = parser.parse_args()

    if not ENV_PATH.exists():
        print(f"❌ .env not found at {ENV_PATH}. Run scripts/parse_raw_keys.py first.", file=sys.stderr)
        return 2

    env = load_env(ENV_PATH)
    ok, missing, per_key = audit(env)

    print("═" * 72)
    print("🚀 NAYA V19.3 — PRODUCTION ACTIVATION")
    print("═" * 72)
    print(f"📦 {len(env)} variables loaded from {ENV_PATH.name}")
    real_count = sum(1 for v in per_key.values() if v)
    print(f"🔑 {real_count}/{len(per_key)} critical keys validated as real values")
    print()

    print("── GO ──")
    for line in ok:
        print(f"  ✅ {line}")
    print()
    if missing:
        print("── NO-GO ──")
        for line in missing:
            print(f"  ❌ {line}")
        print()

    if args.apply:
        env = apply_flags(env)
        write_env(ENV_PATH, env)
        print(f"✅ ENABLE_* flags written to {ENV_PATH.name} ({len(ENABLE_FLAGS)} flags set to true)")

    if args.strict and missing:
        print("\n❌ STRICT mode: missing keys → exit 1", file=sys.stderr)
        return 1
    if missing:
        print("ℹ️  Non-strict mode: missing keys won't block startup, affected pipelines will no-op.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
