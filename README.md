# NAYA SUPREME V19 — Autonomous AI Business System

> Systeme IA autonome de generation de revenue multi-stream.
> 11 Agents IA | 29 Modules Revenue | 32 Pain Engines | Pipeline < 4h
>
> **Proprietaire** : Stephanie MAMA | **Territoire** : Polynesie francaise -> Global
> **Actif souverain, non-vendable, transmissible.**

---

## Architecture

```
COUCHE METIER / APPLICATION (racine)       COUCHE NOYAU / INFRASTRUCTURE (NAYA_CORE/)
────────────────────────────────────      ──────────────────────────────────────────
agents/          -> agents metier          NAYA_CORE/agents/      -> protocoles agent de base
api/             -> API FastAPI publique   NAYA_CORE/api/         -> routes internes kernel
core/            -> orchestrateur          NAYA_CORE/core/        -> moteur execution bas niveau
memory/          -> memoire vectorielle    NAYA_CORE/memory/      -> store vectoriel natif
monitoring/      -> dashboard + alertes    NAYA_CORE/monitoring/  -> metriques kernel
workflows/       -> workflows LangGraph   NAYA_CORE/workflows/   -> graphes etat noeuds
```

Voir [`ARCHITECTURE.md`](ARCHITECTURE.md) pour le mapping canonique complet.

## Quickstart

### Pre-requis

- Python 3.11+
- Docker & Docker Compose (pour la stack complete)
- Cles API (voir `.env.example`)

### Installation locale

```bash
# 1. Cloner
git clone https://github.com/nayaintelligencepro-max/N-V19.git
cd N-V19

# 2. Environnement virtuel
python -m venv .venv && source .venv/bin/activate

# 3. Dependances
pip install -r requirements.txt

# 4. Configuration
cp .env.example .env
# Editer .env avec vos cles API

# 5. Lancer
python main.py              # Single cycle
python main.py daemon       # Boucle infinie (1h)
python main.py dashboard    # Dashboard OODA sur :8080
```

### Avec Docker Compose (stack complete)

```bash
cp .env.example .env
# Editer .env avec vos cles API

docker compose up -d        # PostgreSQL, Redis, Qdrant, RabbitMQ, Prometheus, Grafana
docker compose up naya       # Application NAYA
```

### API

```bash
# Demarrer l'API
uvicorn NAYA_CORE.api.main:app --host 0.0.0.0 --port 8000

# Endpoints
GET  /                     # Root info
GET  /api/v1/health        # Health check
GET  /api/v1/modules       # Status modules
GET  /docs                 # OpenAPI Swagger
GET  /redoc                # ReDoc
```

## Commandes CLI

| Commande | Description |
|----------|-------------|
| `python main.py cycle` | Single execution cycle |
| `python main.py daemon` | Boucle infinie (default 1h) |
| `python main.py dashboard` | Dashboard OODA sur :8080 |
| `python main.py status` | Status systeme complet |
| `python main.py pains` | Top 10 douleurs discretes |
| `python main.py briefing` | Briefing quotidien Telegram |
| `python main.py regulatory` | Opportunites reglementaires |
| `python main.py ooda` | OODA Speed Layer test |
| `python main.py score` | Composite Scorer demo |
| `python main.py preflight` | Verification pre-deploiement |

## Les 11 Agents IA

| # | Agent | Fichier | Role |
|---|-------|---------|------|
| 1 | Pain Hunter | `agents/pain_hunter_agent.py` | Scanner marches pour douleurs solvables >= 1000 EUR |
| 2 | Researcher | `agents/researcher_agent.py` | Enrichissement prospects (Apollo, Hunter, Serper) |
| 3 | Offer Writer | `agents/offer_writer_agent.py` | Generation offres personnalisees PDF |
| 4 | Outreach | `agents/outreach_agent.py` | Sequences 7 touches multi-canal 21 jours |
| 5 | Closer | `agents/closer_agent.py` | Closing, objections, negociations |
| 6 | Audit | `agents/audit_agent.py` | Audits IEC 62443 / NIS2 automatises |
| 7 | Content | `agents/content_agent.py` | Contenu B2B recurrent |
| 8 | Contract | `agents/contract_generator_agent.py` | Contrats PDF signables + facturation |
| 9 | Revenue Tracker | `agents/revenue_tracker_agent.py` | Tracking 4 streams revenus temps reel |
| 10 | Pipeline | `agents/parallel_pipeline_agent.py` | 4 slots projets paralleles |
| 11 | Guardian | `agents/guardian_agent.py` | Securite 24/7 + auto-reparation |

## Constitution & Invariants

Le systeme est regi par des invariants fondamentaux definis dans `CONSTITUTION/`:

- **Plancher Premium** : 1 000 EUR minimum par contrat (INVIOLABLE)
- **Non-vendable** : Actif personnel, transmissible aux enfants
- **Zero Waste** : Rien n'est jete, tout est recycle
- **Non-regression** : Aucune evolution ne reduit les capacites
- **Stealth Mode** : Operations furtives par defaut
- **Legal Only** : Uniquement des operations legales

## Streams de Revenus

| Stream | Description | Ticket moyen |
|--------|-------------|--------------|
| Outreach Deals | Prospection -> closing | 1k-20k EUR |
| Audits automatises | IEC 62443 / NIS2 | 5k-20k EUR |
| Contenu B2B recurrent | Articles, whitepapers | 3k-15k EUR/mois |
| SaaS NIS2 Checker | Conformite en ligne | 500-2k EUR/mois |

## Stack Technique

- **Backend** : Python 3.11+ / FastAPI / Uvicorn / Uvloop
- **Agents IA** : LangGraph / CrewAI / Multi-Agent Orchestrator
- **LLM Router** : Groq -> DeepSeek -> Anthropic -> OpenAI -> Templates
- **Base de donnees** : PostgreSQL 15 / SQLAlchemy / Alembic
- **Cache** : Redis 7
- **Vector DB** : Qdrant / ChromaDB / Pinecone
- **Message Broker** : RabbitMQ / Celery
- **Monitoring** : Prometheus / Grafana / Loki / Sentry
- **Deploiement** : Docker / Cloud Run / Render / Vercel / Railway

## Tests

```bash
# Tests smoke
python -m pytest tests/test_smoke.py -v

# Tous les tests
python -m pytest tests/ -v

# Lint
ruff check . --select F821
```

## Deploiement

```bash
# Docker
docker build -t naya-supreme .
docker run -p 8000:8000 --env-file .env naya-supreme

# Cloud Run
gcloud run deploy naya-supreme --source .

# Railway
railway up
```

## Securite

- Toutes les cles API dans `SECRETS/keys/` (jamais dans le code)
- Chiffrement AES-256 des donnees sensibles
- JWT + RBAC pour l'authentification API
- Guardian Agent scan automatique toutes les 6h
- Rate limiting sur toutes les API externes
- Log immuable SHA-256 pour les operations financieres

## Structure des dossiers

```
N-V19/
├── agents/                    # 11 agents IA autonomes
├── api/                       # API FastAPI + routers
├── audit/                     # Moteur audit IEC 62443 / NIS2
├── BUSINESS_ENGINES/          # Moteurs business verticaux
├── CHANNEL_INTELLIGENCE/      # Intelligence canal multi-canal
├── CONSTITUTION/              # Regles souveraines immuables
├── core/                      # Orchestrateur principal
├── EVOLUTION_SYSTEM/          # Auto-evolution + regression guard
├── EXECUTIVE_ARCHITECTURE/    # Architecture executive decisions
├── HUNTING_AGENTS/            # Agents chasseurs autonomes
├── intelligence/              # Scoring, A/B testing, pricing
├── KERNEL/                    # Noyau systeme
├── memory/                    # Memoire vectorielle persistante
├── ML_ENGINE/                 # Modeles ML scoring
├── monitoring/                # Prometheus + Grafana configs
├── NAYA_ACCELERATION/         # BlitzHunter, FlashOffer, InstantCloser
├── NAYA_CLOUD_RUN/            # Configuration Cloud Run
├── NAYA_COMMAND_GATEWAY/      # Gateway commandes Telegram
├── NAYA_CORE/                 # Couche infrastructure kernel
├── NAYA_DASHBOARD/            # Dashboard revenue temps reel
├── NAYA_ORCHESTRATION/        # Orchestrateur multi-agents
├── NAYA_PROJECT_ENGINE/       # Moteur projets business
├── NAYA_REAL_SALES/           # Pipeline ventes reelles
├── NAYA_REVENUE_ENGINE/       # Tracking revenus
├── NAYA_SCHEDULER/            # Jobs autonomes planifies
├── OUTREACH/                  # Sequenceur multi-touch
├── PERSISTENCE/               # SQLAlchemy + migrations
├── PROTOCOLS/                 # Protocoles inter-agents
├── REAPERS/                   # Recuperation leads abandonnes
├── SAAS_NIS2/                 # SaaS NIS2 compliance checker
├── SECRETS/                   # Gestion cles API chiffrees
├── security/                  # Securite + auto-reparation
├── tests/                     # Suite de tests
├── TORI_APP/                  # Application TORI dashboard
├── V20_INTELLIGENCE/          # Intelligence V20 avancee
├── workflows/                 # LangGraph stateful workflows
└── ZERO_WASTE/                # Recyclage zero dechet
```

## Licence

Propriete exclusive de Stephanie MAMA. Non-vendable. Transmissible.
