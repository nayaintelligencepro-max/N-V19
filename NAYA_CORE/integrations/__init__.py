"""NAYA — Integrations Package. Toutes les clés lues dynamiquement depuis SECRETS.

V19.3 : Stripe retiré (non disponible en Polynésie française).
Paiements : PayPal.me + Deblock.me via NAYA_REVENUE_ENGINE.payment_engine.
"""
from .apollo_integration   import get_apollo,   ApolloIntegration,   ApolloContact
from .hunter_integration   import get_hunter,   HunterIntegration,   HunterEmail
from .sendgrid_integration import get_sendgrid, SendGridIntegration
from .linkedin_integration import get_linkedin, LinkedInIntegration
from .webhook_receiver     import get_webhook_receiver, WebhookReceiver
from .telegram_integration import TelegramIntegration
from .notion_integration   import NotionIntegration
from .shopify_integration  import ShopifyIntegration

__all__ = [
    "get_apollo", "ApolloIntegration", "ApolloContact",
    "get_hunter", "HunterIntegration", "HunterEmail",
    "get_sendgrid", "SendGridIntegration",
    "get_linkedin", "LinkedInIntegration",
    "get_webhook_receiver", "WebhookReceiver",
    "TelegramIntegration", "NotionIntegration", "ShopifyIntegration",
]
