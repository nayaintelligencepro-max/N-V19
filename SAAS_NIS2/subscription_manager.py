"""
NAYA V19.3 — Subscription Manager
Gestion abonnements SaaS NIS2 (500 EUR/mois) et IEC 62443 Portal (2 000 EUR/mois).
Intégration PayPal + Deblock + webhooks paiement (Stripe retiré — non dispo Polynésie).
"""
import json
import logging
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

log = logging.getLogger("NAYA.SAAS_NIS2.SUBSCRIPTION")

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "saas_nis2"
DATA_DIR.mkdir(parents=True, exist_ok=True)

PLANS = {
    "nis2_freemium": {"name": "NIS2 Freemium", "price_eur": 0, "features": ["score_only"]},
    "nis2_starter": {"name": "NIS2 Starter", "price_eur": 500, "features": ["full_report", "pdf", "recommendations"]},
    "nis2_pro": {"name": "NIS2 Pro", "price_eur": 1200, "features": ["full_report", "pdf", "api_access", "unlimited_scans"]},
    "iec62443_portal": {"name": "IEC 62443 Portal", "price_eur": 2000, "features": ["iec62443", "roadmap", "tracking", "api"]},
    "naya_api": {"name": "NAYA API Marketplace", "price_eur": 300, "features": ["pain_hunter_api", "audit_api", "offer_api"]},
}


@dataclass
class Subscription:
    """Abonnement client SaaS."""
    subscription_id: str
    company: str
    contact_email: str
    plan: str
    price_eur: int
    status: str  # active|pending|cancelled|trial
    payment_method: str  # deblok|paypal
    start_date: str
    end_date: str
    mrr_contribution: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def is_active(self) -> bool:
        return self.status == "active"


class SubscriptionManager:
    """Gestionnaire d'abonnements SaaS — calcul MRR en temps réel."""

    def __init__(self):
        self._subscriptions: Dict[str, Subscription] = {}
        self._load_data()
        log.info("✅ SubscriptionManager initialisé (%d subscriptions)", len(self._subscriptions))

    def _data_path(self) -> Path:
        return DATA_DIR / "subscriptions.json"

    def _load_data(self) -> None:
        p = self._data_path()
        if p.exists():
            try:
                raw = json.loads(p.read_text())
                for k, v in raw.items():
                    self._subscriptions[k] = Subscription(**v)
            except Exception as exc:
                log.warning("Subscription data load error: %s", exc)

    def _save_data(self) -> None:
        p = self._data_path()
        try:
            p.write_text(json.dumps(
                {k: v.to_dict() for k, v in self._subscriptions.items()},
                ensure_ascii=False, indent=2,
            ))
        except Exception as exc:
            log.warning("Subscription save error: %s", exc)

    def get_plans(self) -> Dict:
        return PLANS

    def create_subscription(
        self,
        company: str,
        contact_email: str,
        plan: str,
        payment_method: str = "paypal",
    ) -> Subscription:
        if plan not in PLANS:
            raise ValueError(f"Plan inconnu: {plan}")
        plan_info = PLANS[plan]
        start = datetime.now()
        end = start + timedelta(days=30)
        sub = Subscription(
            subscription_id=str(uuid.uuid4()),
            company=company,
            contact_email=contact_email,
            plan=plan,
            price_eur=plan_info["price_eur"],
            status="active" if plan_info["price_eur"] == 0 else "pending",
            payment_method=payment_method,
            start_date=start.isoformat(),
            end_date=end.isoformat(),
            mrr_contribution=plan_info["price_eur"],
        )
        self._subscriptions[sub.subscription_id] = sub
        self._save_data()
        log.info(
            "Subscription %s: %s — plan=%s price=%d EUR",
            sub.subscription_id, company, plan, sub.price_eur,
        )
        return sub

    def activate_subscription(self, subscription_id: str) -> bool:
        sub = self._subscriptions.get(subscription_id)
        if not sub:
            return False
        sub.status = "active"
        self._save_data()
        log.info("Subscription %s activated", subscription_id)
        return True

    def cancel_subscription(self, subscription_id: str) -> bool:
        sub = self._subscriptions.get(subscription_id)
        if not sub:
            return False
        sub.status = "cancelled"
        self._save_data()
        return True

    def handle_payment_webhook(self, subscription_id: str, event: str, amount_eur: int) -> Dict:
        """Traitement webhook paiement (PayPal/Deblock)."""
        sub = self._subscriptions.get(subscription_id)
        if not sub:
            log.warning("Webhook: subscription %s not found", subscription_id)
            return {"success": False, "error": "Subscription not found"}
        if event == "payment_succeeded":
            sub.status = "active"
            sub.end_date = (datetime.now() + timedelta(days=30)).isoformat()
            self._save_data()
            log.info("Payment webhook: %s renewed for %d EUR", subscription_id, amount_eur)
            return {"success": True, "status": "active", "renewed_until": sub.end_date}
        if event == "payment_failed":
            sub.status = "pending"
            self._save_data()
            return {"success": False, "status": "pending"}
        return {"success": True, "event": event}

    def get_mrr(self) -> Dict:
        """Calcule le MRR (Monthly Recurring Revenue) temps réel."""
        active = [s for s in self._subscriptions.values() if s.status == "active"]
        mrr = sum(s.mrr_contribution for s in active)
        by_plan: Dict[str, int] = {}
        for s in active:
            by_plan[s.plan] = by_plan.get(s.plan, 0) + s.mrr_contribution
        return {
            "mrr_eur": mrr,
            "arr_eur": mrr * 12,
            "active_subscriptions": len(active),
            "by_plan": by_plan,
            "target_m6_eur": 10_000,
            "progress_pct": round(mrr * 100 / 10_000, 1) if mrr > 0 else 0,
        }

    def list_subscriptions(self, status: Optional[str] = None) -> List[Subscription]:
        subs = list(self._subscriptions.values())
        if status:
            subs = [s for s in subs if s.status == status]
        return sorted(subs, key=lambda s: s.created_at, reverse=True)


# ── Singleton ─────────────────────────────────────────────────────────────────
_manager: Optional[SubscriptionManager] = None


def get_subscription_manager() -> SubscriptionManager:
    global _manager
    if _manager is None:
        _manager = SubscriptionManager()
    return _manager
