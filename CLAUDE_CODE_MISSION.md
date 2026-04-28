# 🎯 NAYA SUPREME — MISSION BRIEF POUR CLAUDE CODE

> **À LIRE EN PREMIER.** Ce document est ta mission. Lis-le intégralement avant la moindre commande.

---

## 1. CONTEXTE

Tu reprends un projet qui a été nettoyé et stabilisé. **Tu n'as PAS à refaire l'audit ni le ménage** — c'est déjà fait. Ta mission est concrète et limitée :

> **Builder, tester, et déployer NAYA SUPREME V19 sur Google Cloud Run en production.**

Le projet contient :
- 1 052 fichiers Python (0 erreur de syntaxe)
- 11 agents IA, 32 pain engines, 98 routes HTTP FastAPI
- 798/818 tests pytest passent (97,6 %)
- Dockerfile multi-stage validé
- 42 vraies clés API dans `.env` (déjà hydratées)
- 5 cibles de déploiement disponibles (Cloud Run, Render, Vercel, Docker Compose, Railway)

---

## 2. CE QUI EST DÉJÀ VÉRIFIÉ ✅

Ne refais pas ces vérifications, elles ont été faites avant ta prise en charge :

- ✅ `python3 -m compileall .` → 0 erreur
- ✅ `pytest tests/` → 798 passent, 18 nécessitent services live
- ✅ `uvicorn NAYA_CORE.api.main:app` boot et `GET /api/v1/health` → 200 OK
- ✅ Les 11 routers FastAPI chargent sans erreur
- ✅ Le registry des 32 pain specs s'enregistre au boot
- ✅ Les 22/36 clés critiques + 20 clés additionnelles sont dans `.env`
- ✅ Doublons critiques résolus
- ✅ Healthcheck Docker pointe sur la bonne route (`/api/v1/health`)

---

## 3. CE QUE TU DOIS FAIRE — DANS L'ORDRE

### Étape 1 : Validation locale (15 min)

```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Vérifier que tout compile
python3 -m compileall -q . 2>&1 | grep -i error
# → Doit être vide

# 3. Lancer la suite de tests rapide
pytest tests/test_unit.py tests/test_pre_deploy_gate.py -q
# → 75 + 118 tests doivent passer

# 4. Démarrer l'API en local
uvicorn NAYA_CORE.api.main:app --port 8000 &
sleep 3
curl http://localhost:8000/api/v1/health
# → {"status": "healthy", ...}
kill %1
```

**Si l'une de ces 4 étapes échoue, STOP et reporte le problème exact. Ne continue pas.**

### Étape 2 : Régénération des 2 clés API corrompues (manuel — humain requis)

⚠️ **Ces 2 clés sont corrompues dans le dump source (caractères cyrilliques mélangés)** et **ne peuvent pas être réparées automatiquement**. Demande à l'humain de :

1. **Anthropic** → générer une nouvelle clé sur https://console.anthropic.com/settings/keys
   → ajouter dans `.env` : `ANTHROPIC_API_KEY=sk-ant-api03-...`

2. **Stripe** → récupérer les 3 clés sur https://dashboard.stripe.com/apikeys (mode live OU test selon préférence)
   → ajouter dans `.env` :
   ```
   STRIPE_API_KEY=sk_live_...
   STRIPE_PUBLIC_KEY=pk_live_...
   STRIPE_WEBHOOK_SECRET=whsec_...
   ```

**Ne tente PAS d'inventer ces clés ni de les placeholder. Demande à l'humain.**

### Étape 3 : Build Docker local (10 min)

```bash
docker build -t naya-supreme:v19.3 .

# Test du conteneur en isolation
docker run --rm -d --name naya-test \
  -p 8000:8000 \
  --env-file .env \
  naya-supreme:v19.3

sleep 10
curl http://localhost:8000/api/v1/health
# → 200 OK attendu

docker logs naya-test | tail -30
docker stop naya-test
```

**Si le healthcheck du conteneur échoue, vérifie en priorité :**
- Les variables d'environnement passent-elles bien ? (`docker exec naya-test env | grep API_KEY`)
- Le boot complet a-t-il pris > 20s ? (start_period du healthcheck)
- Postgres/Redis sont-ils requis pour le boot ? (le code doit dégrader proprement sans eux)

### Étape 4 : Déploiement Google Cloud Run (cible primaire)

**Pré-requis humain :**
- Compte Google Cloud actif (project: `naya-pro-ultime`, ID: `735034661802`)
- `gcloud` CLI installé et authentifié
- Service Account JSON dans `SECRETS/service_accounts/naya-pro-ultime.json` (à fournir par l'humain)

```bash
# 1. Authentification
gcloud auth login
gcloud config set project naya-pro-ultime

# 2. Activer les APIs requises (une seule fois)
gcloud services enable cloudbuild.googleapis.com run.googleapis.com \
  artifactregistry.googleapis.com secretmanager.googleapis.com

# 3. Créer les secrets dans Secret Manager (une seule fois)
# Lis chaque clé du .env et crée un secret correspondant
while IFS='=' read -r key value; do
  [[ "$key" =~ ^#.*$ ]] && continue
  [[ -z "$key" ]] && continue
  printf "%s" "$value" | gcloud secrets create "$key" --data-file=- 2>/dev/null \
    || printf "%s" "$value" | gcloud secrets versions add "$key" --data-file=-
done < .env

# 4. Build & deploy via Cloud Build
gcloud builds submit --config cloudbuild.yaml

# 5. Vérifier
SERVICE_URL=$(gcloud run services describe naya-supreme --region=europe-west1 --format='value(status.url)')
curl "$SERVICE_URL/api/v1/health"
```

**Région recommandée** : `europe-west1` (Belgique) — la fondatrice est en Polynésie, mais la majorité des prospects B2B sont en EU. Latence acceptable, conformité RGPD respectée.

### Étape 5 : Cibles secondaires (optionnel — uniquement si Cloud Run OK)

- **Render** : `git push` → auto-deploy via `render.yaml`
- **Vercel** : `vercel --prod` → edge functions (API en serverless)
- **Self-hosted VPS** : `docker compose -f docker-compose.prod.yml up -d`

---

## 4. RÈGLES NON-NÉGOCIABLES

1. **NE JAMAIS commit `.env`, `SECRETS/keys/naya_raw_dump.env`, ou tout fichier contenant une vraie clé.** Le `.gitignore` les protège — vérifie qu'il n'a pas été modifié.

2. **NE JAMAIS reformatter ou refactorer le code en masse.** Le projet a 163 000 lignes : un refactor large casserait quelque chose. Limite-toi aux corrections nécessaires au déploiement.

3. **NE JAMAIS supprimer un dossier sans avoir vérifié ses imports avec `grep -rn "from <DOSSIER>" --include="*.py"`.** Beaucoup de modules apparemment isolés sont importés dynamiquement via `importlib`.

4. **TOUJOURS demander à l'humain avant** : régénérer une clé, modifier un schéma DB, changer la cible de déploiement, ou abandonner une étape.

5. **Si un test échoue**, lis l'erreur, comprends-la, fixe-la précisément. **Ne désactive pas le test pour passer.**

6. **Les 18 tests qui échouent actuellement** (`test_comprehensive.py::TestPrometheusMetrics`, `test_evolution_system.py::TestDynamicScaler`, `test_smoke.py`, `test_production.py::TestRedisRateLimiting`) sont **acceptables** : ils requièrent Redis live ou config production. Ne les touche pas tant que l'infra n'est pas en place.

---

## 5. STRUCTURE — REPÈRES RAPIDES

| Tu cherches… | Va voir… |
|---|---|
| Le point d'entrée HTTP | `NAYA_CORE/api/main.py` |
| L'orchestrateur multi-agent | `NAYA_CORE/multi_agent_orchestrator.py` |
| Les 32 pain specs | `NAYA_CORE/pain/pain_specs_registry.py` |
| Les 11 agents | `NAYA_CORE/agents/` |
| Le routing LLM | `NAYA_CORE/llm_router.py` |
| Les 11 routers HTTP | `api/routers/` |
| Le chargement des secrets | `SECRETS/secrets_loader.py` |
| Le preflight (boot checks) | `NAYA_CORE/preflight.py` |
| Le healthcheck | `api/routers/system.py` |
| Le pipeline ventes réelles | `NAYA_REAL_SALES/live_sales_ops.py` |
| Le dashboard OODA | `NAYA_DASHBOARD/ooda_dashboard.py` |

---

## 6. EN CAS DE BLOCAGE

Si tu es bloqué sur une étape :

1. **Lis les logs en entier.** L'erreur exacte est presque toujours dedans.
2. **Vérifie le `.env`.** 80 % des bugs en cloud viennent de variables absentes.
3. **Teste en local d'abord.** Si ça marche en local et casse en cloud, c'est l'environnement.
4. **Reporte à l'humain** avec : (a) la commande exacte exécutée, (b) la sortie complète, (c) ton hypothèse, (d) ta proposition.

**Ne passe PAS à l'étape suivante tant que l'étape actuelle n'est pas verte.**

---

## 7. CRITÈRE DE FIN DE MISSION

Tu as terminé quand **TOUS** ces points sont vrais :

- [ ] L'API tourne sur Cloud Run en `europe-west1`
- [ ] `curl <SERVICE_URL>/api/v1/health` retourne 200 OK
- [ ] `curl <SERVICE_URL>/docs` affiche la doc Swagger
- [ ] Les 42 secrets sont dans Google Secret Manager
- [ ] Les logs Cloud Run montrent `🔐 22/36 clés API chargées` (ou plus si Anthropic + Stripe ont été régénérées)
- [ ] Le service est configuré en `min-instances=0, max-instances=10` (scale-to-zero)
- [ ] Le coût mensuel estimé est < 50 EUR (sans trafic) → vérifie dans la console GCP
- [ ] Tu as remis à l'humain : l'URL du service, le coût estimé, et la liste des clés à régénérer si applicable

---

## 8. ENGAGEMENT QUALITÉ

Tu es Claude Code. Tu as accès à un terminal réel et à un système de fichiers. **Tu fais le travail, tu ne le simules pas.** Chaque commande que tu exécutes doit être réelle, chaque sortie que tu rapportes doit être authentique.

**Ne fabrique JAMAIS de sortie de commande, JAMAIS de résultat de test, JAMAIS d'URL de déploiement.** Si une commande échoue ou si une étape n'est pas faisable dans ton environnement, dis-le explicitement.

---

**Bonne mission. Le système est solide — fais-le tourner en production.**
