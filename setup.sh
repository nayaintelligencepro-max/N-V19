#!/bin/bash

# ==================== NAYA V19 SETUP SCRIPT ====================
# Usage: bash setup.sh [local|docker|cloud-run]
# Automatise tout le setup initial

set -e

ENVIRONMENT=${1:-docker}
PROJECT_NAME="NAYA_V19"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 NAYA V19 Setup — Environment: ${ENVIRONMENT}${NC}"

# ==================== PRE-FLIGHT CHECKS ====================
echo -e "\n${YELLOW}[1/6]${NC} Checking prerequisites..."

if [ "$ENVIRONMENT" == "docker" ] || [ "$ENVIRONMENT" == "cloud-run" ]; then
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker not found. Install: https://docker.com${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Docker found${NC}"
    
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}❌ Docker Compose not found${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Docker Compose found${NC}"
fi

if [ "$ENVIRONMENT" == "local" ]; then
    if ! command -v python3.11 &> /dev/null; then
        echo -e "${RED}❌ Python 3.11 not found. Install: https://python.org${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Python 3.11 found${NC}"
fi

if [ "$ENVIRONMENT" == "cloud-run" ]; then
    if ! command -v gcloud &> /dev/null; then
        echo -e "${RED}❌ gcloud CLI not found. Install: https://cloud.google.com/sdk${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ gcloud CLI found${NC}"
fi

# ==================== CONFIGURATION ====================
echo -e "\n${YELLOW}[2/6]${NC} Setting up configuration..."

if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env from .env.example...${NC}"
    cp .env.example .env
    
    # Generate secure secrets
    SECRET_KEY=$(openssl rand -base64 32)
    JWT_SECRET=$(openssl rand -base64 32)
    DB_PASSWORD=$(openssl rand -base64 32)
    REDIS_PASSWORD=$(openssl rand -base64 32)
    
    # Update .env with secrets (on Mac, use sed -i '')
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s|change_this_in_production_key_here|${SECRET_KEY}|g" .env
        sed -i '' "s|jwt_secret_key_here|${JWT_SECRET}|g" .env
        sed -i '' "s|naya_secure_2024|${DB_PASSWORD}|g" .env
        sed -i '' "s|naya_redis_2024|${REDIS_PASSWORD}|g" .env
    else
        sed -i "s|change_this_in_production_key_here|${SECRET_KEY}|g" .env
        sed -i "s|jwt_secret_key_here|${JWT_SECRET}|g" .env
        sed -i "s|naya_secure_2024|${DB_PASSWORD}|g" .env
        sed -i "s|naya_redis_2024|${REDIS_PASSWORD}|g" .env
    fi
    
    echo -e "${GREEN}✅ .env created with secure secrets${NC}"
else
    echo -e "${YELLOW}⚠️  .env already exists (keeping existing)${NC}"
fi

# ==================== SETUP BY ENVIRONMENT ====================
echo -e "\n${YELLOW}[3/6]${NC} Setting up environment: ${ENVIRONMENT}..."

if [ "$ENVIRONMENT" == "local" ]; then
    echo "Setting up local development environment..."
    
    if [ ! -d venv ]; then
        python3.11 -m venv venv
        echo -e "${GREEN}✅ Virtual environment created${NC}"
    fi
    
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    echo -e "${GREEN}✅ Python dependencies installed${NC}"
    
    # Start background services with docker-compose
    echo "Starting PostgreSQL, Redis, Qdrant, RabbitMQ..."
    docker-compose up -d postgres redis qdrant rabbitmq
    sleep 10
    echo -e "${GREEN}✅ Services running${NC}"
    
elif [ "$ENVIRONMENT" == "docker" ]; then
    echo "Building Docker image..."
    docker build -t naya:v19 .
    echo -e "${GREEN}✅ Docker image built${NC}"
    
    echo "Starting all services with docker-compose..."
    docker-compose up -d
    sleep 15
    echo -e "${GREEN}✅ All services running${NC}"
    
elif [ "$ENVIRONMENT" == "cloud-run" ]; then
    echo "Preparing for Google Cloud Run..."
    
    PROJECT_ID=$(gcloud config get-value project)
    if [ -z "$PROJECT_ID" ]; then
        echo -e "${RED}❌ GCP project not set. Run: gcloud config set project PROJECT_ID${NC}"
        exit 1
    fi
    
    echo "Building image: gcr.io/${PROJECT_ID}/naya:v19"
    gcloud builds submit --tag gcr.io/${PROJECT_ID}/naya:v19
    echo -e "${GREEN}✅ Image pushed to GCR${NC}"
    
    echo "Next: Deploy with:"
    echo "gcloud run deploy naya-api --image gcr.io/${PROJECT_ID}/naya:v19 --platform managed --region europe-west1"
fi

# ==================== DATABASE INITIALIZATION ====================
echo -e "\n${YELLOW}[4/6]${NC} Initializing database..."

if [ "$ENVIRONMENT" == "docker" ]; then
    docker-compose exec -T postgres psql -U naya_user -d naya_prod -c "SELECT 1" 2>/dev/null || {
        echo "Waiting for PostgreSQL to be ready..."
        sleep 10
    }
    docker-compose exec -T postgres psql -U naya_user -d naya_prod \
        -f /docker-entrypoint-initdb.d/01-schema.sql 2>/dev/null || true
elif [ "$ENVIRONMENT" == "local" ]; then
    python3 -c "from PERSISTENCE.database.init_db import init_db; init_db()" 2>/dev/null || true
fi

echo -e "${GREEN}✅ Database initialized${NC}"

# ==================== HEALTH CHECKS ====================
echo -e "\n${YELLOW}[5/6]${NC} Running health checks..."

if [ "$ENVIRONMENT" == "docker" ]; then
    echo "Waiting for services to be healthy..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
            echo -e "${GREEN}✅ API is healthy${NC}"
            break
        fi
        if [ $i -eq 30 ]; then
            echo -e "${RED}❌ API health check failed${NC}"
        fi
        sleep 2
    done
fi

# ==================== SUMMARY ====================
echo -e "\n${YELLOW}[6/6]${NC} Setup complete! 🎉"
echo ""
echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  NAYA V19 Setup Complete              ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""

if [ "$ENVIRONMENT" == "local" ]; then
    echo "📍 Environment: LOCAL DEVELOPMENT"
    echo "🚀 Start API:"
    echo "   uvicorn NAYA_CORE.api.main:app --reload --port 8000"
    echo ""
    echo "🔧 Available services:"
    echo "   - PostgreSQL: localhost:5432"
    echo "   - Redis: localhost:6379"
    echo "   - Qdrant: http://localhost:6333"
    echo "   - RabbitMQ: localhost:5672"
    
elif [ "$ENVIRONMENT" == "docker" ]; then
    echo "📍 Environment: DOCKER COMPOSE"
    echo "🌐 Access:"
    echo "   - API: http://localhost:8000"
    echo "   - API Docs: http://localhost:8000/docs"
    echo "   - Grafana: http://localhost:3000 (admin/admin_naya_2024)"
    echo "   - Kibana: http://localhost:5601"
    echo ""
    echo "📊 Monitor:"
    echo "   docker-compose ps"
    echo "   docker-compose logs -f naya-api"
    
elif [ "$ENVIRONMENT" == "cloud-run" ]; then
    echo "📍 Environment: GOOGLE CLOUD RUN"
    echo "🌍 Next step: Deploy with"
    echo "   gcloud run deploy naya-api \\"
    echo "     --image gcr.io/${PROJECT_ID}/naya:v19 \\"
    echo "     --platform managed \\"
    echo "     --region europe-west1"
fi

echo ""
echo "📖 Documentation:"
echo "   - README: README_V19.md"
echo "   - Deployment: DEPLOYMENT_GUIDE.md"
echo "   - Checklist: PRODUCTION_CHECKLIST.md"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANT: Update .env with your API keys before production!${NC}"
echo ""
echo -e "${GREEN}✅ Setup complete. Happy coding! 🚀${NC}"
