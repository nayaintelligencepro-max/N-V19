"""
AMÉLIORATION REVENU #8 — Moteur d'expansion marchés.

Identifie et pénètre automatiquement de nouveaux marchés verticaux
et géographiques basés sur l'analyse des tendances et des signaux faibles.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class MarketOpportunity:
    """Opportunité de marché identifiée."""
    market_id: str
    market_name: str
    vertical: str
    geography: str
    estimated_tam_eur: int
    entry_barrier: str  # low / medium / high
    competition_level: str  # low / medium / high
    time_to_revenue_months: int
    recommended_entry_strategy: str
    priority_score: float
    signals: List[str] = field(default_factory=list)


MARKET_DATABASE: List[Dict[str, Any]] = [
    {
        "name": "PME industrielles françaises (NIS2)",
        "vertical": "Cybersécurité industrielle",
        "geography": "France",
        "tam_eur": 2_000_000_000,
        "entry_barrier": "low",
        "competition": "medium",
        "time_to_revenue": 1,
        "strategy": "Outreach ciblé sur les PME soumises à NIS2 sans prestataire — approche éducative",
        "signals": ["NIS2 deadline", "80% des PME non conformes", "Manque de prestataires spécialisés OT"],
    },
    {
        "name": "Ports et infrastructures maritimes EU",
        "vertical": "Transport maritime",
        "geography": "Europe",
        "tam_eur": 500_000_000,
        "entry_barrier": "medium",
        "competition": "low",
        "time_to_revenue": 2,
        "strategy": "Partenariat avec autorités portuaires — démonstration sur site pilote",
        "signals": ["IMO cyber guidelines", "Incidents portuaires en hausse", "Budget sécurité portuaire x3"],
    },
    {
        "name": "Énergies renouvelables décentralisées",
        "vertical": "Énergie",
        "geography": "Europe + Afrique",
        "tam_eur": 800_000_000,
        "entry_barrier": "medium",
        "competition": "low",
        "time_to_revenue": 3,
        "strategy": "Offre packagée sécurité SCADA pour parcs éoliens/solaires",
        "signals": ["Croissance 15%/an", "Vulnérabilités IoT solaires", "Réglementation émergente"],
    },
    {
        "name": "Hôpitaux et systèmes de santé connectés",
        "vertical": "Santé",
        "geography": "France + EU",
        "tam_eur": 1_200_000_000,
        "entry_barrier": "high",
        "competition": "medium",
        "time_to_revenue": 3,
        "strategy": "Audit sécurité dispositifs médicaux connectés — partenariat GHT",
        "signals": ["Cyberattaques hôpitaux x5", "NIS2 santé", "RGPD données de santé"],
    },
    {
        "name": "Industrie 4.0 / Smart Manufacturing",
        "vertical": "Manufacturing",
        "geography": "DACH + France",
        "tam_eur": 3_000_000_000,
        "entry_barrier": "medium",
        "competition": "high",
        "time_to_revenue": 2,
        "strategy": "Focus sur la convergence OT/IT — offre IEC 62443 + monitoring IoT",
        "signals": ["Transformation digitale usines", "Incidents ransomware manufacturing", "Budget cybersécurité +25%"],
    },
    {
        "name": "Marchés oubliés Pacifique Sud",
        "vertical": "Multi-secteur",
        "geography": "Polynésie + Pacifique",
        "tam_eur": 50_000_000,
        "entry_barrier": "low",
        "competition": "very_low",
        "time_to_revenue": 1,
        "strategy": "Premier prestataire cybersécurité OT local — avantage géographique unique",
        "signals": ["Aucun concurrent local", "Infrastructure critique non protégée", "Programmes gouvernementaux"],
    },
    {
        "name": "Assurance cyber OT/IT",
        "vertical": "Assurance",
        "geography": "Europe",
        "tam_eur": 400_000_000,
        "entry_barrier": "medium",
        "competition": "low",
        "time_to_revenue": 2,
        "strategy": "Partenariat avec assureurs — évaluation de risque OT pour souscription",
        "signals": ["Primes cyber x4", "Manque de données OT", "Assureurs cherchent experts"],
    },
    {
        "name": "Supply Chain Security",
        "vertical": "Logistique",
        "geography": "Global",
        "tam_eur": 1_500_000_000,
        "entry_barrier": "medium",
        "competition": "medium",
        "time_to_revenue": 3,
        "strategy": "Audit sécurité chaîne d'approvisionnement — scoring fournisseurs OT",
        "signals": ["Incidents supply chain +200%", "Exigence NIS2 fournisseurs", "Auto-certification insuffisante"],
    },
]


class MarketExpansionEngine:
    """
    Identifie et priorise les opportunités d'expansion vers de nouveaux marchés.

    Analyse les signaux faibles, la concurrence et les barrières à l'entrée
    pour recommander les marchés à conquérir en priorité.
    """

    def __init__(self) -> None:
        self._opportunities: List[MarketOpportunity] = []
        self._load_markets()
        logger.info(f"[MarketExpansionEngine] Initialisé — {len(self._opportunities)} marchés analysés")

    def _load_markets(self) -> None:
        barrier_score = {"low": 0.9, "medium": 0.6, "high": 0.3, "very_low": 1.0}
        competition_score = {"very_low": 1.0, "low": 0.8, "medium": 0.5, "high": 0.3}

        for i, m in enumerate(MARKET_DATABASE):
            priority = (
                barrier_score.get(m["entry_barrier"], 0.5) *
                competition_score.get(m["competition"], 0.5) *
                (1.0 / max(m["time_to_revenue"], 1)) *
                (m["tam_eur"] / 3_000_000_000)
            )

            self._opportunities.append(MarketOpportunity(
                market_id=f"MKT_{i:03d}",
                market_name=m["name"],
                vertical=m["vertical"],
                geography=m["geography"],
                estimated_tam_eur=m["tam_eur"],
                entry_barrier=m["entry_barrier"],
                competition_level=m["competition"],
                time_to_revenue_months=m["time_to_revenue"],
                recommended_entry_strategy=m["strategy"],
                priority_score=round(priority, 3),
                signals=m["signals"],
            ))

        self._opportunities.sort(key=lambda o: o.priority_score, reverse=True)

    def top_markets(self, limit: int = 5) -> List[MarketOpportunity]:
        """Retourne les marchés les plus prometteurs."""
        return self._opportunities[:limit]

    def markets_by_vertical(self, vertical: str) -> List[MarketOpportunity]:
        """Retourne les marchés d'un vertical donné."""
        vertical_lower = vertical.lower()
        return [o for o in self._opportunities if vertical_lower in o.vertical.lower()]

    def quick_wins(self) -> List[MarketOpportunity]:
        """Retourne les marchés à entrée rapide (< 2 mois)."""
        return [o for o in self._opportunities if o.time_to_revenue_months <= 2 and o.entry_barrier == "low"]

    def stats(self) -> Dict[str, Any]:
        total_tam = sum(o.estimated_tam_eur for o in self._opportunities)
        return {
            "markets_analyzed": len(self._opportunities),
            "total_addressable_market_eur": total_tam,
            "quick_wins": len(self.quick_wins()),
            "top_market": self._opportunities[0].market_name if self._opportunities else None,
        }


market_expansion_engine = MarketExpansionEngine()
