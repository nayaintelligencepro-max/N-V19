#!/bin/bash
#
# NAYA SUPREME V19 — RAILWAY.APP DEPLOYMENT
# One-command deployment to production on Railway
#
# Usage:
#   ./deploy-railway.sh                    # Deploy to production
#   ./deploy-railway.sh staging            # Deploy to staging
#   ./deploy-railway.sh --delete           # Delete deployment
#

set -e

ENVIRONMENT=${1:-production}
RAILWAY_TOKEN=${RAILWAY_TOKEN:-}
RAILWAY_PROJECT_ID=${RAILWAY_PROJECT_ID:-}
RAILWAY_SERVICE_NAME="naya-supreme"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  🚀 NAYA SUPREME V19 — RAILWAY.APP DEPLOYMENT                 ║${NC}"
echo -e "${BLUE}║     Environment: $ENVIRONMENT                                  ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v railway &> /dev/null; then
    echo -e "${RED}❌ Railway CLI not installed${NC}"
    echo "Install: npm install -g @railway/cli"
    exit 1
fi

if [ -z "$RAILWAY_TOKEN" ]; then
    echo -e "${YELLOW}Railway token not found in RAILWAY_TOKEN${NC}"
    echo "Please set: export RAILWAY_TOKEN=<your_token>"
    read -p "Or enter token now (leave blank to use railway login): " RAILWAY_TOKEN
fi

# Login if needed
if [ -z "$RAILWAY_TOKEN" ]; then
    echo -e "${YELLOW}Logging into Railway...${NC}"
    railway login
else
    export RAILWAY_TOKEN=$RAILWAY_TOKEN
fi

# === DEPLOYMENT LOGIC ===

if [ "$ENVIRONMENT" = "--delete" ]; then
    echo -e "${RED}Deleting deployment...${NC}"
    railway service delete $RAILWAY_SERVICE_NAME
    exit 0
fi

# === BUILD & DEPLOY ===

echo ""
echo -e "${YELLOW}Starting deployment...${NC}"

# 1. Build Docker image
echo -e "${YELLOW}1. Building Docker image...${NC}"
docker build -f Dockerfile.optimized -t naya-supreme:latest .
echo -e "${GREEN}✅ Docker image built${NC}"

# 2. Tag image for Railway
echo -e "${YELLOW}2. Tagging image for Railway...${NC}"
docker tag naya-supreme:latest railway-registry.io/naya-supreme:$ENVIRONMENT
echo -e "${GREEN}✅ Image tagged${NC}"

# 3. Create/Update service
echo -e "${YELLOW}3. Initializing Railway service...${NC}"

# Check if service exists
if railway service list | grep -q $RAILWAY_SERVICE_NAME; then
    echo -e "${YELLOW}Service exists, updating...${NC}"
    railway service select $RAILWAY_SERVICE_NAME
else
    echo -e "${YELLOW}Creating new service...${NC}"
    railway service create $RAILWAY_SERVICE_NAME
fi

echo -e "${GREEN}✅ Service ready${NC}"

# 4. Set environment variables
echo -e "${YELLOW}4. Setting environment variables...${NC}"

# Load from .env
if [ -f ".env" ]; then
    while IFS='=' read -r key value; do
        if [[ ! $key =~ ^#.*$ && ! -z $key ]]; then
            # Skip certain sensitive values
            if [[ ! "$key" =~ ^(SECRETS_|ENCRYPTION_KEY|JWT_SECRET|DB_PASSWORD)$ ]]; then
                railway variable set $key "$value" 2>/dev/null || true
            fi
        fi
    done < .env
fi

# Set critical production variables
railway variable set ENVIRONMENT production
railway variable set LOG_LEVEL INFO
railway variable set ENABLE_GUARDIAN true
railway variable set ENABLE_AUTO_LEARNING true

echo -e "${GREEN}✅ Environment variables set${NC}"

# 5. Configure plugin (PostgreSQL + Redis)
echo -e "${YELLOW}5. Configuring database plugins...${NC}"

# PostgreSQL
if ! railway plugin list | grep -q postgresql; then
    railway plugin add postgresql
    echo -e "${GREEN}✅ PostgreSQL plugin added${NC}"
fi

# Redis
if ! railway plugin list | grep -q redis; then
    railway plugin add redis
    echo -e "${GREEN}✅ Redis plugin added${NC}"
fi

# 6. Deploy
echo -e "${YELLOW}6. Deploying to Railway...${NC}"

railway up --force

echo -e "${GREEN}✅ Deployment complete!${NC}"

# 7. Get deployment URL
echo ""
echo -e "${BLUE}Deployment Summary:${NC}"
echo -e "${GREEN}✅ Service: $RAILWAY_SERVICE_NAME${NC}"
echo -e "${GREEN}✅ Environment: $ENVIRONMENT${NC}"
echo -e "${GREEN}✅ Status: Deployed${NC}"

echo ""
echo "Next steps:"
echo "1. railway open (to view dashboard)"
echo "2. railway logs (to see logs)"
echo "3. railway variable get (to view env vars)"
echo ""

# 8. Health check
echo -e "${YELLOW}Waiting for service to be healthy...${NC}"
sleep 5

SERVICE_URL=$(railway variable get RAILWAY_PUBLIC_DOMAIN 2>/dev/null || echo "https://naya-supreme.railway.app")

echo -e "${GREEN}✅ Service available at: $SERVICE_URL${NC}"

# Try health check
for i in {1..10}; do
    if curl -s -f $SERVICE_URL/health > /dev/null; then
        echo -e "${GREEN}✅ Health check PASSED${NC}"
        echo ""
        echo -e "${BLUE}🎉 DEPLOYMENT SUCCESSFUL!${NC}"
        echo "API: $SERVICE_URL"
        echo "Docs: $SERVICE_URL/docs"
        exit 0
    fi
    echo "Waiting for service... ($i/10)"
    sleep 2
done

echo -e "${YELLOW}⚠️  Health check not responding yet${NC}"
echo "Check logs with: railway logs -f"

exit 0
