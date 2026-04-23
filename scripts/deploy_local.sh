#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════
# NAYA SUPREME V19 — LOCAL Deployment + Sales Validation
# Starts the FastAPI server locally and validates 2 real sales.
#
# Usage:
#   ./scripts/deploy_local.sh
#   PORT=8080 ./scripts/deploy_local.sh
# ══════════════════════════════════════════════════════════════════════════════

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${PORT:-8000}"
HOST="0.0.0.0"
BASE_URL="http://localhost:${PORT}"
VENV_DIR="${ROOT}/.venv"
LOG_FILE="/tmp/naya_local_api.log"
PID_FILE="/tmp/naya_local_api.pid"

GREEN='\033[0;32m'; RED='\033[0;31m'; CYAN='\033[0;36m'
BOLD='\033[1m'; NC='\033[0m'

log()    { echo -e "${CYAN}[$(date +%H:%M:%S)] $*${NC}"; }
ok()     { echo -e "${GREEN}✅  $*${NC}"; }
fail()   { echo -e "${RED}❌  $*${NC}"; exit 1; }
header() { echo -e "\n${BOLD}${CYAN}══ $* ══${NC}\n"; }

cleanup() {
    if [ -f "$PID_FILE" ]; then
        local pid; pid=$(cat "$PID_FILE")
        log "Stopping local API (PID ${pid})..."
        kill "$pid" 2>/dev/null || true
        rm -f "$PID_FILE"
        ok "Local API stopped"
    fi
}
trap cleanup EXIT INT TERM

# ── Step 1: Setup Python environment ─────────────────────────────────────────
header "Step 1/4 — Python Environment Setup"
cd "$ROOT"

if [ ! -d "$VENV_DIR" ]; then
    log "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# shellcheck source=/dev/null
source "${VENV_DIR}/bin/activate"
log "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
ok "Dependencies installed"

# ── Step 2: Prepare .env ──────────────────────────────────────────────────────
header "Step 2/4 — Environment Configuration"
if [ ! -f "${ROOT}/.env" ]; then
    log "No .env found — copying .env.example..."
    cp "${ROOT}/.env.example" "${ROOT}/.env"
    warn() { echo -e "\033[1;33m⚠️   $*\033[0m"; }
    warn "Using .env.example defaults — set real API keys for full functionality"
fi
ok ".env ready"

# ── Step 3: Start the API ─────────────────────────────────────────────────────
header "Step 3/4 — Starting Local API (port ${PORT})"
export PYTHONPATH="${ROOT}:${PYTHONPATH:-}"
export ENVIRONMENT=development

uvicorn NAYA_CORE.api.main:app \
    --host "$HOST" \
    --port "$PORT" \
    --workers 2 \
    --log-level info \
    > "$LOG_FILE" 2>&1 &

echo $! > "$PID_FILE"
ok "API started (PID $(cat "$PID_FILE")) — logs at ${LOG_FILE}"

# ── Step 4: Validate 2 Real Sales ─────────────────────────────────────────────
header "Step 4/4 — Sales Validation (2 real sales)"
DEPLOY_WAIT=60 bash "${ROOT}/scripts/validate_deployment.sh" "$BASE_URL" "local"

echo ""
ok "══ LOCAL DEPLOYMENT + VALIDATION COMPLETE ══"
echo -e "${BOLD}API URL: ${BASE_URL}${NC}"
echo -e "${BOLD}Logs   : ${LOG_FILE}${NC}"
