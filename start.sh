#!/bin/bash
# ═══════════════════════════════════════════════════════════
# NAYA SUPREME V13 — Demarrage ONE-CLICK
# Usage: bash start.sh
# Fonctionne sur Linux, Mac, et Windows (Git Bash/WSL)
# ═══════════════════════════════════════════════════════════
set -e
cd "$(dirname "$0")"

GREEN='\033[0;32m' YELLOW='\033[1;33m' RED='\033[0;31m' NC='\033[0m'
log() { echo -e "${GREEN}[NAYA]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
err() { echo -e "${RED}[ERR]${NC} $1"; }

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}   NAYA SUPREME V13 — Demarrage automatique${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo ""

# 1. Verifier Python 3.10+
if command -v python3 &>/dev/null; then
    PY=python3
elif command -v python &>/dev/null; then
    PY=python
else
    err "Python 3 introuvable. Installer Python 3.11+ depuis python.org"
    exit 1
fi

PY_VER=$($PY --version 2>&1 | grep -oP '\d+\.\d+')
log "Python $PY_VER detecte"

# 2. Creer venv si absent
if [ ! -d "venv" ]; then
    log "Creation environnement virtuel..."
    $PY -m venv venv
fi

# 3. Activer venv
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
fi

# 4. Installer dependances
log "Installation dependances..."
pip install -q --upgrade pip 2>/dev/null
pip install -q -r requirements.txt 2>/dev/null || {
    warn "Installation partielle — installation des essentiels..."
    pip install -q fastapi uvicorn httpx aiohttp python-dotenv pydantic \
        pydantic-settings python-multipart cryptography pyjwt requests \
        anthropic openai tenacity structlog beautifulsoup4 2>/dev/null
}

# 5. Creer dossiers
mkdir -p data/db data/cache data/exports logs

# 6. Verifier les cles API
log "Verification des cles API..."
$PY -c "
import sys; sys.path.insert(0, '.')
try:
    from SECRETS.secrets_loader import load_all_secrets, get_status
    load_all_secrets()
    st = get_status()
    print(f'  Cles actives: {st["score"]}')
    print(f'  LLM actif: {st["active_llm"]}')
    for g, keys in st['groups'].items():
        for k, ok in keys.items():
            symbol = '  OK' if ok else '  --'
            print(f'  {symbol} {g}.{k}')
except Exception as e:
    print(f'  Secrets: {e}')
"

echo ""
log "Demarrage NAYA SUPREME V13..."
echo ""
echo -e "${GREEN}  API:        http://localhost:${PORT:-8080}${NC}"
echo -e "${GREEN}  Docs:       http://localhost:${PORT:-8080}/docs${NC}"
echo -e "${GREEN}  Health:     http://localhost:${PORT:-8080}/health${NC}"
echo -e "${GREEN}  Diagnostic: http://localhost:${PORT:-8080}/api/diagnostic${NC}"
echo -e "${GREEN}  Status:     http://localhost:${PORT:-8080}/system/status${NC}"
echo ""

exec $PY main.py
