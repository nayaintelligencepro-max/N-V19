"""
NAYA — REVENUE INTELLIGENCE V8
════════════════════════════════════════════════════════════════════════════════
Le système apprend ce qui génère réellement de l'argent.

À chaque cycle:
  1. Mesure quels secteurs, quelles douleurs, quels prix convertissent le mieux
  2. Intensifie la chasse sur les patterns qui marchent
  3. Abandonne ce qui ne convertit pas
  4. Optimise automatiquement les prix et les canaux

C'est l'équivalent d'un directeur commercial qui analyse ses stats
et réoriente l'équipe chaque semaine.
════════════════════════════════════════════════════════════════════════════════
"""
import json, time, logging
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone

log = logging.getLogger("NAYA.REVENUE_INTEL")

def _gs(key: str, default: str = "") -> str:
    try:
        from SECRETS.secrets_loader import get_secret
        return get_secret(key, default) or default
    except Exception:
        return __import__('os').environ.get(key, default)


ROOT = Path(__file__).resolve().parent.parent
INTEL_FILE = ROOT / "data" / "cache" / "revenue_intelligence.json"
INTEL_FILE.parent.mkdir(parents=True, exist_ok=True)


@dataclass
class SectorPerformance:
    """Performance mesurée d'un secteur."""
    sector: str
    deals_detected: int = 0
    deals_won: int = 0
    revenue_total: float = 0.0
    avg_price: float = 0.0
    avg_conversion_days: float = 0.0
    best_pain_category: str = ""
    best_channel: str = ""
    conversion_rate: float = 0.0
    last_win_at: float = 0.0

    @property
    def priority_score(self) -> float:
        """Score de priorité pour orienter la chasse."""
        if self.deals_detected == 0:
            return 50.0  # Secteur non testé — potentiel inconnu
        conv = self.deals_won / self.deals_detected
        rev_per_deal = self.revenue_total / max(self.deals_detected, 1)
        recency = 1.0 if (time.time() - self.last_win_at) < 30 * 86400 else 0.7
        return round((conv * 40 + min(rev_per_deal / 50000, 1) * 40 + recency * 20), 1)


class RevenueIntelligence:
    """
    Intelligence revenus — apprend et optimise en continu.
    """

    def __init__(self):
        self._sector_perf: Dict[str, SectorPerformance] = {}
        self._pain_conv: Dict[str, Dict] = {}  # {pain_cat: {won, detected, avg_price}}
        self._price_conv: Dict[str, float] = {}  # {price_bucket: conversion_rate}
        self._load()
        self._init_defaults()

    def _init_defaults(self):
        """Initialise les secteurs avec des données de base si absent."""
        default_sectors = [
            "pme_b2b", "artisan_trades", "liberal_professions", "restaurant_food",
            "ecommerce", "startup_scaleup", "healthcare_wellness", "diaspora_markets",
            "real_estate_investors"
        ]
        for s in default_sectors:
            if s not in self._sector_perf:
                self._sector_perf[s] = SectorPerformance(sector=s)

    def _load(self):
        try:
            if INTEL_FILE.exists():
                data = json.loads(INTEL_FILE.read_text())
                for s, v in data.get("sectors", {}).items():
                    self._sector_perf[s] = SectorPerformance(
                        sector=s, deals_detected=v.get("detected", 0),
                        deals_won=v.get("won", 0), revenue_total=v.get("revenue", 0),
                        avg_price=v.get("avg_price", 0),
                        conversion_rate=v.get("conv_rate", 0),
                        best_pain_category=v.get("best_pain", ""),
                        best_channel=v.get("best_channel", ""),
                        last_win_at=v.get("last_win_at", 0),
                    )
                self._pain_conv = data.get("pain_conv", {})
                self._price_conv = data.get("price_conv", {})
        except Exception as e:
            log.debug(f"[INTEL] Load: {e}")

    def _save(self):
        try:
            data = {
                "sectors": {
                    s: {
                        "detected": p.deals_detected, "won": p.deals_won,
                        "revenue": p.revenue_total, "avg_price": p.avg_price,
                        "conv_rate": p.conversion_rate, "best_pain": p.best_pain_category,
                        "best_channel": p.best_channel, "last_win_at": p.last_win_at,
                    }
                    for s, p in self._sector_perf.items()
                },
                "pain_conv": self._pain_conv,
                "price_conv": self._price_conv,
                "saved_at": datetime.now(timezone.utc).isoformat(),
            }
            INTEL_FILE.write_text(json.dumps(data, indent=2))
        except Exception as e:
            log.debug(f"[INTEL] Save: {e}")

    def record_detection(self, sector: str, pain_category: str, price: float):
        """Enregistre une nouvelle détection."""
        if sector not in self._sector_perf:
            self._sector_perf[sector] = SectorPerformance(sector=sector)
        self._sector_perf[sector].deals_detected += 1

        if pain_category not in self._pain_conv:
            self._pain_conv[pain_category] = {"detected": 0, "won": 0, "total_price": 0}
        self._pain_conv[pain_category]["detected"] += 1
        self._pain_conv[pain_category]["total_price"] += price
        self._save()

    def record_win(self, sector: str, pain_category: str, price: float, days_to_close: float = 0):
        """Enregistre un deal gagné — données de conversion réelle."""
        sp = self._sector_perf.get(sector)
        if sp:
            sp.deals_won += 1
            sp.revenue_total += price
            sp.avg_price = sp.revenue_total / sp.deals_won
            sp.conversion_rate = sp.deals_won / max(sp.deals_detected, 1)
            sp.best_pain_category = pain_category
            sp.last_win_at = time.time()
            if days_to_close:
                sp.avg_conversion_days = (sp.avg_conversion_days + days_to_close) / 2

        pc = self._pain_conv.get(pain_category, {})
        pc["won"] = pc.get("won", 0) + 1
        self._pain_conv[pain_category] = pc

        # Enregistrer bucket prix
        bucket = self._price_bucket(price)
        old_rate = self._price_conv.get(bucket, 0.15)
        self._price_conv[bucket] = min(old_rate * 0.7 + 0.3, 0.8)  # EMA update

        self._save()
        log.info(f"[INTEL] WIN recorded: {sector} | {pain_category} | {price:,.0f}€")

    def _price_bucket(self, price: float) -> str:
        if price < 5000: return "1k-5k"
        elif price < 15000: return "5k-15k"
        elif price < 30000: return "15k-30k"
        elif price < 60000: return "30k-60k"
        else: return "60k+"

    def get_priority_sectors(self, n: int = 5) -> List[Dict]:
        """Retourne les secteurs à chasser en priorité."""
        ranked = sorted(
            self._sector_perf.values(),
            key=lambda s: s.priority_score,
            reverse=True
        )
        return [
            {
                "sector": s.sector,
                "priority_score": s.priority_score,
                "conversion_rate": round(s.conversion_rate, 2),
                "avg_revenue": round(s.avg_price),
                "best_pain": s.best_pain_category,
                "total_revenue": round(s.revenue_total),
                "recommendation": "HUNT_AGGRESSIVELY" if s.priority_score >= 70
                                  else "HUNT_NORMAL" if s.priority_score >= 40
                                  else "MONITOR",
            }
            for s in ranked[:n]
        ]

    def get_best_price_range(self) -> Dict:
        """Identifie la fourchette de prix avec le meilleur taux de conversion."""
        if not self._price_conv:
            return {"best_bucket": "5k-15k", "reason": "default — données insuffisantes"}

        best = max(self._price_conv.items(), key=lambda x: x[1])
        return {
            "best_bucket": best[0],
            "conversion_rate": round(best[1], 2),
            "all_buckets": {k: round(v, 2) for k, v in sorted(self._price_conv.items())},
        }

    def get_top_pain_categories(self, n: int = 5) -> List[Dict]:
        """Douleurs qui convertissent le mieux."""
        result = []
        for pain, data in self._pain_conv.items():
            detected = data.get("detected", 0)
            won = data.get("won", 0)
            if detected == 0:
                continue
            result.append({
                "pain": pain,
                "conversion_rate": round(won / detected, 2),
                "detected": detected,
                "won": won,
                "avg_price": round(data.get("total_price", 0) / max(detected, 1)),
            })
        return sorted(result, key=lambda x: x["conversion_rate"], reverse=True)[:n]

    def get_hunt_directives(self) -> Dict:
        """
        Directives de chasse intelligentes basées sur les données réelles.
        C'est ce que le système suit pour maximiser les revenus.
        """
        priority_sectors = self.get_priority_sectors(3)
        best_price = self.get_best_price_range()
        top_pains = self.get_top_pain_categories(3)

        directives = {
            "focus_sectors": [s["sector"] for s in priority_sectors if s["recommendation"] == "HUNT_AGGRESSIVELY"],
            "monitor_sectors": [s["sector"] for s in priority_sectors if s["recommendation"] == "HUNT_NORMAL"],
            "target_price_bucket": best_price["best_bucket"],
            "priority_pain_categories": [p["pain"] for p in top_pains],
            "rationale": {
                "top_sector": priority_sectors[0]["sector"] if priority_sectors else "pme_b2b",
                "top_sector_score": priority_sectors[0]["priority_score"] if priority_sectors else 50,
                "best_conversion_pain": top_pains[0]["pain"] if top_pains else "underpriced",
                "best_price_range": best_price["best_bucket"],
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        return directives


# ── Singleton ──────────────────────────────────────────────────────────────────
_intel: Optional[RevenueIntelligence] = None

def get_revenue_intelligence() -> RevenueIntelligence:
    global _intel
    if _intel is None:
        _intel = RevenueIntelligence()
    return _intel
