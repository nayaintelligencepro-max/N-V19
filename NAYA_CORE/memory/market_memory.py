#!/usr/bin/env python3
"""
NAYA MEMORY - Market Memory Module
Accumulation de patterns marché et signaux faibles
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class MarketSignal:
    """Signal marché détecté"""
    signal_id: str
    source: str  # job_offer, news, linkedin, regulatory, competitor
    sector: str
    company: Optional[str]
    signal_type: str  # pain, opportunity, threat, trend
    description: str
    urgency_score: int  # 0-100
    budget_estimate_eur: Optional[float]
    detected_at: str
    expires_at: Optional[str]
    metadata: Dict


class MarketMemory:
    """
    Mémoire des signaux marché et patterns accumulés
    Intelligence continue sur les secteurs cibles
    """

    def __init__(self, storage_path: str = "data/memory/market.json"):
        self.storage_path = storage_path
        self.signals: List[MarketSignal] = []
        self._load_memory()

    def _load_memory(self):
        """Charge la mémoire depuis le fichier"""
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.signals = [MarketSignal(**signal) for signal in data]
        except FileNotFoundError:
            self.signals = []
        except Exception as e:
            print(f"Error loading market memory: {e}")
            self.signals = []

    def _save_memory(self):
        """Sauvegarde la mémoire"""
        try:
            import os
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump([asdict(signal) for signal in self.signals], f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving market memory: {e}")

    async def save_signal(self, signal_data: Dict) -> str:
        """
        Enregistre un nouveau signal marché

        Args:
            signal_data: Données du signal

        Returns:
            signal_id généré
        """
        signal_id = f"SIGNAL_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(self.signals)+1}"

        signal = MarketSignal(
            signal_id=signal_id,
            source=signal_data.get("source", "unknown"),
            sector=signal_data.get("sector", "Unknown"),
            company=signal_data.get("company"),
            signal_type=signal_data.get("signal_type", "opportunity"),
            description=signal_data.get("description", ""),
            urgency_score=min(100, max(0, signal_data.get("urgency_score", 50))),
            budget_estimate_eur=signal_data.get("budget_estimate_eur"),
            detected_at=datetime.now().isoformat(),
            expires_at=signal_data.get("expires_at"),
            metadata=signal_data.get("metadata", {})
        )

        self.signals.append(signal)
        self._save_memory()

        return signal_id

    async def get_hot_signals(self, min_urgency: int = 70, sector: Optional[str] = None) -> List[MarketSignal]:
        """
        Récupère les signaux chauds (haute urgence)

        Args:
            min_urgency: Score minimum d'urgence (0-100)
            sector: Filtrer par secteur (optionnel)

        Returns:
            Liste des signaux chauds triés par urgence
        """
        hot_signals = [s for s in self.signals if s.urgency_score >= min_urgency]

        if sector:
            hot_signals = [s for s in hot_signals if s.sector == sector]

        # Filtrer les signaux expirés
        now = datetime.now().isoformat()
        hot_signals = [s for s in hot_signals if not s.expires_at or s.expires_at > now]

        # Trier par urgence décroissante
        hot_signals.sort(key=lambda x: x.urgency_score, reverse=True)

        return hot_signals

    async def analyze_sector_trends(self, sector: str) -> Dict:
        """
        Analyse les tendances d'un secteur

        Args:
            sector: Nom du secteur

        Returns:
            Analyse des tendances (signaux dominants, opportunités, menaces)
        """
        sector_signals = [s for s in self.signals if s.sector == sector]

        if not sector_signals:
            return {
                "sector": sector,
                "total_signals": 0,
                "trends": [],
                "top_opportunities": [],
                "top_threats": []
            }

        # Compter par type
        type_counts = {}
        for signal in sector_signals:
            type_counts[signal.signal_type] = type_counts.get(signal.signal_type, 0) + 1

        # Top opportunités
        opportunities = [s for s in sector_signals if s.signal_type == "opportunity"]
        opportunities.sort(key=lambda x: x.urgency_score, reverse=True)

        # Top menaces
        threats = [s for s in sector_signals if s.signal_type == "threat"]
        threats.sort(key=lambda x: x.urgency_score, reverse=True)

        # Budget total estimé
        total_budget = sum(s.budget_estimate_eur or 0 for s in sector_signals if s.budget_estimate_eur)

        return {
            "sector": sector,
            "total_signals": len(sector_signals),
            "signal_types": type_counts,
            "total_budget_estimate_eur": total_budget,
            "top_opportunities": [
                {
                    "description": s.description,
                    "urgency": s.urgency_score,
                    "budget_eur": s.budget_estimate_eur
                }
                for s in opportunities[:5]
            ],
            "top_threats": [
                {
                    "description": s.description,
                    "urgency": s.urgency_score
                }
                for s in threats[:5]
            ]
        }

    async def get_signals_by_source(self, source: str, limit: int = 10) -> List[MarketSignal]:
        """
        Récupère les signaux par source

        Args:
            source: Type de source (job_offer, news, linkedin, etc.)
            limit: Nombre maximum de résultats

        Returns:
            Liste des signaux de cette source
        """
        source_signals = [s for s in self.signals if s.source == source]
        source_signals.sort(key=lambda x: x.detected_at, reverse=True)
        return source_signals[:limit]

    async def get_stats(self) -> Dict:
        """Statistiques globales de la mémoire marché"""
        total = len(self.signals)
        if total == 0:
            return {"total": 0, "by_sector": {}, "by_source": {}, "by_type": {}}

        by_sector = {}
        by_source = {}
        by_type = {}

        for signal in self.signals:
            by_sector[signal.sector] = by_sector.get(signal.sector, 0) + 1
            by_source[signal.source] = by_source.get(signal.source, 0) + 1
            by_type[signal.signal_type] = by_type.get(signal.signal_type, 0) + 1

        total_budget = sum(s.budget_estimate_eur or 0 for s in self.signals if s.budget_estimate_eur)

        return {
            "total": total,
            "by_sector": by_sector,
            "by_source": by_source,
            "by_type": by_type,
            "total_budget_estimate_eur": total_budget,
            "avg_urgency": sum(s.urgency_score for s in self.signals) / total
        }


# Instance globale
market_memory = MarketMemory()
