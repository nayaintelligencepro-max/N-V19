#!/bin/bash
# NAYA SUPREME V13 - Installation complete
echo "NAYA SUPREME V13 - Installation"
echo "================================"

pip install --upgrade pip

# Core (obligatoire)
pip install fastapi uvicorn[standard] httpx aiohttp requests \
    python-dotenv pydantic pydantic-settings python-multipart \
    cryptography pyjwt python-jose tenacity structlog \
    python-json-logger websockets aiofiles python-dateutil

# LLM providers
pip install anthropic openai

# Scraping + search
pip install beautifulsoup4 lxml

# Email
pip install sendgrid

# Database
pip install sqlalchemy alembic

# Monitoring
pip install prometheus-client

# Redis (optionnel)
pip install redis || echo "Redis optionnel - skip"

echo ""
echo "Installation terminee"
echo "Demarrage: bash start.sh (Linux/Mac) ou start.bat (Windows)"
