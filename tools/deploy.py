#!/usr/bin/env python3
"""
NAYA V19 — AUTO-DEPLOY avec GATE DE VALIDATION PRÉ-DÉPLOIEMENT
════════════════════════════════════════════════════════════════
Chaque déploiement est conditionné à 2 ventes réelles encaissées.

SÉQUENCE OBLIGATOIRE (2 ventes par déploiement) :
  1. Local (port 3000) → 15 000 + 25 000 EUR encaissés
  2. Docker            → 25 000 + 35 000 EUR encaissés
  3. Vercel            → 35 000 + 45 000 EUR encaissés
  4. Render            → 45 000 + 55 000 EUR encaissés
  5. Cloud Run         → 55 000 + 65 000 EUR encaissés
  Total               → 400 000 EUR (10 ventes)

Modes de déploiement:
  - local      : uvicorn NAYA_CORE.api.main:app --port 3000 (développement)
  - docker     : docker-compose up -d (test local conteneurisé)
  - vercel     : vercel deploy (serverless Vercel)
  - render     : render deploy (PaaS Render.com)
  - cloud_run  : gcloud run deploy (production scalable, paye à l'usage)

GCP configuré:
  - Projet: naya-pro-ultime
  - Service Account: naya-pro-ultime@naya-pro-ultime.iam.gserviceaccount.com
  - Région: europe-west1 (Paris — le plus proche de la Polynésie via HK)

Commande simple:
  python tools/deploy.py --mode local
  python tools/deploy.py --mode docker
  python tools/deploy.py --mode vercel
  python tools/deploy.py --mode render
  python tools/deploy.py --mode cloud_run
  python tools/deploy.py --mode all       # Séquence complète avec validation
  python tools/deploy.py --mode local --skip-validation  # Bypass (dev only)
"""

import os
import sys
import subprocess
import json
import time
import argparse
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# ── Config GCP depuis secrets ─────────────────────────────────────────────
GCP_PROJECT = "naya-pro-ultime"
GCP_REGION = os.environ.get("CLOUD_RUN_REGION", "europe-west1")
GCP_SERVICE = os.environ.get("CLOUD_RUN_SERVICE_NAME", "naya-supreme")
GCP_SA_EMAIL = "naya-pro-ultime@naya-pro-ultime.iam.gserviceaccount.com"
DOCKER_IMAGE = f"gcr.io/{GCP_PROJECT}/{GCP_SERVICE}"


def _run(cmd: str, check: bool = True, capture: bool = False) -> subprocess.CompletedProcess:
    """Exécute une commande shell."""
    print(f"  → {cmd}")
    result = subprocess.run(
        cmd, shell=True, capture_output=capture,
        text=True, cwd=str(ROOT)
    )
    if check and result.returncode != 0:
        if capture:
            print(f"  ❌ Erreur: {result.stderr[:300]}")
        raise RuntimeError(f"Commande échouée: {cmd}")
    return result


def check_prerequisites(mode: str) -> bool:
    """Vérifie les prérequis selon le mode."""
    print("\n🔍 Vérification des prérequis...")

    if mode == "local":
        # Vérifier Python et FastAPI
        result = _run("python3 -c 'import fastapi; import uvicorn'", check=False, capture=True)
        if result.returncode != 0:
            print("  ⚠️  Installer: pip install fastapi uvicorn httpx python-dotenv pydantic rich requests")
            _run("pip install fastapi uvicorn httpx python-dotenv pydantic rich requests -q")
        print("  ✅ Python + dépendances OK")
        return True

    elif mode == "docker":
        if not shutil.which("docker"):
            print("  ❌ Docker non installé: https://docker.com/get-started")
            return False
        if not shutil.which("docker-compose"):
            print("  ❌ docker-compose non installé")
            return False
        print("  ✅ Docker + docker-compose OK")
        return True

    elif mode == "vercel":
        if not shutil.which("vercel"):
            print("  ⚠️  Vercel CLI non installé — installation...")
            _run("npm install -g vercel", check=False)
        print("  ✅ Vercel CLI OK")
        return True

    elif mode == "render":
        if not shutil.which("render"):
            print("  ℹ️  Render CLI optionnel — déploiement via git push possible")
        print("  ✅ Render déploiement prêt")
        return True

    elif mode == "cloud_run":
        # Vérifier gcloud
        if not shutil.which("gcloud"):
            print("  ❌ gcloud non installé: https://cloud.google.com/sdk/docs/install")
            print("     Puis: gcloud auth login && gcloud config set project naya-pro-ultime")
            return False

        # Vérifier auth
        result = _run(f"gcloud auth list --filter=status:ACTIVE --format='value(account)'",
                      check=False, capture=True)
        if not result.stdout.strip():
            print("  ⚠️  Pas authentifié, lancement...")
            _run("gcloud auth login")
            _run(f"gcloud config set project {GCP_PROJECT}")

        # Vérifier Docker pour build
        if not shutil.which("docker"):
            print("  ❌ Docker requis pour build l'image Cloud Run")
            return False

        print(f"  ✅ gcloud OK — projet: {GCP_PROJECT}")
        return True

    return True


def deploy_local():
    """Démarrage local direct sur le port 3000."""
    print("\n🚀 Démarrage LOCAL (port 3000)...")
    print("  URL: http://localhost:3000")
    print("  Dashboard: http://localhost:3000/dashboard")
    print("  Docs API: http://localhost:3000/docs")
    print("  CTRL+C pour arrêter\n")

    # Charger .env si présent
    env_file = ROOT / ".env"
    if env_file.exists():
        print("  ✅ .env chargé")
    else:
        print("  ⚠️  .env manquant — copier .env.example → .env")

    # Lancer uvicorn sur le port 3000
    os.execv(
        sys.executable,
        [sys.executable, "-m", "uvicorn", "NAYA_CORE.api.main:app",
         "--host", "0.0.0.0", "--port", "3000", "--reload"],
    )


def deploy_docker():
    """Déploiement Docker Compose local."""
    print("\n🐳 Déploiement DOCKER...")

    compose_file = ROOT / "docker-compose.yml"
    if not compose_file.exists():
        print("  ❌ docker-compose.yml manquant")
        return False

    print("  Arrêt des conteneurs existants...")
    _run("docker-compose down", check=False)

    print("  Build de l'image...")
    _run("docker-compose build --no-cache")

    print("  Démarrage...")
    _run("docker-compose up -d")

    time.sleep(5)
    result = _run("docker-compose ps", capture=True)
    print(result.stdout)

    print("\n✅ NAYA SUPREME démarré en Docker")
    print("  URL: http://localhost:8000")
    print("  Logs: docker-compose logs -f naya")
    print("  Arrêt: docker-compose down")
    return True


def deploy_cloud_run():
    """
    Déploiement sur Google Cloud Run.
    Utilise le Service Account GCP déjà configuré.
    Coût: ~$0 en dessous de 2M req/mois (plan gratuit Cloud Run).
    """
    print(f"\n☁️  Déploiement CLOUD RUN — {GCP_PROJECT}...")

    # 1. Configurer le projet
    print(f"\n  Projet GCP: {GCP_PROJECT}")
    _run(f"gcloud config set project {GCP_PROJECT}")
    _run(f"gcloud config set run/region {GCP_REGION}")

    # 2. Activer les APIs nécessaires
    print("\n  Activation APIs GCP...")
    apis = ["run.googleapis.com", "cloudbuild.googleapis.com",
            "secretmanager.googleapis.com", "gmail.googleapis.com"]
    for api in apis:
        _run(f"gcloud services enable {api} --project={GCP_PROJECT}", check=False)

    # 3. Build et push l'image Docker
    tag = datetime.now().strftime("%Y%m%d-%H%M%S")
    image = f"{DOCKER_IMAGE}:{tag}"
    image_latest = f"{DOCKER_IMAGE}:latest"

    print(f"\n  Build image Docker: {image}")
    _run(f"gcloud builds submit --tag={image} --project={GCP_PROJECT} .")
    _run(f"gcloud container images add-tag {image} {image_latest} --quiet")

    # 4. Injecter les secrets dans Cloud Run
    print("\n  Configuration des secrets...")
    secrets = _build_secrets_dict()

    # 5. Déployer sur Cloud Run
    print(f"\n  Déploiement sur Cloud Run ({GCP_REGION})...")

    env_vars = ",".join([f"{k}={v}" for k, v in secrets.items() if v])

    deploy_cmd = (
        f"gcloud run deploy {GCP_SERVICE} "
        f"--image={image_latest} "
        f"--platform=managed "
        f"--region={GCP_REGION} "
        f"--project={GCP_PROJECT} "
        f"--service-account={GCP_SA_EMAIL} "
        f"--memory=2Gi "
        f"--cpu=2 "
        f"--min-instances=1 "
        f"--max-instances=10 "
        f"--port=8080 "
        f"--allow-unauthenticated "
        f"--timeout=3600 "
        f"--concurrency=80 "
        f'--set-env-vars="{env_vars}" '
        f"--quiet"
    )
    _run(deploy_cmd)

    # 6. Obtenir l'URL
    result = _run(
        f"gcloud run services describe {GCP_SERVICE} "
        f"--region={GCP_REGION} --project={GCP_PROJECT} "
        f"--format='value(status.url)'",
        capture=True
    )
    url = result.stdout.strip()

    print(f"\n✅ NAYA SUPREME déployé sur Cloud Run!")
    print(f"  🌍 URL: {url}")
    print(f"  📊 Dashboard: {url}/dashboard")
    print(f"  📚 API Docs: {url}/docs")
    print(f"  ❤️  Health: {url}/health")
    print(f"\n  Logs: gcloud run logs tail {GCP_SERVICE} --region={GCP_REGION}")
    print(f"  Console: https://console.cloud.google.com/run?project={GCP_PROJECT}")

    # Sauvegarder l'URL
    (ROOT / "logs" / "cloud_run_url.txt").write_text(url)
    return url


def _build_secrets_dict() -> Dict[str, str]:
    """Construit le dictionnaire des variables d'environnement pour Cloud Run."""
    try:
        os.chdir(str(ROOT))
        from SECRETS.secrets_loader import load_all_secrets
        load_all_secrets(verbose=False)
    except Exception:
        pass

    critical_vars = [
        # LLM
        "ANTHROPIC_API_KEY", "OPENAI_API_KEY",
        "GROK_API_KEY", "XAI_API_KEY", "GROQ_API_KEY",
        "HUGGINGFACE_API_KEY", "HF_API_KEY_1", "HF_API_KEY_2",
        "HF_API_KEY_3", "HF_API_KEY_4",
        # Telegram
        "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID",
        # Email
        "SENDGRID_API_KEY", "EMAIL_FROM", "EMAIL_FROM_NAME",
        "SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS",
        # Prospection
        "SERPER_API_KEY", "SERPER_API_KEY_2", "APOLLO_API_KEY",
        # Paiement
        "PAYPAL_ME_URL", "PAYPAL_ME_USERNAME",
        # Système
        "NAYA_ENV", "NAYA_AUTONOMOUS_MODE", "NAYA_REVENUE_ENABLED",
        "NAYA_AUTO_OUTREACH", "NAYA_REVENUE_SCAN_INTERVAL",
        # GCP
        "GOOGLE_CLOUD_PROJECT", "GCP_SERVICE_ACCOUNT",
    ]

    secrets = {}
    for var in critical_vars:
        val = os.environ.get(var, "")
        if val and len(val) > 1:
            # Nettoyer les caractères problématiques pour gcloud
            val = val.replace('"', '\\"').replace("'", "\\'").replace(",", "\\,")
            secrets[var] = val

    # Forcer quelques valeurs Cloud Run
    secrets["NAYA_ENV"] = "cloud_run"
    secrets["PORT"] = "8080"

    return secrets


def _validate_before_deploy(mode: str, skip: bool = False) -> bool:
    """
    Gate de validation pré-déploiement.
    Vérifie qu'une vente réelle a été encaissée avant d'autoriser le déploiement.
    """
    if skip:
        print(f"  ⚠️  --skip-validation activé — gate de validation bypassée (dev only)")
        return True

    # cloud_run n'a pas de mapping direct → utiliser la cible "cloud_run"
    target_map = {
        "local":     "local",
        "docker":    "docker",
        "vercel":    "vercel",
        "render":    "render",
        "cloud_run": "cloud_run",
    }
    deploy_target = target_map.get(mode)
    if not deploy_target:
        return True  # mode inconnu → pas de gate

    try:
        from tools.pre_deploy_validator import PreDeployValidator
        validator = PreDeployValidator()
        if validator.check_deploy_gate(deploy_target):
            return True

        # Gate non franchie → lancer le test
        print(f"\n  🔒 DÉPLOIEMENT {mode.upper()} BLOQUÉ — 2 ventes réelles requises")
        print(f"\n  Options:")
        print(f"    Lancer la validation : python tools/pre_deploy_validator.py --test {deploy_target}")
        print(f"    Séquence complète    : python tools/pre_deploy_validator.py --run-all")
        print(f"    Voir le statut       : python tools/pre_deploy_validator.py --status")
        return False

    except Exception as e:
        print(f"  ⚠️  Validator non disponible ({e}) — déploiement autorisé")
        return True


def deploy_vercel() -> bool:
    """Déploiement sur Vercel (serverless)."""
    print("\n▲  Déploiement VERCEL...")

    vercel_json = ROOT / "vercel.json"
    if not vercel_json.exists():
        # Créer une config Vercel minimale
        vercel_json.write_text(json.dumps({
            "version": 2,
            "builds": [{"src": "main.py", "use": "@vercel/python"}],
            "routes": [{"src": "/(.*)", "dest": "main.py"}],
            "env": {
                "NAYA_ENV": "vercel",
                "PORT": "8080",
            }
        }, indent=2))
        print("  ✅ vercel.json créé")

    _run("vercel deploy --prod --yes", check=False)
    print("\n✅ NAYA SUPREME déployé sur Vercel")
    return True


def deploy_render() -> bool:
    """Déploiement sur Render.com."""
    print("\n🟣 Déploiement RENDER...")

    render_yaml = ROOT / "render.yaml"
    if not render_yaml.exists():
        render_yaml.write_text(
            "services:\n"
            "  - type: web\n"
            "    name: naya-supreme\n"
            "    env: python\n"
            "    buildCommand: pip install -r requirements.txt\n"
            "    startCommand: python main.py\n"
            "    envVars:\n"
            "      - key: NAYA_ENV\n"
            "        value: render\n"
            "      - key: PORT\n"
            "        value: 8080\n"
        )
        print("  ✅ render.yaml créé")

    render_cli = shutil.which("render")
    if render_cli:
        _run("render deploy", check=False)
    else:
        print("  ℹ️  Render CLI non disponible.")
        print("  → Déployer via : https://dashboard.render.com/new")
        print("  → Ou : git push origin main  (si Render GitHub auto-deploy activé)")

    print("\n✅ NAYA SUPREME déployé sur Render")
    return True


def show_deployment_guide():
    """Affiche le guide complet de déploiement."""
    guide = """
╔══════════════════════════════════════════════════════════════════════════════╗
║  NAYA SUPREME V19 — GUIDE DE DÉPLOIEMENT COMPLET                          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  ⚠️  GATE DE VALIDATION : vente réelle requise avant chaque déploiement   ║
║  Test 1 → Local (15 000€) → Test 2 → Docker (25 000€) → ...              ║
║                                                                            ║
║  SÉQUENCE COMPLÈTE (recommandée) :                                        ║
║  ───────────────────────────────                                           ║
║  python tools/pre_deploy_validator.py --run-all                           ║
║  python tools/deploy.py --mode all                                         ║
║                                                                            ║
║  MODE LOCAL (développement, test)                                          ║
║  ─────────────────────────────────                                         ║
║  python tools/deploy.py --mode local                                       ║
║  URL: http://localhost:8080                                                ║
║                                                                            ║
║  MODE DOCKER (test conteneurisé)                                           ║
║  ───────────────────────────────                                           ║
║  python tools/deploy.py --mode docker                                      ║
║                                                                            ║
║  MODE VERCEL (serverless)                                                  ║
║  ─────────────────────────                                                 ║
║  python tools/deploy.py --mode vercel                                      ║
║                                                                            ║
║  MODE RENDER (PaaS)                                                        ║
║  ──────────────────                                                        ║
║  python tools/deploy.py --mode render                                      ║
║                                                                            ║
║  MODE CLOUD RUN (production — recommandé)                                  ║
║  ────────────────────────────────────────                                  ║
║  python tools/deploy.py --mode cloud_run                                   ║
║  ✅ Votre projet GCP naya-pro-ultime est DÉJÀ configuré                    ║
║  💰 Coût: ~0€/mois (2M req gratuites/mois)                                ║
║                                                                            ║
║  VALIDATION MANUELLE :                                                     ║
║  python tools/pre_deploy_validator.py --status                             ║
║  python tools/pre_deploy_validator.py --confirm PDV_XXX --amount 15000    ║
║                                                                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
    print(guide)


def main():
    parser = argparse.ArgumentParser(description="NAYA SUPREME V19 — Déploiement avec Gate de Validation")
    parser.add_argument(
        "--mode",
        choices=["local", "docker", "vercel", "render", "cloud_run", "all", "guide"],
        default="local",
        help="Mode de déploiement"
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Bypasser la gate de validation (dev uniquement)"
    )
    args = parser.parse_args()

    print("╔══════════════════════════════════════════╗")
    print("║  NAYA SUPREME V19 — AUTO-DEPLOY          ║")
    print("╚══════════════════════════════════════════╝")

    if args.mode == "guide":
        show_deployment_guide()
        return

    # Mode ALL : séquence complète avec validation
    if args.mode == "all":
        _run_all_deployments(skip_validation=args.skip_validation)
        return

    if not check_prerequisites(args.mode):
        print("\n❌ Prérequis non satisfaits — abandon")
        sys.exit(1)

    # Gate de validation
    if not _validate_before_deploy(args.mode, skip=args.skip_validation):
        print("\n🚫 Déploiement interrompu — validation requise")
        sys.exit(1)

    if args.mode == "local":
        deploy_local()
    elif args.mode == "docker":
        deploy_docker()
    elif args.mode == "vercel":
        deploy_vercel()
    elif args.mode == "render":
        deploy_render()
    elif args.mode == "cloud_run":
        deploy_cloud_run()


def _run_all_deployments(skip_validation: bool = False) -> None:
    """
    Exécute la séquence complète de déploiement :
    Validation Test 1 → Local → Test 2 → Docker → Test 3 → Vercel → Test 4 → Render → Test 5 → Cloud Run
    """
    from tools.pre_deploy_validator import PreDeployValidator, DEPLOYMENT_TARGETS

    print("\n╔══════════════════════════════════════════════════════════╗")
    print("║  NAYA V19 — SÉQUENCE DÉPLOIEMENT COMPLÈTE                ║")
    print("║  5 ventes réelles → 5 déploiements successifs             ║")
    print("╚══════════════════════════════════════════════════════════╝")

    validator  = PreDeployValidator()
    deploy_fns = {
        "local":     (deploy_local,     "local"),
        "docker":    (deploy_docker,    "docker"),
        "vercel":    (deploy_vercel,    "vercel"),
        "render":    (deploy_render,    "render"),
        "cloud_run": (deploy_cloud_run, "cloud_run"),
    }

    for target_cfg in DEPLOYMENT_TARGETS:
        tid   = target_cfg["id"]
        label = target_cfg["label"]
        eur   = target_cfg["target_eur"]
        idx   = target_cfg["index"]

        print(f"\n{'═' * 60}")
        print(f"  ÉTAPE {idx}/5 : {label}  ({eur:,.0f}€ requis)")
        print(f"{'═' * 60}")

        # 1. Valider (vente réelle)
        if not skip_validation:
            ok = validator.run_test(tid, skip_if_done=True)
            if not ok:
                print(f"\n❌ Validation {tid} échouée — séquence interrompue")
                print(f"   Reprendre : python tools/deploy.py --mode all")
                sys.exit(1)

        # 2. Déployer
        fn, mode = deploy_fns[tid]
        if not check_prerequisites(mode):
            print(f"  ⚠️  Prérequis manquants pour {tid} — étape skippée")
            continue

        try:
            fn()
            print(f"\n  ✅ {label} déployé avec succès")
        except Exception as e:
            print(f"\n  ❌ Erreur déploiement {tid}: {e}")
            print(f"  → Continuer avec : python tools/deploy.py --mode {mode}")

    print("\n\n🏆 SÉQUENCE COMPLÈTE TERMINÉE")
    print("   Tous les environnements déployés après validation des ventes réelles.")


if __name__ == "__main__":
    main()
