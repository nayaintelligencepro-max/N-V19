# ⚡ NAYA V19 — Quick Start (5 minutes)

## 🎯 Objectif
Lancer NAYA V19 en production locale via Docker Compose.

---

## 📋 Prérequis
- ✅ Docker + Docker Compose installés
- ✅ 8GB RAM disponible
- ✅ 10GB disk space

---

## 🚀 Setup (3 commandes)

### 1. Clone & Setup
```bash
git clone <votre-repo>
cd NAYA_V19
bash setup.sh docker
```

**Ce que fait `setup.sh`:**
- ✅ Crée `.env` avec secrets auto-générés
- ✅ Build image Docker
- ✅ Lance tous les services (9 containers)
- ✅ Init database
- ✅ Vérifie santé des services

**Durée:** ~2 minutes

### 2. Vérifier
```bash
docker-compose ps
```

**Résultat attendu:**
```
NAME                    STATUS
naya-api                Up (healthy)
naya-postgres           Up (healthy)
naya-redis              Up (healthy)
naya-qdrant             Up (healthy)
naya-rabbitmq           Up (healthy)
naya-prometheus         Up
naya-grafana            Up
naya-elasticsearch      Up
naya-kibana             Up
```

### 3. Accéder
```
🌐 API              http://localhost:8000
📖 Docs             http://localhost:8000/docs
📊 Grafana          http://localhost:3000
📈 Prometheus       http://localhost:9090
📝 Kibana           http://localhost:5601
```

---

## 🔑 Credentials Par Défaut

| Service | User | Password |
|---------|------|----------|
| Grafana | admin | admin_naya_2024 |
| RabbitMQ | guest | guest |
| PostgreSQL | naya_user | *(auto-generated)* |

Voir `.env` pour tous les détails.

---

## ✅ Vérifications Rapides

### Health Check API
```bash
curl -f http://localhost:8000/api/v1/health
# Résultat: {"status":"healthy","uptime":"..."}
```

### Test Base de Données
```bash
docker-compose exec postgres psql -U naya_user -d naya_prod -c "SELECT 1"
# Résultat: ?column?
#     1
```

### Test Cache
```bash
docker-compose exec redis redis-cli -a $(grep REDIS_PASSWORD .env | cut -d= -f2) ping
# Résultat: PONG
```

### Test Message Queue
```bash
docker-compose exec rabbitmq rabbitmq-diagnostics ping
# Résultat: ping succeeded
```

---

## 🧪 Test End-to-End

### 1. Créer un Prospect (API)
```bash
curl -X POST http://localhost:8000/api/v1/prospects \
  -H "Content-Type: application/json" \
  -d '{
    "company": "Acme Corp",
    "contact_email": "cto@acme.com",
    "estimated_budget": 15000,
    "sector": "Manufacturing"
  }'
```

### 2. Voir Dashboards
- Grafana: http://localhost:3000 → "NAYA Overview" dashboard

### 3. Check Logs
```bash
docker-compose logs -f naya-api
```

---

## 🛠️ Commands Utiles

```bash
# Status
docker-compose ps

# Logs
docker-compose logs -f naya-api

# Arrêter
docker-compose down

# Redémarrer service
docker-compose restart naya-api

# Rebuild image
docker-compose build --no-cache

# Clean everything
docker-compose down -v  # ⚠️ Supprime aussi les données!
```

---

## 🌍 Configuration Production

### Avant deployer en PROD:

1. **Générer secrets sécurisés:**
   ```bash
   openssl rand -base64 32  # Pour SECRET_KEY, JWT_SECRET, etc.
   ```

2. **Éditer .env avec:**
   - Vos API keys (Serper, Apollo, Hunter, Sendgrid, etc.)
   - Vos secrets de paiement (Stripe, Alby, etc.)
   - Vos credentials de communication (Telegram, Slack, etc.)

3. **Configurer CORS origins:**
   ```bash
   CORS_ORIGINS=["https://yourdomain.com"]
   ```

4. **Vérifier checklist:**
   ```bash
   cat PRODUCTION_CHECKLIST.md
   ```

---

## 📊 Monitoring

### Grafana Dashboards
1. Aller à http://localhost:3000
2. Login: admin / admin_naya_2024
3. Voir dashboards:
   - **NAYA Overview** - Système global
   - **API Performance** - Latency, throughput
   - **Database** - Queries, connections
   - **Revenue** - Payment streams

### Prometheus Metrics
- http://localhost:9090
- Voir historique metrics (7 jours)

### Logs (Kibana)
- http://localhost:5601
- Créer index pattern: `naya-*`
- Analyser logs en temps réel

---

## 🆘 Troubleshooting

### ❌ "Docker Compose not found"
```bash
# Mac/Linux
brew install docker-compose

# Ou utiliser Docker Desktop (inclus)
```

### ❌ "Port 8000 already in use"
```bash
# Changer port dans docker-compose.yml
# Ou tuer processus:
lsof -i :8000
kill -9 <PID>
```

### ❌ "Database connection refused"
```bash
# Attendre ~30s pour que PostgreSQL démarre
docker-compose logs postgres

# Ou redémarrer service
docker-compose restart postgres
```

### ❌ "Out of disk space"
```bash
# Libérer espace Docker
docker system prune -a --volumes

# Ou supprimer containers
docker-compose down -v
```

---

## 🚀 Prochaines Étapes

1. **Développement Local** → Éditer code dans `NAYA_CORE/`
   - API hot-reload via docker volumes
   - Logs en temps réel

2. **Tester Agents** → Déclencher agents manuellement
   ```bash
   docker-compose exec naya-api python -c "from NAYA_CORE.hunting_agents.pain_hunter import PainHunterAgent; ..."
   ```

3. **Configurer Webhooks** → Ajouter vos API keys à `.env`

4. **Deploy Cloud** → Voir `DEPLOYMENT_GUIDE.md`

5. **Production** → Vérifier `PRODUCTION_CHECKLIST.md`

---

## 📖 Documentation Complète

- **README:** `README_V19.md` - Overview du système
- **Deployment:** `DEPLOYMENT_GUIDE.md` - Local/Docker/Cloud/VPS
- **Checklist:** `PRODUCTION_CHECKLIST.md` - Pre-launch (100+ items)
- **Version:** `VERSION_V19_SUMMARY.md` - Changements V19
- **API Docs:** http://localhost:8000/docs (Swagger interactif)

---

## 💬 Support

- **Issues:** support@nayaintelligence.com
- **Docs:** https://docs.nayaintelligence.com
- **Status:** https://status.nayaintelligence.com

---

**✅ NAYA V19 est maintenant en execution!** 🚀

Vous pouvez:
- ✅ Appeler l'API
- ✅ Voir les dashboards
- ✅ Tester end-to-end
- ✅ Configurer production

**Prochaine étape:** Lire `PRODUCTION_CHECKLIST.md` avant deploiement réel.
