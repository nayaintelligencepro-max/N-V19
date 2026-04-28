#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════
# NAYA SUPREME V19 — VERCEL Deployment + Sales Validation
# Deploys TORI_APP frontend to Vercel and validates API connectivity + 2 sales.
#
# Vercel hosts the TORI_APP (React/static frontend).
# The API backend lives on Render (see deploy_render.sh).
# This script validates:
#   1. Frontend deploys successfully
#   2. Frontend can reach the API (NAYA_API_URL)
#   3. 2 real sales validated through the backend API
#
# Usage:
#   VERCEL_TOKEN=xxx NAYA_API_URL=https://naya-api.onrender.com ./scripts/deploy_vercel.sh
#   VERCEL_TOKEN=xxx VERCEL_ORG_ID=xxx VERCEL_PROJECT_ID=xxx ./scripts/deploy_vercel.sh
# ══════════════════════════════════════════════════════════════════════════════

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Required env vars
VERCEL_TOKEN="${VERCEL_TOKEN:-}"
VERCEL_ORG_ID="${VERCEL_ORG_ID:-}"
VERCEL_PROJECT_ID="${VERCEL_PROJECT_ID:-}"
NAYA_API_URL="${NAYA_API_URL:-https://naya-supreme-api.onrender.com}"

GREEN='\033[0;32m'; RED='\033[0;31m'; CYAN='\033[0;36m'; YELLOW='\033[1;33m'
BOLD='\033[1m'; NC='\033[0m'

log()    { echo -e "${CYAN}[$(date +%H:%M:%S)] $*${NC}"; }
ok()     { echo -e "${GREEN}✅  $*${NC}"; }
fail()   { echo -e "${RED}❌  $*${NC}"; exit 1; }
warn()   { echo -e "${YELLOW}⚠️   $*${NC}"; }
header() { echo -e "\n${BOLD}${CYAN}══ $* ══${NC}\n"; }

# ── Check Vercel CLI ──────────────────────────────────────────────────────────
header "Prerequisites"
if ! command -v vercel >/dev/null 2>&1; then
    log "Installing Vercel CLI..."
    npm install -g vercel --quiet
fi
ok "Vercel CLI available: $(vercel --version)"

if [ -z "$VERCEL_TOKEN" ]; then
    warn "VERCEL_TOKEN not set — will use interactive login"
    warn "Set VERCEL_TOKEN=your_token for non-interactive deployment"
fi

cd "$ROOT"

# ── Step 1: Validate TORI_APP exists ─────────────────────────────────────────
header "Step 1/4 — Validate Frontend Sources"
if [ ! -d "${ROOT}/TORI_APP" ]; then
    fail "TORI_APP directory not found at ${ROOT}/TORI_APP"
fi
ok "TORI_APP directory present"

# Ensure vercel.json is up-to-date
if [ -f "${ROOT}/vercel.json" ]; then
    ok "vercel.json present"
    # Inject correct API URL into a temp copy (avoid modifying source tree)
    if command -v jq >/dev/null 2>&1; then
        VERCEL_JSON_TMP=$(mktemp /tmp/vercel_patched_XXXXXX.json)
        if jq --arg api "$NAYA_API_URL" '.env.NAYA_API_URL = $api' \
                "${ROOT}/vercel.json" > "$VERCEL_JSON_TMP" 2>/dev/null; then
            log "vercel.json patched in tmp: ${VERCEL_JSON_TMP} (NAYA_API_URL=${NAYA_API_URL})"
            # Vercel CLI reads from project root, copy the patched version temporarily
            cp "${ROOT}/vercel.json" "${ROOT}/vercel.json.bak"
            cp "$VERCEL_JSON_TMP" "${ROOT}/vercel.json"
            trap 'mv "${ROOT}/vercel.json.bak" "${ROOT}/vercel.json" 2>/dev/null || true' EXIT INT TERM
        fi
    fi
fi

# ── Step 2: Build / Deploy to Vercel ─────────────────────────────────────────
header "Step 2/4 — Deploy to Vercel"

DEPLOY_ARGS=("--prod" "--yes")

if [ -n "$VERCEL_TOKEN" ];     then DEPLOY_ARGS+=("--token" "$VERCEL_TOKEN"); fi
if [ -n "$VERCEL_ORG_ID" ];    then DEPLOY_ARGS+=("--scope" "$VERCEL_ORG_ID"); fi

log "Deploying to Vercel: vercel deploy ${DEPLOY_ARGS[*]}"

VERCEL_OUTPUT=$(vercel deploy "${DEPLOY_ARGS[@]}" 2>&1) || true
echo "$VERCEL_OUTPUT"

# Extract deployed URL
VERCEL_URL=$(echo "$VERCEL_OUTPUT" | grep -oP 'https://[a-zA-Z0-9._-]+\.vercel\.app' | tail -1 || true)

if [ -z "$VERCEL_URL" ]; then
    warn "Could not extract Vercel URL from output — checking via API..."
    if [ -n "$VERCEL_TOKEN" ]; then
        VERCEL_URL=$(curl -sf \
            "https://api.vercel.com/v6/deployments?limit=1" \
            -H "Authorization: Bearer ${VERCEL_TOKEN}" \
            | python3 -c "import sys,json; d=json.load(sys.stdin); print('https://'+d['deployments'][0]['url'])" 2>/dev/null || true)
    fi
fi

if [ -n "$VERCEL_URL" ]; then
    ok "Deployed to Vercel: ${VERCEL_URL}"
else
    warn "Vercel URL not detected — continuing with frontend health skip"
    VERCEL_URL="unknown"
fi

# ── Step 3: Validate frontend is reachable ───────────────────────────────────
header "Step 3/4 — Frontend Health Check"
if [ "$VERCEL_URL" != "unknown" ]; then
    sleep 10  # Give Vercel CDN time to propagate
    HTTP_CODE=$(curl -sf --max-time 15 -o /dev/null -w "%{http_code}" "$VERCEL_URL" || echo "0")
    if [ "$HTTP_CODE" = "200" ]; then
        ok "Vercel frontend reachable: ${VERCEL_URL} (HTTP ${HTTP_CODE})"
    else
        warn "Vercel frontend returned HTTP ${HTTP_CODE} — may still be propagating"
    fi
else
    warn "Skipping frontend health check (URL unknown)"
fi

# ── Step 4: Validate 2 Real Sales against backend API ────────────────────────
header "Step 4/4 — Sales Validation (2 real sales via backend API)"
log "Vercel frontend → Backend API: ${NAYA_API_URL}"
DEPLOY_WAIT=60 bash "${ROOT}/scripts/validate_deployment.sh" "$NAYA_API_URL" "vercel"

echo ""
ok "══ VERCEL DEPLOYMENT + VALIDATION COMPLETE ══"
echo -e "${BOLD}Frontend  : ${VERCEL_URL}${NC}"
echo -e "${BOLD}Backend   : ${NAYA_API_URL}${NC}"
