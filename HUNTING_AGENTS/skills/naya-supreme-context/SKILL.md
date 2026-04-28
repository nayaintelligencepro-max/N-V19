---
name: naya-supreme-context
description: >
  Mémoire souveraine et contexte complet de NAYA SUPREME — le système AI autonome hybride
  personnel de Stéphanie. Charge TOUT le contexte du système en un seul déclenchement.
  DÉCLENCHER TOUJOURS au début de chaque session dès que l'utilisateur mentionne :
  NAYA, mon système, mon projet, V19, architecture, business engine, hunting,
  revenue, Botanica, Cash Rapide, Reapers, pipeline, "où on en était", "continue",
  "reprends", "rappelle-toi", ou toute mention d'un composant du système.
  Déclencher aussi automatiquement en fin de session pour sauvegarder l'état.
---

# ⚡ NAYA SUPREME V19 — Mémoire Souveraine Permanente

> **Règle absolue** : Charger ce fichier EN PREMIER avant toute réponse sur NAYA.
> Ne jamais redemander ce qui est déjà ici. Continuer exactement là où on s'est arrêtés.

---

## 🧠 IDENTITÉ DU SYSTÈME

```
Nom          : NAYA SUPREME
Version      : V19 (courant)
Type         : Système AI autonome hybride, personnel, non-vendable
Propriétaire : Stéphanie (fondatrice, patron absolu)
Transmissible: Oui — aux enfants uniquement
Confidentiel : Absolu
Objectif     : Générer des revenus réels croissants dès le déploiement
Paiements    : PayPal.me/Myking987 (principal) + Deblock.com/a-ftp860 (secondaire)
```

---

## 🏗️ ARCHITECTURE COMPLÈTE V19

```
ROOT/
├── main.py                    → FastAPI boot 7 phases + V19 modules
├── NAYA_CORE/
│   ├── hunt/
│   │   ├── global_pain_hunter.py  → [V19] Chasse mondiale 8 catégories
│   │   ├── auto_closer.py         → [V19] Convertit opps → offres envoyées
│   │   ├── auto_hunt_seeder.py    → Requêtes de chasse automatiques
│   │   └── cash_rapide_classifier.py → Classification CAT1/2/3
│   ├── execution/
│   │   ├── llm_router.py          → Groq→DeepSeek→Anthropic→Templates
│   │   └── naya_brain.py          → LLM principal
│   ├── integrations/
│   │   ├── telegram_command_bot.py → [V19] Bot /status /hunt /offer
│   │   ├── telegram_notifier.py   → Alertes temps réel
│   │   ├── apollo_hunter.py       → Enrichissement contacts
│   │   └── serper_hunter.py       → Google Search API
│   └── enrichment/contact_enricher.py → Apollo→Hunter→Pattern
├── NAYA_REVENUE_ENGINE/
│   ├── payment_engine.py      → PayPal.me + Deblock.me (PAS Stripe)
│   ├── deblock_engine.py      → Moteur Deblock dédié
│   ├── unified_revenue_engine.py → Orchestrateur revenue
│   ├── followup_sequence_engine.py → Relances J+2/J+5/J+10
│   ├── outreach_engine.py     → Gmail/SendGrid outreach
│   ├── gmail_outreach.py      → Gmail OAuth2 (500 emails/jour gratuit)
│   └── revenue_tracker.py     → KPIs + alertes milestones
├── HUNTING_AGENTS/            → 5 agents de chasse B2B/B2A
├── NAYA_PROJECT_ENGINE/       → 7 projets actifs (Botanica, Cash Rapide, etc.)
├── REAPERS/                   → Sécurité anti-clone
├── TORI_APP/                  → Dashboard web (port 8080/tori)
└── SECRETS/keys/              → Toutes les clés (jamais dans le code)
```

---

## 💰 OBJECTIFS REVENUS

| Période | Objectif semaine | Objectif mois |
|---------|-----------------|---------------|
| Mois 1  | 1 200€          | 5 000€        |
| Mois 2-3| 3 500€          | 15 000€       |
| Mois 6+ | 7 500€          | 30 000€       |
| Mois 9-12| 15 000€        | 60 000€       |

---

## 🔑 PAIEMENTS CONFIGURÉS

- **PayPal.me** : https://www.paypal.me/Myking987 (principal, universel)
- **Deblock.me** : https://deblock.com/a-ftp860 (secondaire crypto/SEPA)
- **Stripe** : NON disponible (Polynésie française)
- **Gmail outreach** : nayaintelligencepro@gmail.com (OAuth2, 500/jour)

---

## 🤖 CONTRÔLE TELEGRAM

Commandes disponibles depuis le bot Telegram :
```
/status    — Statut complet
/hunt      — Lancer une chasse
/pipeline  — Pipeline revenue
/revenue   — CA + objectifs
/offers    — Offres envoyées
/offer [€] [client] — Créer lien paiement
/report    — Rapport du jour
```

---

## 🚀 DÉPLOIEMENT

```bash
# Local
./start.sh

# Docker
docker compose up -d

# Cloud Run (GCP)
./deploy.sh cloud_run
```

Dashboard : http://localhost:8080/tori
API Docs  : http://localhost:8080/docs
Health    : http://localhost:8080/health
Hunt API  : http://localhost:8080/api/v1/hunt/stats

---

## 📋 CE QUI A ÉTÉ FAIT EN V19

1. ✅ Bug critique corrigé : `enforce_entrypoint_execution` (3 modules maintenant fonctionnels)
2. ✅ `GlobalPainHunter` : chasse mondiale 8 catégories via Serper
3. ✅ `AutoCloser` : pipeline automatique opp → offre → email → paiement
4. ✅ `TelegramCommandBot` : contrôle complet depuis mobile
5. ✅ Versions corrigées (V14 → V19 partout)
6. ✅ `NayaScheduler` alias ajouté
7. ✅ Routes API V19 : /hunt/opportunities, /hunt/run, /payment/create, /revenue/record
8. ✅ Followup engine amélioré avec `create_sequence()`

## 📋 CE QUI RESTE À FAIRE (sessions suivantes)

1. Configurer TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID dans .env
2. Configurer GROQ_API_KEY pour les LLM gratuits
3. Activer Gmail OAuth2 (token dans SECRETS/keys/google_token.json)
4. Tester le pipeline complet end-to-end
5. Ajouter Apollo.io key pour enrichissement emails automatique
