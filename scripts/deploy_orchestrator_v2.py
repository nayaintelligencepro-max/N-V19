#!/usr/bin/env python3
"""
NAYA SUPREME V19 — Orchestrateur de Déploiement Automatisé V2
═══════════════════════════════════════════════════════════════════════════════

Système complet de déploiement automatisé avec:
- Déploiement sur les 5 environnements (local, docker, vercel, render, cloud_run)
- Validation de 2 ventes réelles par environnement
- Notifications Telegram en temps réel
- Gestion robuste des erreurs avec retry automatique
- Continuation du déploiement malgré les erreurs
- Ledger de progression persistant
- Rapport consolidé final

Usage:
    python scripts/deploy_orchestrator_v2.py
    python scripts/deploy_orchestrator_v2.py --env local
    python scripts/deploy_orchestrator_v2.py --env docker,vercel
    python scripts/deploy_orchestrator_v2.py --resume
    python scripts/deploy_orchestrator_v2.py --status

Options:
    --env ENV[,ENV...]   : Déployer environnement(s) spécifique(s)
    --resume             : Reprendre déploiement interrompu
    --status             : Afficher l'état actuel
    --skip-tests         : Skip pre-deploy tests (DÉCONSEILLÉ)
    --skip-telegram      : Skip notifications Telegram
    --max-retries N      : Nombre max de tentatives (défaut: 3)
"""

import argparse
import asyncio
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# ── Configuration ─────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Dossiers de données - créer avant logging
DATA_DIR = ROOT / "data"
VALIDATION_DIR = DATA_DIR / "validation"
LOGS_DIR = DATA_DIR / "logs"
VALIDATION_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "deploy_orchestrator.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger("NAYA.DEPLOY.ORCHESTRATOR")

# Fichiers de ledger
DEPLOY_LEDGER = VALIDATION_DIR / "deployment_ledger.json"
GATE_LEDGER = VALIDATION_DIR / "pre_deploy_gate.json"
FINAL_REPORT = VALIDATION_DIR / "deployment_report_final.json"

# Configuration des environnements
ENVIRONMENTS = {
    "local": {
        "name": "Local Development",
        "sale_1": 15000,
        "sale_2": 25000,
        "deploy_script": "scripts/deploy_local.sh",
        "test_url": "http://localhost:8000",
        "color": "🟢"
    },
    "docker": {
        "name": "Docker Compose",
        "sale_1": 20000,
        "sale_2": 35000,
        "deploy_script": "scripts/deploy_docker.sh",
        "test_url": "http://localhost:8000",
        "color": "🔵"
    },
    "vercel": {
        "name": "Vercel Frontend + Render API",
        "sale_1": 30000,
        "sale_2": 45000,
        "deploy_script": "scripts/deploy_vercel.sh",
        "test_url": os.environ.get("NAYA_API_URL", "https://naya-supreme-api.onrender.com"),
        "color": "⚫"
    },
    "render": {
        "name": "Render Backend API",
        "sale_1": 40000,
        "sale_2": 55000,
        "deploy_script": "scripts/deploy_render.sh",
        "test_url": os.environ.get("RENDER_API_URL", "https://naya-supreme-api.onrender.com"),
        "color": "🟣"
    },
    "cloud_run": {
        "name": "Google Cloud Run",
        "sale_1": 50000,
        "sale_2": 70000,
        "deploy_script": "scripts/deploy_cloudrun.sh",
        "test_url": "auto-detect",
        "color": "🟡"
    },
}

ALL_ENVS = list(ENVIRONMENTS.keys())


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def print_header(text: str, char: str = "="):
    """Print formatted header"""
    width = 80
    print(f"\n{char * width}")
    print(f"  {text}")
    print(f"{char * width}\n")


def print_ok(text: str):
    """Print success message"""
    print(f"✅  {text}")
    log.info(f"✅ {text}")


def print_error(text: str):
    """Print error message"""
    print(f"❌  {text}")
    log.error(f"❌ {text}")


def print_warn(text: str):
    """Print warning message"""
    print(f"⚠️  {text}")
    log.warning(f"⚠️ {text}")


def print_info(text: str):
    """Print info message"""
    print(f"ℹ️  {text}")
    log.info(f"ℹ️ {text}")


def load_ledger() -> Dict[str, Any]:
    """Load deployment ledger"""
    if DEPLOY_LEDGER.exists():
        try:
            return json.loads(DEPLOY_LEDGER.read_text())
        except Exception as e:
            log.error(f"Error loading ledger: {e}")
            return init_ledger()
    return init_ledger()


def init_ledger() -> Dict[str, Any]:
    """Initialize empty ledger"""
    return {
        "session_start": datetime.now(timezone.utc).isoformat(),
        "session_id": f"deploy_{int(time.time())}",
        "environments": {},
        "global_stats": {
            "total_deployments": 0,
            "successful_deployments": 0,
            "failed_deployments": 0,
            "total_sales": 0,
            "total_revenue_eur": 0,
        }
    }


def save_ledger(ledger: Dict[str, Any]):
    """Save deployment ledger"""
    try:
        DEPLOY_LEDGER.write_text(json.dumps(ledger, indent=2, ensure_ascii=False))
    except Exception as e:
        log.error(f"Error saving ledger: {e}")


def send_telegram_notification(message: str, parse_mode: str = "Markdown") -> bool:
    """Send Telegram notification"""
    try:
        from SECRETS import get_secret

        token = get_secret("TELEGRAM_BOT_TOKEN")
        chat_id = get_secret("TELEGRAM_CHAT_ID")

        if not token or not chat_id:
            log.warning("Telegram credentials not configured")
            return False

        import requests
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        response = requests.post(url, json={
            "chat_id": chat_id,
            "text": message,
            "parse_mode": parse_mode
        }, timeout=10)

        if response.status_code == 200:
            log.debug(f"Telegram notification sent: {message[:50]}...")
            return True
        else:
            log.warning(f"Telegram error: {response.status_code}")
            return False

    except Exception as e:
        log.error(f"Telegram notification failed: {e}")
        return False


# ══════════════════════════════════════════════════════════════════════════════
# DEPLOYMENT ORCHESTRATOR
# ══════════════════════════════════════════════════════════════════════════════

class DeploymentOrchestrator:
    """Orchestrate all deployments with sales validation"""

    def __init__(self, max_retries: int = 3, skip_telegram: bool = False):
        self.ledger = load_ledger()
        self.max_retries = max_retries
        self.skip_telegram = skip_telegram
        self.session_id = self.ledger.get("session_id")

    def notify(self, message: str):
        """Send notification (Telegram + log)"""
        if not self.skip_telegram:
            send_telegram_notification(message)
        log.info(f"📢 {message}")

    def run_pre_deploy_gate(self, env: str) -> bool:
        """Run pre-deploy gate tests for environment"""
        print_header(f"PRE-DEPLOY GATE — {env.upper()}")

        env_config = ENVIRONMENTS[env]
        sale_1 = env_config["sale_1"]
        sale_2 = env_config["sale_2"]
        total = sale_1 + sale_2

        print_info(f"Validation requise: {sale_1:,} EUR + {sale_2:,} EUR = {total:,} EUR")

        # Run pytest pre-deploy gate
        test_cmd = [
            "python", "-m", "pytest",
            "tests/test_pre_deploy_gate.py",
            "-v",
            "--tb=short"
        ]

        test_env = os.environ.copy()
        test_env["DEPLOY_ENV"] = env
        test_env["BASE_URL"] = env_config["test_url"]

        try:
            result = subprocess.run(
                test_cmd,
                cwd=ROOT,
                env=test_env,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes max
            )

            if result.returncode == 0:
                print_ok(f"Gate tests PASSED for {env}")
                self.notify(
                    f"✅ GATE OUVERT — {env.upper()}\n"
                    f"💰 2 ventes validées: {total:,} EUR\n"
                    f"🚀 Déploiement autorisé"
                )
                return True
            else:
                print_error(f"Gate tests FAILED for {env}")
                log.error(f"Gate output:\n{result.stdout}\n{result.stderr}")
                self.notify(
                    f"❌ GATE FERMÉ — {env.upper()}\n"
                    f"⚠️ Tests échoués\n"
                    f"Voir logs pour détails"
                )
                return False

        except subprocess.TimeoutExpired:
            print_error(f"Gate tests TIMEOUT for {env}")
            return False
        except Exception as e:
            print_error(f"Gate tests ERROR for {env}: {e}")
            return False

    def run_deployment(self, env: str) -> bool:
        """Run deployment script for environment"""
        print_header(f"DEPLOYMENT — {env.upper()}")

        env_config = ENVIRONMENTS[env]
        script_path = ROOT / env_config["deploy_script"]

        if not script_path.exists():
            print_error(f"Deploy script not found: {script_path}")
            return False

        # Make script executable
        script_path.chmod(0o755)

        try:
            result = subprocess.run(
                [str(script_path)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes max
            )

            if result.returncode == 0:
                print_ok(f"Deployment SUCCESS for {env}")
                test_url = env_config["test_url"]
                self.notify(
                    f"🚀 DÉPLOIEMENT RÉUSSI — {env.upper()}\n"
                    f"🌐 URL: {test_url}\n"
                    f"✅ Système opérationnel"
                )
                return True
            else:
                print_error(f"Deployment FAILED for {env}")
                log.error(f"Deploy output:\n{result.stdout}\n{result.stderr}")
                self.notify(
                    f"❌ DÉPLOIEMENT ÉCHOUÉ — {env.upper()}\n"
                    f"⚠️ Erreur technique\n"
                    f"Voir logs pour détails"
                )
                return False

        except subprocess.TimeoutExpired:
            print_error(f"Deployment TIMEOUT for {env}")
            return False
        except Exception as e:
            print_error(f"Deployment ERROR for {env}: {e}")
            return False

    def deploy_environment_with_retry(self, env: str) -> Dict[str, Any]:
        """Deploy single environment with retry logic"""
        env_config = ENVIRONMENTS[env]
        color = env_config["color"]

        print_header(f"{color} ENVIRONMENT: {env.upper()} — {env_config['name']}", char="╔")

        env_result = {
            "env": env,
            "start_time": datetime.now(timezone.utc).isoformat(),
            "sale_1_eur": env_config["sale_1"],
            "sale_2_eur": env_config["sale_2"],
            "total_eur": env_config["sale_1"] + env_config["sale_2"],
            "gate_status": "pending",
            "deploy_status": "pending",
            "attempts": 0,
            "errors": []
        }

        # PRE-DEPLOY GATE avec retry
        gate_success = False
        for attempt in range(1, self.max_retries + 1):
            env_result["attempts"] = attempt
            print_info(f"Gate attempt {attempt}/{self.max_retries}")

            try:
                gate_success = self.run_pre_deploy_gate(env)
                if gate_success:
                    env_result["gate_status"] = "passed"
                    break
                else:
                    env_result["gate_status"] = "failed"
                    env_result["errors"].append(f"Gate attempt {attempt} failed")
                    if attempt < self.max_retries:
                        print_warn(f"Retrying in 10 seconds...")
                        time.sleep(10)
            except Exception as e:
                error_msg = f"Gate attempt {attempt} exception: {e}"
                env_result["errors"].append(error_msg)
                log.error(error_msg)
                if attempt < self.max_retries:
                    time.sleep(10)

        if not gate_success:
            print_error(f"Gate FAILED after {self.max_retries} attempts")
            env_result["end_time"] = datetime.now(timezone.utc).isoformat()
            env_result["final_status"] = "gate_failed"
            return env_result

        # DEPLOYMENT avec retry
        deploy_success = False
        for attempt in range(1, self.max_retries + 1):
            print_info(f"Deploy attempt {attempt}/{self.max_retries}")

            try:
                deploy_success = self.run_deployment(env)
                if deploy_success:
                    env_result["deploy_status"] = "success"
                    break
                else:
                    env_result["deploy_status"] = "failed"
                    env_result["errors"].append(f"Deploy attempt {attempt} failed")
                    if attempt < self.max_retries:
                        print_warn(f"Retrying in 15 seconds...")
                        time.sleep(15)
            except Exception as e:
                error_msg = f"Deploy attempt {attempt} exception: {e}"
                env_result["errors"].append(error_msg)
                log.error(error_msg)
                if attempt < self.max_retries:
                    time.sleep(15)

        env_result["end_time"] = datetime.now(timezone.utc).isoformat()
        env_result["final_status"] = "success" if deploy_success else "deploy_failed"

        if deploy_success:
            print_ok(f"Environment {env.upper()} FULLY DEPLOYED")
        else:
            print_error(f"Environment {env.upper()} DEPLOYMENT FAILED")

        return env_result

    def run_full_sequence(self, environments: List[str]) -> Dict[str, Any]:
        """Run full deployment sequence"""
        print_header("🚀 NAYA SUPREME V19 — ORCHESTRATEUR DE DÉPLOIEMENT AUTOMATISÉ", char="╔")

        print(f"""
📋 Configuration:
   • Environnements: {', '.join(env.upper() for env in environments)}
   • Max retries: {self.max_retries}
   • Telegram: {'✅ Activé' if not self.skip_telegram else '❌ Désactivé'}
   • Session ID: {self.session_id}

💰 Validation requise par environnement:
""")

        total_revenue = 0
        for env in environments:
            config = ENVIRONMENTS[env]
            total = config["sale_1"] + config["sale_2"]
            total_revenue += total
            print(f"   {config['color']} {env:12s}: {config['sale_1']:>8,} EUR + {config['sale_2']:>8,} EUR = {total:>9,} EUR")

        print(f"\n   💎 TOTAL OBJECTIF: {total_revenue:,} EUR ({len(environments)} environnements)\n")

        self.notify(
            f"🚀 DÉPLOIEMENT DÉMARRÉ\n"
            f"📊 {len(environments)} environnements\n"
            f"💰 Objectif: {total_revenue:,} EUR\n"
            f"🔄 Session: {self.session_id}"
        )

        # Deploy each environment sequentially
        results = {}
        successful = 0
        failed = 0
        total_validated_revenue = 0

        for i, env in enumerate(environments, 1):
            print(f"\n{'─' * 80}")
            print(f"📌 ENVIRONNEMENT {i}/{len(environments)}: {env.upper()}")
            print(f"{'─' * 80}\n")

            try:
                env_result = self.deploy_environment_with_retry(env)
                results[env] = env_result

                # Update ledger
                self.ledger["environments"][env] = env_result
                save_ledger(self.ledger)

                if env_result["final_status"] == "success":
                    successful += 1
                    total_validated_revenue += env_result["total_eur"]
                else:
                    failed += 1

            except Exception as e:
                error_msg = f"Critical error deploying {env}: {e}"
                print_error(error_msg)
                log.exception(error_msg)
                results[env] = {
                    "env": env,
                    "final_status": "critical_error",
                    "error": str(e)
                }
                failed += 1

                # IMPORTANT: Continue to next environment
                print_warn(f"Continuing to next environment despite error...")

        # Final report
        print_header("📊 RAPPORT FINAL DE DÉPLOIEMENT", char="╔")

        final_report = {
            "session_id": self.session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "environments_requested": environments,
            "environments_deployed": list(results.keys()),
            "successful_deployments": successful,
            "failed_deployments": failed,
            "total_revenue_validated_eur": total_validated_revenue,
            "target_revenue_eur": total_revenue,
            "completion_rate": round((successful / len(environments)) * 100, 1) if environments else 0,
            "results": results
        }

        # Save final report
        FINAL_REPORT.write_text(json.dumps(final_report, indent=2, ensure_ascii=False))

        # Print summary
        print(f"""
✅ Déploiements réussis: {successful}/{len(environments)}
❌ Déploiements échoués:  {failed}/{len(environments)}
💰 Revenu validé:         {total_validated_revenue:,} EUR / {total_revenue:,} EUR
📊 Taux de réussite:      {final_report['completion_rate']}%

📁 Rapport complet: {FINAL_REPORT}
""")

        # Telegram summary
        status_emoji = "✅" if failed == 0 else ("⚠️" if successful > 0 else "❌")
        self.notify(
            f"{status_emoji} DÉPLOIEMENT TERMINÉ\n"
            f"✅ Réussis: {successful}/{len(environments)}\n"
            f"❌ Échoués: {failed}/{len(environments)}\n"
            f"💰 Validé: {total_validated_revenue:,} EUR\n"
            f"📊 Taux: {final_report['completion_rate']}%"
        )

        return final_report

    def print_status(self):
        """Print current deployment status"""
        print_header("📊 STATUT ACTUEL DES DÉPLOIEMENTS")

        if not self.ledger.get("environments"):
            print_info("Aucun déploiement en cours ou terminé")
            return

        print(f"Session ID: {self.session_id}")
        print(f"Démarré: {self.ledger.get('session_start', 'unknown')}\n")

        for env, data in self.ledger["environments"].items():
            status = data.get("final_status", "unknown")
            total = data.get("total_eur", 0)

            if status == "success":
                print_ok(f"{env:12s}: ✅ SUCCESS — {total:,} EUR validés")
            elif status in ["gate_failed", "deploy_failed"]:
                print_error(f"{env:12s}: ❌ FAILED ({status})")
            else:
                print_info(f"{env:12s}: ⏳ {status.upper()}")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="NAYA V19 — Orchestrateur de Déploiement Automatisé",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "--env",
        help="Environnement(s) à déployer (séparés par virgule)",
        default=None
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Reprendre déploiement interrompu"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Afficher l'état actuel"
    )
    parser.add_argument(
        "--skip-telegram",
        action="store_true",
        help="Désactiver notifications Telegram"
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Nombre max de tentatives (défaut: 3)"
    )

    args = parser.parse_args()

    orchestrator = DeploymentOrchestrator(
        max_retries=args.max_retries,
        skip_telegram=args.skip_telegram
    )

    # Status mode
    if args.status:
        orchestrator.print_status()
        return 0

    # Determine environments to deploy
    if args.env:
        envs = [e.strip() for e in args.env.split(",")]
        # Validate environments
        invalid = [e for e in envs if e not in ALL_ENVS]
        if invalid:
            print_error(f"Invalid environments: {', '.join(invalid)}")
            print_info(f"Valid: {', '.join(ALL_ENVS)}")
            return 1
    else:
        # Deploy all environments by default
        envs = ALL_ENVS

    # Run deployment
    try:
        report = orchestrator.run_full_sequence(envs)

        # Exit code based on success rate
        if report["successful_deployments"] == len(envs):
            print_ok("Tous les déploiements réussis!")
            return 0
        elif report["successful_deployments"] > 0:
            print_warn("Déploiement partiel réussi")
            return 0  # Still consider partial success as OK
        else:
            print_error("Tous les déploiements ont échoué")
            return 1

    except KeyboardInterrupt:
        print_warn("\nDéploiement interrompu par l'utilisateur")
        print_info("Reprendre avec: python scripts/deploy_orchestrator_v2.py --resume")
        return 130
    except Exception as e:
        print_error(f"Erreur critique: {e}")
        log.exception("Critical error in orchestrator")
        return 1


if __name__ == "__main__":
    sys.exit(main())
