"""
NAYA — Pain Silence Engine
Détecte les douleurs cachées = opportunités premium non concurrencées.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum

class SilenceType(Enum):
    INSTITUTIONAL = "institutional"   # Douleur que les institutions cachent
    SHAME_BASED = "shame_based"       # Trop honteux pour demander de l'aide
    UNKNOWN = "unknown"               # Ne sait pas que la solution existe
    COST_PERCEPTION = "cost_perception" # Croit que c'est trop cher
    COMPLEXITY = "complexity"         # Croit que c'est trop compliqué

@dataclass
class LatentPain:
    id: str; name: str; description: str
    silence_type: SilenceType
    affected_market_size: int        # Nb d'entreprises touchées
    avg_financial_loss_monthly: float
    willingness_to_pay_once_aware: float  # 0-1
    detection_difficulty: float      # 0-1 (1 = très difficile)
    monetizable_value_annual: float
    trigger_signals: List[str] = field(default_factory=list)

    @property
    def opportunity_score(self):
        return (self.willingness_to_pay_once_aware * 0.4 +
                self.detection_difficulty * 0.3 +
                min(self.monetizable_value_annual/500000, 1) * 0.3)

class PainSilenceEngine:
    """Révèle les douleurs cachées = blue ocean garanti."""

    LATENT_PAINS = [
        LatentPain("PS01","Perte d'argent sur congés non pris","RH — milliers €/an perdus",
            SilenceType.UNKNOWN, 500000, 8000, 0.85, 0.7, 96000,
            ["gestion RH manuelle","excel congés","no-show vacances"]),
        LatentPain("PS02","Inefficacité réunions","3-5h/semaine perdues par manager",
            SilenceType.SHAME_BASED, 2000000, 5000, 0.70, 0.5, 60000,
            ["trop de réunions","réunions inutiles","pas de compte-rendu"]),
        LatentPain("PS03","Turnover coûteux ignoré","Recrutement = 6-9 mois de salaire",
            SilenceType.COST_PERCEPTION, 300000, 15000, 0.80, 0.6, 180000,
            ["turnover élevé","difficultés recrutement","formation constante"]),
        LatentPain("PS04","Data non monétisée","Entreprises ont des données valant des milliers",
            SilenceType.UNKNOWN, 400000, 10000, 0.90, 0.8, 120000,
            ["données clients","historique ventes","comportements ignorés"]),
        LatentPain("PS05","Créances prescrites","Dettes légalement récupérables mais abandonnées",
            SilenceType.INSTITUTIONAL, 200000, 25000, 0.95, 0.9, 300000,
            ["impayés anciens","dossiers classés","relances arrêtées"]),
    ]

    def detect(self, market_signals: List[str]) -> List[LatentPain]:
        detected = []
        signals_lower = " ".join(market_signals).lower()
        for pain in self.LATENT_PAINS:
            hits = sum(1 for trigger in pain.trigger_signals if trigger in signals_lower)
            if hits > 0:
                detected.append(pain)
        return sorted(detected, key=lambda p: p.opportunity_score, reverse=True)

    def quantify_market(self, pain: LatentPain) -> Dict:
        tam = pain.affected_market_size * pain.avg_financial_loss_monthly * 12
        sam = tam * pain.willingness_to_pay_once_aware * 0.3
        som = sam * 0.05
        return {"TAM": int(tam), "SAM": int(sam), "SOM": int(som),
                "opportunity_score": round(pain.opportunity_score, 2)}
class PainAnalyzer:
    def analyze(self, pain): return {'score': 0.7, 'monetizable': True}

# ─── Aliases et classes manquantes pour compatibilité __init__ ─────────────
from dataclasses import dataclass
from typing import List

class PainLevel:
    LOW = "low"; MEDIUM = "medium"; HIGH = "high"; CRITICAL = "critical"

@dataclass
class PainPoint:
    id: str; name: str; level: str; financial_impact: float

@dataclass  
class SilencePattern:
    id: str; name: str; silence_type: SilenceType; market_size: int

class PainAnalyzer:
    def analyze(self, context: dict) -> dict:
        return {"pain_detected": True, "score": 0.75, "level": PainLevel.HIGH}

class SilenceAnalyzer:
    def detect(self, signals: List[str]) -> List[SilencePattern]:
        return [SilencePattern("S01", "Douleur cachée", SilenceType.UNKNOWN, 100000)]
