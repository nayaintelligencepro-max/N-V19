"""
NAYA V19.3 — Unified multi-channel outreach dispatcher.

One entrypoint for every outbound touch (email / WhatsApp / Telegram) and for
notifying the owner on critical events (contract signed, closing call booked).

All sends are gated by config.production_flags.flags so accidental blasts are
impossible in dev. When a flag is OFF or credentials are missing, the dispatcher
logs & returns status="skipped" — it never raises on caller.
"""
from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from typing import Dict, Optional

from config.production_flags import flags

log = logging.getLogger("NAYA.Outreach.Dispatcher")


# ═══════════════════════════════════════════════════════════════════════════
# Prospect container
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class OutreachProspect:
    name: str
    company: str
    sector: str
    email: Optional[str] = None
    phone_e164: Optional[str] = None  # +33612345678
    decision_maker_title: str = ""
    pain_one_liner: str = ""
    offer_tier: str = "TIER1"         # TIER1=1k-5k, TIER2=5k-20k, etc.
    offer_price_eur: int = 1000
    owner_first_name: str = "Stéphanie"
    extras: Dict[str, str] = field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════════════════
# Touch templates (short, impactful, differentiating, non-spammy)
# ═══════════════════════════════════════════════════════════════════════════

TOUCH_TEMPLATES: Dict[int, Dict[str, str]] = {
    1: {  # J0 — Email hook sur signal détecté
        "channel": "email",
        "subject": "{company} — {pain_hook}",
        "body": (
            "Bonjour {first_name},\n\n"
            "J'ai vu le signal {signal_short} chez {company}. "
            "Nous aidons des {role_plural} à {outcome_one_line} en moins de "
            "{timeframe}, sans réécrire l'existant.\n\n"
            "Un échange de 12 min cette semaine, jeudi ou vendredi ?\n\n"
            "{owner_first_name}"
        ),
    },
    3: {  # J5 — Email angle valeur
        "channel": "email",
        "subject": "Re: {company} — cas {sector_short} comparable",
        "body": (
            "Bonjour {first_name},\n\n"
            "Cas récent (anonymisé, même secteur que {company}) : "
            "{proof_one_liner}. Livrable en {timeframe}, pas un audit de 200 pages "
            "— une trajectoire actionnable.\n\n"
            "12 min cette semaine pour voir si c'est transposable ?\n\n"
            "{owner_first_name}"
        ),
    },
    5: {  # J12 — Email objection anticipée
        "channel": "email",
        "subject": "{company} — un angle auquel personne ne pense",
        "body": (
            "Bonjour {first_name},\n\n"
            "La plupart attaquent {company} sur le sujet {common_angle}. "
            "Nous prenons l'angle inverse : {discrete_angle}. Résultat habituel : "
            "{outcome_one_line}.\n\n"
            "Un créneau de 12 min cette semaine ?\n\n"
            "{owner_first_name}"
        ),
    },
    7: {  # J21 — Email final fermeture bienveillante
        "channel": "email",
        "subject": "{company} — je ferme le dossier",
        "body": (
            "Bonjour {first_name},\n\n"
            "Sans retour, je ferme le dossier proprement. Un simple \"pas "
            "maintenant\" me suffit et je vous rouvrirai au bon moment.\n\n"
            "{owner_first_name}"
        ),
    },
    2: {  # J2 — WhatsApp court
        "channel": "whatsapp",
        "body": (
            "Bonjour {first_name}, {owner_first_name} / NAYA. "
            "Signal {signal_short} chez {company} : on a une approche "
            "« {discrete_angle_short} ». 12 min en visio cette semaine ?"
        ),
    },
    4: {  # J8 — WhatsApp question ouverte
        "channel": "whatsapp",
        "body": (
            "{first_name}, une seule question : sur {pain_hook_short}, "
            "qu'est-ce qui vous empêcherait d'agir avant {quarter} ?"
        ),
    },
    6: {  # J16 — LinkedIn/Telegram message vidéo-like
        "channel": "linkedin",
        "body": (
            "Bonjour {first_name}, {owner_first_name} / NAYA. "
            "Courte vidéo (60s) sur {company} et {pain_hook_short} : "
            "{video_link}\n\n"
            "Si l'angle vous parle, 12 min cette semaine ?"
        ),
    },
}


def _default_context(prospect: OutreachProspect) -> Dict[str, str]:
    return {
        "first_name": prospect.name.split()[0] if prospect.name else "",
        "company": prospect.company or "",
        "role_plural": f"{prospect.decision_maker_title}s" if prospect.decision_maker_title else "décideurs",
        "sector_short": prospect.sector or "industrie",
        "signal_short": prospect.pain_one_liner or "récent sur votre secteur",
        "pain_hook": prospect.pain_one_liner or "point de friction récent",
        "pain_hook_short": (prospect.pain_one_liner or "votre enjeu")[:60],
        "outcome_one_line": "sécuriser la trajectoire NIS2 sans stopper la production",
        "timeframe": "6 semaines",
        "proof_one_liner": "–38% de surface d'exposition OT, 0 downtime",
        "common_angle": "certification ISO",
        "discrete_angle": "cartographie réelle des automates exposés",
        "discrete_angle_short": "cartographie réelle",
        "quarter": "T+1",
        "video_link": os.environ.get("OUTREACH_VIDEO_URL", "https://naya.ai/demo-60s"),
        "owner_first_name": prospect.owner_first_name,
    }


def _render(tpl: str, ctx: Dict[str, str]) -> str:
    try:
        return tpl.format(**ctx)
    except KeyError:
        return tpl


# ═══════════════════════════════════════════════════════════════════════════
# Channel adapters
# ═══════════════════════════════════════════════════════════════════════════

def _send_email(to: str, subject: str, body: str, to_name: str = "") -> Dict[str, str]:
    if not flags.outreach_email:
        return {"status": "skipped", "reason": "ENABLE_OUTREACH_EMAIL=false"}
    if not to:
        return {"status": "skipped", "reason": "missing to email"}
    try:
        from NAYA_CORE.integrations.sendgrid_integration import get_sendgrid
        sg = get_sendgrid()
    except Exception as e:
        log.warning("SendGrid not importable: %s", e)
        return {"status": "error", "reason": f"import:{e}"}
    if not sg.available:
        return {"status": "skipped", "reason": "sendgrid not configured"}
    try:
        body_html = "<p>" + body.replace("\n\n", "</p><p>").replace("\n", "<br>") + "</p>"
        res = sg.send(
            to_email=to,
            subject=subject,
            body_html=body_html,
            body_text=body,
            to_name=to_name,
            categories=["outreach"],
        )
        log.info("[OUTREACH/email] → %s subject=%r", to, subject[:60])
        return {
            "status": "sent" if res.sent else "error",
            "provider": "sendgrid",
            "message_id": res.message_id,
            "error": res.error,
        }
    except Exception as e:
        log.warning("SendGrid send failed: %s", e)
        return {"status": "error", "reason": str(e)[:80]}


def _send_whatsapp(phone_e164: str, body: str) -> Dict[str, str]:
    if not flags.outreach_whatsapp:
        return {"status": "skipped", "reason": "ENABLE_OUTREACH_WHATSAPP=false"}
    if not phone_e164:
        return {"status": "skipped", "reason": "no phone"}
    try:
        from NAYA_CORE.integrations.whatsapp_integration import get_whatsapp_engine
        wa = get_whatsapp_engine()
        res = wa.send_text(phone_e164, body)
        log.info("[OUTREACH/whatsapp] → %s", phone_e164)
        return {"status": res.get("status", "unknown"), **res}
    except Exception as e:
        log.warning("WhatsApp send failed: %s", e)
        return {"status": "error", "reason": str(e)[:80]}


def _send_telegram_owner(body: str) -> Dict[str, str]:
    """Send a DM to the owner's Telegram chat (notifications)."""
    if not flags.outreach_telegram:
        return {"status": "skipped", "reason": "ENABLE_OUTREACH_TELEGRAM=false"}
    try:
        from NAYA_CORE.integrations.telegram_notifier import get_notifier
        notifier = get_notifier()
        notifier.send(body)
        return {"status": "queued", "provider": "telegram"}
    except Exception as e:
        log.warning("Telegram send failed: %s", e)
        return {"status": "error", "reason": str(e)[:80]}


def _log_linkedin_stub(prospect: OutreachProspect, body: str) -> Dict[str, str]:
    """LinkedIn doesn't have an official send API for cold DMs. We log the rendered
    message to data/outreach/linkedin_queue.jsonl for manual processing by the owner."""
    try:
        from pathlib import Path
        import json
        p = Path("data/outreach/linkedin_queue.jsonl")
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({
                "ts": int(time.time()),
                "company": prospect.company,
                "name": prospect.name,
                "body": body,
            }, ensure_ascii=False) + "\n")
        return {"status": "queued", "provider": "linkedin-manual",
                "hint": "Processed manually via LinkedIn UI / Sales Navigator."}
    except Exception as e:
        return {"status": "error", "reason": str(e)[:80]}


# ═══════════════════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════════════════

def dispatch_touch(prospect: OutreachProspect, touch_number: int) -> Dict[str, str]:
    """Dispatch one touch (1..7) through its canonical channel."""
    tpl = TOUCH_TEMPLATES.get(touch_number)
    if not tpl:
        return {"status": "error", "reason": f"unknown touch {touch_number}"}
    ctx = _default_context(prospect)
    ctx.update(prospect.extras)
    channel = tpl["channel"]
    body = _render(tpl["body"], ctx)

    if channel == "email":
        subject = _render(tpl.get("subject", ""), ctx)
        return _send_email(prospect.email or "", subject, body, to_name=prospect.name)
    if channel == "whatsapp":
        return _send_whatsapp(prospect.phone_e164 or "", body)
    if channel == "linkedin":
        return _log_linkedin_stub(prospect, body)
    return {"status": "error", "reason": f"unknown channel {channel}"}


def notify_contract_signed(
    client_company: str, amount_eur: float, contract_id: str, signed_by: str = ""
) -> Dict[str, str]:
    """Owner-facing notification: a contract was just signed."""
    msg = (
        "✍️ <b>CONTRAT SIGNÉ</b>\n"
        f"Client: {client_company}\n"
        f"Montant: {amount_eur:,.0f}€\n"
        f"ID: {contract_id}\n"
        + (f"Signataire: {signed_by}\n" if signed_by else "")
        + f"⏰ {time.strftime('%d/%m %H:%M')}"
    )
    return _send_telegram_owner(msg)


def notify_closing_call_scheduled(
    prospect_name: str, company: str, scheduled_at: str, meeting_url: str = ""
) -> Dict[str, str]:
    """Owner-facing notification: a closing call is scheduled."""
    msg = (
        "📞 <b>CALL DE CLOTURE PROGRAMMÉ</b>\n"
        f"Prospect: {prospect_name}\n"
        f"Entreprise: {company}\n"
        f"Quand: {scheduled_at}\n"
        + (f"Lien: {meeting_url}\n" if meeting_url else "")
        + f"⏰ {time.strftime('%d/%m %H:%M')}"
    )
    return _send_telegram_owner(msg)


def notify_positive_reply(prospect_name: str, company: str, reply_excerpt: str) -> Dict[str, str]:
    msg = (
        "💬 <b>RÉPONSE POSITIVE</b>\n"
        f"Prospect: {prospect_name} ({company})\n"
        f"Extrait: {reply_excerpt[:200]}\n"
        f"⏰ {time.strftime('%d/%m %H:%M')}"
    )
    return _send_telegram_owner(msg)


def notify_payment_received(client: str, amount_eur: float, method: str = "stripe") -> Dict[str, str]:
    msg = (
        "💰 <b>PAIEMENT REÇU</b>\n"
        f"Client: {client}\nMontant: {amount_eur:,.2f}€\n"
        f"Via: {method.upper()}\n⏰ {time.strftime('%d/%m %H:%M')}"
    )
    return _send_telegram_owner(msg)


__all__ = [
    "OutreachProspect",
    "dispatch_touch",
    "notify_contract_signed",
    "notify_closing_call_scheduled",
    "notify_positive_reply",
    "notify_payment_received",
    "TOUCH_TEMPLATES",
]
