"""
NAYA — Pipeline Tracker
Suit chaque prospect de la détection jusqu'au paiement.
Chaque euro dans le pipeline est visible en temps réel dans TORI.
"""
import os, json, time, logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta, timezone
from pathlib import Path

log = logging.getLogger("NAYA.PIPELINE")

PIPELINE_FILE = Path(__file__).parent.parent / "data" / "cache" / "pipeline.json"


class PipelineTracker:
    """
    Suivi complet du pipeline de revenus.
    Chaque prospect a un statut et une valeur associée.
    """

    STAGES = ["NEW", "ALERTED", "CONTACTED", "RESPONDED", "MEETING", "PROPOSAL_SENT",
              "NEGOTIATING", "CLOSED_WON", "CLOSED_LOST", "NURTURING"]

    def __init__(self):
        self._pipeline: Dict[str, Dict] = {}
        self._load()

    def _load(self):
        try:
            PIPELINE_FILE.parent.mkdir(parents=True, exist_ok=True)
            if PIPELINE_FILE.exists():
                self._pipeline = json.loads(PIPELINE_FILE.read_text())
        except Exception:
            self._pipeline = {}

    def _save(self):
        try:
            PIPELINE_FILE.write_text(json.dumps(self._pipeline, indent=2, ensure_ascii=False))
        except Exception as e:
            log.debug(f"Pipeline save: {e}")

    def add(self, prospect: object, offer_price: float = 0) -> str:
        """Ajoute un prospect au pipeline."""
        pid = getattr(prospect, "id", f"P_{int(time.time())}")
        self._pipeline[pid] = {
            "id": pid,
            "company": getattr(prospect, "company_name", ""),
            "contact": getattr(prospect, "contact_name", ""),
            "email": getattr(prospect, "email", ""),
            "sector": getattr(prospect, "sector", ""),
            "city": getattr(prospect, "city", ""),
            "pain_category": getattr(prospect, "pain_category", ""),
            "pain_cost": getattr(prospect, "pain_annual_cost_eur", 0),
            "offer_price": offer_price or getattr(prospect, "offer_price_eur", 0),
            "offer_title": getattr(prospect, "offer_title", ""),
            "priority": getattr(prospect, "priority", "MEDIUM"),
            "score": getattr(prospect, "solvability_score", 0),
            "source": getattr(prospect, "source", ""),
            "status": "NEW",
            "history": [{"status": "NEW", "ts": datetime.now(timezone.utc).isoformat()}],
            "payment_url": "",
            "revenue_collected": 0.0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
        self._save()
        return pid

    def update_status(self, prospect_id: str, new_status: str, note: str = "") -> bool:
        """Met à jour le statut d'un prospect."""
        if prospect_id not in self._pipeline:
            return False
        entry = self._pipeline[prospect_id]
        entry["status"] = new_status
        entry["last_updated"] = datetime.now(timezone.utc).isoformat()
        entry["history"].append({
            "status": new_status, "ts": datetime.now(timezone.utc).isoformat(), "note": note
        })
        if new_status == "CLOSED_WON":
            entry["revenue_collected"] = entry.get("offer_price", 0)
            entry["won_at"] = datetime.now(timezone.utc).isoformat()
        self._save()
        log.info(f"[PIPELINE] {prospect_id} → {new_status}: {entry.get('company','?')}")
        return True

    def set_payment_url(self, prospect_id: str, url: str):
        if prospect_id in self._pipeline:
            self._pipeline[prospect_id]["payment_url"] = url
            self._save()

    def get_kpis(self) -> Dict:
        """KPIs pipeline complets."""
        total = len(self._pipeline)
        if not total:
            return {"total": 0, "pipeline_eur": 0, "revenue_won_eur": 0,
                    "conversion_rate": 0, "stages": {}}

        stages = {}
        for s in self.STAGES:
            entries = [v for v in self._pipeline.values() if v.get("status") == s]
            stages[s] = {
                "count": len(entries),
                "value_eur": sum(e.get("offer_price", 0) for e in entries)
            }

        pipeline_value = sum(
            v.get("offer_price", 0) for v in self._pipeline.values()
            if v.get("status") not in ("CLOSED_LOST",)
        )
        won_value = sum(
            v.get("revenue_collected", 0) for v in self._pipeline.values()
            if v.get("status") == "CLOSED_WON"
        )
        won_count = stages.get("CLOSED_WON", {}).get("count", 0)
        contacted = sum(
            stages.get(s, {}).get("count", 0)
            for s in ["CONTACTED", "RESPONDED", "MEETING", "PROPOSAL_SENT",
                       "NEGOTIATING", "CLOSED_WON", "CLOSED_LOST"]
        )

        return {
            "total_prospects": total,
            "pipeline_eur": round(pipeline_value),
            "revenue_won_eur": round(won_value),
            "won_count": won_count,
            "conversion_rate": round(won_count / max(contacted, 1) * 100, 1),
            "avg_deal_size": round(won_value / max(won_count, 1)),
            "stages": stages,
            "by_priority": {
                p: len([v for v in self._pipeline.values() if v.get("priority") == p])
                for p in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
            },
            "top_prospects": sorted(
                [v for v in self._pipeline.values() if v.get("status") not in ("CLOSED_WON", "CLOSED_LOST")],
                key=lambda x: x.get("score", 0), reverse=True
            )[:5],
        }

    def get_hot_prospects(self, limit: int = 10) -> List[Dict]:
        """Prospects les plus chauds à contacter en priorité."""
        active = [
            v for v in self._pipeline.values()
            if v.get("status") in ("NEW", "ALERTED", "RESPONDED", "MEETING")
        ]
        return sorted(active, key=lambda x: (
            {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}.get(x.get("priority", "LOW"), 1),
            x.get("score", 0)
        ), reverse=True)[:limit]

    def get_daily_report(self) -> Dict:
        """Rapport journalier du pipeline."""
        today = datetime.now(timezone.utc).date().isoformat()
        today_entries = [
            v for v in self._pipeline.values()
            if v.get("created_at", "")[:10] == today
        ]
        today_won = [
            v for v in self._pipeline.values()
            if v.get("won_at", "")[:10] == today
        ]
        return {
            "date": today,
            "new_prospects_today": len(today_entries),
            "won_today": len(today_won),
            "revenue_today_eur": sum(v.get("revenue_collected", 0) for v in today_won),
            "kpis": self.get_kpis(),
        }

    def all(self) -> List[Dict]:
        return list(self._pipeline.values())
