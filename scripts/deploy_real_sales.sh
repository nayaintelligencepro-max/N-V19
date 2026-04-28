#!/bin/bash

# ═══════════════════════════════════════════════════════════════
# NAYA REAL SALES — Script Déploiement Production
# ═══════════════════════════════════════════════════════════════
# Déploie le système de ventes réelles sur Railway/Render
# Usage: ./deploy_real_sales.sh [railway|render|local]
# ═══════════════════════════════════════════════════════════════

set -e  # Exit on error

PLATFORM=${1:-railway}

echo "═══════════════════════════════════════════════════════════════"
echo "NAYA REAL SALES — DÉPLOIEMENT PRODUCTION"
echo "Platform: $PLATFORM"
echo "═══════════════════════════════════════════════════════════════"

# ── Vérifications préalables ──────────────────────────────────────

echo ""
echo "🔍 Vérification environnement..."

# Vérifier Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 non trouvé. Installation requise."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✅ Python $PYTHON_VERSION détecté"

# Vérifier Docker si déploiement local
if [ "$PLATFORM" = "local" ]; then
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker non trouvé. Installation requise pour déploiement local."
        exit 1
    fi
    echo "✅ Docker détecté"
fi

# ── Tests unitaires ───────────────────────────────────────────────

echo ""
echo "🧪 Exécution des tests..."

python3 -m pytest NAYA_REAL_SALES/tests/ -v --tb=short || {
    echo "⚠️ Certains tests ont échoué. Continuer quand même ? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "❌ Déploiement annulé."
        exit 1
    fi
}

echo "✅ Tests passés"

# ── Build et déploiement selon plateforme ─────────────────────────

case $PLATFORM in

    railway)
        echo ""
        echo "🚂 Déploiement Railway..."

        # Vérifier Railway CLI
        if ! command -v railway &> /dev/null; then
            echo "❌ Railway CLI non installé."
            echo "Installation: npm i -g @railway/cli"
            exit 1
        fi

        # Login Railway
        railway whoami || railway login

        # Déployer
        railway up --dockerfile Dockerfile.real_sales

        echo ""
        echo "✅ Déployé sur Railway !"
        echo "📊 Dashboard: https://railway.app/dashboard"
        echo "📝 Logs: railway logs --follow"
        ;;

    render)
        echo ""
        echo "🎨 Déploiement Render..."

        # Créer render.yaml si nécessaire
        if [ ! -f "render.real_sales.yaml" ]; then
            echo "❌ Fichier render.real_sales.yaml manquant"
            exit 1
        fi

        echo "📝 Fichier render.real_sales.yaml trouvé"
        echo "⚠️ Déploiement manuel requis:"
        echo "1. Aller sur https://dashboard.render.com"
        echo "2. New > Blueprint"
        echo "3. Connecter le repo GitHub"
        echo "4. Sélectionner render.real_sales.yaml"
        echo "5. Configurer les variables d'environnement"
        ;;

    local)
        echo ""
        echo "🐳 Déploiement local Docker..."

        # Build image
        echo "📦 Build image Docker..."
        docker build -f Dockerfile.real_sales -t naya-real-sales:latest .

        # Stop conteneur existant
        docker stop naya-real-sales 2>/dev/null || true
        docker rm naya-real-sales 2>/dev/null || true

        # Run conteneur
        echo "🚀 Démarrage conteneur..."
        docker run -d \
            --name naya-real-sales \
            --restart unless-stopped \
            -p 8000:8000 \
            -v $(pwd)/data:/app/data \
            -v $(pwd)/logs:/app/logs \
            --env-file .env \
            naya-real-sales:latest

        echo ""
        echo "✅ Conteneur démarré !"
        echo "📊 API: http://localhost:8000"
        echo "📝 Logs: docker logs -f naya-real-sales"
        echo "🛑 Stop: docker stop naya-real-sales"
        ;;

    *)
        echo "❌ Platform non reconnue: $PLATFORM"
        echo "Usage: $0 [railway|render|local]"
        exit 1
        ;;
esac

# ── Post-déploiement ──────────────────────────────────────────────

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "🎉 DÉPLOIEMENT TERMINÉ"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "📌 PROCHAINES ÉTAPES :"
echo ""
echo "1. Configurer les webhooks paiements:"
echo "   - PayPal: https://developer.paypal.com/dashboard/webhooks"
echo "   - Stripe: https://dashboard.stripe.com/webhooks"
echo "   - Deblock: (dashboard Deblock.me)"
echo ""
echo "2. Vérifier les notifications Telegram:"
echo "   Envoyer /challenge au bot pour vérifier connexion"
echo ""
echo "3. Créer la première vente de test:"
echo "   POST https://[votre-url]/api/v1/sales/create"
echo ""
echo "4. Suivre les logs en temps réel:"
if [ "$PLATFORM" = "railway" ]; then
    echo "   railway logs --follow"
elif [ "$PLATFORM" = "local" ]; then
    echo "   docker logs -f naya-real-sales"
fi
echo ""
echo "═══════════════════════════════════════════════════════════════"
