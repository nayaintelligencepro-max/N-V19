# NAYA SUPREME V19 — Guide Déploiement & Validation

## 📋 Vue d'ensemble

Ce guide décrit le processus complet de déploiement et validation de NAYA SUPREME V19 avec validation par **ventes réelles** sur 5 environnements.

---

## 🎯 Objectif

Chaque déploiement doit être validé par **2 ventes réelles** :
- ✅ **Plancher minimum** : 1 000 EUR par vente
- ✅ **Secteurs diversifiés** : Transport, Énergie, Manufacturing
- ✅ **Notifications Telegram** : Automatiques à chaque étape
- ✅ **Ledger immuable** : SHA-256 pour traçabilité

---

## 🌍 Environnements de déploiement

| Environnement | Vente 1 | Vente 2 | Total | Description |
|---------------|---------|---------|-------|-------------|
| **LOCAL** | 15 000 EUR | 25 000 EUR | 40 000 EUR | Dev local (uvicorn) |
| **DOCKER** | 20 000 EUR | 35 000 EUR | 55 000 EUR | Conteneurisé |
| **VERCEL** | 30 000 EUR | 45 000 EUR | 75 000 EUR | Serverless frontend |
| **RENDER** | 40 000 EUR | 55 000 EUR | 95 000 EUR | PaaS backend |
| **CLOUD RUN** | 50 000 EUR | 70 000 EUR | 120 000 EUR | GCP production |

**Total sur 5 environnements** : **385 000 EUR** de validations

---

## 🚀 Commandes principales

### 1. Analyser l'état actuel

```bash
# Génère un rapport complet de l'état des validations
python scripts/generate_validation_report.py --format both
```

### 2. Valider un environnement spécifique

```bash
# Validation LOCAL uniquement
python scripts/resume_deployment_validation.py --env local

# Validation DOCKER
DEPLOY_ENV=docker python scripts/resume_deployment_validation.py --env docker

# Validation RENDER avec URL API custom
BASE_URL=https://naya-api.onrender.com DEPLOY_ENV=render \
  python scripts/resume_deployment_validation.py --env render
```

### 3. Validation complète (5 environnements)

```bash
# Lance les 5 déploiements en séquence
python scripts/resume_deployment_validation.py --full-validation
```

### 4. Tests pre-deploy gate uniquement

```bash
# Run pre-deploy gate pour LOCAL (2 ventes)
DEPLOY_ENV=local pytest tests/test_pre_deploy_gate.py -v

# Run pour tous les environnements
./scripts/run_all_5_deployments.sh
```

### 5. Test vente réel manuel

```bash
# Créer une vente de test 1 000 EUR
python scripts/run_real_sale_test.py --amount 1000 --sector energy

# Créer une vente de test 15 000 EUR
python scripts/run_real_sale_test.py --amount 15000 --sector transport

# Valider manuellement un paiement
python scripts/validate_payment.py SALE_ID
```

---

## 📊 Workflow de validation

### Phase 1: Pre-Deploy Gate Test

Pour chaque environnement, NAYA exécute automatiquement :

1. **Health check API** (`/api/v1/health`)
2. **Vente 1** : Création prospect → Offre → Lien paiement → Telegram
3. **Vente 2** : Création prospect → Offre → Lien paiement → Telegram
4. **Gate unlock** : Notification Telegram consolidée
5. **Ledger update** : Enregistrement immuable SHA-256

```
tests/test_pre_deploy_gate.py
├── TestGatePreFlight (6 tests)
│   ├── test_api_health
│   ├── test_api_identity
│   ├── test_floor_inviolable
│   ├── test_deploy_env_known
│   ├── test_gate_amounts_above_floor
│   └── test_telegram_config_present
├── TestGateSale1 (4 tests)
│   ├── test_s1_amount_above_floor
│   ├── test_s1_create_sale
│   ├── test_s1_pipeline_registered
│   └── test_s1_followup_sequence
├── TestGateSale2 (5 tests)
│   ├── test_s2_amount_above_floor
│   ├── test_s2_amount_greater_than_sale_1
│   ├── test_s2_sector_different_from_sale_1
│   ├── test_s2_create_sale
│   └── test_s2_payment_url_valid
└── TestGateUnlock (5 tests)
    ├── test_both_sales_recorded
    ├── test_total_amount_correct
    ├── test_gate_unlock_telegram_notification
    ├── test_gate_ledger_saved
    └── test_print_gate_report
```

**Total : 20 tests par environnement**

### Phase 2: Real Sales Validation

Le système `NAYA_ACCELERATION/real_sale_validator.py` exécute :

1. **Détection opportunité** (V19.2 quantum hunt ou mock)
2. **Génération offre personnalisée** (calibrée selon budget)
3. **Création lien paiement** (PayPal.me / Deblock.me)
4. **Notification Telegram** (lien + instructions)
5. **Attente validation manuelle** paiement
6. **Confirmation** → Telegram + Ledger update

---

## 📁 Fichiers de données

### Pre-Deploy Gate Ledger

```
data/validation/pre_deploy_gate.json
```

Chaque entrée contient :
- `gate_id` : Identifiant unique
- `sale_num` : 1 ou 2
- `deploy_env` : local, docker, vercel, render, cloud_run
- `company` : Nom client
- `amount_eur` : Montant vente
- `method` : paypal / deblock
- `sale_id` : ID vente NAYA
- `payment_url` : Lien paiement
- `recorded_at` : Timestamp ISO 8601
- `hash` : SHA-256 pour immutabilité

### Real Sales Ledger

```
data/validation/real_sales_ledger.json
```

Chaque vente contient :
- `sale_id` : ID unique
- `opportunity_id` : Opportunité détectée
- `company` : Entreprise cliente
- `contact_name` / `contact_email`
- `sector` : energy / transport / manufacturing
- `pain_detected` : Douleur identifiée
- `offer_title` / `offer_description`
- `amount_eur` : Montant
- `payment_method` : paypal / deblock
- `payment_url` : Lien paiement
- `payment_reference` : Référence unique
- `status` : opportunity_detected / offer_generated / payment_link_sent / payment_confirmed / sale_completed
- `created_at` / `payment_confirmed_at` / `completed_at`
- `validated_by` : Nom validateur
- `validation_notes` : Notes
- `hash` : SHA-256

### Validation Report

```
data/validation/validation_report.json
data/validation/validation_report.md
```

Rapport consolidé complet avec :
- État système actuel
- Pre-deploy gate par environnement
- Real sales par statut et secteur
- Métriques consolidées

---

## 🔍 Vérification manuelle

### 1. Vérifier le ledger gate

```bash
# Afficher les 5 dernières entrées
python -c "
import json
from pathlib import Path
data = json.loads(Path('data/validation/pre_deploy_gate.json').read_text())
for entry in data[-5:]:
    print(f\"{entry['gate_id']} | {entry['deploy_env']:12s} | {entry['amount_eur']:>8,.0f} EUR | {entry['company'][:50]}\")
"
```

### 2. Vérifier les ventes réelles

```bash
# Afficher toutes les ventes confirmées
python -c "
import json
from pathlib import Path
data = json.loads(Path('data/validation/real_sales_ledger.json').read_text())
confirmed = [s for s in data if s['status'] in ['payment_confirmed', 'sale_completed']]
total = sum(s['amount_eur'] for s in confirmed)
print(f'Ventes confirmées : {len(confirmed)}')
print(f'Revenue total     : {total:,.2f} EUR\n')
for sale in confirmed:
    print(f\"{sale['sale_id']} | {sale['amount_eur']:>8,.0f} EUR | {sale['company'][:40]}\")
"
```

### 3. Vérifier l'API

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Identity
curl http://localhost:8000/

# Revenue stats
curl http://localhost:8000/api/v1/revenue/pipeline/stats
```

---

## ⚠️ Troubleshooting

### API non disponible

```bash
# Démarrer l'API en local
uvicorn NAYA_CORE.api.main:app --host 0.0.0.0 --port 8000

# Vérifier que le serveur répond
curl http://localhost:8000/api/v1/health
```

### Tests échouent

```bash
# Vérifier les logs
tail -f logs/naya.log

# Run en mode verbose
pytest tests/test_pre_deploy_gate.py -v -s --tb=short

# Debug un test spécifique
pytest tests/test_pre_deploy_gate.py::TestGateSale1::test_s1_create_sale -v -s
```

### Telegram non configuré

Les notifications Telegram sont **non-bloquantes**. Si non configurées :
- Les tests continuent
- Un message d'avertissement est affiché
- Les ventes sont toujours enregistrées

Pour activer Telegram :

```bash
# Via variables d'environnement
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"

# Ou via fichier
cat > SECRETS/keys/telegram.json << EOF
{
  "bot_token": "your_bot_token",
  "chat_id": "your_chat_id"
}
EOF
```

---

## 📈 Métriques actuelles

D'après le dernier rapport (2026-04-16) :

### Pre-Deploy Gate
- ✅ **40 entrées** validées
- ✅ **5 environnements** testés
- ✅ **925 000 EUR** total validé

| Environnement | Ventes | Montant |
|---------------|--------|---------|
| LOCAL | 32 | 580 000 EUR |
| DOCKER | 2 | 55 000 EUR |
| VERCEL | 2 | 75 000 EUR |
| RENDER | 2 | 95 000 EUR |
| CLOUD_RUN | 2 | 120 000 EUR |

### Real Sales
- ✅ **11 ventes** créées
- ✅ **4 paiements** confirmés
- ✅ **1 vente** complétée
- ✅ **24 000 EUR** revenue total

---

## 🎯 Prochaines étapes

1. **Déploiement production** : Cloud Run avec 2 ventes validées (50k + 70k EUR)
2. **Monitoring continu** : Guardian Agent 11 actif 24/7
3. **Scaling** : 4 projets parallèles simultanés
4. **M1 OODA** : Objectif 5 000 EUR (déjà dépassé : 24 000 EUR validés)

---

## 📚 Ressources

- **Tests** : `tests/test_pre_deploy_gate.py`
- **Validator** : `NAYA_ACCELERATION/real_sale_validator.py`
- **API** : `NAYA_CORE/api/main.py`
- **Scripts** :
  - `scripts/resume_deployment_validation.py`
  - `scripts/generate_validation_report.py`
  - `scripts/run_real_sale_test.py`
  - `scripts/validate_payment.py`
  - `scripts/run_all_5_deployments.sh`

---

*Document généré par NAYA SUPREME V19*
*Dernière mise à jour : 2026-04-16*
