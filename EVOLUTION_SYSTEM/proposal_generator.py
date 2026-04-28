"""
NAYA V19 — Proposal Generator
══════════════════════════════════════════════════════════════════════════════
Génère des propositions d'évolution contextuelles basées sur les KPIs réels.

LOGIQUE:
  Chaque proposition est déclenchée par un seuil KPI précis :
  - Taux de conversion < 10% → améliorer qualification des leads
  - MRR < cible → activer les streams d'abonnement
  - Taux d'automation < 50% → automatiser les tâches répétitives
  - SHI < 0.6 → renforcer la résilience du système
  - Ticket moyen stagnant → cibler tiers supérieur
  - Slots parallèles saturés → préparer scaling

GARANTIE: Toute proposition est classée par ROI attendu × facilité d'exécution.
══════════════════════════════════════════════════════════════════════════════
"""
import time
import logging
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum

log = logging.getLogger("NAYA.PROPOSAL_GENERATOR")


class ProposalType(Enum):
    REVENUE       = "revenue"
    HUNT          = "hunt"
    AUTOMATION    = "automation"
    RESILIENCE    = "resilience"
    SCALING       = "scaling"
    QUALIFICATION = "qualification"
    RETENTION     = "retention"
    EXPANSION     = "expansion"


@dataclass
class Proposal:
    """Proposition d'évolution concrète avec ROI estimé."""
    id: str
    type: ProposalType
    title: str
    description: str
    trigger: str                # Condition KPI qui a déclenché la proposition
    expected_roi: float         # ROI attendu [0..1] — 1.0 = doublage performance
    execution_effort: float     # Effort d'exécution [0..1] — 0=facile, 1=difficile
    priority_score: float       # = expected_roi × (1 - execution_effort)
    actions: List[str]          # Actions concrètes à prendre
    metrics_to_watch: List[str] # KPIs à surveiller après application
    ts: float = field(default_factory=time.time)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "title": self.title,
            "description": self.description,
            "trigger": self.trigger,
            "expected_roi": round(self.expected_roi, 3),
            "execution_effort": round(self.execution_effort, 3),
            "priority_score": round(self.priority_score, 3),
            "actions": self.actions,
            "metrics_to_watch": self.metrics_to_watch,
        }


# ── Règles de génération ──────────────────────────────────────────────────────
# Chaque règle = (id, condition_fn, proposal_factory)

def _make(pid: str, ptype: ProposalType, title: str, desc: str, trigger: str,
          roi: float, effort: float, actions: List[str], metrics: List[str]) -> Proposal:
    return Proposal(
        id=pid, type=ptype, title=title, description=desc, trigger=trigger,
        expected_roi=roi, execution_effort=effort,
        priority_score=round(roi * (1 - effort), 3),
        actions=actions, metrics_to_watch=metrics,
    )


class ProposalGenerator:
    """
    Génère des propositions d'évolution contextuelles et prioritisées.
    Basé sur les KPIs réels — zéro placeholder.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._generated: List[Proposal] = []
        self._applied: List[str] = []
        self._init_at = time.time()

    def generate_alternatives(self, context: Dict) -> List[Proposal]:
        """
        Génère des propositions d'évolution basées sur le contexte KPI.

        Args:
            context: dict avec clés revenue_growth, conversion_rate, automation_rate,
                     mrr, avg_ticket_eur, shi_score, active_slots, max_slots, etc.

        Returns:
            Liste de propositions triées par priority_score décroissant.
        """
        with self._lock:
            proposals: List[Proposal] = []

            conv = context.get("conversion_rate", 0.0)
            mrr = context.get("mrr", 0.0)
            mrr_target = context.get("mrr_target", 20_000.0)
            automation = context.get("automation_rate", 0.0)
            shi = context.get("shi_score", 0.5)
            avg_ticket = context.get("avg_ticket_eur", 0.0)
            active_slots = context.get("active_slots", 4)
            max_slots = context.get("max_slots", 4)
            revenue_growth = context.get("revenue_growth", 0.0)
            churn = context.get("churn_rate", 0.0)
            hunt_quality = context.get("hunt_quality_score", 0.5)

            # ── Règle 1 : Conversion faible ─────────────────────────────────
            if conv < 0.10:
                proposals.append(_make(
                    "P_CONV_01", ProposalType.QUALIFICATION,
                    "Améliorer la qualification des leads",
                    f"Taux de conversion actuel {conv:.1%} < seuil 10%. "
                    "Renforcer le scoring avant outreach pour ne cibler que les leads ≥ 65/100.",
                    f"conversion_rate={conv:.1%} < 10%",
                    roi=0.35, effort=0.25,
                    actions=[
                        "Augmenter le seuil minimum de score lead à 65/100",
                        "Activer la validation budget AVANT d'envoyer une offre",
                        "Ajouter signal 'deadline réglementaire' dans le scoring",
                        "Retirer les leads sans email vérifié de la séquence",
                    ],
                    metrics=["conversion_rate", "avg_ticket_eur", "hunt_quality_score"],
                ))

            # ── Règle 2 : MRR loin de la cible ──────────────────────────────
            if mrr < mrr_target * 0.5:
                gap = mrr_target - mrr
                proposals.append(_make(
                    "P_MRR_01", ProposalType.REVENUE,
                    "Activer les streams d'abonnement récurrents",
                    f"MRR actuel {mrr:,.0f}€, cible {mrr_target:,.0f}€ (gap {gap:,.0f}€). "
                    "Convertir les deals one-shot en contrats mensuels.",
                    f"mrr={mrr:.0f}€ < {mrr_target*0.5:.0f}€ (50% cible)",
                    roi=0.45, effort=0.30,
                    actions=[
                        "Proposer monitoring mensuel 2k-5k€/mois à tous les clients actifs",
                        "Créer offre abonnement NIS2 Checker 500€/mois",
                        "Upsell contrat annuel avec -10% sur tous les deals en cours",
                        "Objectif: 5 clients × 2k€/mois = 10k€ MRR en 30j",
                    ],
                    metrics=["mrr", "churn_rate", "subscription_count"],
                ))

            # ── Règle 3 : Automation faible ──────────────────────────────────
            if automation < 0.50:
                proposals.append(_make(
                    "P_AUTO_01", ProposalType.AUTOMATION,
                    "Automatiser les tâches répétitives identifiées",
                    f"Taux d'automation {automation:.1%} < 50%. "
                    "Chaque heure gagnée = heure investie en chasse haute valeur.",
                    f"automation_rate={automation:.1%} < 50%",
                    roi=0.40, effort=0.20,
                    actions=[
                        "Activer la séquence de relance automatique J+3/J+7/J+14",
                        "Automatiser l'envoi du rapport hebdomadaire PDF",
                        "Brancher le deal_risk_scorer sur les alertes Telegram",
                        "Activer le recyclage automatique des assets contenu",
                    ],
                    metrics=["automation_rate", "time_per_deal_hours", "outreach_open_rate"],
                ))

            # ── Règle 4 : SHI critique ───────────────────────────────────────
            if shi < 0.60:
                proposals.append(_make(
                    "P_SHI_01", ProposalType.RESILIENCE,
                    "Renforcer la résilience du système",
                    f"SHI={shi:.2f} < 0.60 — système fragile. "
                    "Activer les fallbacks et sécuriser les composants critiques.",
                    f"shi_score={shi:.2f} < 0.60",
                    roi=0.30, effort=0.15,
                    actions=[
                        "Vérifier tous les fallbacks LLM (Groq→DeepSeek→Templates)",
                        "Activer le mode dégradé pour les composants à risque",
                        "Lancer un scan Guardian complet (Agent 11)",
                        "Sauvegarder l'état du pipeline dans data/exports/",
                    ],
                    metrics=["shi_score", "error_rate", "guardian_alerts"],
                ))

            # ── Règle 5 : Ticket moyen stagnant ──────────────────────────────
            if 0 < avg_ticket < 10_000:
                proposals.append(_make(
                    "P_TICKET_01", ProposalType.HUNT,
                    "Monter en gamme — cibler TIER2/TIER3",
                    f"Ticket moyen {avg_ticket:,.0f}€ < 10k€. "
                    "Concentrer la chasse sur des décideurs avec budget ≥ 15k€.",
                    f"avg_ticket_eur={avg_ticket:.0f}€ < 10000€",
                    roi=0.50, effort=0.35,
                    actions=[
                        "Filtrer la chasse Apollo sur entreprises > 500 employés",
                        "Cibler RSSI et DSI (pas DPO ou responsable IT junior)",
                        "Pitcher Pack Sécurité Avancée 40k€ en priorité",
                        "Qualifier explicitement le budget AVANT le pitch",
                    ],
                    metrics=["avg_ticket_eur", "conversion_rate", "hunt_quality_score"],
                ))

            # ── Règle 6 : Slots parallèles saturés ───────────────────────────
            if active_slots >= max_slots and max_slots < 8:
                proposals.append(_make(
                    "P_SCALE_01", ProposalType.SCALING,
                    "Préparer le scaling des slots parallèles",
                    f"Tous les {max_slots} slots actifs sont occupés. "
                    "Préparer l'augmentation à {max_slots+2} slots si SHI le permet.",
                    f"active_slots={active_slots} == max_slots={max_slots}",
                    roi=0.60, effort=0.40,
                    actions=[
                        f"Valider SHI ≥ 0.75 avant d'activer le slot {max_slots+1}",
                        "Préparer 2 nouveaux projets en queue (priorité ≥ 0.80)",
                        "Vérifier que le scheduler peut absorber +2 projets parallèles",
                        "Activer le DynamicScaler si conversion_rate ≥ 15%",
                    ],
                    metrics=["active_slots", "shi_score", "conversion_rate", "revenue_per_slot"],
                ))

            # ── Règle 7 : Croissance revenue négative ────────────────────────
            if revenue_growth < 0:
                proposals.append(_make(
                    "P_REV_NEG_01", ProposalType.REVENUE,
                    "Inverser la tendance revenue — action urgente",
                    f"Croissance revenue {revenue_growth:.1%} est négative. "
                    "Activer une campagne cash rapide sous 48h.",
                    f"revenue_growth={revenue_growth:.1%} < 0",
                    roi=0.55, effort=0.20,
                    actions=[
                        "Appeler 3 clients existants pour upsell immédiat",
                        "Lancer une formation OT 1j à 5k€ (livraison PDF immédiate)",
                        "Proposer audit flash 72h à 3k€ sur 2 prospects chauds",
                        "Créer lien PayPal pour paiement immédiat",
                    ],
                    metrics=["revenue_growth", "mrr", "deals_closed_this_week"],
                ))

            # ── Règle 8 : Churn élevé ────────────────────────────────────────
            if churn > 0.05:
                proposals.append(_make(
                    "P_CHURN_01", ProposalType.RETENTION,
                    "Réduire le churn — programme fidélisation",
                    f"Taux de churn {churn:.1%} > 5%. "
                    "Chaque client perdu = 12× son MRR en coût d'acquisition.",
                    f"churn_rate={churn:.1%} > 5%",
                    roi=0.45, effort=0.25,
                    actions=[
                        "Contacter tous les clients à risque (dernière interaction > 30j)",
                        "Proposer QBR (Quarterly Business Review) gratuit",
                        "Offrir 1 mois gratuit en échange d'un contrat annuel",
                        "Activer les success stories clients dans le contenu",
                    ],
                    metrics=["churn_rate", "mrr", "nps_score", "client_engagement_score"],
                ))

            # ── Règle 9 : Qualité chasse faible ──────────────────────────────
            if hunt_quality < 0.60:
                proposals.append(_make(
                    "P_HUNT_01", ProposalType.HUNT,
                    "Améliorer la qualité de la chasse",
                    f"Score qualité chasse {hunt_quality:.2f} < 0.60. "
                    "Enrichir les signaux et affiner les critères de détection.",
                    f"hunt_quality_score={hunt_quality:.2f} < 0.60",
                    roi=0.40, effort=0.30,
                    actions=[
                        "Ajouter le signal 'offre emploi RSSI OT' comme déclencheur prioritaire",
                        "Croiser signaux Serper + Apollo pour enrichissement double",
                        "Filtrer sur entreprises ayant une OT exposée (SCADA visible)",
                        "Activer le scanner d'appels d'offres BOAMP",
                    ],
                    metrics=["hunt_quality_score", "leads_per_week", "enrichment_rate"],
                ))

            # ── Règle 10 : Expansion géographique ────────────────────────────
            if revenue_growth > 0.20 and mrr > mrr_target * 0.80:
                proposals.append(_make(
                    "P_EXP_01", ProposalType.EXPANSION,
                    "Expansion géographique — Moyen-Orient ou Afrique",
                    f"Croissance {revenue_growth:.1%} et MRR {mrr:,.0f}€ solides. "
                    "Moment idéal pour ouvrir un nouveau marché géographique.",
                    f"revenue_growth={revenue_growth:.1%} > 20% AND mrr ≥ 80% cible",
                    roi=0.70, effort=0.60,
                    actions=[
                        "Contacter 5 RSSI industriels UAE/KSA via LinkedIn",
                        "Adapter le catalogue OT en anglais et arabe",
                        "Identifier un partenaire local intégrateur industriel",
                        "Pitch Pack Sécurité Avancée 40k€ adapté Vision 2030",
                    ],
                    metrics=["new_market_revenue", "international_deals", "pipeline_geo_diversity"],
                ))

            # Trier par priorité décroissante
            proposals.sort(key=lambda p: p.priority_score, reverse=True)

            # Enregistrer dans l'historique
            self._generated.extend(proposals)
            if len(self._generated) > 1000:
                self._generated = self._generated[-500:]

            log.info("[PROPOSAL_GENERATOR] %d propositions générées (context=%s)",
                     len(proposals), {k: context[k] for k in list(context)[:4]})
            return proposals

    def rank_by_roi(self, proposals: List[Proposal]) -> List[Proposal]:
        """Trie une liste de propositions par ROI attendu décroissant."""
        return sorted(proposals, key=lambda p: p.expected_roi, reverse=True)

    def filter_by_type(self, proposals: List[Proposal], ptype: ProposalType) -> List[Proposal]:
        """Filtre les propositions par type."""
        return [p for p in proposals if p.type == ptype]

    def mark_applied(self, proposal_id: str) -> None:
        """Marque une proposition comme appliquée."""
        with self._lock:
            if proposal_id not in self._applied:
                self._applied.append(proposal_id)

    def get_stats(self) -> Dict:
        with self._lock:
            return {
                "total_generated": len(self._generated),
                "total_applied": len(self._applied),
                "application_rate": round(len(self._applied) / max(len(self._generated), 1), 3),
                "uptime_seconds": int(time.time() - self._init_at),
            }
