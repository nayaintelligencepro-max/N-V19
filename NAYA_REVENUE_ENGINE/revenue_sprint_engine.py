"""
NAYA V19 — Revenue Sprint Engine
Séquence agressive structurée pour générer 60 000€ en 72H
puis 300 000€/mois en régime de croisière.

Stratégie en 4 phases :
  PHASE 1 (H0-H24)  : Shopify reactivation + outreach chaud
  PHASE 2 (H24-H48) : TikTok content blitz + LinkedIn B2B
  PHASE 3 (H48-H72) : Follow-up + closing agressif
  PHASE 4 (continu) : Machine autonome 24/7
"""
import os, json, time, logging, threading
from typing import Dict, List, Optional
from datetime import datetime, timedelta, timezone
from pathlib import Path

log = logging.getLogger("NAYA.SPRINT")

def _gs(k, d=""):
    try:
        from SECRETS.secrets_loader import get_secret
        return get_secret(k, d) or d
    except Exception:
        return os.environ.get(k, d)


# ── Offres haute valeur testées en Polynésie ────────────────────────────────

HIGH_VALUE_OFFERS = [
    {
        "id": "AUDIT_TRESORERIE",
        "title": "Audit Trésorerie Express 48H",
        "price": 3500,
        "target": ["PME", "artisan", "restaurant", "commerce"],
        "pain": "cash bloqué, trésorerie tendue",
        "promise": "On identifie 15 000€+ récupérables en 48H ou remboursé",
        "delivery": "2 jours — rapport + plan d'action",
        "paypal_suffix": "3500",
    },
    {
        "id": "CONSULTING_BLITZ",
        "title": "Mission Consulting B2B — Résultat 30 jours",
        "price": 7500,
        "target": ["startup", "TPE", "agence", "professionnel libéral"],
        "pain": "croissance bloquée, clients qui ne reviennent pas",
        "promise": "×2 sur le chiffre d'affaires en 30 jours ou on travaille gratuitement",
        "delivery": "30 jours d'accompagnement intensif",
        "paypal_suffix": "7500",
    },
    {
        "id": "RESCUE_DIGITAL",
        "title": "Rescue Digital — Boutique Shopify ou Site Web",
        "price": 2500,
        "target": ["e-commerce", "boutique", "artisan créateur"],
        "pain": "ventes faibles, panier abandonné, mauvais référencement",
        "promise": "+50% de conversions en 21 jours ou remboursé",
        "delivery": "3 semaines — audit + corrections + formation",
        "paypal_suffix": "2500",
    },
    {
        "id": "CONTENU_SOCIAL_PACK",
        "title": "Pack Contenu Social 30 Jours",
        "price": 1500,
        "target": ["tout secteur", "professionnel indépendant"],
        "pain": "pas de temps pour les réseaux, peu de visibilité",
        "promise": "30 posts professionnels + stratégie + résultats en 30 jours",
        "delivery": "30 jours — livraison hebdomadaire",
        "paypal_suffix": "1500",
    },
    {
        "id": "SHOPIFY_OPTIMISATION",
        "title": "Optimisation Shopify Full Stack",
        "price": 4500,
        "target": ["boutique Shopify", "e-commerce"],
        "pain": "ventes faibles, taux de conversion < 2%",
        "promise": "Taux de conversion × 3 ou remboursé",
        "delivery": "10 jours — SEO + UX + email marketing",
        "paypal_suffix": "4500",
    },
]

# Objectif par phase
SPRINT_TARGETS = {
    "H24":  15000,   # 15k€ en 24H
    "H48":  40000,   # 40k€ en 48H
    "H72":  60000,   # 60k€ en 72H
    "M1":  300000,   # 300k€ en 1 mois
}


class RevenueSprint:
    """
    Moteur de sprint revenue — 60 000€ en 72H.
    Utilise tous les canaux disponibles simultanément.
    """

    def __init__(self):
        self._start_time: Optional[float] = None
        self._total_pipeline = 0.0
        self._total_won = 0.0
        self._actions_taken: List[Dict] = []
        self._lock = threading.Lock()

    def start_sprint(self) -> Dict:
        """Démarre la séquence 72H et retourne le plan d'action immédiat."""
        self._start_time = time.time()
        channels = self._detect_channels()
        plan = self._build_action_plan(channels)
        log.info(f"[SPRINT] 🚀 Sprint 72H démarré — {len(channels)} canaux actifs")
        return {
            "started_at": datetime.now(timezone.utc).isoformat(),
            "target_72h": SPRINT_TARGETS["H72"],
            "target_month": SPRINT_TARGETS["M1"],
            "channels_active": channels,
            "action_plan": plan,
            "first_actions": plan[:5],
        }

    def _detect_channels(self) -> List[str]:
        """Détecte les canaux réellement utilisables maintenant."""
        channels = []
        if _gs("SHOPIFY_ACCESS_TOKEN"): channels.append("shopify_email")
        if _gs("TIKTOK_ACCESS_TOKEN"):  channels.append("tiktok_content")
        if _gs("GOOGLE_OAUTH_REFRESH_TOKEN"): channels.append("gmail_cold")
        if _gs("TELEGRAM_BOT_TOKEN"):   channels.append("telegram_alerts")
        if _gs("INSTAGRAM_USERNAME"):   channels.append("instagram_dm")
        if _gs("WHATSAPP_PHONE"):       channels.append("whatsapp_outreach")
        if _gs("PAYPAL_ME_URL"):        channels.append("paypal_payment")
        if _gs("REVOLUT_ME_URL"):       channels.append("revolut_payment")
        # Toujours disponible (scraping)
        channels.extend(["scraping_ddg", "scraping_pj"])
        return channels

    def _build_action_plan(self, channels: List[str]) -> List[Dict]:
        """Construit le plan d'action heure par heure."""
        plan = []
        now = datetime.now(timezone.utc)

        # H0 — Immédiat
        plan.append({
            "time": "H+0",
            "priority": "CRITIQUE",
            "action": "Configurer Telegram (2 min)",
            "why": "Sans Telegram, 0 alerte sur les prospects. Toutes les opportunités sont perdues.",
            "how": "t.me/BotFather → /newbot → copier token → SECRETS/keys/notifications.env",
            "revenue_impact": "Débloquer 100% du système d'alerte",
        })

        plan.append({
            "time": "H+0",
            "priority": "CRITIQUE",
            "action": "Activer Gmail SMTP (5 min)",
            "why": "Gmail OAuth est configuré mais EMAIL_FROM est vide → aucun email envoyé",
            "how": "Dans notifications.env: EMAIL_FROM=nayaintelligencepro@gmail.com + SMTP_USER + SMTP_PASS (App Password)",
            "revenue_impact": "Activer l'outreach email — canal principal B2B",
        })

        # H1 — Shopify
        if "shopify_email" in channels:
            plan.append({
                "time": "H+1",
                "priority": "HAUTE",
                "action": "Campagne email Shopify clients existants",
                "why": "Tes clients actuels sont les plus faciles à convertir (déjà confiance)",
                "how": "Envoyer offre Audit Trésorerie 3500€ aux clients inactifs depuis +60j",
                "revenue_impact": "5-10% conversion attendue → 2-5 deals × 3500€ = 7 000-17 500€",
            })

        # H2 — TikTok
        if "tiktok_content" in channels:
            plan.append({
                "time": "H+2",
                "priority": "HAUTE",
                "action": "Post TikTok viral — douleur financière",
                "why": "TikTok est configuré. 1 bon post peut générer 10-50 prospects en 24H",
                "how": "Script: 'Je vais te montrer comment récupérer 15 000€ en 48H dans ton entreprise'",
                "revenue_impact": "Lead generation organique — objectif 20+ prospects qualifiés",
            })

        # H3 — Cold outreach
        if "gmail_cold" in channels:
            plan.append({
                "time": "H+3",
                "priority": "HAUTE",
                "action": "Cold email B2B — 50 PME ciblées",
                "why": "Pages Jaunes + scraping + Gmail OAuth actif → pipeline immédiat",
                "how": "Secteurs: PME locales, restaurants, artisans, professions libérales",
                "revenue_impact": "Taux réponse ~5% → 2-3 deals × 5000€ = 10 000-15 000€",
            })

        # H6 — WhatsApp
        if "whatsapp_outreach" in channels:
            plan.append({
                "time": "H+6",
                "priority": "MOYENNE",
                "action": "Outreach WhatsApp — réseau local Polynésie",
                "why": "WhatsApp Business configuré. En PF, c'est le canal de confiance #1",
                "how": "Contacter 20 décideurs locaux avec message personnalisé + lien PayPal",
                "revenue_impact": "Conversion locale élevée (confiance) → 3-5 deals rapides",
            })

        # H12 — Follow-up
        plan.append({
            "time": "H+12",
            "priority": "HAUTE",
            "action": "Premier cycle follow-up",
            "why": "80% des deals se concluent après le 3ème contact",
            "how": "Relancer tous les prospects contactés à H+3 qui n'ont pas répondu",
            "revenue_impact": "+30% de taux de conversion sur le pipeline existant",
        })

        # H24 — Bilan + accélération
        plan.append({
            "time": "H+24",
            "priority": "HAUTE",
            "action": "Bilan 24H + ajustement",
            "why": "Vérifier l'objectif 15 000€. Si en dessous → activer canal suivant",
            "how": "GET /revenue/pipeline pour voir les deals. Intensifier le canal qui performe",
            "revenue_impact": "Corrections en temps réel pour tenir l'objectif 60k€/72H",
        })

        return plan

    def get_sprint_status(self) -> Dict:
        """Statut temps réel du sprint."""
        if not self._start_time:
            return {"started": False}

        elapsed_h = (time.time() - self._start_time) / 3600
        phase = "H24" if elapsed_h < 24 else "H48" if elapsed_h < 48 else "H72"
        target = SPRINT_TARGETS[phase]
        progress_pct = round(self._total_won / max(target, 1) * 100, 1)

        return {
            "started": True,
            "elapsed_hours": round(elapsed_h, 1),
            "phase": phase,
            "target_eur": target,
            "won_eur": round(self._total_won),
            "pipeline_eur": round(self._total_pipeline),
            "progress_pct": progress_pct,
            "on_track": self._total_won >= target * 0.7,
            "actions_taken": len(self._actions_taken),
        }

    def get_offers(self) -> List[Dict]:
        """Retourne les offres avec liens de paiement prêts."""
        paypal_base = _gs("PAYPAL_ME_URL", "https://www.paypal.me/Myking987")
        offers = []
        for offer in HIGH_VALUE_OFFERS:
            o = dict(offer)
            o["paypal_url"] = f"{paypal_base.rstrip('/')}/{offer['price']}"
            o["revolut_url"] = _gs("REVOLUT_ME_URL", "")
            o["whatsapp_msg"] = (
                f"Bonjour ! Je suis intéressé par votre offre "
                f"'{offer['title']}' à {offer['price']}€. "
                f"Pouvez-vous me contacter ? +68989559088"
            )
            offers.append(o)
        return offers


# ── Singleton ────────────────────────────────────────────────────────────────
_sprint: Optional[RevenueSprint] = None
_sprint_lock = threading.Lock()

def get_revenue_sprint() -> RevenueSprint:
    global _sprint
    if _sprint is None:
        with _sprint_lock:
            if _sprint is None:
                _sprint = RevenueSprint()
    return _sprint
