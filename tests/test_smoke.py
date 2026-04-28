#!/usr/bin/env python3
"""
NAYA V19 — Smoke Tests
Valide l'intégrité complète du système au démarrage.
Usage : python3 tests/test_smoke.py
"""
import sys
import os
import ast
import json
import time
from pathlib import Path
from importlib import import_module

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

# ── Compteurs ─────────────────────────────────────────────────────────────────
passed = []
failed = []
warnings = []


def ok(name: str, detail: str = ""):
    passed.append(name)
    print(f"  ✅ {name}" + (f" — {detail}" if detail else ""))


def fail(name: str, error: str):
    failed.append(name)
    print(f"  ❌ {name} — {error[:80]}")


def warn(name: str, detail: str):
    warnings.append(name)
    print(f"  ⚠️  {name} — {detail[:80]}")


def run_smoke_tests() -> bool:
    """Exécute tous les groupes de tests smoke. Retourne True si tout est OK."""
    global passed, failed, warnings
    passed = []
    failed = []
    warnings = []

    # ── GROUPE 1 : Structure fichiers ─────────────────────────────────────────
    print("\n📁  Structure du projet")
    print("=" * 58)

    critical_files = [
        "main.py",
        "requirements.txt",
        ".env.example",
        ".gitignore",
        "SECRETS/secrets_loader.py",
        "NAYA_CORE/execution/naya_brain.py",
        "NAYA_CORE/execution/providers/free_llm_provider.py",
        "NAYA_REVENUE_ENGINE/revenue_engine_v10.py",
        "NAYA_REVENUE_ENGINE/prospect_finder_v10.py",
        "NAYA_REVENUE_ENGINE/outreach_engine.py",
        "NAYA_REVENUE_ENGINE/payment_engine.py",
        "REAPERS/reapers_core.py",
        "api/routers/revenue.py",
        "api/routers/brain.py",
        "api/routers/integrations.py",
        "api/routers/system.py",
        "api/routers/business.py",
        "api/middleware.py",
        "bootstrap/registry/asset_registry.py",
        "NAYA_DASHBOARD/interface/naya_interface.py",
        "NAYA_DASHBOARD/interface/text_channel.py",
        "NAYA_DASHBOARD/interface/voice_channel.py",
        "tests/test_smoke.py",
    ]

    for f in critical_files:
        p = ROOT / f
        if p.exists():
            ok(f, f"{p.stat().st_size // 1024}KB")
        else:
            fail(f, "fichier manquant")

    # ── GROUPE 2 : Sécurité secrets ───────────────────────────────────────────
    print("\n🔐  Sécurité — vérification des secrets exposés")
    print("=" * 58)

    DANGEROUS_PATTERNS = ["sk-ant-api03-F7k1", "sk-proj-5vxC"]

    secrets_dir = ROOT / "SECRETS" / "keys"
    for fname in secrets_dir.rglob("*"):
        if fname.suffix in (".json", ".env", ".txt") and fname.is_file():
            try:
                content = fname.read_text(errors="replace")
                found = [p for p in DANGEROUS_PATTERNS if p in content]
                if found:
                    fail(f"CLÉS EXPOSÉES dans {fname.relative_to(ROOT)}", f"patterns: {found}")
                else:
                    ok(str(fname.relative_to(ROOT)), "propre")
            except Exception as e:
                warn(str(fname.relative_to(ROOT)), str(e))

    gitignore = (ROOT / ".gitignore").read_text()
    if "SECRETS/keys/*.json" in gitignore:
        ok(".gitignore couvre *.json", "")
    else:
        fail(".gitignore", "SECRETS/keys/*.json non couvert")

    # ── GROUPE 3 : Syntaxe Python tous les modules ────────────────────────────
    print("\n🐍  Syntaxe Python — scan complet")
    print("=" * 58)

    syntax_errors = 0
    files_scanned = 0

    for py_file in ROOT.rglob("*.py"):
        if "__pycache__" in str(py_file) or "archive" in str(py_file):
            continue
        try:
            src = py_file.read_text(encoding="utf-8", errors="replace")
            ast.parse(src)
            files_scanned += 1
        except SyntaxError as e:
            fail(f"Syntaxe {py_file.relative_to(ROOT)}", str(e))
            syntax_errors += 1

    if syntax_errors == 0:
        ok(f"Tous les fichiers Python ({files_scanned})", "syntaxe valide")

    # ── GROUPE 4 : Imports modules critiques ──────────────────────────────────
    print("\n📦  Imports modules critiques")
    print("=" * 58)

    modules_to_test = [
        ("SECRETS.secrets_loader",                               "load_all_secrets"),
        ("NAYA_CORE.execution.providers.free_llm_provider",      "get_free_llm"),
        ("NAYA_CORE.execution.naya_brain",                       "get_brain"),
        ("NAYA_REVENUE_ENGINE.revenue_engine_v10",               "get_revenue_engine_v10"),
        ("NAYA_REVENUE_ENGINE.prospect_finder_v10",              "get_prospect_finder_v10"),
        ("NAYA_REVENUE_ENGINE.outreach_engine",                  "OutreachEngine"),
        ("NAYA_REVENUE_ENGINE.payment_engine",                   "PaymentEngine"),
        ("NAYA_REVENUE_ENGINE.pipeline_tracker",                 "PipelineTracker"),
        ("NAYA_CORE.cash_engine_real",                           "get_cash_engine"),
        ("NAYA_CORE.conversion_engine",                          "get_conversion_engine"),
        ("NAYA_CORE.revenue_intelligence",                       "get_revenue_intelligence"),
        ("NAYA_CORE.money_notifier",                             "get_money_notifier"),
        ("NAYA_CORE.scheduler",                                  "get_scheduler"),
        ("NAYA_CORE.autonomous_engine",                          "get_autonomous_engine"),
        ("REAPERS.reapers_core",                                 "ReapersKernel"),
        ("BUSINESS_ENGINES.strategic_pricing_engine.pricing_engine", "StrategicPricingEngine"),
        ("EVOLUTION_SYSTEM.kpi_engine",                          "KPIEngine"),
        ("CONSTITUTION.invariants",                              "SystemInvariants"),
        ("NAYA_DASHBOARD.interface.naya_interface",              "NayaInterface"),
        ("NAYA_DASHBOARD.interface.text_channel",                "TextChannel"),
        ("NAYA_DASHBOARD.interface.voice_channel",               "VoiceChannel"),
        ("bootstrap.registry.asset_registry",                   "get_asset_registry"),
        ("api.middleware",                                       "NayaRateLimitMiddleware"),
        ("NAYA_DASHBOARD.NAYA_MONITORING",                       "MetricsCollector"),
        ("NAYA_DASHBOARD.NAYA_MONITORING",                       "MonitoringBridge"),
        ("NAYA_DASHBOARD.NAYA_SECURITY",                         "AuditTrail"),
        ("NAYA_ORCHESTRATION.orchestrator",                      "NayaOrchestrator"),
        ("api.routers.revenue",                                  "router"),
        ("api.routers.brain",                                    "router"),
        ("api.routers.integrations",                             "router"),
        ("api.routers.system",                                   "router"),
        ("api.routers.business",                                 "router"),
    ]

    for mod_path, attr in modules_to_test:
        try:
            m = import_module(mod_path)
            getattr(m, attr)
            ok(mod_path.split(".")[-1], attr)
        except ImportError as e:
            if "No module named 'fastapi'" in str(e) or "No module named 'uvicorn'" in str(e):
                warn(mod_path.split(".")[-1], f"dépendance: {e} — pip install -r requirements.txt")
            else:
                fail(mod_path.split(".")[-1], str(e))
        except AttributeError as e:
            fail(mod_path.split(".")[-1], f"attribut manquant: {e}")
        except Exception as e:
            warn(mod_path.split(".")[-1], str(e)[:60])

    # ── GROUPE 5 : Cohérence version ─────────────────────────────────────────
    print("\n🔖  Cohérence de version")
    print("=" * 58)

    main_src = (ROOT / "main.py").read_text()
    version_issues = []
    if "NAYA SUPREME V8" in main_src:
        version_issues.append("V8 trouvé dans main.py")
    if "NAYA SUPREME V7" in main_src:
        version_issues.append("V7 trouvé dans main.py")
    if 'VERSION = "14.0.0"' in main_src or "VERSION = '14.0.0'" in main_src:
        ok("VERSION string", "10.0.0")
    else:
        warn("VERSION string", "vérifier la valeur dans main.py")

    if version_issues:
        for issue in version_issues:
            fail("Version cohérence", issue)
    else:
        ok("Pas de versions résiduelles (V7/V8)", "")

    # ── GROUPE 6 : Pas de prints de debug dans modules core ─────────────────
    print("\n🔍  Prints de debug")
    print("=" * 58)

    debug_prints = []
    skip_dirs = {"tools", "tests", "archive", "__pycache__"}

    for py_file in ROOT.rglob("*.py"):
        parts = set(py_file.parts)
        if parts & skip_dirs:
            continue
        if "__pycache__" in str(py_file):
            continue
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8", errors="replace"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name) and node.func.id == "print":
                        debug_prints.append(f"{py_file.relative_to(ROOT)}:{node.lineno}")
        except Exception:
            pass

    if not debug_prints:
        ok("Zéro print() de debug dans les modules core", "")
    else:
        legitimate = {"main.py"}
        real_issues = [p for p in debug_prints if p.split(":")[0] not in legitimate]
        if not real_issues:
            ok("Prints de production — uniquement pré-logger légitimes dans main.py", "")
        else:
            for p in real_issues[:5]:
                warn("print() restant", p)
            if len(real_issues) > 5:
                warn("...", f"{len(real_issues) - 5} autres print() restants")

    # ── RÉSUMÉ ────────────────────────────────────────────────────────────────
    print("\n" + "=" * 58)
    total = len(passed) + len(failed)
    print(f"  Tests passés  : {len(passed)}/{total}")
    print(f"  Échecs        : {len(failed)}")
    print(f"  Avertissements: {len(warnings)}")
    print("=" * 58)

    if not failed:
        print("  🚀 SYSTÈME SAIN — prêt pour python3 main.py")
        return True
    else:
        print(f"  ❌ {len(failed)} problème(s) à corriger avant le démarrage:")
        for f in failed:
            print(f"     → {f}")
        return False


# ── Pytest smoke test wrapper ─────────────────────────────────────────────────
def test_smoke_system_health():
    """Pytest-compatible smoke test. Runs the full smoke suite."""
    result = run_smoke_tests()
    assert result, f"{len(failed)} problème(s) détectés : {failed}"


# ── Exécution directe ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    success = run_smoke_tests()
    sys.exit(0 if success else 1)
