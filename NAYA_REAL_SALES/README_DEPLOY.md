# NAYA REAL SALES — Déploiement Production

## 🎯 Objectif

Système de ventes réelles production-ready qui génère de l'argent réel via :
- **Challenge 10 ventes / 10 jours** (97 500 EUR cible)
- **Ventes autonomes** via scheduler IA
- **Paiements confirmés** (PayPal, Deblock, Stripe)
- **Notifications Telegram** temps réel
- **Décision autonome** post-challenge

---

## 📦 Architecture

```
NAYA_REAL_SALES/
├── main.py                         # Point d'entrée FastAPI
├── api_routes.py                   # Routes /sales et /webhook
├── real_sales_engine.py            # Moteur ventes réelles
├── ten_day_challenge.py            # Challenge 10 jours
├── payment_validator.py            # Validation webhooks paiements
├── autonomous_sales_scheduler.py   # Scheduler autonome
└── data/
    ├── real_sales_ledger.json      # Ledger immuable SHA-256
    └── challenge_progress.json     # Progression challenge
```

**Stack :**
- FastAPI + Uvicorn (API REST)
- AsyncIO (scheduler autonome)
- SQLite (persistance)
- Telegram Bot (notifications)
- Webhooks (PayPal, Deblock, Stripe)

---

## 🚀 Déploiement Railway (Recommandé)

### Pré-requis

```bash
# Installer Railway CLI
npm i -g @railway/cli

# Login
railway login
```

### Déploiement

```bash
# Option 1 : Script automatisé
./scripts/deploy_real_sales.sh railway

# Option 2 : Commandes manuelles
railway up --dockerfile Dockerfile.real_sales
railway logs --follow
```

### Variables d'environnement Railway

Via Dashboard Railway : `Settings > Variables`

**Paiements (REQUIS) :**
```bash
PAYPAL_CLIENT_ID=your_paypal_client_id
PAYPAL_CLIENT_SECRET=your_paypal_client_secret
PAYPALME_USERNAME=nayasupreme
DEBLOKME_SECRET_KEY=your_deblock_secret
STRIPE_SECRET_KEY=sk_live_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
```

**Telegram (REQUIS) :**
```bash
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
TELEGRAM_OWNER_CHAT_ID=123456789
```

**LLM (OPTIONNEL pour IA) :**
```bash
ANTHROPIC_API_KEY=sk-ant-xxx
GROQ_API_KEY=gsk_xxx
OPENAI_API_KEY=sk-xxx
```

---

## 🐳 Déploiement Local Docker

```bash
# 1. Build image
docker build -f Dockerfile.real_sales -t naya-real-sales:latest .

# 2. Run conteneur
docker run -d \
  --name naya-real-sales \
  --restart unless-stopped \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  --env-file .env \
  naya-real-sales:latest

# 3. Vérifier logs
docker logs -f naya-real-sales

# 4. Tester health
curl http://localhost:8000/health
```

---

## 🔧 Configuration Webhooks

### PayPal

1. Aller sur https://developer.paypal.com/dashboard/webhooks
2. Créer un webhook :
   - **URL** : `https://[votre-url]/api/v1/webhook/payment/paypal`
   - **Events** : `PAYMENT.SALE.COMPLETED`
3. Copier le **Webhook ID** et **Secret** → Railway Variables

### Stripe

1. Aller sur https://dashboard.stripe.com/webhooks
2. Add endpoint :
   - **URL** : `https://[votre-url]/api/v1/webhook/payment/stripe`
   - **Events** : `payment_intent.succeeded`
3. Copier **Signing secret** → `STRIPE_WEBHOOK_SECRET`

### Deblock (Polynésie française)

1. Dashboard Deblok.me
2. Webhooks → Ajouter
   - **URL** : `https://[votre-url]/api/v1/webhook/payment/deblock`
3. Copier **Secret** → `DEBLOKME_SECRET_KEY`

---

## 📊 API Endpoints

### Créer une vente

```bash
POST /api/v1/sales/create
Content-Type: application/json

{
  "company": "SNCF Réseau",
  "sector": "transport",
  "amount_eur": 15000,
  "service_type": "iec62443_audit",
  "payment_provider": "stripe",
  "metadata": {
    "signal": "job_offer_rssi_ot"
  }
}
```

**Response :**
```json
{
  "sale_id": "abc123",
  "company": "SNCF Réseau",
  "amount_eur": 15000,
  "payment_status": "pending",
  "payment_url": "https://checkout.stripe.com?sale_id=abc123",
  "message": "Vente créée. Paiement en attente via stripe."
}
```

### Statistiques ventes

```bash
GET /api/v1/sales/stats
```

**Response :**
```json
{
  "total_sales": 12,
  "confirmed_sales": 10,
  "pending_sales": 2,
  "revenue_confirmed_eur": 125000,
  "revenue_pending_eur": 25000,
  "average_deal_eur": 12500
}
```

### Status challenge

```bash
GET /api/v1/challenge/status
```

**Response :**
```json
{
  "status": "active",
  "current_day": 5,
  "current_day_focus": "Deal moyen — Consulting + Formation OT",
  "current_day_target_eur": 8000,
  "confirmed_sales": 5,
  "confirmed_revenue_eur": 35000,
  "total_target_eur": 97500,
  "progress_pct": 35.9,
  "days_remaining": 5,
  "day_target_met": true
}
```

---

## 📱 Commandes Telegram

Une fois le bot configuré :

```
/challenge     → Dashboard temps réel du défi 10 jours
/status        → État global système
/velocity      → Métriques ventes (deals/jour, conversion)
/ooda          → Prochaine action recommandée
/mrr           → MRR actuel + projection
/agents        → État des 11 agents IA
```

---

## 🧪 Tests

```bash
# Tests unitaires
pytest NAYA_REAL_SALES/tests/ -v

# Test API local
curl http://localhost:8000/
curl http://localhost:8000/api/v1/sales/stats
curl http://localhost:8000/api/v1/challenge/status

# Test webhook PayPal (simulation)
curl -X POST http://localhost:8000/api/v1/webhook/payment/paypal \
  -H "Content-Type: application/json" \
  -H "X-Signature: test_signature" \
  -d '{"resource": {"custom_id": "sale_123"}}'
```

---

## 📈 Monitoring

### Logs Railway

```bash
railway logs --follow
```

### Logs Docker local

```bash
docker logs -f naya-real-sales
```

### Métriques temps réel

- **Dashboard** : https://[votre-url]/
- **Health** : https://[votre-url]/health
- **Challenge** : https://[votre-url]/api/v1/challenge/status

---

## 🔒 Sécurité

✅ **Webhooks sécurisés** : HMAC-SHA256 signature validation
✅ **HTTPS only** : Railway/Render forcent HTTPS
✅ **Secrets chiffrés** : Aucun secret dans le code
✅ **Ledger immuable** : SHA-256 hash de chaque vente
✅ **Rate limiting** : Protection contre abus

---

## 🎯 Challenge 10 Jours — Stratégie

| Jour | Target EUR | Focus | Deal Type |
|------|-----------|-------|-----------|
| 1 | 1 500 | Audit Express Quick | audit_express |
| 2 | 3 000 | Audit Flash Transport | audit_flash |
| 3 | 5 000 | Audit IEC62443 Standard | iec62443_audit |
| 4 | 6 000 | Formation OT Sécurité | ot_training |
| 5 | 8 000 | Consulting + Formation | consulting |
| 6 | 10 000 | Audit NIS2 Compliance | nis2_compliance |
| 7 | 12 000 | Contrat IEC62443 Moyen | iec62443_contract |
| 8 | 15 000 | Grand Audit Infrastructure | infrastructure_audit |
| 9 | 17 000 | Contrat Cadre 6 mois | framework_6m |
| 10 | 20 000 | Contrat Cadre 12 mois | framework_12m |

**TOTAL : 97 500 EUR**

---

## 🤖 Système Autonome

Le scheduler exécute automatiquement :

- **6h00 UTC** : Briefing matinal + objectif du jour
- **Toutes les 4h** : Scanner marché + créer opportunités
- **Toutes les 2h** : Check progression + ajuster stratégie
- **18h00 UTC** : Rapport quotidien

**→ Zéro intervention manuelle requise**

---

## 🎉 Post-Challenge

Après les 10 jours, le **PostChallengeDecisionEngine** analyse automatiquement :

- Performance totale (EUR confirmés)
- Secteur dominant
- Taux de conversion
- Time-to-close moyen

Et décide **autonomement** :

- **> 100k EUR** → SCALE_AGGRESSIVE (recruter, automatiser)
- **> 80k EUR** → OPTIMIZE_AND_SCALE (A/B testing, upsell)
- **10+ ventes** → FOCUS_PREMIUM_DEALS (CAC40, OIV)
- **< 50k EUR** → PIVOT_STRATEGY (BOTANICA, TINY HOUSE)

---

## 📞 Support

**Telegram** : `/status` pour état système
**Logs** : `railway logs` ou `docker logs`
**Documentation** : `/docs` (FastAPI Swagger)

---

## ✅ Checklist Déploiement

- [ ] Variables d'environnement configurées (Railway/Render)
- [ ] Webhooks PayPal/Stripe/Deblock configurés
- [ ] Bot Telegram testé (`/challenge`)
- [ ] Health check OK (`/health`)
- [ ] Première vente de test créée
- [ ] Logs temps réel vérifiés
- [ ] Challenge actif (jour 1/10)

---

**🚀 NAYA REAL SALES v19.0.0 — Production Ready**
