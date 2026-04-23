"""
NAYA V19 — Money Notifier
Alertes Telegram ultra-actionnables avec boutons inline.
Chaque message = une action précise à faire maintenant.
"""
import os, logging, time, json
from typing import Dict, Optional, List
from datetime import datetime, timezone
log = logging.getLogger("NAYA.MONEY")

def _gs(k, d=""):
    try:
        from SECRETS.secrets_loader import get_secret
        return get_secret(k,d) or d
    except: return os.environ.get(k,d)

class MoneyNotifier:
    def __init__(self): self._sent = 0; self._failed = 0

    @property
    def token(self) -> str: return _gs("TELEGRAM_BOT_TOKEN")
    @property
    def chat_id(self) -> str: return _gs("TELEGRAM_CHAT_ID")
    @property
    def available(self) -> bool: return bool(self.token and self.chat_id)

    def _send(self, text: str, buttons: List[List[Dict]] = None) -> bool:
        """Envoie un message avec boutons inline optionnels."""
        if not self.available:
            log.info(f"[MONEY] (no telegram) {text[:80]}")
            return False
        try:
            import requests
            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": "HTML",
            }
            if buttons:
                payload["reply_markup"] = json.dumps({"inline_keyboard": buttons})
            r = requests.post(
                f"https://api.telegram.org/bot{self.token}/sendMessage",
                json=payload, timeout=10
            )
            ok = r.status_code == 200
            if ok: self._sent += 1
            else: self._failed += 1; log.warning(f"[MONEY] TG {r.status_code}: {r.text[:80]}")
            return ok
        except Exception as e:
            log.warning(f"[MONEY] {e}"); self._failed += 1; return False

    def alert_opportunity(self, prospect_dict: Dict, offer: Dict, approval_id: str) -> bool:
        """
        Alerte opportunité avec boutons:
        ✅ Approuver email  |  💳 Lien PayPal  |  ❌ Ignorer
        """
        company   = prospect_dict.get("company_name", prospect_dict.get("company","?"))
        city      = prospect_dict.get("city","")
        email     = prospect_dict.get("email","")
        pain_cost = float(prospect_dict.get("pain_annual_cost_eur", prospect_dict.get("pain_cost",0)))
        price     = float(offer.get("price", prospect_dict.get("offer_price_eur",0)))
        title     = offer.get("title", prospect_dict.get("offer_title","Service NAYA"))
        signals   = prospect_dict.get("pain_signals",[])
        priority  = prospect_dict.get("priority","HIGH")
        roi       = round(pain_cost/max(price,1), 1)
        monthly   = round(pain_cost/12)
        pid       = prospect_dict.get("id","?")

        icon = {"CRITICAL":"🔴","HIGH":"🟠","MEDIUM":"🟡"}.get(priority,"🟡")

        text = (
            f"{icon} <b>OPPORTUNITÉ {priority} — {price:,.0f}€</b>\n\n"
            f"🏢 <b>{company}</b>{f' ({city})' if city else ''}\n"
            f"📧 {email or 'email à trouver'}\n\n"
            f"💡 <b>Douleur:</b>\n" +
            "\n".join(f"• {s}" for s in signals[:3]) +
            f"\n\n💸 Coût annuel: <b>{pain_cost:,.0f}€/an</b>\n"
            f"🎯 Offre: <i>{title}</i>\n"
            f"💰 Prix: <b>{price:,.0f}€</b> (ROI ×{roi} client)\n"
            f"⚠️ Inaction: <b>{monthly:,.0f}€/mois perdus</b>\n\n"
            f"<b>➡️ Une action maintenant :</b>"
        )

        buttons = [[
            {"text": f"✅ Envoyer email", "callback_data": f"approve:{approval_id}"},
            {"text": f"💳 Lien PayPal {price:.0f}€", "callback_data": f"paypal:{pid}:{price:.0f}"},
        ],[
            {"text": "❌ Ignorer", "callback_data": f"skip:{pid}"},
            {"text": "📋 Voir pipeline", "callback_data": "pipeline"},
        ]]
        return self._send(text, buttons)

    def alert_payment_link_created(self, url: str, amount: float, client: str) -> bool:
        text = (
            f"💳 <b>LIEN PAIEMENT CRÉÉ — {amount:.0f}€</b>\n\n"
            f"👤 Client: {client}\n"
            f"🔗 <b>{url}</b>\n\n"
            f"<i>Montant pré-rempli — le client n'a qu'à cliquer et payer</i>\n\n"
            f"⏰ Dès réception → marquer WON dans le pipeline"
        )
        return self._send(text)

    def alert_won(self, deal: Dict) -> bool:
        revenue = float(deal.get("revenue_collected", deal.get("price", deal.get("offer_price",0))))
        company = deal.get("company", deal.get("company_profile","?"))
        text = (
            f"🏆 <b>DEAL WON — {revenue:,.0f}€ 💰</b>\n\n"
            f"🏢 {company}\n"
            f"💼 {deal.get('sector','').replace('_',' ')}\n"
            f"🎯 {deal.get('pain','').replace('_',' ')}\n\n"
            f"<b>L'argent est en route.</b>\n"
            f"<i>Prochaine étape: livrer → upsell → demander un témoignage</i>"
        )
        return self._send(text)

    def alert_pipeline_daily(self, summary: Dict) -> bool:
        deals   = summary.get("active_deals", summary.get("total_prospects",0))
        total   = summary.get("pipeline_total_eur", summary.get("pipeline_eur",0))
        won     = summary.get("won_total_eur", summary.get("revenue_won_eur",0))
        next_a  = summary.get("next_actions",[])

        actions_text = ""
        if next_a:
            actions_text = "\n⚡ <b>À faire maintenant:</b>\n" + \
                "\n".join(f"• {a.get('action',a) if isinstance(a,dict) else a}" for a in next_a[:3])

        text = (
            f"📊 <b>PIPELINE {datetime.now(timezone.utc).strftime('%d/%m')}</b>\n\n"
            f"💼 {deals} deals actifs\n"
            f"💰 Pipeline: <b>{total:,.0f}€</b>\n"
            f"✅ WON: <b>{won:,.0f}€</b>\n"
            f"{actions_text}\n\n"
            f"<i>NAYA V19 — autonome 24h/24</i>"
        )
        buttons = [[
            {"text":"📋 Pipeline complet","callback_data":"pipeline"},
            {"text":"🎯 Lancer hunt","callback_data":"hunt"},
        ]]
        return self._send(text, buttons)

    def alert_revenue_intel(self, directives: Dict) -> bool:
        top = directives.get("rationale",{}).get("top_sector","?")
        sectors = directives.get("focus_sectors",[])
        pains = directives.get("priority_pains",[])
        text = (
            f"🧠 <b>INTELLIGENCE REVENUS</b>\n\n"
            f"🎯 Top secteur: <b>{top.replace('_',' ')}</b>\n"
            f"📋 Focus: {', '.join(s.replace('_',' ') for s in sectors[:3])}\n"
            f"💡 Douleurs: {', '.join(p.replace('_',' ') for p in pains[:3])}\n\n"
            f"➡️ Concentrer la chasse sur ces cibles"
        )
        return self._send(text)

    def notify_boot(self, status_dict: Dict) -> bool:
        score   = status_dict.get("score","?")
        llm     = status_dict.get("active_llm","?")
        modules = status_dict.get("modules",0)
        text = (
            f"⚡ <b>NAYA V19 — OPÉRATIONNEL</b>\n\n"
            f"🔐 Clés: <b>{score}</b>\n"
            f"🧠 LLM: <b>{llm}</b>\n"
            f"🧩 Modules: <b>{modules}</b>\n\n"
            f"💰 Revenue Engine actif — chasse autonome démarrée\n"
            f"📱 Alertes Telegram actives\n\n"
            f"<i>Dashboard: /docs | Status: /secrets/status</i>"
        )
        buttons = [[
            {"text":"🎯 Lancer scan maintenant","callback_data":"hunt"},
            {"text":"📊 Pipeline","callback_data":"pipeline"},
        ]]
        return self._send(text, buttons)

    def get_stats(self) -> Dict:
        return {"available":self.available,"sent":self._sent,"failed":self._failed}

_mn: Optional[MoneyNotifier] = None
_mn_lock = __import__('threading').Lock()
def get_money_notifier() -> MoneyNotifier:
    global _mn
    if _mn is None:
        with _mn_lock:
            if _mn is None: _mn = MoneyNotifier()
    return _mn
