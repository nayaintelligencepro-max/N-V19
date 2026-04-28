# 🔐 SECRETS — Gestion des Clés API & Tokens NAYA SUPREME

> ⚠️ CE DOSSIER EST EXCLU DU GIT — Ne jamais commiter tes fichiers JSON de clés.

---

## Où mettre tes fichiers JSON

```
SECRETS/
│
├── service_accounts/
│   └── 👉 google_service_account.json       ← ton fichier GCP Service Account
│
└── keys/
    ├── google/
    │   ├── 👉 google_oauth2.json             ← ton OAuth 2.0
    │   └── 👉 google_token.json              ← ton token Google
    │
    ├── ai/
    │   ├── 👉 anthropic.json                 ← ta clé API Anthropic
    │   └── 👉 openai.json                    ← ta clé API OpenAI
    │
    ├── social_media/
    │   ├── 👉 meta.json                      ← Facebook / Instagram / Threads / WhatsApp
    │   └── 👉 tiktok_business.json           ← TikTok Business + nom de compte
    │
    ├── messaging/
    │   └── 👉 telegram.json                  ← token bot + chatbot
    │
    ├── ecommerce/
    │   ├── 👉 shopify.json                   ← token + nom de boutique
    │   └── 👉 notion.json                    ← token Notion
    │
    ├── payment/
    │   └── 👉 paypal.json                    ← credentials PayPal
    │
    └── domains/
        └── 👉 cheapname.json                 ← tes 3 noms de domaine + credentials
```

---

## Structure

```
SECRETS/
├── README.md               ← ce fichier (le seul commitable)
├── .gitkeep                ← garde le dossier dans git (vide)
├── keys/
│   ├── llm.env             ← Clés LLM (Anthropic, OpenAI, Mistral...)
│   ├── payments.env        ← Clés paiement (Stripe, Revolut, PayPal)
│   ├── notifications.env   ← Tokens (Telegram, Twilio, Slack, SendGrid)
│   ├── market_data.env     ← APIs données marché (Apollo, Hunter, Clearbit...)
│   ├── automation.env      ← Outils auto (n8n, Make, Zapier)
│   ├── cloud.env           ← GCP / Cloud Run credentials
│   ├── voice.env           ← ElevenLabs, Whisper
│   └── database.env        ← URLs DB (PostgreSQL, Redis)
└── service_accounts/
    └── gcp-service-account.json   ← Fichier GCP (NE PAS COMMITER)
```

---

## Comment utiliser

### Option 1 — Charger un fichier `.env` spécifique
```bash
export $(cat SECRETS/keys/llm.env | xargs)
```

### Option 2 — Charger tous les secrets d'un coup
```bash
for f in SECRETS/keys/*.env; do export $(cat $f | xargs); done
```

### Option 3 — Via Python (automatique au boot)
Le fichier `SECRETS/secrets_loader.py` charge tout automatiquement.

---

## Règle de sécurité
- ✅ Commiter : `README.md`, `.gitkeep`, `secrets_loader.py`, `*.env.example`
- ❌ Ne jamais commiter : `*.env` (avec vraies valeurs), `*.json` (service accounts)
