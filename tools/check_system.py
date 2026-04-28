#!/usr/bin/env python3
"""NAYA V19 — Diagnostic système. Usage: python3 tools/check_system.py"""
import os, sys
from pathlib import Path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

# Charger les secrets
try:
    from SECRETS.secrets_loader import load_all_secrets
    r = load_all_secrets()
    print(f"🔐 {r.get('loaded',0)} variables chargées ({r.get('real_keys',0)} clés actives)\n")
except Exception as e:
    print(f"⚠️  Secrets: {e}\n")

from SECRETS.secrets_loader import is_configured

print("=" * 58)
print("  NAYA SUPREME V10 — Diagnostic")
print("=" * 58)

# Clés critiques avec fichier source
keys = [
    ("LLM Claude",    "ANTHROPIC_API_KEY",     "llm.env"),
    ("LLM Groq",      "GROQ_API_KEY",           "llm.env"),
    ("LLM OpenAI",    "OPENAI_API_KEY",         "llm.env"),
    ("Telegram Bot",  "TELEGRAM_BOT_TOKEN",    "notifications.env"),
    ("Telegram Chat", "TELEGRAM_CHAT_ID",      "notifications.env"),
    ("PayPal.me URL", "PAYPAL_ME_URL",     "payments.env"),
    ("Deblock URL",   "DEBLOCK_ME_URL",    "payments.env"),
    ("SendGrid",      "SENDGRID_API_KEY",      "notifications.env"),
    ("Email From",    "EMAIL_FROM",            "notifications.env"),
    ("Apollo.io",     "APOLLO_API_KEY",        "market_data.env"),
    ("Hunter.io",     "HUNTER_IO_API_KEY",     "market_data.env"),
    ("Serper Search", "SERPER_API_KEY",        "market_data.env"),
    ("LinkedIn",      "LINKEDIN_ACCESS_TOKEN", "social_media/.env"),
    ("ElevenLabs",    "ELEVENLABS_API_KEY",    "voice.env"),
    ("Notion",        "NOTION_TOKEN",          "ecommerce/.env"),
    ("Shopify",       "SHOPIFY_ACCESS_TOKEN",  "ecommerce/.env"),
]

configured = 0
for label, key, file in keys:
    ok = is_configured(key)
    if ok:
        configured += 1
    val_preview = os.environ.get(key, "")[:12] + "..." if ok else f"SECRETS/keys/{file}"
    status = "✅" if ok else "⚠️ "
    print(f"  {status} {label:<25} {val_preview}")

print(f"\n  Clés actives: {configured}/{len(keys)}")

# Test modules Python
print("\n  Modules Python:")
from importlib import import_module

modules = [
    ("Revenue Engine V10", "NAYA_REVENUE_ENGINE.revenue_engine_v10", "get_revenue_engine_v10"),
    ("Cash Engine",        "NAYA_CORE.cash_engine_real",              "get_cash_engine"),
    ("Outreach Engine",    "NAYA_REVENUE_ENGINE.outreach_engine",     "OutreachEngine"),
    ("Payment Engine",     "NAYA_REVENUE_ENGINE.payment_engine",      "PaymentEngine"),
    ("Prospect Finder V10","NAYA_REVENUE_ENGINE.prospect_finder_v10", "get_prospect_finder_v10"),
    ("Money Notifier",     "NAYA_CORE.money_notifier",                "get_money_notifier"),
    ("LLM Brain",          "NAYA_CORE.execution.naya_brain",          "get_brain"),
    ("FreeLLM Provider",   "NAYA_CORE.execution.providers.free_llm_provider", "get_free_llm"),
    ("Sovereign Engine",   "NAYA_CORE.naya_sovereign_engine",         "get_sovereign"),
    ("Scheduler",          "NAYA_CORE.scheduler",                     "get_scheduler"),
    ("Apollo Integ.",      "NAYA_CORE.integrations.apollo_integration","get_apollo"),
    ("SendGrid Integ.",    "NAYA_CORE.integrations.sendgrid_integration","get_sendgrid"),
    ("REAPERS",            "REAPERS.reapers_core",                    "ReapersKernel"),
]

mok = merr = 0
for label, mod, fn in modules:
    try:
        m = import_module(mod)
        getattr(m, fn)
        print(f"  ✅ {label}")
        mok += 1
    except Exception as e:
        print(f"  ❌ {label}: {str(e)[:50]}")
        merr += 1

print(f"\n  Modules OK: {mok}/{mok + merr}")
print("\n" + "=" * 58)

# Verdict
if configured >= 4 and merr == 0:
    print("  🚀 SYSTÈME PRÊT — python3 main.py")
elif merr == 0:
    print("  ⚡ Modules OK — Ajouter les clés dans SECRETS/keys/")
    critical = all(is_configured(k) for k in ["TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"])
    if not critical:
        print("  Minimum requis:")
        print("    → SECRETS/keys/llm.env:            GROQ_API_KEY (gratuit) ou ANTHROPIC_API_KEY")
        print("    → SECRETS/keys/notifications.env:  TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID")
        print("    → SECRETS/keys/payments.env:       PAYPAL_ME_URL (optionnel)")
else:
    print("  ⚠️  Corriger les modules cassés")
print("=" * 58 + "\n")
