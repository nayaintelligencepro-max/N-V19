#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════
# NAYA SUPREME V19 — Deployment Validator
# Usage: ./scripts/validate_deployment.sh <BASE_URL> <ENV_NAME>
# Example:
#   ./scripts/validate_deployment.sh http://localhost:8000 local
#   ./scripts/validate_deployment.sh https://naya-api.onrender.com render
# ══════════════════════════════════════════════════════════════════════════════

set -euo pipefail

BASE_URL="${1:-http://localhost:8000}"
ENV_NAME="${2:-unknown}"
TIMEOUT="${SALES_TIMEOUT:-30}"
MAX_WAIT="${DEPLOY_WAIT:-120}"       # seconds to wait for API to be ready
STEP=5

# ── Colors ────────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

log()    { echo -e "${CYAN}[$(date +%H:%M:%S)] $*${NC}"; }
ok()     { echo -e "${GREEN}✅  $*${NC}"; }
fail()   { echo -e "${RED}❌  $*${NC}"; exit 1; }
warn()   { echo -e "${YELLOW}⚠️   $*${NC}"; }
header() { echo -e "\n${BOLD}${CYAN}══ $* ══${NC}\n"; }

# ── Wait for API to be ready ──────────────────────────────────────────────────
wait_for_api() {
    local url="${BASE_URL}/api/v1/health"
    local elapsed=0

    log "Waiting for API at ${url} (max ${MAX_WAIT}s)..."
    while [ $elapsed -lt $MAX_WAIT ]; do
        if curl -sf --max-time 5 "${url}" | grep -q "healthy" 2>/dev/null; then
            ok "API ready after ${elapsed}s"
            return 0
        fi
        sleep $STEP
        elapsed=$((elapsed + STEP))
        log "  Still waiting... ${elapsed}/${MAX_WAIT}s"
    done
    fail "API not ready after ${MAX_WAIT}s — aborting validation"
}

# ── Run pytest sales validation ───────────────────────────────────────────────
run_sales_validation() {
    header "Running 2-Sales Validation on ${ENV_NAME}"

    local report_xml="/tmp/naya_sales_${ENV_NAME}_$(date +%s).xml"

    BASE_URL="${BASE_URL}" \
    DEPLOY_ENV="${ENV_NAME}" \
    SALES_TIMEOUT="${TIMEOUT}" \
    MIN_AMOUNT="1000" \
    python -m pytest \
        "$(dirname "$0")/../tests/test_sales_validation.py" \
        -v \
        --tb=short \
        --no-header \
        -p no:cacheprovider \
        --junit-xml="${report_xml}" \
        2>&1

    local exit_code=$?

    if [ $exit_code -eq 0 ]; then
        ok "All sales validation tests PASSED for ${ENV_NAME}"
    else
        fail "Sales validation FAILED for ${ENV_NAME} (exit code ${exit_code})"
    fi

    log "JUnit report saved to: ${report_xml}"
    return $exit_code
}

# ── Main ──────────────────────────────────────────────────────────────────────
header "NAYA SUPREME V19 — Deployment Validation: ${ENV_NAME^^}"
log "Target URL : ${BASE_URL}"
log "Environment: ${ENV_NAME}"
log "Timeout    : ${TIMEOUT}s per request"

wait_for_api
run_sales_validation

echo ""
ok "══ DEPLOYMENT VALIDATION COMPLETE: ${ENV_NAME^^} ══"
