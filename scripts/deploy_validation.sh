#!/bin/bash
set -e

echo "======================================================================"
echo "🚀 NAYA SUPREME V19 - DEPLOYMENT VALIDATION PIPELINE"
echo "======================================================================"

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Fonction de validation
validate_deployment() {
    local env=$1
    local test_command=$2
    
    echo -e "\n${YELLOW}🔍 Validating ${env} deployment...${NC}"
    
    if eval "$test_command"; then
        echo -e "${GREEN}✅ ${env} deployment validated${NC}"
        return 0
    else
        echo -e "${RED}❌ ${env} deployment FAILED${NC}"
        return 1
    fi
}

# 1. VALIDATION LOCAL
echo -e "\n${YELLOW}📍 PHASE 1: LOCAL DEPLOYMENT${NC}"
validate_deployment "LOCAL" "python scripts/validate_system.py"

# 2. VALIDATION DOCKER
echo -e "\n${YELLOW}🐳 PHASE 2: DOCKER DEPLOYMENT${NC}"
echo "Building Docker image..."
docker build -t naya-supreme:v19 . || {
    echo -e "${RED}❌ Docker build failed${NC}"
    exit 1
}

echo "Running Docker container..."
docker run -d --name naya-v19-test -p 8000:8000 naya-supreme:v19 || {
    echo -e "${RED}❌ Docker run failed${NC}"
    exit 1
}

sleep 10

validate_deployment "DOCKER" "curl -f http://localhost:8000/health" || {
    docker logs naya-v19-test
    docker stop naya-v19-test
    docker rm naya-v19-test
    exit 1
}

docker stop naya-v19-test
docker rm naya-v19-test

# 3. VALIDATION TESTS
echo -e "\n${YELLOW}🧪 PHASE 3: COMPREHENSIVE TEST SUITE${NC}"
validate_deployment "TESTS" "pytest tests/ --ignore=tests/test_production.py --ignore=tests/test_comprehensive.py -v"

# 4. PRE-DEPLOY GATE
echo -e "\n${YELLOW}🚪 PHASE 4: PRE-DEPLOY GATE${NC}"
validate_deployment "GATE" "pytest tests/test_pre_deploy_gate.py -v"

echo -e "\n${GREEN}======================================================================"
echo "🎉 ALL VALIDATIONS PASSED - READY FOR PRODUCTION DEPLOYMENT"
echo "======================================================================${NC}"

echo -e "\n${YELLOW}Next steps:${NC}"
echo "  1. Deploy to Railway: railway up"
echo "  2. Deploy to Cloud Run: gcloud run deploy naya-supreme --source ."
echo "  3. Monitor: scripts/monitor_deployment.sh"

exit 0
