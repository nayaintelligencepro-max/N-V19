# 🔐 GUIDE COMPLET — Chargement des Clés API NAYA V19

## Vue d'ensemble

Le système NAYA V19 dispose d'un **système de chargement automatique** de toutes les clés API depuis le dossier `SECRETS/keys/`. Ce guide explique comment fonctionne le système et comment l'utiliser.

---

## 🚀 Chargement Automatique au Boot

### Comportement par défaut

**Toutes les clés sont chargées automatiquement** dès que vous importez le module SECRETS :

```python
from SECRETS import load_all_secrets, get_secret

# Les clés sont DÉJÀ chargées automatiquement à ce stade !
# Vous pouvez immédiatement utiliser get_secret()
telegram_token = get_secret("TELEGRAM_BOT_TOKEN")
```

### Points d'entrée automatiques

Le chargement automatique se déclenche dans :

1. **`main.py`** — Entry point principal du système
2. **`NAYA_CORE/api/main.py`** — API FastAPI
3. **`SECRETS/__init__.py`** — Import du module SECRETS
4. Tout script qui fait `from SECRETS import ...`

---

## 📂 Structure des Fichiers de Clés

### Organisation dans SECRETS/keys/

```
SECRETS/keys/
├── naya_raw_dump.env           # Fichier .env consolidé (toutes les clés)
├── ai/
│   └── .env.template           # Template pour clés IA (Anthropic, OpenAI, etc.)
├── google/
│   └── .env.template           # Google OAuth, Service Account
├── messaging/
│   └── .env.template           # Telegram, Twilio, SendGrid
├── payment/
│   ├── .env.template           # Stripe, PayPal
│   └── lien révolut me         # Fichier texte avec URL Revolut
├── social_media/
│   └── .env.template           # TikTok, Instagram, Facebook
├── domains/
│   └── .env.template           # Domaines et emails
└── ecommerce/
    └── .env.template           # Shopify, Notion
```

### Formats supportés

Le système charge **automatiquement** :

1. **Fichiers `.env`** dans `keys/` et sous-dossiers
2. **Fichiers `.env.template`** si `.env` n'existe pas (fallback)
3. **Fichiers JSON** (via mapping défini dans `_JSON_MAP`)
4. **Fichiers `.txt`** : `NOM_CLE.txt` → variable `NOM_CLE`
5. **URLs dans fichiers texte** : détection auto Revolut/PayPal/Deblock

---

## 🔧 Utilisation

### 1. Vérifier les clés chargées

```bash
# Rapport standard
python SECRETS/secrets_loader.py

# Rapport diagnostic complet
python SECRETS/secrets_loader.py --diagnostic
python scripts/check_api_keys.py -d

# Validation stricte (exit 1 si clés manquantes)
python SECRETS/secrets_loader.py --validate
python scripts/check_api_keys.py -v
```

### 2. Utiliser les clés dans le code

```python
from SECRETS import get_secret, is_configured

# Récupérer une clé (avec valeur par défaut)
api_key = get_secret("ANTHROPIC_API_KEY", default="")

# Vérifier si une clé est configurée
if is_configured("TELEGRAM_BOT_TOKEN"):
    # Utiliser Telegram
    pass

# Récupérer le statut complet
from SECRETS import get_status
status = get_status()
print(f"LLM actif: {status['active_llm']}")
print(f"Score: {status['score']}")
```

### 3. Ajouter de nouvelles clés

#### Option A : Fichier .env dans un sous-dossier

```bash
# Créer ou éditer ai/.env
nano SECRETS/keys/ai/.env
```

```env
# Contenu de ai/.env
ANTHROPIC_API_KEY=sk-ant-votre-cle-ici
OPENAI_API_KEY=sk-votre-cle-openai
GROQ_API_KEY=gsk_votre-cle-groq
```

#### Option B : Fichier texte simple

```bash
# Créer un fichier avec le nom de la clé
echo "votre_token_ici" > SECRETS/keys/messaging/TELEGRAM_BOT_TOKEN.txt
```

Le système chargera automatiquement la variable `TELEGRAM_BOT_TOKEN`.

#### Option C : URL de paiement

```bash
# Fichier texte contenant une URL
echo "https://revolut.me/stephanie" > SECRETS/keys/payment/revolut.txt
```

Le système détectera automatiquement que c'est une URL Revolut et chargera `REVOLUT_ME_URL`.

---

## 📊 Clés Critiques

### Liste des clés critiques surveillées

Le système surveille **automatiquement** ces clés :

#### LLM / IA
- `ANTHROPIC_API_KEY`
- `OPENAI_API_KEY`
- `GROK_API_KEY` / `XAI_API_KEY`
- `GROQ_API_KEY`
- `DEEPSEEK_API_KEY`
- `HUGGINGFACE_API_KEY`
- `MISTRAL_API_KEY`

#### Communication
- `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID`
- `SENDGRID_API_KEY` + `EMAIL_FROM`
- `TWILIO_ACCOUNT_SID` + `TWILIO_AUTH_TOKEN`

#### Paiements
- `PAYPAL_ME_URL`
- `REVOLUT_ME_URL`
- `DEBLOCK_ME_URL`
- `STRIPE_API_KEY`
- `PAYPAL_CLIENT_ID`

#### Intégrations Business
- `NOTION_TOKEN`
- `SHOPIFY_ACCESS_TOKEN` + `SHOPIFY_SHOP_NAME`
- `TIKTOK_ACCESS_TOKEN`
- `INSTAGRAM_ID`
- `FACEBOOK_PAGE_ID`
- `WHATSAPP_PHONE` + `WHATSAPP_ID`

#### Data & Recherche
- `SERPER_API_KEY`
- `APOLLO_API_KEY`
- `HUNTER_API_KEY`

#### Cloud / Infrastructure
- `GOOGLE_CLOUD_PROJECT`
- `GOOGLE_APPLICATION_CREDENTIALS`
- `SUPABASE_URL` + `SUPABASE_ANON_KEY`

---

## 🛠️ Diagnostic et Dépannage

### Problème : Clés non chargées

```bash
# 1. Vérifier le diagnostic complet
python scripts/check_api_keys.py -d

# 2. Vérifier que les fichiers existent
ls -la SECRETS/keys/
ls -la SECRETS/keys/*/

# 3. Tester le chargement manuel
python -c "from SECRETS import load_all_secrets; print(load_all_secrets(verbose=True))"
```

### Problème : Erreur "API key missing"

```bash
# 1. Identifier quelle clé manque
python scripts/check_api_keys.py

# 2. Vérifier si elle est dans les fichiers
grep -r "VOTRE_CLE" SECRETS/keys/

# 3. Ajouter la clé dans le bon fichier
nano SECRETS/keys/ai/.env  # Par exemple
```

### Problème : Clé présente mais non reconnue

Vérifier que la clé n'est pas un **stub/placeholder** :

```python
from SECRETS.secrets_loader import _stub

# Ces valeurs sont considérées comme des placeholders
placeholders = [
    "METS_TA_CLE", "METS_TON", "_ICI",
    "tondomaine.com", "YOUR_KEY", "PLACEHOLDER"
]

# Si votre clé contient un de ces patterns, elle sera ignorée
```

---

## 🔄 Ordre de Chargement

Le système charge les clés dans cet ordre (le dernier écrase le précédent) :

1. **JSON** via `_JSON_MAP` et `_inject_real_keys()`
2. **`.env`** à la racine de `SECRETS/keys/`
3. **Sous-dossiers** : `.env` ou `.env.template`
4. **Fichiers `.txt`** : `NOM_CLE.txt`
5. **Service accounts** Google
6. **Injections spéciales** (HuggingFace multi-keys, etc.)
7. **`.env` racine projet** (override final)

### Exemple concret

```
# 1. Chargement JSON
SECRETS/keys/anthropic.json → ANTHROPIC_API_KEY=sk-ant-abc123

# 2. Chargement .env (écrase si déjà défini)
SECRETS/keys/ai/.env → ANTHROPIC_API_KEY=sk-ant-xyz789

# 3. Override final
.env (racine) → ANTHROPIC_API_KEY=sk-ant-production-key
```

Résultat final : `ANTHROPIC_API_KEY=sk-ant-production-key`

---

## 📋 Validation des Clés

### Configuration Minimale Viable

Pour que NAYA soit opérationnel, ces 4 clés sont **critiques** :

1. **LLM** : Au moins une clé IA (Anthropic/OpenAI/Groq)
2. **Telegram** : Bot token + Chat ID
3. **Email** : SendGrid API key
4. **Paiement** : Au moins un lien de paiement (PayPal/Revolut)

Vérification :

```python
from SECRETS import get_status

status = get_status()
mv = status['minimum_viable']

if all(mv.values()):
    print("✅ Configuration minimale OK")
else:
    print("❌ Configuration incomplète")
    for key, ok in mv.items():
        if not ok:
            print(f"  Manque: {key}")
```

---

## 🔒 Sécurité

### Règles importantes

1. **Ne JAMAIS committer** les fichiers `.env` avec vraies clés
2. **Committer uniquement** les `.env.template` (placeholders)
3. Les vraies clés doivent être dans `.gitignore`
4. Utiliser le vault chiffré AES-256 pour production

### Fichiers à committer vs ignorer

✅ **Committer** :
- `README.md`
- `*.env.template`
- `secrets_loader.py`
- `GUIDE_CHARGEMENT_CLES.md`

❌ **Ne JAMAIS committer** :
- `*.env` (sauf `.env.example`)
- `*.json` (sauf si template)
- Fichiers avec vraies clés

---

## 🎯 Exemples d'Utilisation

### Exemple 1 : Boot complet avec validation

```python
from SECRETS import load_all_secrets, validate_all_keys

# Charger toutes les clés
result = load_all_secrets(verbose=True)
print(f"✅ {result['loaded']} variables chargées")

# Valider (mode strict)
try:
    report = validate_all_keys(strict=True)
    print(f"✅ Toutes les clés critiques présentes")
except RuntimeError as e:
    print(f"❌ {e}")
    exit(1)
```

### Exemple 2 : Utilisation dans un agent

```python
from SECRETS import get_secret, is_configured

class TelegramAgent:
    def __init__(self):
        if not is_configured("TELEGRAM_BOT_TOKEN"):
            raise ValueError("Telegram bot token manquant")

        self.token = get_secret("TELEGRAM_BOT_TOKEN")
        self.chat_id = get_secret("TELEGRAM_CHAT_ID")

    async def send_message(self, text: str):
        # Utiliser self.token pour envoyer le message
        pass
```

### Exemple 3 : Diagnostic automatique au boot

```python
# main.py
from SECRETS import load_all_secrets, print_diagnostic_report
import sys

if "--check-keys" in sys.argv:
    print_diagnostic_report()
    exit(0)

# Boot normal
result = load_all_secrets(verbose=False)
print(f"🔐 {result['real_keys']} clés API chargées")
```

---

## 🆘 Support et Documentation

### Commandes utiles

```bash
# Diagnostic complet
python scripts/check_api_keys.py -d

# Validation stricte
python scripts/check_api_keys.py -v

# Export JSON
python scripts/check_api_keys.py --json

# Help
python scripts/check_api_keys.py --help
```

### Fichiers de référence

- `SECRETS/secrets_loader.py` — Code source du loader
- `SECRETS/README.md` — Documentation structure SECRETS
- `scripts/check_api_keys.py` — Utilitaire de diagnostic
- `.env.example` — Template complet de toutes les variables

---

## 📝 Checklist Déploiement

Avant chaque déploiement, vérifier :

- [ ] Toutes les clés critiques sont présentes
- [ ] Aucune clé placeholder/stub restante
- [ ] Les clés de production sont dans le bon environnement
- [ ] Le diagnostic passe : `python scripts/check_api_keys.py -v`
- [ ] Les tests de validation passent
- [ ] Les secrets ne sont PAS dans le code source

---

**Version :** 1.0
**Dernière mise à jour :** 2026-04-16
**Propriétaire :** NAYA SUPREME V19
