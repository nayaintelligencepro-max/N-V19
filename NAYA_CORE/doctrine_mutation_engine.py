"""NAYA — Doctrine Mutation Engine

Moteur d'évolution des doctrines NAYA en fonction des résultats observés.
Permet au système d'adapter ses règles d'action selon les performances réelles.
"""
from typing import Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


@dataclass
class DoctrineMutation:
    """Représente une mutation proposée de la doctrine."""
    doctrine_id: str
    parameter: str
    old_value: Any
    new_value: Any
    rationale: str
    confidence: float
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class DoctrineMutationEngine:
    """
    Moteur de mutation doctrinale — adapte les règles NAYA
    selon les KPIs observés et les résultats business.
    Contrainte constitutionnelle : plancher 1000€/mission inviolable.
    """

    IMMUTABLE_DOCTRINES = {
        "minimum_price_floor": 1000,
        "reapers_always_active": True,
        "client_sovereignty": True,
    }

    def __init__(self):
        self._mutations: List[DoctrineMutation] = []
        self._active_doctrines: Dict[str, Any] = {}
        self._mutation_history: List[DoctrineMutation] = []

    def propose_mutation(self, doctrine_id: str, parameter: str,
                         new_value: Any, rationale: str,
                         confidence: float = 0.8) -> DoctrineMutation:
        """Propose une mutation de doctrine. Vérifie les contraintes immuables."""
        if doctrine_id in self.IMMUTABLE_DOCTRINES:
            logger.warning(f"Doctrine immuable {doctrine_id} — mutation refusée")
            raise ValueError(f"Doctrine {doctrine_id} est constitutionnellement immuable")

        old_value = self._active_doctrines.get(doctrine_id, {}).get(parameter)
        mutation = DoctrineMutation(
            doctrine_id=doctrine_id,
            parameter=parameter,
            old_value=old_value,
            new_value=new_value,
            rationale=rationale,
            confidence=confidence,
        )
        self._mutations.append(mutation)
        logger.info(f"Mutation proposée: {doctrine_id}.{parameter} → {new_value} (conf={confidence})")
        return mutation

    def apply_mutation(self, mutation: DoctrineMutation) -> bool:
        """Applique une mutation si elle est valide et au-dessus du seuil de confiance."""
        if mutation.confidence < 0.7:
            logger.warning(f"Confiance insuffisante ({mutation.confidence}) pour {mutation.doctrine_id}")
            return False

        self._active_doctrines.setdefault(mutation.doctrine_id, {})[mutation.parameter] = mutation.new_value
        self._mutation_history.append(mutation)
        self._mutations = [m for m in self._mutations if m is not mutation]
        return True

    def get_doctrine_state(self, doctrine_id: str) -> Dict:
        """Retourne l'état actuel d'une doctrine."""
        return self._active_doctrines.get(doctrine_id, {})

    def get_pending_mutations(self) -> List[DoctrineMutation]:
        """Liste les mutations en attente d'approbation."""
        return list(self._mutations)

    def get_mutation_history(self, limit: int = 50) -> List[DoctrineMutation]:
        """Retourne l'historique des mutations appliquées."""
        return self._mutation_history[-limit:]

    def propose_mutations(self, kpis: Dict, context: Dict = None) -> List[DoctrineMutation]:
        """
        Propose des mutations automatiques basées sur les KPIs observés.
        Retourne une liste de mutations ordonnées par priorité.
        """
        mutations = []
        context = context or {}

        # Analyser les KPIs et proposer des adaptations
        conv_rate = kpis.get("conversion_rate", 0)
        avg_deal = kpis.get("avg_deal_size_eur", 0)
        scan_interval = kpis.get("scan_interval_s", 1800)
        missions_failed = kpis.get("missions_failed_rate", 0)

        # Si taux de conversion < 10% → réduire le prix minimum
        if conv_rate < 10 and avg_deal > 0:
            try:
                m = self.propose_mutation(
                    "pricing_strategy", "base_floor_multiplier",
                    new_value=0.85,
                    rationale=f"Taux conversion {conv_rate}% < 10% — réduire barrière prix de 15%",
                    confidence=0.75,
                )
                mutations.append(m)
            except ValueError:
                pass

        # Si missions échouées > 20% → réduire agressivité de la chasse
        if missions_failed > 0.2:
            try:
                m = self.propose_mutation(
                    "hunt_strategy", "sectors_per_cycle",
                    new_value=3,
                    rationale=f"Taux échec {missions_failed:.0%} → réduire à 3 secteurs/cycle",
                    confidence=0.8,
                )
                mutations.append(m)
            except ValueError:
                pass

        # Si scan_interval > 3600s → accélérer les scans si résultats bons
        if scan_interval > 3600 and conv_rate > 20:
            try:
                m = self.propose_mutation(
                    "revenue_engine", "scan_interval_s",
                    new_value=900,
                    rationale=f"Conversion {conv_rate}% élevée → scan 15 min pour capitaliser",
                    confidence=0.85,
                )
                mutations.append(m)
            except ValueError:
                pass

        # Si bon pipeline → proposer expansion de secteurs
        if avg_deal > 5000 and conv_rate > 15:
            try:
                m = self.propose_mutation(
                    "hunt_strategy", "expansion_mode",
                    new_value="aggressive",
                    rationale=f"Deal moyen {avg_deal:,.0f}€ + conversion {conv_rate}% → expansion agressive",
                    confidence=0.9,
                )
                mutations.append(m)
            except ValueError:
                pass

        logger.info(f"[DOCTRINE] {len(mutations)} mutations proposées depuis {len(kpis)} KPIs")
        return mutations

    def get_status(self) -> Dict:
        """État complet du moteur de mutation doctrinale."""
        return {
            "engine": "DoctrineMutationEngine",
            "immutable_doctrines": list(self.IMMUTABLE_DOCTRINES.keys()),
            "active_doctrines": len(self._active_doctrines),
            "pending_mutations": len(self._mutations),
            "mutations_applied": len(self._mutation_history),
            "doctrine_states": {
                k: v for k, v in self._active_doctrines.items()
            },
            "pending": [
                {"id": m.doctrine_id, "param": m.parameter,
                 "new_value": m.new_value, "confidence": m.confidence}
                for m in self._mutations[-5:]
            ],
        }


_dme_instance = None
_dme_lock = __import__('threading').Lock()

def get_doctrine_engine() -> DoctrineMutationEngine:
    global _dme_instance
    if _dme_instance is None:
        with _dme_lock:
            if _dme_instance is None:
                _dme_instance = DoctrineMutationEngine()
    return _dme_instance
