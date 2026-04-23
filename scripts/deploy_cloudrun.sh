#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════
# NAYA SUPREME V19 — GOOGLE CLOUD RUN Deployment + Sales Validation
# Builds Docker image, pushes to GCR, deploys to Cloud Run, validates 2 sales.
#
# Prerequisites:
#   - gcloud CLI authenticated: gcloud auth login
#   - Docker configured for GCR: gcloud auth configure-docker
#   - PROJECT_ID set: export PROJECT_ID=your-gcp-project
#
# Usage:
#   PROJECT_ID=my-project ./scripts/deploy_cloudrun.sh
#   PROJECT_ID=my-project REGION=us-central1 ./scripts/deploy_cloudrun.sh
# ══════════════════════════════════════════════════════════════════════════════

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

PROJECT_ID="${PROJECT_ID:-}"
REGION="${REGION:-europe-west1}"
SERVICE_NAME="${SERVICE_NAME:-naya-supreme}"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
COMMIT_SHA="${COMMIT_SHA:-$(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || echo "latest")}"
MEMORY="${MEMORY:-1Gi}"
CPU="${CPU:-1}"
MIN_INSTANCES="${MIN_INSTANCES:-0}"
MAX_INSTANCES="${MAX_INSTANCES:-3}"

GREEN='\033[0;32m'; RED='\033[0;31m'; CYAN='\033[0;36m'; YELLOW='\033[1;33m'
BOLD='\033[1m'; NC='\033[0m'

log()    { echo -e "${CYAN}[$(date +%H:%M:%S)] $*${NC}"; }
ok()     { echo -e "${GREEN}✅  $*${NC}"; }
fail()   { echo -e "${RED}❌  $*${NC}"; exit 1; }
warn()   { echo -e "${YELLOW}⚠️   $*${NC}"; }
header() { echo -e "\n${BOLD}${CYAN}══ $* ══${NC}\n"; }

# ── Prerequisite checks ───────────────────────────────────────────────────────
header "Prerequisites"

if [ -z "$PROJECT_ID" ]; then
    # Try to get from gcloud config
    PROJECT_ID=$(gcloud config get-value project 2>/dev/null || true)
    if [ -z "$PROJECT_ID" ]; then
        fail "PROJECT_ID not set and no gcloud default project. Export PROJECT_ID=your-project-id"
    fi
    log "Using gcloud project: ${PROJECT_ID}"
fi

command -v gcloud >/dev/null 2>&1 || fail "gcloud CLI not installed. Install from https://cloud.google.com/sdk"
command -v docker  >/dev/null 2>&1 || fail "Docker not installed"

ok "gcloud available: $(gcloud version --format='value(Google Cloud SDK)' 2>/dev/null | head -1)"
ok "Docker available: $(docker --version)"
log "Project  : ${PROJECT_ID}"
log "Region   : ${REGION}"
log "Service  : ${SERVICE_NAME}"
log "Image    : ${IMAGE_NAME}:${COMMIT_SHA}"

cd "$ROOT"

# ── Step 1: Configure Docker auth for GCR ────────────────────────────────────
header "Step 1/5 — GCR Authentication"
gcloud auth configure-docker --quiet
ok "Docker configured for GCR"

# ── Step 2: Build Docker image ────────────────────────────────────────────────
header "Step 2/5 — Docker Build"
log "Building: ${IMAGE_NAME}:${COMMIT_SHA}"
docker build \
    --tag "${IMAGE_NAME}:${COMMIT_SHA}" \
    --tag "${IMAGE_NAME}:latest" \
    --file "${ROOT}/Dockerfile" \
    --build-arg PYTHON_VERSION=3.11 \
    "${ROOT}"
ok "Image built: ${IMAGE_NAME}:${COMMIT_SHA}"

# ── Step 3: Push to Container Registry ───────────────────────────────────────
header "Step 3/5 — Push to GCR"
log "Pushing ${IMAGE_NAME}..."
docker push "${IMAGE_NAME}:${COMMIT_SHA}"
docker push "${IMAGE_NAME}:latest"
ok "Image pushed to GCR"

# ── Step 4: Deploy to Cloud Run ───────────────────────────────────────────────
header "Step 4/5 — Cloud Run Deploy"

# Build set-secrets flags — batch lookup to avoid 8 serial API calls
SET_SECRETS=""
WANTED_SECRETS="SECRET_KEY ANTHROPIC_API_KEY TELEGRAM_BOT_TOKEN TELEGRAM_CHAT_ID STRIPE_API_KEY STRIPE_WEBHOOK_SECRET SENDGRID_API_KEY SERPER_API_KEY"

AVAILABLE_SECRETS=$(gcloud secrets list --project="$PROJECT_ID" --format='value(name)' 2>/dev/null || true)
for secret in $WANTED_SECRETS; do
    if echo "$AVAILABLE_SECRETS" | grep -qx "$secret"; then
        SET_SECRETS="${SET_SECRETS},${secret}=${secret}:latest"
    fi
done
SET_SECRETS="${SET_SECRETS#,}"

DEPLOY_ARGS=(
    "run" "deploy" "$SERVICE_NAME"
    "--image=${IMAGE_NAME}:${COMMIT_SHA}"
    "--platform=managed"
    "--region=${REGION}"
    "--allow-unauthenticated"
    "--port=8000"
    "--memory=${MEMORY}"
    "--cpu=${CPU}"
    "--min-instances=${MIN_INSTANCES}"
    "--max-instances=${MAX_INSTANCES}"
    "--concurrency=80"
    "--timeout=300"
    "--set-env-vars=ENVIRONMENT=production,NAYA_ENV=production,LOG_LEVEL=INFO"
    "--set-env-vars=ENABLE_SELF_HEALING=true,ENABLE_GUARDIAN=true"
    "--set-env-vars=NAYA_AUTO_OUTREACH=false,API_WORKERS=2"
    "--project=${PROJECT_ID}"
    "--quiet"
)

if [ -n "$SET_SECRETS" ]; then
    DEPLOY_ARGS+=("--set-secrets=${SET_SECRETS}")
    log "Attaching secrets: ${SET_SECRETS}"
fi

log "Deploying to Cloud Run..."
gcloud "${DEPLOY_ARGS[@]}"

# Get the deployed URL
CLOUDRUN_URL=$(gcloud run services describe "$SERVICE_NAME" \
    --platform=managed \
    --region="$REGION" \
    --project="$PROJECT_ID" \
    --format='value(status.url)' 2>/dev/null || true)

if [ -z "$CLOUDRUN_URL" ]; then
    warn "Could not retrieve Cloud Run URL from gcloud — using default pattern"
    CLOUDRUN_URL="https://${SERVICE_NAME}-$(echo "$PROJECT_ID" | tr '.' '-').${REGION}.run.app"
fi
ok "Cloud Run deployed: ${CLOUDRUN_URL}"

# ── Step 5: Validate 2 Real Sales ─────────────────────────────────────────────
header "Step 5/5 — Sales Validation (2 real sales on Cloud Run)"
DEPLOY_WAIT=60 bash "${ROOT}/scripts/validate_deployment.sh" "$CLOUDRUN_URL" "cloudrun"

echo ""
ok "══ CLOUD RUN DEPLOYMENT + VALIDATION COMPLETE ══"
echo -e "${BOLD}URL      : ${CLOUDRUN_URL}${NC}"
echo -e "${BOLD}Docs     : ${CLOUDRUN_URL}/docs${NC}"
echo -e "${BOLD}Project  : ${PROJECT_ID}${NC}"
echo -e "${BOLD}Region   : ${REGION}${NC}"
echo -e "${BOLD}Image    : ${IMAGE_NAME}:${COMMIT_SHA}${NC}"
