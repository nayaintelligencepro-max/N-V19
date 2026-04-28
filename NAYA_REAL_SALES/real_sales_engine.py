"""
NAYA REAL SALES ENGINE — Moteur de Ventes Réelles
═══════════════════════════════════════════════════════════════
Gère les ventes réelles avec paiements effectifs confirmés.
ZÉRO simulation. Chaque vente = argent réel encaissé.
"""
import json
import logging
import uuid
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, List, Any

log = logging.getLogger("NAYA.REAL_SALES")

ROOT = Path(__file__).resolve().parent.parent
REAL_SALES_DIR = ROOT / "data" / "real_sales"
REAL_SALES_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class RealSale:
    """Vente réelle avec paiement confirmé."""
    sale_id: str
    company: str
    contact: str
    email: str
    sector: str
    offer_title: str
    amount_eur: float
    payment_method: str  # paypal | deblock | bank_transfer
    payment_url: str
    payment_status: str  # pending | confirmed | failed
    payment_confirmed_at: Optional[str] = None
    invoice_id: Optional[str] = None
    contract_signed: bool = False
    created_at: str = ""
    day_number: int = 0  # Jour du challenge (1-10)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return asdict(self)


class RealSalesEngine:
    """
    Moteur de ventes réelles NAYA.
    Chaque vente nécessite une confirmation de paiement avant comptabilisation.
    """

    def __init__(self):
        self.ledger_path = REAL_SALES_DIR / "real_sales_ledger.json"
        self.sales: List[RealSale] = []
        self.require_webhook_proof = os.getenv("REAL_SALES_REQUIRE_WEBHOOK_PROOF", "1") == "1"
        self._load_ledger()
        log.info("✅ RealSalesEngine initialized - %d real sales loaded", len(self.sales))

    def _load_ledger(self) -> None:
        """Charge le ledger des ventes réelles."""
        if self.ledger_path.exists():
            try:
                data = json.loads(self.ledger_path.read_text())
                self.sales = [RealSale(**s) for s in data]
            except Exception as e:
                log.warning("Ledger load error: %s", e)
                self.sales = []

    def _save_ledger(self) -> None:
        """Sauvegarde le ledger de manière immutable."""
        try:
            data = [s.to_dict() for s in self.sales]
            self.ledger_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        except Exception as e:
            log.error("Ledger save error: %s", e)

    def create_sale(
        self,
        company: str,
        contact: str = "Contact NAYA",
        email: str = "contact@unknown.local",
        sector: str = "general",
        offer_title: str = "Offre NAYA",
        amount_eur: float = 1000,
        payment_method: str = "paypal",
        day_number: int = 0,
        **kwargs,
    ) -> RealSale:
        """
        Crée une nouvelle vente avec statut 'pending'.
        La vente n'est comptabilisée qu'après confirmation de paiement.
        """
        # Compatibilité appelants existants (api/scheduler)
        service_type = kwargs.get("service_type")
        payment_provider = kwargs.get("payment_provider")
        if payment_provider and not payment_method:
            payment_method = payment_provider
        if service_type and (not offer_title or offer_title == "Offre NAYA"):
            offer_title = f"NAYA Service — {service_type}"

        if amount_eur < 1000:
            raise ValueError(f"Montant {amount_eur} EUR < plancher 1000 EUR")

        sale_id = f"REAL_SALE_{uuid.uuid4().hex[:8].upper()}"

        # Générer payment URL selon la méthode
        if payment_method == "paypal":
            payment_url = f"https://www.paypal.me/Myking987/{amount_eur:.2f}?note={sale_id}"
        elif payment_method == "deblock":
            payment_url = f"https://www.deblock.me/pay/{sale_id}"
        else:
            payment_url = f"https://pay.naya-supreme.com/{sale_id}"

        invoice_id = f"INV_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:6].upper()}"

        sale = RealSale(
            sale_id=sale_id,
            company=company,
            contact=contact,
            email=email,
            sector=sector,
            offer_title=offer_title,
            amount_eur=amount_eur,
            payment_method=payment_method,
            payment_url=payment_url,
            payment_status="pending",
            invoice_id=invoice_id,
            day_number=day_number,
        )

        self.sales.append(sale)
        self._save_ledger()

        log.info(
            "💰 Vente créée: %s - %s - %.0f EUR - Status: PENDING",
            sale_id, company, amount_eur
        )

        return sale

    def create_sale_from_api(
        self,
        company: str,
        sector: str,
        amount_eur: float,
        service_type: str,
        payment_provider: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> RealSale:
        """Factory dédiée aux appels API pour éviter les incompatibilités de signature."""
        md = metadata or {}
        contact = str(md.get("contact") or md.get("contact_name") or "Contact NAYA")
        email = str(md.get("email") or md.get("contact_email") or "contact@unknown.local")
        offer_title = str(md.get("offer_title") or f"NAYA Service — {service_type}")
        day_number = int(md.get("day_number") or 0)
        return self.create_sale(
            company=company,
            contact=contact,
            email=email,
            sector=sector,
            offer_title=offer_title,
            amount_eur=amount_eur,
            payment_method=payment_provider,
            day_number=day_number,
            service_type=service_type,
            payment_provider=payment_provider,
        )

    def confirm_payment(
        self,
        sale_id: str,
        source: str = "manual",
        provider: Optional[str] = None,
        webhook_verified: bool = False,
    ) -> bool:
        """
        Confirme le paiement d'une vente.
        Cette méthode est appelée par le webhook PayPal/Deblock.
        """
        if self.require_webhook_proof and not webhook_verified:
            log.warning(
                "❌ Confirmation refusée pour %s: preuve webhook requise (source=%s)",
                sale_id,
                source,
            )
            return False

        for sale in self.sales:
            if sale.sale_id == sale_id:
                if sale.payment_status == "confirmed":
                    log.warning("Paiement déjà confirmé: %s", sale_id)
                    return True

                sale.payment_status = "confirmed"
                sale.payment_confirmed_at = datetime.now(timezone.utc).isoformat()
                self._save_ledger()

                log.info(
                    "✅ PAIEMENT CONFIRMÉ: %s - %s - %.0f EUR (provider=%s, source=%s)",
                    sale_id,
                    sale.company,
                    sale.amount_eur,
                    provider or sale.payment_method,
                    source,
                )
                return True

        log.error("Vente introuvable pour confirmation: %s", sale_id)
        return False

    def confirm_payment_for_test(self, sale_id: str) -> bool:
        """Bypass explicite réservé aux tests internes et smoke locaux."""
        return self.confirm_payment(
            sale_id=sale_id,
            source="test",
            provider="test",
            webhook_verified=True,
        )

    def get_confirmed_sales(self) -> List[RealSale]:
        """Retourne uniquement les ventes avec paiement confirmé."""
        return [s for s in self.sales if s.payment_status == "confirmed"]

    def get_pending_sales(self) -> List[RealSale]:
        """Retourne les ventes en attente de paiement."""
        return [s for s in self.sales if s.payment_status == "pending"]

    def get_total_revenue_confirmed(self) -> float:
        """Revenus réels confirmés uniquement."""
        return sum(s.amount_eur for s in self.get_confirmed_sales())

    def get_stats(self) -> Dict[str, Any]:
        """Statistiques complètes des ventes réelles."""
        confirmed = self.get_confirmed_sales()
        pending = self.get_pending_sales()

        return {
            "total_sales": len(self.sales),
            "confirmed_sales": len(confirmed),
            "pending_sales": len(pending),
            "revenue_confirmed_eur": self.get_total_revenue_confirmed(),
            "revenue_pending_eur": sum(s.amount_eur for s in pending),
            "average_deal_eur": (
                sum(s.amount_eur for s in confirmed) / len(confirmed)
                if confirmed else 0
            ),
            "conversion_rate_pct": (
                len(confirmed) / len(self.sales) * 100
                if self.sales else 0
            ),
        }


# ── Singleton ─────────────────────────────────────────────────────────────────
_engine: Optional[RealSalesEngine] = None


def get_real_sales_engine() -> RealSalesEngine:
    """Retourne l'instance singleton du RealSalesEngine."""
    global _engine
    if _engine is None:
        _engine = RealSalesEngine()
    return _engine
