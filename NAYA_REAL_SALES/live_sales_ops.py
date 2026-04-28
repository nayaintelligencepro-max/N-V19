"""NAYA Real Sales Live Ops.

Mode opérationnel pour:
- chasser des leads chauds (Apollo + Serper + fallback)
- créer des ventes pending avec lien de paiement
- notifier en temps réel

Important: aucun encaissement n'est confirmé automatiquement.
Seul le webhook provider peut confirmer un paiement réel.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from NAYA_REAL_SALES.real_sales_engine import get_real_sales_engine

log = logging.getLogger("NAYA.REAL_SALES_LIVE")
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "real_sales" / "live_ops_report.json"


@dataclass
class HotLead:
    company: str
    contact: str
    email: str
    sector: str
    pain: str
    urgency: str
    budget_estimate_eur: float
    source: str
    heat_score: float


class RealSalesLiveOps:
    def __init__(self) -> None:
        self.engine = get_real_sales_engine()

    def preflight(self) -> Dict[str, Any]:
        try:
            from SECRETS import get_status
            st = get_status()
        except Exception:
            st = {}
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "webhook_proof_required": self.engine.require_webhook_proof,
            "secrets_status": st,
        }

    async def gather_hot_leads(self, limit: int = 6) -> List[HotLead]:
        leads: List[HotLead] = []

        # 1) Apollo (si dispo)
        try:
            from NAYA_CORE.integrations.apollo_hunter import get_apollo

            ap = get_apollo()
            if ap.available:
                ppl = ap.search_people(
                    job_titles=["CISO", "RSSI", "DSI", "CTO", "Directeur Usine"],
                    countries=["France", "Belgium", "Morocco", "Senegal"],
                    limit=10,
                )
                for p in ppl[:limit]:
                    if not p.email:
                        continue
                    budget = 10000 if p.score >= 0.7 else 5000
                    leads.append(
                        HotLead(
                            company=p.company or "Unknown Company",
                            contact=p.name or "Unknown Contact",
                            email=p.email,
                            sector=(p.industry or "cross_sector").lower(),
                            pain="Conformité NIS2 / exposition OT",
                            urgency="high" if p.score >= 0.7 else "medium",
                            budget_estimate_eur=budget,
                            source="apollo",
                            heat_score=round(float(p.score), 2),
                        )
                    )
        except Exception as exc:
            log.debug("Apollo unavailable: %s", exc)

        # 2) Serper signaux (si dispo)
        try:
            from NAYA_CORE.integrations.serper_hunter import get_serper

            sp = get_serper()
            if sp.available:
                signals = sp.hunt_pains(["douleur_operationnelle", "marchés_publics", "afrique_francophone"])
                for s in signals[:limit]:
                    leads.append(
                        HotLead(
                            company=(s.get("title") or "Prospect signal")[0:60],
                            contact="Decision Maker",
                            email="contact@unknown.local",
                            sector=(s.get("category") or "cross_sector").lower(),
                            pain=(s.get("snippet") or "Pain signal")[0:140],
                            urgency="high",
                            budget_estimate_eur=10000,
                            source="serper",
                            heat_score=0.72,
                        )
                    )
        except Exception as exc:
            log.debug("Serper unavailable: %s", exc)

        # 3) Fallback chaud si APIs indisponibles
        if not leads:
            fallback = [
                ("RATP Dev", "Thomas Martin", "transport", 15000),
                ("EDF Renouvelables", "Marie Dubois", "energy", 10000),
                ("Michelin", "Sophie Bernard", "manufacturing", 12000),
            ]
            for c, contact, sec, amt in fallback:
                leads.append(
                    HotLead(
                        company=c,
                        contact=contact,
                        email=f"{contact.lower().replace(' ', '.')}@example.com",
                        sector=sec,
                        pain="Risque conformité / continuité opérationnelle",
                        urgency="high",
                        budget_estimate_eur=amt,
                        source="fallback_hotlist",
                        heat_score=0.8,
                    )
                )

        # dédup + tri heat/amount
        dedup: Dict[str, HotLead] = {}
        for l in leads:
            key = f"{l.company.lower()}::{l.email.lower()}"
            if key not in dedup or l.heat_score > dedup[key].heat_score:
                dedup[key] = l
        hot = sorted(dedup.values(), key=lambda x: (x.heat_score, x.budget_estimate_eur), reverse=True)
        return hot[:limit]

    def _offer_for(self, lead: HotLead) -> Dict[str, Any]:
        amt = max(1000, int(lead.budget_estimate_eur))
        service = "audit_express" if amt <= 10000 else "iec62443_compliance"
        title = "Audit Express OT/NIS2" if service == "audit_express" else "Mission Conformité NIS2 + IEC62443"
        return {
            "amount_eur": amt,
            "service_type": service,
            "offer_title": title,
            "payment_provider": "paypal",
        }

    async def run_cycle(self, max_sales: int = 3) -> Dict[str, Any]:
        leads = await self.gather_hot_leads(limit=max_sales * 2)
        created = []

        for lead in leads[:max_sales]:
            offer = self._offer_for(lead)
            sale = self.engine.create_sale_from_api(
                company=lead.company,
                sector=lead.sector,
                amount_eur=offer["amount_eur"],
                service_type=offer["service_type"],
                payment_provider=offer["payment_provider"],
                metadata={
                    "contact": lead.contact,
                    "email": lead.email,
                    "offer_title": offer["offer_title"],
                    "source": lead.source,
                    "heat_score": lead.heat_score,
                    "pain": lead.pain,
                    "urgency": lead.urgency,
                },
            )
            created.append({
                "sale_id": sale.sale_id,
                "company": sale.company,
                "amount_eur": sale.amount_eur,
                "payment_url": sale.payment_url,
                "status": sale.payment_status,
            })

        stats = self.engine.get_stats()
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cycle_created": len(created),
            "created_sales": created,
            "stats": stats,
            "note": "Payments remain pending until provider webhook confirms them.",
        }
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

        # Telegram best-effort
        try:
            from NAYA_CORE.integrations.telegram_notifier import get_notifier

            n = get_notifier()
            n.send(
                f"🔥 LIVE SALES CYCLE\n"
                f"Created: {len(created)} ventes pending\n"
                f"Pending total: {stats.get('revenue_pending_eur', 0):,.0f} EUR\n"
                f"Confirmed total: {stats.get('revenue_confirmed_eur', 0):,.0f} EUR"
            )
        except Exception:
            pass

        return report

    async def run_daemon(self, interval_seconds: int = 1800, max_sales_per_cycle: int = 3) -> None:
        while True:
            try:
                await self.run_cycle(max_sales=max_sales_per_cycle)
            except Exception as exc:
                log.warning("live sales cycle failed: %s", exc)
            await asyncio.sleep(max(300, interval_seconds))


_OPS: RealSalesLiveOps | None = None


def get_live_sales_ops() -> RealSalesLiveOps:
    global _OPS
    if _OPS is None:
        _OPS = RealSalesLiveOps()
    return _OPS
