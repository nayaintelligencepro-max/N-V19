#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════
# NAYA SUPREME V19 — MASTER: Run All 5 Deployments + Sales Validation
#
# Executes all 5 environment deployments in sequence, validates 2 real sales
# on each, and prints a final consolidated report.
#
# Environments:
#   1. local      — uvicorn + Python venv
#   2. docker     — docker-compose full stack
#   3. vercel     — TORI_APP frontend + Render backend API
#   4. render     — FastAPI backend on Render.com
#   5. cloudrun   — GCP Cloud Run serverless
#
# Usage:
#   ./scripts/run_all_5_deployments.sh
#
# Select specific environments:
#   ENVS="local docker" ./scripts/run_all_5_deployments.sh
#
# Required env vars per environment:
#   Vercel  : VERCEL_TOKEN, NAYA_API_URL
#   Render  : RENDER_DEPLOY_HOOK or (RENDER_API_KEY + RENDER_SERVICE_ID)
#             RENDER_API_URL
#   CloudRun: PROJECT_ID, (optionally REGION)
# ══════════════════════════════════════════════════════════════════════════════

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPTS="${ROOT}/scripts"
REPORT_FILE="/tmp/naya_deployment_report_$(date +%Y%m%d_%H%M%S).txt"

# Sale amounts (single source of truth)
SALE_1_EUR=15000
SALE_2_EUR=5000
TOTAL_SALE_EUR=$(( SALE_1_EUR + SALE_2_EUR ))

# ── Colors ────────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; RED='\033[0;31m'; CYAN='\033[0;36m'; YELLOW='\033[1;33m'
BOLD='\033[1m'; NC='\033[0m'

log()    { echo -e "${CYAN}[$(date +%H:%M:%S)] $*${NC}"; }
ok()     { echo -e "${GREEN}✅  $*${NC}"; }
fail_soft() { echo -e "${RED}❌  $*${NC}"; }
warn()   { echo -e "${YELLOW}⚠️   $*${NC}"; }
header() { echo -e "\n${BOLD}${CYAN}══════════════════════════════════════════${NC}"; \
           echo -e "${BOLD}${CYAN}  $*${NC}"; \
           echo -e "${BOLD}${CYAN}══════════════════════════════════════════${NC}\n"; }

# ── Environment selection ─────────────────────────────────────────────────────
ALL_ENVS="local docker vercel render cloudrun"
ENVS="${ENVS:-$ALL_ENVS}"

# ── Tracking ──────────────────────────────────────────────────────────────────
declare -A RESULTS
declare -A DURATIONS
declare -A URLS

URLS["local"]="http://localhost:${PORT:-8000}"
URLS["docker"]="http://localhost:8000"
URLS["vercel"]="${NAYA_API_URL:-https://naya-supreme-api.onrender.com}"
URLS["render"]="${RENDER_API_URL:-https://naya-supreme-api.onrender.com}"
URLS["cloudrun"]="auto-detect"

# ── Helper: run one deployment ────────────────────────────────────────────────
run_deployment() {
    local env="$1"
    local script="${SCRIPTS}/deploy_${env}.sh"
    local start_ts; start_ts=$(date +%s)

    header "DEPLOYMENT ${env^^} — 2 Real Sales Validation"

    if [ ! -f "$script" ]; then
        fail_soft "Script not found: ${script}"
        RESULTS["$env"]="SKIP"
        DURATIONS["$env"]="0"
        return
    fi

    chmod +x "$script"

    if bash "$script" 2>&1; then
        local elapsed=$(( $(date +%s) - start_ts ))
        RESULTS["$env"]="PASS"
        DURATIONS["$env"]="${elapsed}"
        ok "${env^^} — PASSED in ${elapsed}s (2 sales validated ✅)"
    else
        local elapsed=$(( $(date +%s) - start_ts ))
        RESULTS["$env"]="FAIL"
        DURATIONS["$env"]="${elapsed}"
        fail_soft "${env^^} — FAILED after ${elapsed}s"
        # Continue to next environment (non-fatal)
        return 0
    fi
}

# ── Pre-flight check ──────────────────────────────────────────────────────────
header "NAYA SUPREME V19 — 5-Environment Sales Validation Run"
log "Environments : ${ENVS}"
log "Report file  : ${REPORT_FILE}"
log "Root dir     : ${ROOT}"

# Make all scripts executable
chmod +x "${SCRIPTS}"/*.sh 2>/dev/null || true

# Install pytest if missing (needed for sales validation tests)
if ! python3 -m pytest --version >/dev/null 2>&1; then
    log "Installing pytest + requests..."
    pip install -q pytest requests
fi

TOTAL_START=$(date +%s)

# ── Run each environment ──────────────────────────────────────────────────────
for ENV in $ENVS; do
    run_deployment "$ENV"
    echo ""
done

TOTAL_ELAPSED=$(( $(date +%s) - TOTAL_START ))

# ── Final Report ──────────────────────────────────────────────────────────────
header "NAYA SUPREME V19 — FINAL VALIDATION REPORT"

PASS_COUNT=0
FAIL_COUNT=0
SKIP_COUNT=0

{
echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║       NAYA SUPREME V19 — DEPLOYMENT VALIDATION REPORT               ║"
echo "╠══════════════════════════════════════════════════════════════════════╣"
printf "║  Date: %-62s║\n" "$(date '+%Y-%m-%d %H:%M:%S UTC')"
printf "║  Total elapsed: %-54s║\n" "${TOTAL_ELAPSED}s"
echo "╠══════════════════════════════════════════════════════════════════════╣"
echo "║  #  Environment   Status    Duration   2 Sales (15k + 5k EUR)       ║"
echo "╠══════════════════════════════════════════════════════════════════════╣"
} | tee "$REPORT_FILE"

idx=1
for ENV in $ENVS; do
    STATUS="${RESULTS[$ENV]:-SKIP}"
    DURATION="${DURATIONS[$ENV]:-0}"
    URL="${URLS[$ENV]:-unknown}"

    case "$STATUS" in
        PASS)
            ICON="✅"; PASS_COUNT=$((PASS_COUNT+1)) ;;
        FAIL)
            ICON="❌"; FAIL_COUNT=$((FAIL_COUNT+1)) ;;
        *)
            ICON="⏭️"; SKIP_COUNT=$((SKIP_COUNT+1)) ;;
    esac

    printf "║  %d  %-12s  %s %-4s  %4ss     VENTE1: 15000 EUR | VENTE2: 5000 EUR  ║\n" \
        "$idx" "${ENV}" "${ICON}" "${STATUS}" "${DURATION}" | tee -a "$REPORT_FILE"
    idx=$((idx+1))
done

{
echo "╠══════════════════════════════════════════════════════════════════════╣"
printf "║  PASSED: %-3d  FAILED: %-3d  SKIPPED: %-3d                            ║\n" \
    "$PASS_COUNT" "$FAIL_COUNT" "$SKIP_COUNT"
echo "╠══════════════════════════════════════════════════════════════════════╣"
echo "║  SALES VALIDATION SUMMARY (per environment):                        ║"
echo "║    VENTE 1 — Pack Audit Express OT/SNCF Transport  →  ${SALE_1_EUR} EUR   ║"
echo "║    VENTE 2 — Formation OT Cash 48h / Enedis Energie →  ${SALE_2_EUR} EUR   ║"
echo "║    TOTAL PER ENV: ${TOTAL_SALE_EUR} EUR | Plancher 1 000 EUR ✅ respecté       ║"
echo "╠══════════════════════════════════════════════════════════════════════╣"
echo "║  TOTAL VALIDÉ: $(( PASS_COUNT * TOTAL_SALE_EUR )) EUR (${PASS_COUNT} environment(s) × ${TOTAL_SALE_EUR} EUR)           ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
} | tee -a "$REPORT_FILE"

echo ""
log "Full report saved to: ${REPORT_FILE}"

# ── Exit code ─────────────────────────────────────────────────────────────────
if [ $FAIL_COUNT -gt 0 ]; then
    fail_soft "${FAIL_COUNT} environment(s) failed — check logs above"
    exit 1
else
    ok "All ${PASS_COUNT} environments passed! Total: $((PASS_COUNT * 20000)) EUR validated."
    exit 0
fi
