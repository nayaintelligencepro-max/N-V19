# 🔐 NAYA SUPREME V8 — Guide des Clés API

## Étapes simples avant déploiement

1. **Ouvre chaque fichier `.env`** dans ce dossier
2. **Remplace les valeurs** `METS_TA_CLE_ICI` par tes vraies clés
3. **Lance** `./start.sh` — les clés sont chargées automatiquement

---

## Clés prioritaires (minimum pour fonctionner)

### 1. `keys/llm.env` → Cerveau IA
```
ANTHROPIC_API_KEY=sk-ant-api03-...    ← console.anthropic.com
OPENAI_API_KEY=sk-...                  ← platform.openai.com (optionnel)
```

### 2. `keys/notifications.env` → Alertes business Telegram + Email
```
TELEGRAM_BOT_TOKEN=123456:ABC...       ← @BotFather sur Telegram
TELEGRAM_CHAT_ID=-100123456...         ← @userinfobot sur Telegram
SENDGRID_API_KEY=SG.xxx...             ← app.sendgrid.com
EMAIL_FROM=ton@domaine.com             ← ton email d'envoi
EMAIL_FROM_NAME=NAYA SUPREME
```

### 3. `keys/payments.env` → Stripe (liens de paiement automatiques)
```
STRIPE_SECRET_KEY=sk_live_...          ← dashboard.stripe.com/apikeys
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...        ← dashboard.stripe.com/webhooks
```

### 4. `keys/market_data.env` → Prospection B2B
```
APOLLO_API_KEY=xxx...                  ← app.apollo.io/settings/api
HUNTER_IO_API_KEY=xxx...               ← app.hunter.io/api_keys
SERPER_API_KEY=xxx...                  ← serper.dev (Google Search)
```

---

## Clés secondaires (activent des fonctionnalités supplémentaires)

### `keys/social_media/.env` → Publication LinkedIn/Meta
```
LINKEDIN_ACCESS_TOKEN=...              ← LinkedIn Developer Portal
META_ACCESS_TOKEN=...                  ← developers.facebook.com
```

### `keys/ecommerce/.env` → CRM Notion + Boutique Shopify
```
NOTION_TOKEN=secret_...                ← notion.so/profile/integrations
SHOPIFY_ACCESS_TOKEN=shpat_...         ← ton_shop.myshopify.com/admin/apps
```

### `keys/cloud.env` → Google Cloud Run (déploiement cloud)
```
GOOGLE_CLOUD_PROJECT=ton-projet-gcp   ← console.cloud.google.com
GOOGLE_CLOUD_REGION=europe-west1
```

### `keys/voice.env` → Synthèse vocale
```
ELEVENLABS_API_KEY=...                 ← elevenlabs.io
```

---

## Vérifier l'état des clés

```bash
# Via terminal
python3 SECRETS/secrets_loader.py

# Via API (quand le système tourne)
curl http://localhost:8080/secrets/status

# Recharger les secrets sans redémarrer
curl -X POST http://localhost:8080/secrets/reload
```

---

## Règle de sécurité

- ✅ **Commiter** : `README.md`, `README_KEYS.md`, `*.env.template`, `secrets_loader.py`
- ❌ **Ne jamais commiter** : `*.env` avec de vraies valeurs, `*.json` service accounts

## 🔄 DEBOCK ME CONFIGURATION (NEW)

Remplace Revolut Me (qui se retire du marché polynésien)

### Setup:
1. Go to https://debock.me
2. Create your Debock account
3. Get your Debock Me URL (format: https://debock.me/your_username)
4. Add to SECRETS/keys/payment/debock_me.txt

### Environment Variable:
```bash
DEBOCK_ME_URL=https://debock.me/your_username
```

### In system:
- Primary payment method: **PayPal Me** (https://www.paypal.me/Myking987)
- Secondary method: **Debock Me** (your_debock_url)
- Fallback: Bank transfer (configure in SECRETS/keys/bank)

### Fees:
- PayPal Me: 3.49% + €0.35
- Debock Me: ~1-2% (more favorable for Polynesian transactions)

