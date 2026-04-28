#!/usr/bin/env bash
#
# NAYA SUPREME V19 — MASTER START SCRIPT
# Démarrage complet du système en production
#
# Usage:
#   ./RUN.sh                          # Start single cycle
#   ./RUN.sh daemon                   # Start daemon
#   ./RUN.sh dashboard                # Start dashboard
#   ./RUN.sh full                     # Full Docker stack
#

MODE=${1:-cycle}

echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║                                                                    ║"
echo "║     🚀 NAYA SUPREME V19 — AUTONOMOUS AI REVENUE SYSTEM            ║"
echo "║                                                                    ║"
echo "║     11 Agents IA | 29 Modules Revenue | 32 Pain Engines          ║"
echo "║     Production-Ready | 200% Performance | Auto-Scaling           ║"
echo "║                                                                    ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

if [ "$MODE" = "full" ]; then
    echo "🐳 Starting full Docker stack..."
    docker-compose up -d
    echo ""
    echo "✅ Services running:"
    echo "  - API: http://localhost:8000"
    echo "  - Dashboard: http://localhost:8080"
    echo "  - Grafana: http://localhost:3000"
    echo "  - Prometheus: http://localhost:9090"
    echo ""
    docker-compose logs -f

elif [ "$MODE" = "daemon" ]; then
    echo "🔄 Starting NAYA SUPREME in daemon mode..."
    python main.py daemon --interval 3600

elif [ "$MODE" = "dashboard" ]; then
    echo "🖥️  Starting OODA Dashboard..."
    python main.py dashboard --host 0.0.0.0 --port 8080

else
    # Default: single cycle
    echo "⚙️  Running single cycle..."
    python main.py cycle
fi
