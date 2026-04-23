# 🔥 NAYA SUPREME V19 — Autonomous Revenue Intelligence System

**Version:** 19.0.0  
**Status:** Production Ready  
**Propriétaire:** Stéphanie MAMA  
**Territoire:** Polynésie française → Global  

---

## 🎯 Qu'est-ce que NAYA V19?

NAYA est un **système autonome hybride** qui détecte automatiquement des opportunités commerciales discrètes sur les marchés globaux et génère des revenus réels (minimum 1 000 EUR par deal).

### Capacités Principales
✅ **Multi-canal outreach** (Email, LinkedIn, WhatsApp, Telegram)  
✅ **Enrichissement prospect** automatisé (Apollo, Hunter, Serper)  
✅ **Génération d'offres** personnalisées par IA  
✅ **Scoring & qualification** intelligent  
✅ **Multi-streams de revenue** (Stripe, Lightning, PayPal, subscriptions)  
✅ **Auto-learning & feedback loops** (vector memory + RAG)  
✅ **Self-healing infrastructure** (99.9% uptime)  
✅ **Monitoring & alerts** complets (Prometheus, Grafana, Kibana)  

---

## 📊 Architecture V19

```
┌─────────────────────────────────────────────────┐
│         NAYA CORE (11 Agents Autonomes)         │
│  Pain Hunter | Researcher | Offer Writer | ... │
└─────────────────────┬───────────────────────────┘
                      │
    ┌─────────────────┼─────────────────┐
    │                 │                 │
┌───▼──────┐    ┌────▼──────┐    ┌───▼─────┐
│ Data     │    │ Decision  │    │Revenue  │
│ Engines  │    │ Kernel    │    │Engines  │
├──────────┤    ├───────────┤    ├─────────┤
│•Enriched │    │•Scoring   │    │•Stripe  │
│•Vector DB│    │•Analytics │    │•Crypto  │
│•Cache    │    │•ML Models │    │•PayPal  │
└──────────┘    └───────────┘    └─────────┘
                      │
┌─────────────────────▼─────────────────────┐
│     Infrastructure Layer                  │
│ PostgreSQL|Redis|Qdrant|RabbitMQ|Monitors│
└──────────────────────────────────────────┘
```

---

## 🚀 Démarrage Rapide

### Prérequis
- Docker & Docker Compose
- Python 3.11+ (pour mode local)
- 8GB RAM minimum (12GB recommandé)
- 10GB disk space

### 1️⃣ Déploiement 60 secondes (Docker)
```bash
git clone <votre-repo>
cd NAYA_V19

# Copier config
cp .env.example .env
# ⚠️ Éditer .env avec vos clés API (Serper, Apollo, etc.)

# Lancer
docker-compose up -d

# Vérifier
docker-compose ps
curl http://localhost:8000/api/v1/health
```

**Accès:**
- API: `http://localhost:8000`
- Docs: `http://localhost:8000/docs`
- Grafana: `http://localhost:3000` (admin/admin_naya_2024)
- Kibana: `http://localhost:5601`

### 2️⃣ Mode Développement (Local)
```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Démarrer services (docker-compose up en arrière-plan)
docker-compose up -d

# Lancer API en mode live-reload
uvicorn NAYA_CORE.api.main:app --reload --port 8000
```

### 3️⃣ Déploiement Cloud Run (Google Cloud)
```bash
gcloud run deploy naya-api \
  --image gcr.io/YOUR_PROJECT/naya:v19 \
  --platform managed \
  --region europe-west1 \
  --memory 2Gi \
  --cpu 2
```

---

## 🔑 Configuration Essentielle

### Variables Critiques (.env)
```bash
# ===== CREDENTIALS =====
SECRET_KEY=votre_secret_key_tres_securise
JWT_SECRET=votre_jwt_secret
ENCRYPTION_KEY=votre_encryption_key

# ===== DATABASE =====
DB_HOST=postgres
DB_PASSWORD=votre_db_password

# ===== REDIS =====
REDIS_PASSWORD=votre_redis_password

# ===== EXTERNAL APIs (voir .env.example pour tous) =====
SERPER_API_KEY=your_serper_key
APOLLO_API_KEY=your_apollo_key
HUNTER_API_KEY=your_hunter_key
SENDGRID_API_KEY=your_sendgrid_key

# ===== PAYMENT =====
STRIPE_API_KEY=sk_live_your_key
ALBY_API_KEY=your_alby_key
```

**⚠️ Jamais commiter .env en version control!**

---

## 📦 Structure du Projet

```
NAYA_V19/
├── NAYA_CORE/                    # Coeur du système
│   ├── core/                     # Decision kernel
│   ├── economic/                 # Revenue engines (Lightning, Subscription)
│   ├── evolution/                # Feedback loops & learning
│   ├── memory/                   # Redis cache + Vector DB (Qdrant)
│   ├── resilience/               # Self-healing engine
│   ├── api/                      # FastAPI endpoints
│   └── orchestration/            # Celery tasks
├── NAYA_DASHBOARD/               # Web UI (React/Next.js)
├── NAYA_INTERFACE/               # API gateways & security
├── NAYA_ORCHESTRATION/           # Distributed task scheduling
├── NAYA_REVENUE_ENGINE/          # Payment processing
├── PERSISTENCE/                  # Database migrations & schema
├── HUNTING_AGENTS/               # Pain detection agents
├── docker-compose.yml            # Multi-container setup
├── Dockerfile                    # Production image
├── requirements.txt              # Python dependencies
└── DEPLOYMENT_GUIDE.md           # Setup instructions
```

---

## 💰 Revenue Streams Actifs

| Stream | Ticket Min | Ticket Max | Status |
|--------|-----------|-----------|--------|
| Stripe (Credit Card) | 1K EUR | Illimité | ✅ Actif |
| Lightning Network (Crypto) | 1K EUR | Illimité | ✅ Actif |
| Subscriptions (Monthly) | 500 EUR | 50K+ EUR | ✅ Actif |
| PayPal / Deblok | 1K EUR | Illimité | ✅ Actif |

---

## 🤖 11 Agents IA Autonomes

1. **Pain Hunter Agent** - Détecte douleurs solvables sur les marchés
2. **Researcher Agent** - Enrichit prospects (emails, LinkedIn, metadata)
3. **Offer Writer Agent** - Génère offres personnalisées par IA
4. **Outreach Agent** - Exécute séquences multi-touch (7 touchdowns)
5. **Decision Maker Agent** - Évalue probabilité de conversion
6. **Negotiation Agent** - Gère contre-offres et deals
7. **Closing Agent** - Finalise contrats et paiements
8. **Self-Healing Agent** - Répare erreurs automatiquement
9. **Analytics Agent** - Produit rapports & dashboards
10. **Learning Agent** - Améliore en continu via feedback
11. **Evolution Agent** - Adapte stratégie basée sur données

---

## 📊 Monitoring & Observability

### Dashboards Inclus
- **Prometheus** (port 9090) - Métriques brutes
- **Grafana** (port 3000) - Dashboards visuels
- **Kibana** (port 5601) - Log analysis
- **API Docs** (port 8000/docs) - Swagger interactif

### Métriques Clés Trackées
- Request latency (p50, p95, p99)
- Error rate & types
- Database query performance
- Cache hit/miss ratio
- Revenue by channel
- Payment success rate

---

## 🧪 Tests & Quality

```bash
# Lancer tests
pytest tests/

# Coverage report
pytest --cov=NAYA_CORE tests/

# Code quality
ruff check .
black --check .

# Load testing (optionnel)
k6 run load_tests/api_load.js
```

---

## 🔒 Sécurité

- ✅ JWT authentication avec expiration
- ✅ RBAC (Role-Based Access Control)
- ✅ Encryption at transit (HTTPS)
- ✅ Encryption at rest (optionnel)
- ✅ Rate limiting par IP & user
- ✅ SQL injection prevention
- ✅ XSS protection
- ✅ CSRF tokens
- ✅ CORS whitelisting
- ✅ Audit logging

**Vérifier:** `PRODUCTION_CHECKLIST.md` avant déploiement

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| `DEPLOYMENT_GUIDE.md` | Setup local/Docker/Cloud |
| `PRODUCTION_CHECKLIST.md` | Pre-launch verification |
| `.env.example` | All configuration options |
| `CLAUDE.md` | System architecture |
| `API documentation` | `http://localhost:8000/docs` |

---

## 🆘 Troubleshooting

### API ne démarre pas
```bash
docker-compose logs naya-api
# Vérifier .env variables
# Vérifier DB connection
```

### Database connection error
```bash
docker-compose exec postgres psql -U naya_user -d naya_prod -c "SELECT 1"
```

### Cache/Redis issues
```bash
docker-compose exec redis redis-cli -a $REDIS_PASSWORD ping
```

### Memory leak detection
```bash
docker stats
# Monitor container memory
```

### Performance bottleneck
```bash
# Voir Grafana dashboard
# Check slow query log (PostgreSQL)
# Verify cache hit rate
```

---

## 🚀 Déploiement Production

### 1. Checklist Security
```bash
✅ All secrets in .env (not in git)
✅ SSL/TLS certificates obtained
✅ Database backups automated
✅ Monitoring alerts configured
✅ Health checks passing
```

### 2. Deploy
```bash
# Docker Compose (VPS)
docker-compose -f docker-compose.yml up -d

# Cloud Run (Google Cloud)
gcloud run deploy naya-api --image gcr.io/PROJECT/naya:v19

# Kubernetes (Enterprise)
kubectl apply -f k8s/
```

### 3. Post-Launch
```bash
# Monitor metrics (first hour)
# Watch error logs
# Verify payment processing
# Test critical workflows
```

**Voir:** `DEPLOYMENT_GUIDE.md` pour détails complets

---

## 📈 Métriques de Succès

| KPI | Target | Current |
|-----|--------|---------|
| System Uptime | 99.9% | - |
| API Response (p95) | < 200ms | - |
| Cache Hit Rate | > 80% | - |
| Payment Success Rate | > 99.5% | - |
| Deal Close Rate | > 25% | - |
| MRR (Monthly Recurring) | > 50K EUR | - |

---

## 🔄 Support & Maintenance

- **Critical Issues:** support@nayaintelligence.com
- **Status Page:** https://status.nayaintelligence.com
- **Documentation:** https://docs.nayaintelligence.com
- **Slack Channel:** #naya-support

---

## 📝 License & Ownership

**NAYA SUPREME V19** est un actif propriétaire et non-vendable.  
Transmissible aux enfants/héritiers légaux uniquement.  
Propriétaire: Stéphanie MAMA  
Territoire: Polynésie française  

---

## 🔮 Roadmap

### V19.1 (Q2 2024)
- [ ] Whatsapp Business API integration
- [ ] Video prospecting (Loom automation)
- [ ] Advanced NLP sentiment analysis
- [ ] Predictive deal forecasting

### V19.2 (Q3 2024)
- [ ] Kubernetes auto-scaling
- [ ] Blockchain payment integration
- [ ] Multi-language support (5+ languages)
- [ ] Advanced fraud detection

### V20 (Q4 2024)
- [ ] Full autonomous operation
- [ ] Distributed agents (edge computing)
- [ ] Real-time market intelligence
- [ ] Sovereign AI core

---

**Status:** ✅ PRODUCTION READY  
**Version:** 19.0.0  
**Last Updated:** April 2024  
**Next Review:** Q2 2024  
