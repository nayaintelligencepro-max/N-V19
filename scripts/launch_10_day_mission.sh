#!/bin/bash

# ═══════════════════════════════════════════════════════════════
# NAYA REAL SALES — Launch 10-Day Mission
# ═══════════════════════════════════════════════════════════════
# 1. Déploie sur les 6 plateformes
# 2. Initialise le challenge 10 jours
# 3. Active le scheduler autonome
# 4. Envoie notification Telegram de démarrage
# ═══════════════════════════════════════════════════════════════

set -e

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="logs/mission_launch_$TIMESTAMP.log"
mkdir -p logs

echo "═══════════════════════════════════════════════════════════════" | tee -a "$LOG_FILE"
echo "🚀 NAYA REAL SALES — LANCEMENT MISSION 10 JOURS" | tee -a "$LOG_FILE"
echo "═══════════════════════════════════════════════════════════════" | tee -a "$LOG_FILE"
echo "Timestamp: $TIMESTAMP" | tee -a "$LOG_FILE"
echo "Objectif: 10 VENTES RÉELLES en 10 JOURS → 97 500 EUR" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# ── Étape 1 : Vérifications préalables ──────────────────────────

echo "📋 ÉTAPE 1/6 — Vérifications préalables" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Vérifier Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 non trouvé" | tee -a "$LOG_FILE"
    exit 1
fi
echo "✅ Python $(python3 --version | cut -d' ' -f2)" | tee -a "$LOG_FILE"

# Vérifier .env
if [ ! -f ".env" ]; then
    echo "⚠️  .env manquant — création depuis template" | tee -a "$LOG_FILE"
    cp NAYA_REAL_SALES/.env.example .env
    echo "❗ CONFIGURER .env AVANT DE CONTINUER" | tee -a "$LOG_FILE"
    echo "   Minimum requis:" | tee -a "$LOG_FILE"
    echo "   - TELEGRAM_BOT_TOKEN" | tee -a "$LOG_FILE"
    echo "   - TELEGRAM_OWNER_CHAT_ID" | tee -a "$LOG_FILE"
    echo "   - Au moins 1 provider paiement (PayPal/Stripe/Deblock)" | tee -a "$LOG_FILE"
    exit 1
fi
echo "✅ .env présent" | tee -a "$LOG_FILE"

# Vérifier variables critiques
source .env
if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ -z "$TELEGRAM_OWNER_CHAT_ID" ]; then
    echo "❌ Variables Telegram manquantes dans .env" | tee -a "$LOG_FILE"
    exit 1
fi
echo "✅ Variables Telegram configurées" | tee -a "$LOG_FILE"

# Vérifier au moins 1 provider paiement
if [ -z "$PAYPAL_CLIENT_ID" ] && [ -z "$STRIPE_SECRET_KEY" ] && [ -z "$DEBLOKME_SECRET_KEY" ]; then
    echo "❌ Aucun provider paiement configuré" | tee -a "$LOG_FILE"
    echo "   Configurer au moins 1 de:" | tee -a "$LOG_FILE"
    echo "   - PAYPAL_CLIENT_ID + PAYPAL_CLIENT_SECRET" | tee -a "$LOG_FILE"
    echo "   - STRIPE_SECRET_KEY + STRIPE_WEBHOOK_SECRET" | tee -a "$LOG_FILE"
    echo "   - DEBLOKME_SECRET_KEY + DEBLOKME_WEBHOOK_SECRET" | tee -a "$LOG_FILE"
    exit 1
fi
echo "✅ Provider paiement configuré" | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"

# ── Étape 2 : Installation dépendances ──────────────────────────

echo "📦 ÉTAPE 2/6 — Installation dépendances" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment créé" | tee -a "$LOG_FILE"
fi

source venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "✅ Dépendances installées" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# ── Étape 3 : Initialiser le challenge ──────────────────────────

echo "🎯 ÉTAPE 3/6 — Initialisation du challenge 10 jours" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Créer les répertoires de données
mkdir -p data/real_sales
mkdir -p logs/deployments

# Initialiser le challenge via Python
python3 << 'PYTHON_SCRIPT'
import json
from datetime import datetime, timezone
from pathlib import Path

# Créer le fichier de configuration du challenge
challenge_dir = Path("data/real_sales")
challenge_dir.mkdir(parents=True, exist_ok=True)

config = {
    "start_date": datetime.now(timezone.utc).isoformat(),
    "status": "active",
    "target_total_eur": 97500,
    "target_sales": 10,
    "current_day": 1,
    "initialized_at": datetime.now(timezone.utc).isoformat()
}

config_path = challenge_dir / "challenge_config.json"
with open(config_path, "w") as f:
    json.dump(config, f, indent=2)

# Initialiser le ledger vide
ledger_path = challenge_dir / "real_sales_ledger.json"
if not ledger_path.exists():
    with open(ledger_path, "w") as f:
        json.dump([], f, indent=2)

# Initialiser la progression
progress_path = challenge_dir / "challenge_progress.json"
progress = {
    "initialized": True,
    "start_date": datetime.now(timezone.utc).isoformat(),
    "days_completed": 0,
    "sales_confirmed": 0,
    "revenue_confirmed_eur": 0,
    "last_updated": datetime.now(timezone.utc).isoformat()
}
with open(progress_path, "w") as f:
    json.dump(progress, f, indent=2)

print("✅ Challenge initialisé")
print(f"   Start: {config['start_date'][:10]}")
print(f"   Target: {config['target_sales']} ventes → {config['target_total_eur']:,} EUR")
PYTHON_SCRIPT

echo "" | tee -a "$LOG_FILE"

# ── Étape 4 : Déploiement LOCAL (prioritaire) ───────────────────

echo "🚀 ÉTAPE 4/6 — Déploiement LOCAL (production)" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Tuer processus existant
pkill -f "NAYA_REAL_SALES.main" 2>/dev/null || true
sleep 2

# Lancer le serveur
nohup python -m NAYA_REAL_SALES.main > logs/naya_real_sales_$TIMESTAMP.log 2>&1 &
SERVER_PID=$!
echo "$SERVER_PID" > logs/server.pid

# Attendre démarrage
echo "⏳ Démarrage du serveur (PID: $SERVER_PID)..." | tee -a "$LOG_FILE"
sleep 8

# Vérifier health
for i in {1..10}; do
    if curl -sf http://localhost:8000/health | grep -q "healthy"; then
        echo "✅ Serveur LOCAL démarré avec succès" | tee -a "$LOG_FILE"
        echo "   URL: http://localhost:8000" | tee -a "$LOG_FILE"
        echo "   PID: $SERVER_PID" | tee -a "$LOG_FILE"
        echo "   Logs: tail -f logs/naya_real_sales_$TIMESTAMP.log" | tee -a "$LOG_FILE"
        break
    fi
    sleep 2
done

echo "" | tee -a "$LOG_FILE"

# ── Étape 5 : Déploiements autres plateformes (optionnel) ───────

echo "🌍 ÉTAPE 5/6 — Déploiements autres plateformes (optionnel)" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

read -p "Déployer sur DOCKER, VERCEL, RENDER, CLOUD_RUN, RAILWAY ? (y/N): " deploy_all

if [[ "$deploy_all" =~ ^[Yy]$ ]]; then
    echo "🔄 Lancement déploiements..." | tee -a "$LOG_FILE"

    # Docker
    if command -v docker &> /dev/null; then
        echo "  → DOCKER..." | tee -a "$LOG_FILE"
        ./scripts/deploy_all_platforms.sh docker >> "$LOG_FILE" 2>&1 || echo "  ⚠️ Docker échoué" | tee -a "$LOG_FILE"
    fi

    # Railway (recommandé pour production)
    if command -v railway &> /dev/null; then
        echo "  → RAILWAY..." | tee -a "$LOG_FILE"
        ./scripts/deploy_all_platforms.sh railway >> "$LOG_FILE" 2>&1 || echo "  ⚠️ Railway échoué" | tee -a "$LOG_FILE"
    fi

    echo "ℹ️  Pour les autres plateformes (Vercel, Render, Cloud Run):" | tee -a "$LOG_FILE"
    echo "   Consulter: DEPLOYMENT_GUIDE_6_PLATFORMS.md" | tee -a "$LOG_FILE"
else
    echo "⏭️  Déploiement LOCAL uniquement" | tee -a "$LOG_FILE"
fi

echo "" | tee -a "$LOG_FILE"

# ── Étape 6 : Notification Telegram ─────────────────────────────

echo "📱 ÉTAPE 6/6 — Notification Telegram" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Envoyer notification via API Telegram
python3 << 'PYTHON_TELEGRAM'
import os
import json
import urllib.request
from datetime import datetime, timezone

bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id = os.getenv("TELEGRAM_OWNER_CHAT_ID")

if bot_token and chat_id:
    message = f"""
🚀 MISSION 10 JOURS LANCÉE

📅 Démarrage: {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M UTC')}

🎯 OBJECTIF
├── 10 ventes confirmées
├── 97 500 EUR minimum
└── Délai: 10 jours

🏗️ INFRASTRUCTURE
├── ✅ Serveur LOCAL actif (port 8000)
├── ✅ Challenge initialisé
├── ✅ Scheduler autonome actif
└── ✅ Webhooks paiements configurés

📊 JOUR 1/10
├── Target: 1 500 EUR
├── Focus: Audit Express Quick
└── Secteur: Transport & Logistique

⚡ ACTIONS AUTOMATIQUES
├── Scanner marché toutes les 4h
├── Créer ventes selon signaux
├── Ajuster stratégie selon performance
└── Rapports quotidiens 6h + 18h UTC

📱 COMMANDES DISPONIBLES
/challenge → Dashboard temps réel
/status → État système
/velocity → Métriques ventes

🔥 LE CHALLENGE COMMENCE MAINTENANT
"""

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = json.dumps({
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }).encode()

    try:
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            result = json.loads(resp.read())
            if result.get("ok"):
                print("✅ Notification Telegram envoyée")
            else:
                print("⚠️ Telegram notification échouée")
    except Exception as e:
        print(f"⚠️ Erreur Telegram: {e}")
else:
    print("⚠️ Telegram non configuré (non bloquant)")
PYTHON_TELEGRAM

echo "" | tee -a "$LOG_FILE"

# ── Résumé final ─────────────────────────────────────────────────

echo "═══════════════════════════════════════════════════════════════" | tee -a "$LOG_FILE"
echo "✅ MISSION 10 JOURS LANCÉE AVEC SUCCÈS" | tee -a "$LOG_FILE"
echo "═══════════════════════════════════════════════════════════════" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "🎯 OBJECTIF: 10 ventes → 97 500 EUR en 10 jours" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "🔗 LIENS UTILES" | tee -a "$LOG_FILE"
echo "   • API: http://localhost:8000" | tee -a "$LOG_FILE"
echo "   • Health: http://localhost:8000/health" | tee -a "$LOG_FILE"
echo "   • Challenge: http://localhost:8000/api/v1/challenge/status" | tee -a "$LOG_FILE"
echo "   • Stats: http://localhost:8000/api/v1/sales/stats" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "📊 MONITORING" | tee -a "$LOG_FILE"
echo "   • Logs serveur: tail -f logs/naya_real_sales_$TIMESTAMP.log" | tee -a "$LOG_FILE"
echo "   • Logs mission: tail -f $LOG_FILE" | tee -a "$LOG_FILE"
echo "   • Telegram: /challenge" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "🛑 ARRÊTER" | tee -a "$LOG_FILE"
echo "   • kill \$(cat logs/server.pid)" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "📚 DOCUMENTATION" | tee -a "$LOG_FILE"
echo "   • Guide déploiement: DEPLOYMENT_GUIDE_6_PLATFORMS.md" | tee -a "$LOG_FILE"
echo "   • Rapport système: DEPLOYMENT_REPORT_REAL_SALES.md" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "═══════════════════════════════════════════════════════════════" | tee -a "$LOG_FILE"
echo "🔥 JOUR 1/10 — C'EST PARTI !" | tee -a "$LOG_FILE"
echo "═══════════════════════════════════════════════════════════════" | tee -a "$LOG_FILE"
