#!/bin/bash

# ═══════════════════════════════════════════════════════════════
# NAYA REAL SALES — Master Deployment Script
# ═══════════════════════════════════════════════════════════════
# Déploie sur LES 6 PLATEFORMES : local, docker, vercel, render, cloud_run, railway
# Usage: ./deploy_all_platforms.sh [all|local|docker|vercel|render|cloud_run|railway]
# ═══════════════════════════════════════════════════════════════

set -e  # Exit on error

PLATFORM=${1:-all}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_DIR="logs/deployments"
mkdir -p "$LOG_DIR"

echo "═══════════════════════════════════════════════════════════════"
echo "NAYA REAL SALES — MASTER DEPLOYMENT"
echo "Platform(s): $PLATFORM"
echo "Timestamp: $TIMESTAMP"
echo "═══════════════════════════════════════════════════════════════"

# ── Functions ─────────────────────────────────────────────────────

log_success() {
    echo "✅ $1" | tee -a "$LOG_DIR/deploy_$TIMESTAMP.log"
}

log_error() {
    echo "❌ $1" | tee -a "$LOG_DIR/deploy_$TIMESTAMP.log"
}

log_info() {
    echo "ℹ️  $1" | tee -a "$LOG_DIR/deploy_$TIMESTAMP.log"
}

# ── Pre-checks ────────────────────────────────────────────────────

check_python() {
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 non trouvé"
        exit 1
    fi
    log_success "Python $(python3 --version | cut -d' ' -f2) détecté"
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker non trouvé"
        return 1
    fi
    log_success "Docker détecté"
    return 0
}

check_vercel() {
    if ! command -v vercel &> /dev/null; then
        log_error "Vercel CLI non installé (npm i -g vercel)"
        return 1
    fi
    log_success "Vercel CLI détecté"
    return 0
}

check_railway() {
    if ! command -v railway &> /dev/null; then
        log_error "Railway CLI non installé (npm i -g @railway/cli)"
        return 1
    fi
    log_success "Railway CLI détecté"
    return 0
}

check_gcloud() {
    if ! command -v gcloud &> /dev/null; then
        log_error "Google Cloud SDK non installé"
        return 1
    fi
    log_success "Google Cloud SDK détecté"
    return 0
}

# ── Deployment Functions ──────────────────────────────────────────

deploy_local() {
    log_info "═══ DÉPLOIEMENT LOCAL ═══"

    # Créer environnement virtuel si nécessaire
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        log_success "Virtual environment créé"
    fi

    # Activer venv et installer dépendances
    source venv/bin/activate
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    log_success "Dépendances installées"

    # Créer .env si manquant
    if [ ! -f ".env" ]; then
        cp NAYA_REAL_SALES/.env.example .env
        log_info ".env créé depuis .env.example — CONFIGURER LES CLÉS API"
    fi

    # Lancer le serveur en background
    pkill -f "NAYA_REAL_SALES.main" 2>/dev/null || true
    nohup python -m NAYA_REAL_SALES.main > "$LOG_DIR/local_$TIMESTAMP.log" 2>&1 &
    SERVER_PID=$!

    # Attendre démarrage
    sleep 5

    # Test health check
    if curl -sf http://localhost:8000/health | grep -q "healthy"; then
        log_success "Déploiement LOCAL réussi — PID: $SERVER_PID"
        log_info "API: http://localhost:8000"
        log_info "Logs: tail -f $LOG_DIR/local_$TIMESTAMP.log"
        log_info "Stop: kill $SERVER_PID"
        echo "$SERVER_PID" > "$LOG_DIR/local.pid"
    else
        log_error "Health check échoué"
        kill $SERVER_PID 2>/dev/null || true
        return 1
    fi
}

deploy_docker() {
    log_info "═══ DÉPLOIEMENT DOCKER ═══"

    if ! check_docker; then
        return 1
    fi

    # Build image
    docker build -f Dockerfile.real_sales -t naya-real-sales:latest . \
        > "$LOG_DIR/docker_build_$TIMESTAMP.log" 2>&1
    log_success "Image Docker buildée"

    # Stop conteneur existant
    docker stop naya-real-sales 2>/dev/null || true
    docker rm naya-real-sales 2>/dev/null || true

    # Run conteneur
    docker run -d \
        --name naya-real-sales \
        --restart unless-stopped \
        -p 8001:8000 \
        -v $(pwd)/data:/app/data \
        -v $(pwd)/logs:/app/logs \
        --env-file .env \
        naya-real-sales:latest \
        > "$LOG_DIR/docker_run_$TIMESTAMP.log" 2>&1

    # Wait et test
    sleep 10

    if curl -sf http://localhost:8001/health | grep -q "healthy"; then
        log_success "Déploiement DOCKER réussi"
        log_info "API: http://localhost:8001"
        log_info "Logs: docker logs -f naya-real-sales"
        log_info "Stop: docker stop naya-real-sales"
    else
        log_error "Health check Docker échoué"
        docker logs naya-real-sales
        return 1
    fi
}

deploy_vercel() {
    log_info "═══ DÉPLOIEMENT VERCEL ═══"

    if ! check_vercel; then
        return 1
    fi

    # Login si nécessaire
    vercel whoami &>/dev/null || vercel login

    # Deploy avec config spécifique
    vercel deploy --prod --yes \
        --build-env ENVIRONMENT=production \
        --build-env MIN_CONTRACT_VALUE=1000 \
        > "$LOG_DIR/vercel_$TIMESTAMP.log" 2>&1

    VERCEL_URL=$(vercel ls | grep naya-real-sales | head -1 | awk '{print $2}')

    if [ -n "$VERCEL_URL" ]; then
        log_success "Déploiement VERCEL réussi"
        log_info "URL: https://$VERCEL_URL"
        log_info "Dashboard: https://vercel.com/dashboard"
    else
        log_error "Déploiement Vercel échoué"
        return 1
    fi
}

deploy_render() {
    log_info "═══ DÉPLOIEMENT RENDER ═══"

    # Render nécessite push Git + config dashboard
    if [ -z "$(git remote get-url origin 2>/dev/null)" ]; then
        log_error "Pas de remote Git configuré"
        return 1
    fi

    log_info "Push vers GitHub..."
    git add -A
    git commit -m "deploy: NAYA REAL SALES to Render ($TIMESTAMP)" || true
    git push origin $(git branch --show-current)

    log_success "Code poussé vers GitHub"
    log_info "⚠️  Configuration manuelle requise:"
    log_info "1. Aller sur https://dashboard.render.com"
    log_info "2. New > Blueprint"
    log_info "3. Sélectionner render.real_sales.yaml"
    log_info "4. Configurer les variables d'environnement (secrets)"
    log_info "5. Déployer"
}

deploy_cloud_run() {
    log_info "═══ DÉPLOIEMENT CLOUD RUN ═══"

    if ! check_gcloud; then
        return 1
    fi

    # Vérifier projet GCP
    PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
    if [ -z "$PROJECT_ID" ]; then
        log_error "Projet GCP non configuré (gcloud config set project PROJECT_ID)"
        return 1
    fi

    log_info "Projet GCP: $PROJECT_ID"

    # Soumettre build via Cloud Build
    gcloud builds submit \
        --config=cloudbuild.real_sales.yaml \
        --timeout=20m \
        > "$LOG_DIR/cloud_run_$TIMESTAMP.log" 2>&1

    # Récupérer l'URL
    SERVICE_URL=$(gcloud run services describe naya-real-sales \
        --region=europe-west1 \
        --format='value(status.url)' 2>/dev/null)

    if [ -n "$SERVICE_URL" ]; then
        log_success "Déploiement CLOUD RUN réussi"
        log_info "URL: $SERVICE_URL"
        log_info "Logs: gcloud run logs read naya-real-sales --region=europe-west1"
    else
        log_error "Déploiement Cloud Run échoué"
        return 1
    fi
}

deploy_railway() {
    log_info "═══ DÉPLOIEMENT RAILWAY ═══"

    if ! check_railway; then
        return 1
    fi

    # Login si nécessaire
    railway whoami &>/dev/null || railway login

    # Deploy avec Dockerfile spécifique
    railway up --dockerfile Dockerfile.real_sales \
        > "$LOG_DIR/railway_$TIMESTAMP.log" 2>&1

    # Récupérer l'URL
    RAILWAY_URL=$(railway domain 2>/dev/null || echo "")

    if [ -n "$RAILWAY_URL" ]; then
        log_success "Déploiement RAILWAY réussi"
        log_info "URL: https://$RAILWAY_URL"
        log_info "Dashboard: https://railway.app/dashboard"
        log_info "Logs: railway logs --follow"
    else
        log_error "Déploiement Railway échoué"
        return 1
    fi
}

# ── Main Execution ────────────────────────────────────────────────

main() {
    log_info "Démarrage des déploiements..."

    # Pre-checks communs
    check_python

    DEPLOYED=0
    FAILED=0

    case $PLATFORM in
        all)
            for platform in local docker vercel render cloud_run railway; do
                echo ""
                if deploy_$platform; then
                    ((DEPLOYED++))
                else
                    ((FAILED++))
                fi
            done
            ;;
        local|docker|vercel|render|cloud_run|railway)
            deploy_$PLATFORM && ((DEPLOYED++)) || ((FAILED++))
            ;;
        *)
            log_error "Plateforme inconnue: $PLATFORM"
            log_info "Usage: $0 [all|local|docker|vercel|render|cloud_run|railway]"
            exit 1
            ;;
    esac

    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "RÉSUMÉ DES DÉPLOIEMENTS"
    echo "═══════════════════════════════════════════════════════════════"
    echo "✅ Réussis: $DEPLOYED"
    echo "❌ Échoués: $FAILED"
    echo "📝 Logs: $LOG_DIR/deploy_$TIMESTAMP.log"
    echo "═══════════════════════════════════════════════════════════════"

    if [ $FAILED -gt 0 ]; then
        exit 1
    fi
}

main "$@"
