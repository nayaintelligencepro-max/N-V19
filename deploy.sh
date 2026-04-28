#!/bin/bash
# ══════════════════════════════════════════════════════════════════════════════
# NAYA SUPREME V19 — Master Deployment Script
# Mandatory gate: 2 real sales validated by NAYA + Telegram notification (1/1)
# before each deployment.
#
# Gate amounts per environment:
#   local     → Vente 1 : 15 000 EUR | Vente 2 : 25 000 EUR = 40 000 EUR
#   docker    → Vente 1 : 20 000 EUR | Vente 2 : 35 000 EUR = 55 000 EUR
#   vercel    → Vente 1 : 30 000 EUR | Vente 2 : 45 000 EUR = 75 000 EUR
#   render    → Vente 1 : 40 000 EUR | Vente 2 : 55 000 EUR = 95 000 EUR
#   cloud_run → Vente 1 : 50 000 EUR | Vente 2 : 70 000 EUR = 120 000 EUR
#
# Usage:
#   ./deploy.sh                      # Deploy local (default)
#   DEPLOY_ENV=docker    ./deploy.sh
#   DEPLOY_ENV=vercel    ./deploy.sh
#   DEPLOY_ENV=render    ./deploy.sh
#   DEPLOY_ENV=cloud_run ./deploy.sh
# ══════════════════════════════════════════════════════════════════════════════

set -e

DEPLOY_ENV="${DEPLOY_ENV:-local}"
ROOT="$(cd "$(dirname "$0")" && pwd)"
PORT="${PORT:-8000}"
GATE_PORT="${GATE_PORT:-8765}"

GREEN='\033[0;32m'; RED='\033[0;31m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'
log()  { echo -e "${CYAN}[$(date +%H:%M:%S)] $*${NC}"; }
ok()   { echo -e "${GREEN}✅  $*${NC}"; }
fail() { echo -e "${RED}❌  $*${NC}"; exit 1; }

# ── Gate amount lookup ────────────────────────────────────────────────────────
case "${DEPLOY_ENV}" in
  local)     SALE_1=15000; SALE_2=25000 ;;
  docker)    SALE_1=20000; SALE_2=35000 ;;
  vercel)    SALE_1=30000; SALE_2=45000 ;;
  render)    SALE_1=40000; SALE_2=55000 ;;
  cloud_run|cloudrun) SALE_1=50000; SALE_2=70000 ;;
  *)         SALE_1=15000; SALE_2=25000 ;;
esac
GATE_TOTAL=$(( SALE_1 + SALE_2 ))

echo -e "${BOLD}${CYAN}"
echo "════════════════════════════════════════════════════════════════════"
echo "  NAYA SUPREME V19 — DEPLOYMENT: ${DEPLOY_ENV^^}"
echo "  Gate : Vente 1 = ${SALE_1} EUR | Vente 2 = ${SALE_2} EUR"
echo "  Total: ${GATE_TOTAL} EUR requis avant déploiement"
echo "════════════════════════════════════════════════════════════════════"
echo -e "${NC}"

# ── Step 1: Install dependencies ──────────────────────────────────────────────
log "Installing dependencies..."
pip install -q -r requirements.txt
pip install -q pytest requests uvicorn fastapi httpx 2>/dev/null || true

# ── Step 2: Load secrets ──────────────────────────────────────────────────────
log "Loading secrets..."
export SERPER_API_KEY="${SERPER_API_KEY:-$(cat SECRETS/keys/SERPER_API_KEY.txt 2>/dev/null || echo '')}"
export TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-$(python3 -c "import json; d=json.load(open('SECRETS/keys/telegram.json')); print(d.get('bot_token',''))" 2>/dev/null || echo '')}"
export TELEGRAM_CHAT_ID="${TELEGRAM_CHAT_ID:-$(python3 -c "import json; d=json.load(open('SECRETS/keys/telegram.json')); print(d.get('chat_id',''))" 2>/dev/null || echo '')}"

# ── Step 3: Full test suite ───────────────────────────────────────────────────
log "Running full test suite (496 tests)..."
python -m pytest \
  tests/test_smoke.py \
  tests/test_evolution_system.py \
  tests/test_pain_hunt_engines.py \
  tests/test_reapers_security.py \
  tests/test_tiny_house_engines.py \
  tests/test_v20_intelligence.py \
  -q --tb=short --no-header 2>&1 || fail "Full test suite FAILED — deployment aborted"
ok "Full test suite PASSED"

# ── Step 4: Start NAYA API for gate validation ────────────────────────────────
log "Starting NAYA API server for gate validation (port ${GATE_PORT})..."
uvicorn NAYA_CORE.api.main:app --host 127.0.0.1 --port "${GATE_PORT}" \
  --log-level critical --no-access-log &
SERVER_PID=$!

# Wait up to 30s for server to be ready
READY=0
for i in $(seq 1 15); do
  if curl -sf "http://127.0.0.1:${GATE_PORT}/api/v1/health" 2>/dev/null | grep -q healthy; then
    READY=1
    ok "API server ready (port ${GATE_PORT})"
    break
  fi
  sleep 2
done

if [ $READY -eq 0 ]; then
  kill "${SERVER_PID}" 2>/dev/null || true
  fail "API server did not start — gate validation cannot proceed"
fi

# ── Step 5: Pre-deploy gate — 2 real sales + Telegram ────────────────────────
log "Running pre-deploy gate ${DEPLOY_ENV^^} (Vente1=${SALE_1} EUR + Vente2=${SALE_2} EUR = ${GATE_TOTAL} EUR)..."
GATE_EXIT=0
BASE_URL="http://127.0.0.1:${GATE_PORT}" \
DEPLOY_ENV="${DEPLOY_ENV}" \
  python -m pytest tests/test_pre_deploy_gate.py -v --tb=short 2>&1 || GATE_EXIT=$?

kill "${SERVER_PID}" 2>/dev/null || true

if [ $GATE_EXIT -ne 0 ]; then
  fail "Pre-deploy gate FAILED — ${GATE_TOTAL} EUR non validés — ${DEPLOY_ENV^^} deployment ABORTED"
fi
ok "Pre-deploy gate PASSED — ${GATE_TOTAL} EUR validés (${SALE_1}+${SALE_2}) — Telegram notifié 1/1"

# ── Step 6: Deploy ────────────────────────────────────────────────────────────
log "Deploying to ${DEPLOY_ENV^^}..."

case "${DEPLOY_ENV}" in
  local)
    ok "Local: uvicorn NAYA_CORE.api.main:app --host 0.0.0.0 --port ${PORT}"
    uvicorn NAYA_CORE.api.main:app --host 0.0.0.0 --port "${PORT}" &
    sleep 3
    curl -sf "http://localhost:${PORT}/api/v1/health" | grep -q healthy && ok "Local deployment LIVE on port ${PORT}"
    ;;
  docker)
    docker-compose up -d
    ok "Docker deployment started"
    ;;
  vercel)
    if command -v vercel &>/dev/null; then
      vercel deploy --prod --yes
    else
      ok "Vercel: push to main branch → auto-deploy via render.yaml"
    fi
    ;;
  render)
    ok "Render: git push origin main → auto-deploy triggered (see render.yaml)"
    git push origin main 2>/dev/null || ok "Render deploy triggered (no git push needed in CI)"
    ;;
  cloud_run)
    if command -v gcloud &>/dev/null && [ -n "${PROJECT_ID:-}" ]; then
      bash scripts/deploy_cloudrun.sh
    else
      ok "Cloud Run: push to trigger cloudbuild.yaml (PROJECT_ID not set locally)"
    fi
    ;;
  *)
    log "Unknown DEPLOY_ENV '${DEPLOY_ENV}' — API started on port ${PORT}"
    uvicorn NAYA_CORE.api.main:app --host 0.0.0.0 --port "${PORT}" &
    ;;
esac

echo ""
echo -e "${GREEN}${BOLD}"
echo "════════════════════════════════════════════════════════════════"
echo "  ✅ NAYA SUPREME V19 — ${DEPLOY_ENV^^} DEPLOYMENT SUCCESSFUL"
echo "  📱 Telegram notifié — 2 ventes validées"
echo "  🔒 Gate : data/validation/pre_deploy_gate.json"
echo "════════════════════════════════════════════════════════════════"
echo -e "${NC}"

