#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════
# NAYA SUPREME V19 — RENDER Deployment + Sales Validation
# Triggers a Render deploy via webhook or CLI, waits for it, validates 2 sales.
#
# Render deploy methods (in priority order):
#   1. RENDER_DEPLOY_HOOK  — deploy hook URL (preferred, no CLI needed)
#   2. render CLI          — requires RENDER_API_KEY + RENDER_SERVICE_ID
#   3. git push to branch  — triggers auto-deploy via render.yaml
#
# Usage:
#   RENDER_DEPLOY_HOOK=https://api.render.com/deploy/srv-xxx ./scripts/deploy_render.sh
#   RENDER_API_KEY=rnd_xxx RENDER_SERVICE_ID=srv-xxx ./scripts/deploy_render.sh
#   RENDER_API_URL=https://naya-supreme-api.onrender.com ./scripts/deploy_render.sh
# ══════════════════════════════════════════════════════════════════════════════

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

RENDER_DEPLOY_HOOK="${RENDER_DEPLOY_HOOK:-}"
RENDER_API_KEY="${RENDER_API_KEY:-}"
RENDER_SERVICE_ID="${RENDER_SERVICE_ID:-}"
RENDER_API_URL="${RENDER_API_URL:-https://naya-supreme-api.onrender.com}"
RENDER_REGION="${RENDER_REGION:-frankfurt}"

GREEN='\033[0;32m'; RED='\033[0;31m'; CYAN='\033[0;36m'; YELLOW='\033[1;33m'
BOLD='\033[1m'; NC='\033[0m'

log()    { echo -e "${CYAN}[$(date +%H:%M:%S)] $*${NC}"; }
ok()     { echo -e "${GREEN}✅  $*${NC}"; }
fail()   { echo -e "${RED}❌  $*${NC}"; exit 1; }
warn()   { echo -e "${YELLOW}⚠️   $*${NC}"; }
header() { echo -e "\n${BOLD}${CYAN}══ $* ══${NC}\n"; }

cd "$ROOT"

# ── Step 1: Validate render.yaml ──────────────────────────────────────────────
header "Step 1/4 — Render Configuration"
if [ ! -f "${ROOT}/render.yaml" ]; then
    fail "render.yaml not found — required for Render deployment"
fi
ok "render.yaml present"
log "Service name  : naya-supreme-api"
log "Region        : ${RENDER_REGION}"
log "Start command : uvicorn NAYA_CORE.api.main:app"

# ── Step 2: Trigger Deploy ────────────────────────────────────────────────────
header "Step 2/4 — Triggering Render Deploy"

if [ -n "$RENDER_DEPLOY_HOOK" ]; then
    # Method 1: Deploy Hook (fastest, no auth needed besides the URL)
    log "Triggering deploy via webhook..."
    RESPONSE=$(curl -sf --max-time 30 -X POST "${RENDER_DEPLOY_HOOK}" || echo "error")
    if echo "$RESPONSE" | grep -qi "error"; then
        warn "Deploy hook response: ${RESPONSE} — may already be deploying"
    else
        ok "Deploy triggered via webhook"
    fi

elif [ -n "$RENDER_API_KEY" ] && [ -n "$RENDER_SERVICE_ID" ]; then
    # Method 2: Render API
    log "Triggering deploy via Render API (service: ${RENDER_SERVICE_ID})..."
    RESPONSE=$(curl -sf --max-time 30 \
        -X POST \
        "https://api.render.com/v1/services/${RENDER_SERVICE_ID}/deploys" \
        -H "Authorization: Bearer ${RENDER_API_KEY}" \
        -H "Content-Type: application/json" \
        -d '{"clearCache": "do_not_clear"}' || echo '{"error":"api_call_failed"}')
    DEPLOY_ID=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id',''))" 2>/dev/null || true)
    if [ -n "$DEPLOY_ID" ]; then
        ok "Deploy triggered via Render API (ID: ${DEPLOY_ID})"
    else
        warn "Render API response: ${RESPONSE}"
        warn "Assuming auto-deploy is configured via render.yaml → git push"
    fi

else
    # Method 3: Assume auto-deploy is active (git push already triggers it)
    warn "No RENDER_DEPLOY_HOOK or RENDER_API_KEY set"
    warn "Assuming auto-deploy is active via git push → render.yaml"
    log "To enable explicit deploy: set RENDER_DEPLOY_HOOK or RENDER_API_KEY+RENDER_SERVICE_ID"
fi

# ── Step 3: Wait for deploy to complete ──────────────────────────────────────
header "Step 3/4 — Waiting for Render Deploy"
log "Target URL: ${RENDER_API_URL}"

MAX_WAIT=300  # Render cold-starts can take up to 5 minutes
log "Max wait: ${MAX_WAIT}s (Render free tier may be slower on first deploy)"

elapsed=0
while [ $elapsed -lt $MAX_WAIT ]; do
    HTTP_CODE=$(curl -sf --max-time 5 -o /dev/null -w "%{http_code}" \
        "${RENDER_API_URL}/api/v1/health" 2>/dev/null || echo "0")

    if [ "$HTTP_CODE" = "200" ]; then
        ok "Render API is live (HTTP ${HTTP_CODE}) after ${elapsed}s"
        break
    fi

    sleep 10
    elapsed=$((elapsed + 10))
    log "  Waiting... ${elapsed}/${MAX_WAIT}s (last HTTP: ${HTTP_CODE})"
done

if [ $elapsed -ge $MAX_WAIT ]; then
    # Check if API exists but is slow
    HTTP_CODE=$(curl -sf --max-time 30 -o /dev/null -w "%{http_code}" \
        "${RENDER_API_URL}/api/v1/health" 2>/dev/null || echo "0")
    if [ "$HTTP_CODE" != "200" ]; then
        fail "Render deploy not ready after ${MAX_WAIT}s (HTTP ${HTTP_CODE}) — check Render dashboard"
    fi
fi

# ── Step 4: Validate 2 Real Sales ─────────────────────────────────────────────
header "Step 4/4 — Sales Validation (2 real sales on Render)"
DEPLOY_WAIT=30 bash "${ROOT}/scripts/validate_deployment.sh" "$RENDER_API_URL" "render"

echo ""
ok "══ RENDER DEPLOYMENT + VALIDATION COMPLETE ══"
echo -e "${BOLD}API URL  : ${RENDER_API_URL}${NC}"
echo -e "${BOLD}Docs     : ${RENDER_API_URL}/docs${NC}"
echo -e "${BOLD}Region   : ${RENDER_REGION}${NC}"
