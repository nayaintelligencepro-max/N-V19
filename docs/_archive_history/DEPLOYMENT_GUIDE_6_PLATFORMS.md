# NAYA REAL SALES — Guide Déploiement 6 Plateformes

## 🎯 Objectif

Déployer le système NAYA REAL SALES sur **LES 6 PLATEFORMES** :
1. **LOCAL** — Développement local
2. **DOCKER** — Conteneur Docker local
3. **VERCEL** — Serverless Vercel
4. **RENDER** — PaaS Render.com
5. **CLOUD RUN** — Google Cloud Run
6. **RAILWAY** — Railway.app

---

## 🚀 Déploiement Rapide (Toutes Plateformes)

```bash
# Déployer sur TOUTES les plateformes
./scripts/deploy_all_platforms.sh all

# Déployer sur UNE plateforme spécifique
./scripts/deploy_all_platforms.sh local
./scripts/deploy_all_platforms.sh docker
./scripts/deploy_all_platforms.sh vercel
./scripts/deploy_all_platforms.sh render
./scripts/deploy_all_platforms.sh cloud_run
./scripts/deploy_all_platforms.sh railway
```

---

## 1️⃣ DÉPLOIEMENT LOCAL

### Configuration

```bash
# Copier .env.example vers .env
cp NAYA_REAL_SALES/.env.example .env

# Éditer .env et configurer AU MINIMUM :
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_OWNER_CHAT_ID=your_chat_id
PAYPAL_CLIENT_ID=your_paypal_id  # ou Stripe/Deblock
```

### Déploiement

```bash
# Option 1 : Script automatique
./scripts/deploy_all_platforms.sh local

# Option 2 : Manuel
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m NAYA_REAL_SALES.main
```

### Vérification

```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/challenge/status
```

### Logs

```bash
tail -f logs/deployments/local_*.log
```

---

## 2️⃣ DÉPLOIEMENT DOCKER

### Pré-requis

```bash
# Installer Docker
https://docs.docker.com/get-docker/

# Vérifier installation
docker --version
```

### Configuration

```bash
# Créer .env avec vos clés API
cp NAYA_REAL_SALES/.env.example .env
# Éditer .env
```

### Déploiement

```bash
# Option 1 : Script automatique
./scripts/deploy_all_platforms.sh docker

# Option 2 : Manuel
docker build -f Dockerfile.real_sales -t naya-real-sales:latest .
docker run -d \
  --name naya-real-sales \
  --restart unless-stopped \
  -p 8001:8000 \
  -v $(pwd)/data:/app/data \
  --env-file .env \
  naya-real-sales:latest
```

### Vérification

```bash
curl http://localhost:8001/health
docker logs -f naya-real-sales
```

### Gestion

```bash
# Arrêter
docker stop naya-real-sales

# Redémarrer
docker start naya-real-sales

# Supprimer
docker rm -f naya-real-sales

# Rebuild
docker build -f Dockerfile.real_sales -t naya-real-sales:latest .
```

---

## 3️⃣ DÉPLOIEMENT VERCEL

### Pré-requis

```bash
# Installer Vercel CLI
npm install -g vercel

# Login
vercel login
```

### Configuration

**Fichier :** `vercel.real_sales.json` (déjà créé)

### Variables d'environnement

Via Dashboard Vercel : https://vercel.com/dashboard

**Settings > Environment Variables** :

```
TELEGRAM_BOT_TOKEN=xxx
TELEGRAM_OWNER_CHAT_ID=xxx
PAYPAL_CLIENT_ID=xxx
PAYPAL_CLIENT_SECRET=xxx
STRIPE_SECRET_KEY=xxx
STRIPE_WEBHOOK_SECRET=xxx
ANTHROPIC_API_KEY=xxx
GROQ_API_KEY=xxx
```

### Déploiement

```bash
# Option 1 : Script automatique
./scripts/deploy_all_platforms.sh vercel

# Option 2 : Manuel
vercel --prod
```

### Vérification

```bash
# URL affichée après déploiement
https://naya-real-sales-api.vercel.app/health
```

### Logs

```bash
vercel logs
```

---

## 4️⃣ DÉPLOIEMENT RENDER

### Pré-requis

- Compte Render.com : https://dashboard.render.com
- Repo GitHub public ou privé connecté

### Configuration

**Fichier :** `render.real_sales.yaml` (déjà créé)

### Déploiement

1. **Push code vers GitHub**

```bash
git add -A
git commit -m "deploy: NAYA REAL SALES"
git push origin main
```

2. **Dashboard Render**

   - Aller sur https://dashboard.render.com
   - **New** > **Blueprint**
   - Connecter repo GitHub
   - Sélectionner `render.real_sales.yaml`
   - Cliquer **Apply**

3. **Configurer Secrets**

   Dans Render Dashboard > Service > Environment :

```
TELEGRAM_BOT_TOKEN=xxx
TELEGRAM_OWNER_CHAT_ID=xxx
PAYPAL_CLIENT_ID=xxx
STRIPE_SECRET_KEY=xxx
ANTHROPIC_API_KEY=xxx
```

### Vérification

```bash
# URL fournie par Render
https://naya-real-sales-api.onrender.com/health
```

### Logs

Dashboard Render > Logs (temps réel)

---

## 5️⃣ DÉPLOIEMENT CLOUD RUN (Google Cloud)

### Pré-requis

```bash
# Installer Google Cloud SDK
https://cloud.google.com/sdk/docs/install

# Login
gcloud auth login

# Configurer projet
gcloud config set project YOUR_PROJECT_ID

# Activer APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

### Configuration Secrets

```bash
# Créer secrets dans Secret Manager
echo -n "your_telegram_token" | gcloud secrets create telegram-bot-token --data-file=-
echo -n "your_chat_id" | gcloud secrets create telegram-chat-id --data-file=-
echo -n "your_paypal_id" | gcloud secrets create paypal-client-id --data-file=-
echo -n "your_paypal_secret" | gcloud secrets create paypal-client-secret --data-file=-
echo -n "your_stripe_key" | gcloud secrets create stripe-secret-key --data-file=-
echo -n "your_stripe_webhook" | gcloud secrets create stripe-webhook-secret --data-file=-
echo -n "your_deblock_key" | gcloud secrets create deblokme-secret-key --data-file=-
echo -n "your_anthropic_key" | gcloud secrets create anthropic-api-key --data-file=-
echo -n "your_groq_key" | gcloud secrets create groq-api-key --data-file=-
```

### Déploiement

```bash
# Option 1 : Script automatique
./scripts/deploy_all_platforms.sh cloud_run

# Option 2 : Manuel
gcloud builds submit --config=cloudbuild.real_sales.yaml
```

### Vérification

```bash
# Récupérer URL
gcloud run services describe naya-real-sales \
  --region=europe-west1 \
  --format='value(status.url)'

# Test
curl https://naya-real-sales-xxx.run.app/health
```

### Logs

```bash
gcloud run logs read naya-real-sales --region=europe-west1 --limit=100
```

### Gestion

```bash
# Lister services
gcloud run services list

# Mettre à jour
gcloud builds submit --config=cloudbuild.real_sales.yaml

# Supprimer
gcloud run services delete naya-real-sales --region=europe-west1
```

---

## 6️⃣ DÉPLOIEMENT RAILWAY

### Pré-requis

```bash
# Installer Railway CLI
npm install -g @railway/cli

# Login
railway login
```

### Configuration

**Fichier :** `railway.real_sales.toml` (déjà créé)

### Déploiement

```bash
# Option 1 : Script automatique
./scripts/deploy_all_platforms.sh railway

# Option 2 : Manuel
railway up --dockerfile Dockerfile.real_sales
```

### Variables d'environnement

Via Dashboard Railway : https://railway.app/dashboard

**Settings > Variables** :

```
TELEGRAM_BOT_TOKEN=xxx
TELEGRAM_OWNER_CHAT_ID=xxx
PAYPAL_CLIENT_ID=xxx
PAYPAL_CLIENT_SECRET=xxx
PAYPALME_USERNAME=xxx
STRIPE_SECRET_KEY=xxx
STRIPE_WEBHOOK_SECRET=xxx
DEBLOKME_SECRET_KEY=xxx
ANTHROPIC_API_KEY=xxx
GROQ_API_KEY=xxx
```

### Vérification

```bash
# URL fournie par Railway
railway domain
curl https://your-app.up.railway.app/health
```

### Logs

```bash
railway logs --follow
```

---

## 📊 Comparaison Plateformes

| Plateforme | Type | Coût | Setup | Scaling | Recommandé pour |
|------------|------|------|-------|---------|-----------------|
| **LOCAL** | Dev | Gratuit | 1 min | N/A | Développement |
| **DOCKER** | Container | Gratuit | 2 min | Manuel | Dev + Staging |
| **VERCEL** | Serverless | Gratuit→Pro | 5 min | Auto | Frontend + API légère |
| **RENDER** | PaaS | Gratuit→Pro | 10 min | Auto | Production simple |
| **CLOUD RUN** | Container | Pay-as-go | 15 min | Auto | Production scalable |
| **RAILWAY** | PaaS | Gratuit→Pro | 5 min | Auto | **Production recommandé** |

---

## 🔐 Variables d'Environnement Requises

### Minimum absolu (système opérationnel)

```bash
TELEGRAM_BOT_TOKEN=xxx          # Notifications
TELEGRAM_OWNER_CHAT_ID=xxx      # Votre chat ID

# Au moins 1 provider paiement
PAYPAL_CLIENT_ID=xxx
PAYPAL_CLIENT_SECRET=xxx
# OU
STRIPE_SECRET_KEY=xxx
STRIPE_WEBHOOK_SECRET=xxx
# OU
DEBLOKME_SECRET_KEY=xxx
```

### Recommandé (IA autonome)

```bash
GROQ_API_KEY=xxx               # LLM gratuit (recommandé)
# OU
ANTHROPIC_API_KEY=xxx          # Claude Sonnet
# OU
OPENAI_API_KEY=xxx             # GPT-4o
```

### Optionnel (prospection automatique)

```bash
APOLLO_API_KEY=xxx             # Enrichissement prospects
HUNTER_API_KEY=xxx             # Email finder
SERPER_API_KEY=xxx             # Google search
LINKEDIN_ACCESS_TOKEN=xxx      # LinkedIn Sales Nav
```

---

## 🧪 Tests Post-Déploiement

### Health Check

```bash
curl https://[votre-url]/health
# Expected: {"status": "healthy", "system": "NAYA REAL SALES"}
```

### Status Système

```bash
curl https://[votre-url]/
# Expected: JSON avec "status": "online", "system": "NAYA REAL SALES v19.0.0"
```

### Challenge Status

```bash
curl https://[votre-url]/api/v1/challenge/status
# Expected: JSON avec challenge details
```

### Créer Vente Test

```bash
curl -X POST https://[votre-url]/api/v1/sales/create \
  -H "Content-Type: application/json" \
  -d '{
    "company": "Test Company",
    "sector": "transport",
    "amount_eur": 1500,
    "service_type": "audit_express",
    "payment_provider": "paypal"
  }'
```

---

## 📱 Webhooks Configuration

### PayPal

1. https://developer.paypal.com/dashboard/webhooks
2. Add webhook : `https://[votre-url]/api/v1/webhook/payment/paypal`
3. Events : `PAYMENT.SALE.COMPLETED`
4. Copier Webhook Secret → env var `PAYPAL_WEBHOOK_SECRET`

### Stripe

1. https://dashboard.stripe.com/webhooks
2. Add endpoint : `https://[votre-url]/api/v1/webhook/payment/stripe`
3. Events : `payment_intent.succeeded`
4. Copier Signing secret → env var `STRIPE_WEBHOOK_SECRET`

### Deblock.me

1. Dashboard Deblok.me > Webhooks
2. URL : `https://[votre-url]/api/v1/webhook/payment/deblock`
3. Copier Secret → env var `DEBLOKME_WEBHOOK_SECRET`

---

## 🚨 Dépannage

### Erreur : "Module NAYA_REAL_SALES not found"

```bash
# Vérifier PYTHONPATH
export PYTHONPATH=/app:$PYTHONPATH

# Ou utiliser -m
python -m NAYA_REAL_SALES.main
```

### Erreur : "Telegram notification failed"

```bash
# Vérifier variables
echo $TELEGRAM_BOT_TOKEN
echo $TELEGRAM_OWNER_CHAT_ID

# Tester bot manuellement
curl https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getMe
```

### Erreur : "Payment webhook signature invalid"

```bash
# Vérifier secret
echo $STRIPE_WEBHOOK_SECRET

# Logs détaillés
tail -f logs/naya_real_sales.log | grep webhook
```

### Docker : "Port already in use"

```bash
# Changer port
docker run -p 8002:8000 ...

# Ou tuer processus
lsof -ti:8001 | xargs kill -9
```

---

## 📈 Monitoring

### Logs Centralisés

```bash
# Local/Docker
tail -f logs/deployments/*.log

# Vercel
vercel logs --follow

# Render
Dashboard > Logs

# Cloud Run
gcloud run logs read naya-real-sales --region=europe-west1 --follow

# Railway
railway logs --follow
```

### Métriques

- **Telegram** : `/challenge` pour dashboard temps réel
- **API** : `GET /api/v1/sales/stats`
- **Challenge** : `GET /api/v1/challenge/status`

---

## ✅ Checklist Déploiement

- [ ] Variables d'environnement configurées
- [ ] Webhooks paiements configurés
- [ ] Bot Telegram testé (`/challenge`)
- [ ] Health check OK (`/health`)
- [ ] Première vente test créée
- [ ] Logs temps réel vérifiés
- [ ] Notification Telegram reçue

---

## 📞 Support

**Logs** : `tail -f logs/deployments/*.log`
**Status** : `curl https://[url]/health`
**Telegram** : `/status` ou `/challenge`

---

**🚀 NAYA REAL SALES v19.0.0**
*6 Plateformes — 1 Commande — Production Ready*
