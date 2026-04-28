"""NAYA V19 — Integrations API Router — Production Ready"""
import os
from fastapi import APIRouter, HTTPException
from typing import Dict
from pydantic import BaseModel

router = APIRouter()


class TelegramMessage(BaseModel):
    message: str


class EmailPayload(BaseModel):
    to_email: str
    subject: str
    body: str


@router.get("/status")
async def integrations_status() -> Dict:
    """Statut de toutes les intégrations externes."""
    from SECRETS.secrets_loader import is_configured
    integrations = {
        "telegram": {
            "configured": is_configured("TELEGRAM_BOT_TOKEN") and is_configured("TELEGRAM_CHAT_ID"),
            "purpose": "Notifications fondateur",
        },
        "gmail_oauth": {
            "configured": is_configured("GOOGLE_OAUTH_REFRESH_TOKEN"),
            "purpose": "Envoi emails outreach",
        },
        "sendgrid": {
            "configured": is_configured("SENDGRID_API_KEY"),
            "purpose": "Email fallback",
        },
        "serper": {
            "configured": is_configured("SERPER_API_KEY"),
            "purpose": "Recherche prospects (Google)",
        },
        "apollo": {
            "configured": is_configured("APOLLO_API_KEY"),
            "purpose": "Enrichissement contacts",
        },
        "shopify": {
            "configured": is_configured("SHOPIFY_ACCESS_TOKEN"),
            "purpose": "E-commerce Botanica",
        },
        "supabase": {
            "configured": is_configured("SUPABASE_URL"),
            "purpose": "Cloud database sync",
        },
        "notion": {
            "configured": is_configured("NOTION_TOKEN"),
            "purpose": "CRM & documentation",
        },
        "paypal": {
            "configured": is_configured("PAYPAL_ME_URL"),
            "purpose": "Paiement clients",
        },
        "groq": {
            "configured": is_configured("GROQ_API_KEY"),
            "purpose": "LLM rapide gratuit",
        },
        "deepseek": {
            "configured": is_configured("DEEPSEEK_API_KEY"),
            "purpose": "LLM analyse",
        },
        "tiktok": {
            "configured": is_configured("TIKTOK_ACCESS_TOKEN"),
            "purpose": "Contenu social / lead gen",
        },
    }
    configured = sum(1 for v in integrations.values() if v["configured"])
    return {
        "integrations": integrations,
        "configured": configured,
        "total": len(integrations),
        "score": f"{configured}/{len(integrations)}",
    }


@router.post("/telegram/send")
async def send_telegram(payload: TelegramMessage) -> Dict:
    """Envoie un message Telegram au fondateur."""
    try:
        from NAYA_CORE.integrations.telegram_integration import TelegramIntegration
        tg = TelegramIntegration()
        tg.send(payload.message)
        return {"status": "sent", "length": len(payload.message)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)[:200])


@router.post("/email/send")
async def send_email(payload: EmailPayload) -> Dict:
    """Envoie un email via Gmail OAuth ou SendGrid."""
    try:
        from NAYA_CORE.integrations.gmail_oauth2 import GmailOAuth2Sender
        gmail = GmailOAuth2Sender()
        if gmail.has_oauth or gmail.has_sendgrid:
            gmail.send(
                to_email=payload.to_email,
                subject=payload.subject,
                body_html=payload.body.replace("\n", "<br>"),
                body_text=payload.body,
            )
            return {"status": "sent", "to": payload.to_email, "via": "gmail_oauth" if gmail.has_oauth else "sendgrid"}
        return {"status": "not_configured", "message": "Ni Gmail OAuth ni SendGrid configuré"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)[:200])


@router.get("/serper/test")
async def test_serper() -> Dict:
    """Test la connexion Serper."""
    try:
        from NAYA_CORE.integrations.serper_multi import SerperMultiKeySearch
        serper = SerperMultiKeySearch()
        results = serper.search("test PME France", num_results=3)
        return {"status": "ok", "results_count": len(results) if isinstance(results, list) else 0}
    except Exception as e:
        return {"status": "error", "error": str(e)[:100]}


@router.get("/enrichment/test")
async def test_enrichment() -> Dict:
    """Test l'enrichissement de contact."""
    try:
        from NAYA_CORE.enrichment.contact_enricher import get_contact_enricher
        enricher = get_contact_enricher()
        contact = enricher.enrich("Anthropic", "https://anthropic.com")
        return {
            "status": "ok",
            "email_found": bool(contact.email),
            "source": contact.source,
            "confidence": contact.confidence,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)[:100]}
