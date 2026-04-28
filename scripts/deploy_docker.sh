#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════
# NAYA SUPREME V19 — DOCKER Deployment + Sales Validation
# Builds the Docker image, starts docker-compose, validates 2 real sales.
#
# Usage:
#   ./scripts/deploy_docker.sh
#   DOCKER_TAG=v19.2 ./scripts/deploy_docker.sh
# ══════════════════════════════════════════════════════════════════════════════

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DOCKER_TAG="${DOCKER_TAG:-naya-supreme:v19}"
DOCKER_NO_CACHE="${DOCKER_NO_CACHE:-false}"
BASE_URL="http://localhost:8000"
COMPOSE_FILE="${ROOT}/docker-compose.yml"

GREEN='\033[0;32m'; RED='\033[0;31m'; CYAN='\033[0;36m'
BOLD='\033[1m'; NC='\033[0m'

log()    { echo -e "${CYAN}[$(date +%H:%M:%S)] $*${NC}"; }
ok()     { echo -e "${GREEN}✅  $*${NC}"; }
fail()   { echo -e "${RED}❌  $*${NC}"; exit 1; }
header() { echo -e "\n${BOLD}${CYAN}══ $* ══${NC}\n"; }

cleanup() {
    log "Cleaning up Docker Compose stack..."
    docker compose -f "$COMPOSE_FILE" down --remove-orphans 2>/dev/null || true
    ok "Docker stack stopped"
}
trap cleanup EXIT INT TERM

# ── Prerequisite check ────────────────────────────────────────────────────────
header "Docker Prerequisites"
command -v docker >/dev/null 2>&1 || fail "Docker not installed"
command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1 || fail "docker compose plugin required"
ok "Docker available: $(docker --version)"

cd "$ROOT"

# ── Step 1: Prepare .env ──────────────────────────────────────────────────────
header "Step 1/4 — Environment Configuration"
if [ ! -f "${ROOT}/.env" ]; then
    log "Copying .env.example → .env..."
    cp "${ROOT}/.env.example" "${ROOT}/.env"
fi
ok ".env ready"

# ── Step 2: Build Docker image ────────────────────────────────────────────────
header "Step 2/4 — Docker Build"
log "Building image: ${DOCKER_TAG}"
NO_CACHE_FLAG=""
if [ "${DOCKER_NO_CACHE:-false}" = "true" ]; then NO_CACHE_FLAG="--no-cache"; fi
docker build \
    --tag "$DOCKER_TAG" \
    --file "${ROOT}/Dockerfile" \
    --build-arg PYTHON_VERSION=3.11 \
    ${NO_CACHE_FLAG} \
    "${ROOT}"
ok "Image built: ${DOCKER_TAG}"

# ── Step 3: Start Docker Compose stack ───────────────────────────────────────
header "Step 3/4 — Docker Compose Stack"
log "Starting all services (postgres, redis, qdrant, rabbitmq, naya-api)..."

# Only start the API with lightweight deps (skip ELK/Grafana for validation speed)
docker compose -f "$COMPOSE_FILE" up -d \
    postgres redis qdrant rabbitmq naya-api

log "Waiting for all services to become healthy..."
local_wait=0
max_wait=180
while [ $local_wait -lt $max_wait ]; do
    if docker compose -f "$COMPOSE_FILE" ps | grep -q "naya-api" && \
       docker compose -f "$COMPOSE_FILE" ps naya-api | grep -q "healthy"; then
        ok "naya-api container is healthy"
        break
    fi
    sleep 5
    local_wait=$((local_wait + 5))
    log "  Waiting for containers... ${local_wait}/${max_wait}s"
done

if [ $local_wait -ge $max_wait ]; then
    log "Container health status:"
    docker compose -f "$COMPOSE_FILE" ps
    log "API logs (last 50 lines):"
    docker compose -f "$COMPOSE_FILE" logs --tail=50 naya-api
    fail "Docker stack not ready after ${max_wait}s"
fi

# ── Step 4: Validate 2 Real Sales ─────────────────────────────────────────────
header "Step 4/4 — Sales Validation (2 real sales via Docker)"
DEPLOY_WAIT=30 bash "${ROOT}/scripts/validate_deployment.sh" "$BASE_URL" "docker"

# Print container status
log "Container status:"
docker compose -f "$COMPOSE_FILE" ps

echo ""
ok "══ DOCKER DEPLOYMENT + VALIDATION COMPLETE ══"
echo -e "${BOLD}API URL   : ${BASE_URL}${NC}"
echo -e "${BOLD}Docs      : ${BASE_URL}/docs${NC}"
echo -e "${BOLD}Docker tag: ${DOCKER_TAG}${NC}"
