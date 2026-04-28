# 🚀 LANCEMENT MISSION 10 JOURS — Guide Rapide

## 🎯 Objectif

**10 VENTES RÉELLES EN 10 JOURS → 97 500 EUR**

---

## ⚡ Lancement en 1 Commande

```bash
./scripts/launch_10_day_mission.sh
```

Ce script fait **TOUT automatiquement** :
1. ✅ Vérifie les pré-requis (Python, .env, variables)
2. ✅ Installe les dépendances
3. ✅ Initialise le challenge 10 jours
4. ✅ Démarre le serveur LOCAL
5. ✅ Propose déploiements autres plateformes (optionnel)
6. ✅ Envoie notification Telegram de lancement

---

## 📋 Pré-requis MINIMUM

### 1. Créer .env

```bash
cp NAYA_REAL_SALES/.env.example .env
```

### 2. Configurer variables OBLIGATOIRES

Éditer `.env` et configurer **AU MINIMUM** :

```bash
# Telegram (REQUIS)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_OWNER_CHAT_ID=your_chat_id

# Au moins 1 provider paiement (REQUIS)
# Option 1: PayPal
PAYPAL_CLIENT_ID=your_paypal_id
PAYPAL_CLIENT_SECRET=your_paypal_secret

# Option 2: Stripe
STRIPE_SECRET_KEY=sk_live_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx

# Option 3: Deblock (Polynésie)
DEBLOKME_SECRET_KEY=your_deblock_key
DEBLOKME_WEBHOOK_SECRET=your_webhook_secret
```

### 3. Optionnel mais recommandé (IA autonome)

```bash
# LLM pour IA autonome
GROQ_API_KEY=gsk_xxx  # Gratuit, recommandé
# OU
ANTHROPIC_API_KEY=sk-ant-xxx
# OU
OPENAI_API_KEY=sk-xxx
```

---

## 🚀 Lancement Pas-à-Pas

### Étape 1 : Configurer .env

```bash
cp NAYA_REAL_SALES/.env.example .env
# Éditer .env avec vos clés API
```

### Étape 2 : Lancer la mission

```bash
./scripts/launch_10_day_mission.sh
```

### Étape 3 : Vérifier

```bash
# Health check
curl http://localhost:8000/health

# Status challenge
curl http://localhost:8000/api/v1/challenge/status

# Telegram
/challenge
```

---

## 📊 Monitoring en Temps Réel

### API Endpoints

```bash
# Health
GET http://localhost:8000/health

# Status système
GET http://localhost:8000/

# Challenge status
GET http://localhost:8000/api/v1/challenge/status

# Stats ventes
GET http://localhost:8000/api/v1/sales/stats
```

### Telegram (recommandé)

```
/challenge     → Dashboard temps réel
/status        → État système
/velocity      → Métriques ventes
/ooda          → Prochaine action
```

### Logs

```bash
# Logs serveur
tail -f logs/naya_real_sales_*.log

# Logs mission
tail -f logs/mission_launch_*.log
```

---

## 🎯 Stratégie 10 Jours

| Jour | Target EUR | Focus | Deal Type |
|------|-----------|-------|-----------|
| 1 | 1 500 | Audit Express Quick | audit_express |
| 2 | 2 500 | Formation OT 48h | training |
| 3 | 4 000 | Audit + Conseil | consulting |
| 4 | 6 000 | Formation OT Avancée | training_advanced |
| 5 | 8 000 | Consulting IEC62443 | consulting_iec |
| 6 | 10 000 | Audit NIS2 Compliance | nis2_audit |
| 7 | 12 000 | Contrat IEC62443 Moyen | iec62443_contract |
| 8 | 15 000 | Grand Audit Infrastructure | infrastructure_audit |
| 9 | 17 000 | Contrat Cadre 6 mois | framework_6m |
| 10 | 20 000 | Contrat Cadre 12 mois | framework_12m |

**TOTAL : 97 500 EUR**

---

## 🤖 Système Autonome

Le scheduler exécute **automatiquement** :

- **6h00 UTC** : Briefing matinal + objectif du jour
- **Toutes les 4h** : Scanner marché + créer opportunités
- **Toutes les 2h** : Check progression + ajuster
- **18h00 UTC** : Rapport quotidien

**→ Intervention humaine : 0%**

---

## 🌍 Déploiements Autres Plateformes

Le script propose de déployer sur :
- **DOCKER** (conteneur local)
- **RAILWAY** (recommandé production)
- **VERCEL** (serverless)
- **RENDER** (PaaS)
- **CLOUD RUN** (Google)

Pour déployer manuellement :

```bash
# Docker
./scripts/deploy_all_platforms.sh docker

# Railway (production)
./scripts/deploy_all_platforms.sh railway

# Tous
./scripts/deploy_all_platforms.sh all
```

Guide complet : `DEPLOYMENT_GUIDE_6_PLATFORMS.md`

---

## 🛑 Arrêter la Mission

```bash
# Arrêter le serveur
kill $(cat logs/server.pid)

# Ou
pkill -f "NAYA_REAL_SALES.main"
```

---

## 🧪 Tests Post-Lancement

### 1. Health Check

```bash
curl http://localhost:8000/health
# Expected: {"status": "healthy", "system": "NAYA REAL SALES"}
```

### 2. Challenge Status

```bash
curl http://localhost:8000/api/v1/challenge/status
# Expected: JSON avec current_day, targets, etc.
```

### 3. Créer Vente Test

```bash
curl -X POST http://localhost:8000/api/v1/sales/create \
  -H "Content-Type: application/json" \
  -d '{
    "company": "Test SNCF",
    "sector": "transport",
    "amount_eur": 1500,
    "service_type": "audit_express",
    "payment_provider": "paypal"
  }'
```

### 4. Vérifier Notification Telegram

→ Vous devez recevoir un message sur Telegram

---

## 🔧 Dépannage

### Erreur : "TELEGRAM_BOT_TOKEN manquant"

```bash
# Vérifier .env
cat .env | grep TELEGRAM

# Configurer
echo "TELEGRAM_BOT_TOKEN=your_token" >> .env
echo "TELEGRAM_OWNER_CHAT_ID=your_chat_id" >> .env
```

### Erreur : "Aucun provider paiement"

```bash
# Configurer au moins 1 provider
echo "PAYPAL_CLIENT_ID=your_id" >> .env
echo "PAYPAL_CLIENT_SECRET=your_secret" >> .env
```

### Serveur ne démarre pas

```bash
# Vérifier logs
tail -f logs/naya_real_sales_*.log

# Vérifier port
lsof -i :8000

# Tuer processus bloquant
lsof -ti:8000 | xargs kill -9
```

### Notification Telegram non reçue

```bash
# Tester bot manuellement
curl https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getMe

# Vérifier chat ID
curl https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getUpdates
```

---

## 📈 Progression Attendue

### Jour 1-3 : Deals Faciles (warm up)
- Objectif : 7 500 EUR
- 3 ventes rapides
- Valider workflow

### Jour 4-6 : Deals Moyens (accélération)
- Objectif : 24 000 EUR
- 3 ventes consulting
- Optimiser conversion

### Jour 7-10 : Deals Premium (closing)
- Objectif : 64 000 EUR
- 4 contrats cadre
- Maximiser revenue

---

## 🎉 Post-Challenge

Après 10 jours, le **PostChallengeDecisionEngine** décide **autonomement** :

- **> 100k EUR** → SCALE_AGGRESSIVE (recruter, automatiser)
- **> 80k EUR** → OPTIMIZE_AND_SCALE (A/B testing, upsell)
- **10+ ventes** → FOCUS_PREMIUM_DEALS (CAC40, OIV)
- **< objectif** → PIVOT_STRATEGY (BOTANICA, TINY HOUSE)

---

## 📞 Support

**Logs** : `tail -f logs/*.log`
**Status** : `curl http://localhost:8000/health`
**Telegram** : `/challenge`
**Documentation** : `DEPLOYMENT_REPORT_REAL_SALES.md`

---

## ✅ Checklist Lancement

- [ ] .env créé et configuré
- [ ] Variables Telegram configurées
- [ ] Au moins 1 provider paiement configuré
- [ ] Script lancé : `./scripts/launch_10_day_mission.sh`
- [ ] Health check OK
- [ ] Notification Telegram reçue
- [ ] Challenge status visible
- [ ] Logs serveur OK

---

**🚀 NAYA REAL SALES v19.0.0**
*Mission 10 Jours — Génération Revenue Autonome*
*1 Script — 10 Jours — 97 500 EUR*
