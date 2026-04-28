"""
NAYA V19.2 — AUTO-LEARNING ENGINE
═══════════════════════════════════════════════════════════════════════════════
Système d'apprentissage autonome qui:
- Analyse les patterns de succès des opportunités gagnantes
- Adapte les stratégies en temps réel selon les performances
- Mémorise et capitalise sur chaque interaction réussie
- Optimise les approches par secteur, géographie, langage
- Ajuste la cognition selon les résultats obtenus

100% autonome. Zéro intervention humaine.
═══════════════════════════════════════════════════════════════════════════════
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

log = logging.getLogger("NAYA.V192.LEARNING")

ROOT = Path(__file__).resolve().parent.parent
LEARNING_DATA = ROOT / "data" / "v192_learning.json"
LEARNING_DATA.parent.mkdir(parents=True, exist_ok=True)


class SuccessLevel(Enum):
    """Niveaux de succès d'une opportunité"""
    WON_HIGH = "won_high"         # Fermé > 50k EUR
    WON_MID = "won_mid"           # Fermé 10k-50k EUR
    WON_LOW = "won_low"           # Fermé 1k-10k EUR
    ENGAGED = "engaged"           # Interactions positives
    COLD = "cold"                 # Peu d'engagement
    LOST = "lost"                 # Perdu définitivement


@dataclass
class SuccessPattern:
    """Pattern de succès extrait d'une opportunité gagnante"""
    sector: str
    market_type: str              # forgotten, ultra_discrete, cross_sector, etc.
    geography: str                # Polynésie, Afrique francophone, Europe, etc.
    language: str                 # fr, en, es, pt, ar, wo
    entry_strategy: str
    value_proposition: str
    budget_range: str             # "1k-5k", "5k-20k", "20k-50k", "50k+"
    pain_signals: List[str]
    decision_maker_role: str
    success_level: SuccessLevel
    conversion_time_days: int
    interactions_count: int
    recorded_at: float = field(default_factory=time.time)
    confidence: float = 1.0


@dataclass
class AdaptationDirective:
    """Directive d'adaptation générée par l'apprentissage"""
    target_area: str              # "market_detection", "entry_strategy", "value_prop", etc.
    old_approach: str
    new_approach: str
    reason: str
    supporting_patterns: int      # Nombre de patterns qui supportent ce changement
    confidence: float             # 0-1
    applied: bool = False
    applied_at: Optional[float] = None


class AutoLearningEngine:
    """
    Moteur d'apprentissage autonome V19.2
    Apprend de chaque succès et adapte les stratégies en continu.
    """

    def __init__(self):
        self.success_patterns: List[SuccessPattern] = []
        self.adaptation_directives: List[AdaptationDirective] = []
        self.learning_cycles = 0
        self._load()
        log.info(f"[V19.2][LEARNING] Moteur initialisé | {len(self.success_patterns)} patterns | "
                f"{len(self.adaptation_directives)} directives")

    def record_success(self, opportunity_data: Dict[str, Any], outcome: str, value_eur: float,
                      conversion_days: int, interactions: int) -> None:
        """
        Enregistre un succès pour apprentissage futur.

        Args:
            opportunity_data: Données de l'opportunité (secteur, marché, géo, etc.)
            outcome: "won" | "engaged" | "lost"
            value_eur: Valeur fermée ou potentielle
            conversion_days: Nombre de jours pour conversion
            interactions: Nombre d'interactions
        """
        # Déterminer le niveau de succès
        if outcome == "won":
            if value_eur >= 50000:
                level = SuccessLevel.WON_HIGH
            elif value_eur >= 10000:
                level = SuccessLevel.WON_MID
            else:
                level = SuccessLevel.WON_LOW
        elif outcome == "engaged":
            level = SuccessLevel.ENGAGED
        elif outcome == "cold":
            level = SuccessLevel.COLD
        else:
            level = SuccessLevel.LOST

        # Déterminer la tranche de budget
        if value_eur >= 50000:
            budget_range = "50k+"
        elif value_eur >= 20000:
            budget_range = "20k-50k"
        elif value_eur >= 5000:
            budget_range = "5k-20k"
        else:
            budget_range = "1k-5k"

        pattern = SuccessPattern(
            sector=opportunity_data.get('sector', 'Unknown'),
            market_type=opportunity_data.get('type', 'Unknown'),
            geography=opportunity_data.get('geography', 'Unknown'),
            language=opportunity_data.get('language', 'fr'),
            entry_strategy=opportunity_data.get('entry_strategy', ''),
            value_proposition=opportunity_data.get('value_proposition', ''),
            budget_range=budget_range,
            pain_signals=opportunity_data.get('pain_signals', []),
            decision_maker_role=opportunity_data.get('decision_maker_role', ''),
            success_level=level,
            conversion_time_days=conversion_days,
            interactions_count=interactions,
        )

        self.success_patterns.append(pattern)
        self._save()

        log.info(f"[V19.2][LEARNING] ✅ Pattern enregistré | {pattern.sector} | "
                f"{level.value} | {value_eur:,.0f} EUR | {conversion_days}j")

    async def analyze_and_adapt(self) -> Dict[str, Any]:
        """
        Analyse tous les patterns de succès et génère des directives d'adaptation.
        Exécution automatique toutes les 6h via scheduler.
        """
        self.learning_cycles += 1
        log.info(f"[V19.2][LEARNING] Cycle #{self.learning_cycles} — Analyse patterns...")

        if len(self.success_patterns) < 5:
            log.info("[V19.2][LEARNING] Pas assez de données (< 5 patterns)")
            return {'status': 'insufficient_data', 'patterns_count': len(self.success_patterns)}

        # Analyser par secteur
        sector_analysis = self._analyze_by_sector()

        # Analyser par géographie
        geo_analysis = self._analyze_by_geography()

        # Analyser par type de marché
        market_analysis = self._analyze_by_market_type()

        # Analyser les stratégies d'entrée
        strategy_analysis = self._analyze_entry_strategies()

        # Générer des directives d'adaptation
        new_directives = self._generate_adaptations(
            sector_analysis, geo_analysis, market_analysis, strategy_analysis
        )

        self.adaptation_directives.extend(new_directives)
        self._save()

        result = {
            'cycle': self.learning_cycles,
            'patterns_analyzed': len(self.success_patterns),
            'directives_generated': len(new_directives),
            'top_sectors': list(sector_analysis.keys())[:5],
            'top_geographies': list(geo_analysis.keys())[:3],
            'best_strategies': self._get_best_strategies(strategy_analysis),
        }

        log.info(f"[V19.2][LEARNING] ✅ Cycle #{self.learning_cycles} | "
                f"{len(new_directives)} nouvelles directives | "
                f"Total patterns: {len(self.success_patterns)}")

        return result

    def _analyze_by_sector(self) -> Dict[str, Dict]:
        """Analyse des performances par secteur"""
        sectors = {}
        for p in self.success_patterns:
            if p.sector not in sectors:
                sectors[p.sector] = {'wins': 0, 'total_value': 0, 'avg_days': [], 'patterns': []}

            if p.success_level in (SuccessLevel.WON_HIGH, SuccessLevel.WON_MID, SuccessLevel.WON_LOW):
                sectors[p.sector]['wins'] += 1

            # Estimer la valeur (mid-point de la tranche)
            value_map = {"1k-5k": 3000, "5k-20k": 12500, "20k-50k": 35000, "50k+": 75000}
            sectors[p.sector]['total_value'] += value_map.get(p.budget_range, 0)
            sectors[p.sector]['avg_days'].append(p.conversion_time_days)
            sectors[p.sector]['patterns'].append(p)

        # Calculer moyennes et trier par succès
        for sector, data in sectors.items():
            if data['avg_days']:
                data['avg_conversion_days'] = sum(data['avg_days']) / len(data['avg_days'])

        return dict(sorted(sectors.items(), key=lambda x: x[1]['wins'], reverse=True))

    def _analyze_by_geography(self) -> Dict[str, Dict]:
        """Analyse des performances par géographie"""
        geos = {}
        for p in self.success_patterns:
            if p.geography not in geos:
                geos[p.geography] = {'wins': 0, 'total_value': 0, 'patterns': []}

            if p.success_level in (SuccessLevel.WON_HIGH, SuccessLevel.WON_MID, SuccessLevel.WON_LOW):
                geos[p.geography]['wins'] += 1

            value_map = {"1k-5k": 3000, "5k-20k": 12500, "20k-50k": 35000, "50k+": 75000}
            geos[p.geography]['total_value'] += value_map.get(p.budget_range, 0)
            geos[p.geography]['patterns'].append(p)

        return dict(sorted(geos.items(), key=lambda x: x[1]['wins'], reverse=True))

    def _analyze_by_market_type(self) -> Dict[str, Dict]:
        """Analyse des performances par type de marché"""
        markets = {}
        for p in self.success_patterns:
            if p.market_type not in markets:
                markets[p.market_type] = {'wins': 0, 'total_value': 0, 'patterns': []}

            if p.success_level in (SuccessLevel.WON_HIGH, SuccessLevel.WON_MID, SuccessLevel.WON_LOW):
                markets[p.market_type]['wins'] += 1

            value_map = {"1k-5k": 3000, "5k-20k": 12500, "20k-50k": 35000, "50k+": 75000}
            markets[p.market_type]['total_value'] += value_map.get(p.budget_range, 0)
            markets[p.market_type]['patterns'].append(p)

        return dict(sorted(markets.items(), key=lambda x: x[1]['wins'], reverse=True))

    def _analyze_entry_strategies(self) -> Dict[str, int]:
        """Analyse quelles stratégies d'entrée marchent le mieux"""
        strategies = {}
        for p in self.success_patterns:
            if p.success_level in (SuccessLevel.WON_HIGH, SuccessLevel.WON_MID, SuccessLevel.WON_LOW):
                if p.entry_strategy:
                    strategies[p.entry_strategy] = strategies.get(p.entry_strategy, 0) + 1
        return dict(sorted(strategies.items(), key=lambda x: x[1], reverse=True))

    def _generate_adaptations(self, sector_analysis: Dict, geo_analysis: Dict,
                             market_analysis: Dict, strategy_analysis: Dict) -> List[AdaptationDirective]:
        """Génère des directives d'adaptation basées sur l'analyse"""
        directives = []

        # Directive 1: Prioriser les secteurs gagnants
        if sector_analysis:
            top_sector = list(sector_analysis.keys())[0]
            if sector_analysis[top_sector]['wins'] >= 3:
                directives.append(AdaptationDirective(
                    target_area="market_detection",
                    old_approach="Scan équilibré tous secteurs",
                    new_approach=f"Prioriser secteur {top_sector} (3x+ victoires)",
                    reason=f"{sector_analysis[top_sector]['wins']} deals gagnés | "
                          f"{sector_analysis[top_sector]['total_value']:,.0f} EUR",
                    supporting_patterns=sector_analysis[top_sector]['wins'],
                    confidence=0.85,
                ))

        # Directive 2: Prioriser les géographies performantes
        if geo_analysis:
            top_geo = list(geo_analysis.keys())[0]
            if geo_analysis[top_geo]['wins'] >= 2:
                directives.append(AdaptationDirective(
                    target_area="geographic_focus",
                    old_approach="Focus géographique standard",
                    new_approach=f"Intensifier chasse {top_geo}",
                    reason=f"{geo_analysis[top_geo]['wins']} victoires confirmées",
                    supporting_patterns=geo_analysis[top_geo]['wins'],
                    confidence=0.80,
                ))

        # Directive 3: Adopter les stratégies gagnantes
        if strategy_analysis:
            top_strategy = list(strategy_analysis.keys())[0]
            directives.append(AdaptationDirective(
                target_area="entry_strategy",
                old_approach="Approche générique multi-canal",
                new_approach=top_strategy,
                reason=f"{strategy_analysis[top_strategy]} conversions réussies",
                supporting_patterns=strategy_analysis[top_strategy],
                confidence=0.75,
            ))

        return directives

    def _get_best_strategies(self, strategy_analysis: Dict) -> List[str]:
        """Retourne top 3 stratégies"""
        return list(strategy_analysis.keys())[:3]

    def get_recommendations(self, sector: str = "", geography: str = "") -> Dict[str, Any]:
        """
        Obtenir des recommandations pour un secteur/géographie donné.
        Utilisé par le moteur V19.2 pour adapter les approches.
        """
        recommendations = {
            'entry_strategy': 'Approche humanisée via réseaux locaux',
            'value_proposition': 'Expertise unique + discrétion absolue',
            'confidence_boost': 0,
            'suggested_budget_range': '5k-20k',
        }

        # Rechercher des patterns similaires
        similar_patterns = [
            p for p in self.success_patterns
            if (not sector or p.sector == sector) and (not geography or p.geography == geography)
            and p.success_level in (SuccessLevel.WON_HIGH, SuccessLevel.WON_MID, SuccessLevel.WON_LOW)
        ]

        if similar_patterns:
            # Prendre la stratégie la plus fréquente
            strategies = [p.entry_strategy for p in similar_patterns if p.entry_strategy]
            if strategies:
                from collections import Counter
                most_common = Counter(strategies).most_common(1)[0][0]
                recommendations['entry_strategy'] = most_common

            # Boost de confiance si patterns multiples
            recommendations['confidence_boost'] = min(0.2, len(similar_patterns) * 0.05)

        return recommendations

    def get_stats(self) -> Dict[str, Any]:
        """Statistiques du moteur d'apprentissage"""
        wins = sum(1 for p in self.success_patterns
                  if p.success_level in (SuccessLevel.WON_HIGH, SuccessLevel.WON_MID, SuccessLevel.WON_LOW))

        return {
            'learning_cycles': self.learning_cycles,
            'total_patterns': len(self.success_patterns),
            'wins_recorded': wins,
            'adaptation_directives': len(self.adaptation_directives),
            'directives_applied': sum(1 for d in self.adaptation_directives if d.applied),
        }

    def _save(self) -> None:
        try:
            data = {
                'success_patterns': [asdict(p) for p in self.success_patterns],
                'adaptation_directives': [asdict(d) for d in self.adaptation_directives],
                'learning_cycles': self.learning_cycles,
                'saved_at': time.time(),
            }
            # Convertir Enums en valeurs
            for p in data['success_patterns']:
                p['success_level'] = p['success_level'].value if hasattr(p['success_level'], 'value') else p['success_level']

            tmp = LEARNING_DATA.with_suffix('.tmp')
            tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
            tmp.replace(LEARNING_DATA)
        except Exception as e:
            log.warning(f"[V19.2][LEARNING] Save error: {e}")

    def _load(self) -> None:
        try:
            if not LEARNING_DATA.exists():
                return
            data = json.loads(LEARNING_DATA.read_text(encoding='utf-8'))

            for p_data in data.get('success_patterns', []):
                try:
                    p_data['success_level'] = SuccessLevel(p_data['success_level'])
                    self.success_patterns.append(SuccessPattern(**p_data))
                except Exception:
                    pass

            for d_data in data.get('adaptation_directives', []):
                try:
                    self.adaptation_directives.append(AdaptationDirective(**d_data))
                except Exception:
                    pass

            self.learning_cycles = data.get('learning_cycles', 0)
        except Exception as e:
            log.warning(f"[V19.2][LEARNING] Load error: {e}")


# Singleton
_ENGINE: Optional[AutoLearningEngine] = None


def get_auto_learning_engine() -> AutoLearningEngine:
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = AutoLearningEngine()
    return _ENGINE


# Export API
async def run_learning_cycle() -> Dict[str, Any]:
    """API: Lance un cycle d'apprentissage et d'adaptation"""
    engine = get_auto_learning_engine()
    return await engine.analyze_and_adapt()
