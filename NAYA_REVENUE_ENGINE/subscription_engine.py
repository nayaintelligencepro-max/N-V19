"""
NAYA SUBSCRIPTION ENGINE v1
Facturation récurrente, usage-based metering, invoicing automatique
+300% revenue via MRR (Monthly Recurring Revenue)
"""

import asyncio, logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

log = logging.getLogger("NAYA.SUBSCRIPTIONS")

# ═══════════════════════════════════════════════════════════════════════════
# 1. PLAN DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════

class SubscriptionTier(Enum):
    FREE = "free"           # 100 API calls/month
    PRO = "pro"             # $99/month - unlimited calls + priority
    ENTERPRISE = "enterprise"  # $999/month - custom + SLA

@dataclass
class PlanConfig:
    tier: SubscriptionTier
    price_usd: float
    billing_cycle: str      # "monthly", "yearly", "usage"
    api_calls_limit: Optional[int]  # None = unlimited
    features: List[str]
    support_level: str      # "community", "email", "24/7"
    
    # Usage-based overages
    overage_price_per_1k_calls: float = 0.10

PLANS = {
    SubscriptionTier.FREE: PlanConfig(
        tier=SubscriptionTier.FREE,
        price_usd=0,
        billing_cycle="monthly",
        api_calls_limit=100,
        features=["basic_prospecting", "email_hunting", "webhook_api"],
        support_level="community",
        overage_price_per_1k_calls=0.50  # Expensive overages encourage upgrade
    ),
    SubscriptionTier.PRO: PlanConfig(
        tier=SubscriptionTier.PRO,
        price_usd=99,
        billing_cycle="monthly",
        api_calls_limit=None,  # Unlimited
        features=["advanced_hunting", "crypto_payments", "a_b_testing", 
                  "feedback_loops", "priority_queue"],
        support_level="email",
        overage_price_per_1k_calls=0.0  # No overages, truly unlimited
    ),
    SubscriptionTier.ENTERPRISE: PlanConfig(
        tier=SubscriptionTier.ENTERPRISE,
        price_usd=999,
        billing_cycle="monthly",
        api_calls_limit=None,
        features=["all_features", "white_label", "sso", "sla_99_9", 
                  "dedicated_account", "monthly_strategy_call"],
        support_level="24/7",
        overage_price_per_1k_calls=0.0
    )
}

# ═══════════════════════════════════════════════════════════════════════════
# 2. SUBSCRIPTION DATA MODEL
# ═══════════════════════════════════════════════════════════════════════════

class SubscriptionStatus(Enum):
    TRIAL = "trial"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"

@dataclass
class Subscription:
    subscription_id: str
    user_id: str
    tier: SubscriptionTier
    status: SubscriptionStatus
    created_at: datetime
    current_period_start: datetime
    current_period_end: datetime
    
    # Payment (V19.3: PayPal/Deblock uniquement, Stripe retiré)
    payment_subscription_id: Optional[str] = None
    payment_method_id: Optional[str] = None
    
    # Usage tracking
    api_calls_this_period: int = 0
    api_calls_limit: Optional[int] = None
    
    # Dates
    trial_ends: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    
    def is_trial_active(self) -> bool:
        return self.trial_ends and datetime.now(timezone.utc) < self.trial_ends
    
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.current_period_end
    
    def api_calls_remaining(self) -> Optional[int]:
        if self.api_calls_limit is None:
            return None
        return max(0, self.api_calls_limit - self.api_calls_this_period)
    
    def usage_percentage(self) -> float:
        if self.api_calls_limit is None:
            return 0.0
        return (self.api_calls_this_period / self.api_calls_limit) * 100

# ═══════════════════════════════════════════════════════════════════════════
# 3. USAGE METERING & TRACKING
# ═══════════════════════════════════════════════════════════════════════════

class UsageTracker:
    """Track API calls, detect overages, suggest upgrades"""
    
    def __init__(self):
        self.usage_events: List[Dict[str, Any]] = []
    
    async def track_api_call(self, 
                            subscription_id: str,
                            endpoint: str,
                            cost: float = 1.0) -> bool:
        """Record API call usage"""
        self.usage_events.append({
            "subscription_id": subscription_id,
            "endpoint": endpoint,
            "cost": cost,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        log.debug(f"API call tracked: {subscription_id} → {endpoint}")
        return True
    
    async def get_usage_this_period(self, subscription_id: str) -> Dict[str, Any]:
        """Get usage stats for current billing period"""
        events = [e for e in self.usage_events 
                 if e["subscription_id"] == subscription_id]
        
        total_calls = len(events)
        total_cost = sum(e["cost"] for e in events)
        
        endpoints = {}
        for e in events:
            ep = e["endpoint"]
            if ep not in endpoints:
                endpoints[ep] = 0
            endpoints[ep] += 1
        
        return {
            "total_calls": total_calls,
            "total_cost": total_cost,
            "by_endpoint": endpoints,
            "events_count": len(events)
        }
    
    async def check_overage(self, 
                           subscription: Subscription) -> Dict[str, Any]:
        """Check if usage exceeded limit"""
        usage = await self.get_usage_this_period(subscription.subscription_id)
        
        if subscription.api_calls_limit is None:
            return {"overage": False, "message": "Unlimited plan"}
        
        calls = usage["total_calls"]
        limit = subscription.api_calls_limit
        
        if calls > limit:
            overage_calls = calls - limit
            overage_cost = (overage_calls / 1000) * subscription.api_calls_limit
            
            return {
                "overage": True,
                "overage_calls": overage_calls,
                "overage_cost_usd": overage_cost,
                "message": f"You exceeded limit by {overage_calls} calls (${overage_cost:.2f})"
            }
        
        return {
            "overage": False,
            "remaining": limit - calls,
            "percentage_used": (calls / limit) * 100
        }

# ═══════════════════════════════════════════════════════════════════════════
# 4. BILLING ENGINE
# ═══════════════════════════════════════════════════════════════════════════

class BillingEngine:
    """Handle invoicing, payment collection, renewals.

    V19.3 : PayPal.me + Deblock.me uniquement (Polynésie française).
    Pas de charge automatique — le client reçoit un lien de paiement à cliquer.
    """

    def __init__(self):
        self.paypal_url = os.getenv("PAYPAL_ME_URL", "https://www.paypal.me/Myking987")
        self.deblock_url = os.getenv("DEBLOCK_ME_URL", "")
        self.invoices: Dict[str, Dict] = {}

    async def create_invoice(self,
                            subscription: Subscription,
                            overage_cost: float = 0) -> str:
        """Generate invoice for period"""
        plan = PLANS[subscription.tier]
        total = plan.price_usd + overage_cost

        invoice_data = {
            "invoice_id": f"INV-{subscription.subscription_id}-{datetime.now().strftime('%Y%m%d')}",
            "subscription_id": subscription.subscription_id,
            "user_id": subscription.user_id,
            "period_start": subscription.current_period_start.isoformat(),
            "period_end": subscription.current_period_end.isoformat(),
            "plan_price": plan.price_usd,
            "overages": overage_cost,
            "total": total,
            "status": "draft",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "due_date": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        }

        self.invoices[invoice_data["invoice_id"]] = invoice_data
        log.info(f"✅ Invoice created: {invoice_data['invoice_id']} (${total:.2f})")
        return invoice_data["invoice_id"]

    async def send_invoice(self, invoice_id: str, email: str) -> bool:
        """Send invoice PDF to customer via SendGrid."""
        if invoice_id not in self.invoices:
            return False

        invoice = self.invoices[invoice_id]

        try:
            from NAYA_CORE.integrations.sendgrid_integration import get_sendgrid
            sg = get_sendgrid()
            amount = invoice.get("total", 0)
            # PayPal.me format: /username/AMOUNTEUR
            paypal_link = f"{self.paypal_url}/{amount:.0f}EUR?note={invoice_id}"
            body = (
                f"Votre facture {invoice_id}\n\n"
                f"Montant : {amount:.2f} EUR\n"
                f"Lien de paiement PayPal : {paypal_link}\n"
            )
            if self.deblock_url:
                body += f"Lien Deblock (alternative) : {self.deblock_url}\n"
            if hasattr(sg, "send_email"):
                sg.send_email(to=email, subject=f"Facture NAYA {invoice_id}", body=body)
            invoice["status"] = "sent"
            log.info(f"📧 Invoice sent to {email}: {invoice_id}")
            return True
        except Exception as exc:
            log.warning(f"Invoice send failed: {exc}")
            invoice["status"] = "sent_failed"
            return False

    async def charge_subscription(self,
                                 subscription: Subscription,
                                 overage_cost: float = 0) -> Dict[str, Any]:
        """
        Crée un lien de paiement et l'envoie au client.
        V19.3 : pas de charge automatique (PayPal.me / Deblock.me n'ont pas d'API de prélèvement).
        Le client reçoit le lien et paye manuellement → webhook confirme le paiement.
        """
        plan = PLANS[subscription.tier]
        total = plan.price_usd + overage_cost

        try:
            invoice_id = await self.create_invoice(subscription, overage_cost)
            paypal_link = f"{self.paypal_url}/{total:.0f}EUR?note={invoice_id}"

            # Envoyer la facture par email
            user_email = getattr(subscription, "user_email", None) or subscription.user_id
            await self.send_invoice(invoice_id, user_email)

            # Marquer la souscription en attente de paiement
            subscription.payment_subscription_id = invoice_id

            return {
                "success": True,
                "invoice_id": invoice_id,
                "payment_link": paypal_link,
                "deblock_link": self.deblock_url,
                "amount": total,
                "status": "awaiting_payment",
            }
        except Exception as exc:
            log.warning(f"❌ Charge subscription failed: {exc}")
            subscription.status = SubscriptionStatus.PAST_DUE
            return {"success": False, "error": str(exc)}
    
    async def process_renewals(self, subscriptions: List[Subscription]) -> Dict[str, Any]:
        """Process all expired subscriptions"""
        results = {"renewed": 0, "failed": 0, "revenue": 0}
        
        for sub in subscriptions:
            if sub.is_expired() and sub.status == SubscriptionStatus.ACTIVE:
                success = await self.charge_subscription(sub)
                if success.get("success"):
                    results["renewed"] += 1
                    results["revenue"] += success.get("amount", 0)
                else:
                    results["failed"] += 1
        
        log.info(f"✅ Renewals: {results['renewed']} success, {results['failed']} failed (${results['revenue']:.2f})")
        return results

# ═══════════════════════════════════════════════════════════════════════════
# 5. SUBSCRIPTION MANAGER
# ═══════════════════════════════════════════════════════════════════════════

class SubscriptionManager:
    """Unified subscription management"""
    
    def __init__(self):
        self.subscriptions: Dict[str, Subscription] = {}
        self.usage_tracker = UsageTracker()
        self.billing_engine = BillingEngine()
    
    async def create_subscription(self,
                                 user_id: str,
                                 tier: SubscriptionTier,
                                 trial_days: int = 14) -> Subscription:
        """Create new subscription with trial"""
        plan = PLANS[tier]
        now = datetime.now(timezone.utc)
        
        subscription = Subscription(
            subscription_id=f"sub_{user_id}_{int(now.timestamp())}",
            user_id=user_id,
            tier=tier,
            status=SubscriptionStatus.TRIAL if trial_days > 0 else SubscriptionStatus.ACTIVE,
            created_at=now,
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
            trial_ends=now + timedelta(days=trial_days) if trial_days > 0 else None,
            api_calls_limit=plan.api_calls_limit
        )
        
        self.subscriptions[subscription.subscription_id] = subscription
        log.info(f"✅ Subscription created: {user_id} → {tier.value} (trial: {trial_days}d)")
        return subscription
    
    async def upgrade_subscription(self,
                                  subscription_id: str,
                                  new_tier: SubscriptionTier) -> bool:
        """Upgrade to higher tier"""
        if subscription_id not in self.subscriptions:
            return False
        
        sub = self.subscriptions[subscription_id]
        old_tier = sub.tier
        
        # Prorate: calculate credit for unused days
        days_remaining = (sub.current_period_end - datetime.now(timezone.utc)).days
        old_plan = PLANS[old_tier]
        new_plan = PLANS[new_tier]
        
        daily_difference = (new_plan.price_usd - old_plan.price_usd) / 30
        upgrade_cost = daily_difference * days_remaining
        
        sub.tier = new_tier
        sub.api_calls_limit = new_plan.api_calls_limit
        
        log.info(f"✅ Upgraded: {sub.user_id} {old_tier.value}→{new_tier.value} (+${upgrade_cost:.2f})")
        return True
    
    async def cancel_subscription(self, subscription_id: str) -> bool:
        """Cancel subscription (effective end of period)"""
        if subscription_id not in self.subscriptions:
            return False
        
        sub = self.subscriptions[subscription_id]
        sub.status = SubscriptionStatus.CANCELLED
        sub.cancelled_at = datetime.now(timezone.utc)
        
        log.info(f"🚫 Cancelled: {sub.user_id}")
        return True
    
    async def track_usage(self, subscription_id: str, endpoint: str):
        """Track API call for metering"""
        await self.usage_tracker.track_api_call(subscription_id, endpoint)
    
    async def get_subscription_status(self, subscription_id: str) -> Dict[str, Any]:
        """Get detailed subscription status"""
        if subscription_id not in self.subscriptions:
            return {"error": "Not found"}
        
        sub = self.subscriptions[subscription_id]
        usage = await self.usage_tracker.get_usage_this_period(subscription_id)
        overage = await self.usage_tracker.check_overage(sub)
        
        return {
            "tier": sub.tier.value,
            "status": sub.status.value,
            "trial_active": sub.is_trial_active(),
            "period_end": sub.current_period_end.isoformat(),
            "usage": usage,
            "overage": overage,
            "api_calls_remaining": sub.api_calls_remaining()
        }
    
    async def process_monthly_billing(self) -> Dict[str, Any]:
        """Process all monthly renewals"""
        active_subs = [s for s in self.subscriptions.values() 
                      if s.status == SubscriptionStatus.ACTIVE]
        
        # Check for renewals
        renewals_result = await self.billing_engine.process_renewals(active_subs)
        
        # Check for trials ending
        trials_ending = [s for s in active_subs 
                        if s.is_trial_active() and 
                        (s.trial_ends - datetime.now(timezone.utc)).days <= 3]
        
        for sub in trials_ending:
            log.warning(f"⚠️ Trial ending in 3 days: {sub.user_id}")
        
        return {
            "billing_results": renewals_result,
            "trials_ending_soon": len(trials_ending)
        }

# ═══════════════════════════════════════════════════════════════════════════
# 6. SINGLETON
# ═══════════════════════════════════════════════════════════════════════════

import os

_subscription_manager: Optional['SubscriptionManager'] = None

def get_subscription_manager() -> SubscriptionManager:
    global _subscription_manager
    if _subscription_manager is None:
        _subscription_manager = SubscriptionManager()
        log.info("✅ Subscription Manager initialized")
    return _subscription_manager
