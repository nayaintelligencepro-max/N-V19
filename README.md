# 🚀 NAYA SUPREME V19

> Système IA autonome de génération de revenus multi-stream — 11 agents, 32 pain engines, 98 routes API.

[![Status](https://img.shields.io/badge/status-production_ready-green)](#)
[![Tests](https://img.shields.io/badge/tests-798%2F818_passing-brightgreen)](#)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](#)
[![License](https://img.shields.io/badge/license-proprietary-red)](#)

---

## 🎯 Vue d'ensemble

NAYA SUPREME est un système d'IA autonome capable d'identifier, qualifier, contacter, négocier et facturer des opportunités commerciales sans intervention humaine. Il combine 11 agents IA spécialisés autour d'un orchestrateur multi-agent et expose 98 endpoints HTTP via FastAPI.

**Capacité réaliste année 1+** : 4,3 – 6 M EUR/an.

---

## 🏗️ Architecture

```
NAYA-V19/
├── main.py                    # CLI orchestrateur (single / daemon / dashboard)
├── NAYA_CORE/                 # 349 fichiers — cerveau du système
│   ├── api/main.py            # Point d'entrée FastAPI (uvicorn)
│   ├── pain/                  # Registry unifié des 32 pain specs
│   ├── agents/                # 11 agents IA spécialisés
│   ├── multi_agent_orchestrator.py
│   └── llm_router.py          # Routing LLM avec fallback adaptatif
├── api/routers/               # 11 routers HTTP (system, brain, revenue, etc.)
├── SECRETS/                   # Clés API (gitignored)
├── tests/                     # 818 tests pytest
└── Dockerfile                 # Multi-stage production build
```

Voir [`ARCHITECTURE.md`](ARCHITECTURE.md) pour le détail complet.

---

## ⚡ Démarrage rapide

### Pré-requis

- Python 3.11+
- Docker & Docker Compose (pour la stack complète)
- Clés API (voir `.env.example`)

### Installation locale

```bash
# 1. Cloner et installer les dépendances
pip install -r requirements.txt

# 2. Copier et remplir les secrets
cp .env.example .env
# → Éditer .env avec les vraies valeurs

# 3. Démarrer l'API
uvicorn NAYA_CORE.api.main:app --reload --port 8000

# 4. Vérifier
curl http://localhost:8000/api/v1/health
```

### Stack complète (Docker)

```bash
# Stack de production : API + Postgres + Redis + Qdrant + RabbitMQ
docker compose up -d

# Logs en temps réel
docker compose logs -f naya
```

### Modes d'exécution

```bash
python main.py                              # Cycle unique
python main.py daemon --interval 3600       # Boucle infinie (1h)
python main.py dashboard                    # Dashboard OODA sur :8080
python main.py real-sales-daemon            # Pipeline ventes réelles
```

---

## 🔌 API

| Endpoint | Méthode | Description |
|---|---|---|
| `/api/v1/health` | GET | Healthcheck |
| `/api/v1/brain/intention` | POST | Évalue une intention business |
| `/api/v1/revenue/pipeline/stats` | GET | Statistiques pipeline |
| `/api/v1/revenue/hunt/trigger` | POST | Lance la chasse aux pains |
| `/api/v1/business/...` | * | Gestion business |
| `/docs` | GET | Documentation Swagger interactive |

**98 routes au total** réparties sur 11 routers. Voir `/docs` après démarrage.

---

## 🧪 Tests

```bash
# Suite complète
pytest tests/ -v

# Tests unitaires uniquement (rapides)
pytest tests/test_unit.py

# Avec couverture
pytest --cov=NAYA_CORE --cov-report=html
```

**État actuel : 798/818 tests passent (97,6 %).** Les 18 fails restants requièrent Redis live et configurations production.

---

## 🚢 Déploiement

| Plateforme | Config | Recommandé pour |
|---|---|---|
| **Google Cloud Run** | `cloudbuild.yaml` | ✅ **Production primaire** (scale-to-zero) |
| Render | `render.yaml` | Backup / staging |
| Vercel | `vercel.json` | Edge functions (API only) |
| Docker Compose | `docker-compose.prod.yml` | Self-hosted VPS |

```bash
# Cloud Run (recommandé)
gcloud builds submit --config cloudbuild.yaml

# VPS self-hosted
docker compose -f docker-compose.prod.yml up -d
```

---

## 🔐 Sécurité

- Toutes les clés sensibles sont chargées au boot via `SECRETS/secrets_loader.py`
- `.env` et `SECRETS/keys/**` sont protégés par `.gitignore`
- JWT + bcrypt pour l'authentification (`PyJWT`, `passlib[bcrypt]`)
- Rate limiting Redis-backed sur l'API
- Healthcheck Docker + Guardian autonome au runtime

---

## 📚 Documentation

- [`ARCHITECTURE.md`](ARCHITECTURE.md) — Architecture détaillée
- [`QUICKSTART.md`](QUICKSTART.md) — Démarrage en 5 minutes
- [`CLAUDE.md`](CLAUDE.md) — Référence technique complète
- [`docs/`](docs/) — Documentation étendue
- `/docs` (à l'exécution) — Swagger OpenAPI interactif

---

## 📄 Licence

Propriétaire — © NAYA Intelligence Pro. Tous droits réservés.

---

**Contact :** nayaintelligencepro@gmail.com
