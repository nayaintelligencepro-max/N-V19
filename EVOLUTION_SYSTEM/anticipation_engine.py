"""
NAYA V19 — Anticipation Engine
══════════════════════════════════════════════════════════════════════════════
Anticipe les opportunités marché sur un horizon de 36 mois (3 ans).

DOCTRINE:
  Agir AVANT le marché. Voir 3 ans devant pour préparer 3 mois à l'avance.
  Chaque cycle réglementaire, technologique ou économique prévisible
  est une opportunité commerciale à préparer maintenant.

STRUCTURE:
  - Roadmap 36 mois avec jalons cibles (EUR)
  - Moteur de tendances macro (réglementaire, techno, marché)
  - File d'opportunités anticipées triées par valeur × probabilité × proximité
  - Adaptation trimestrielle automatique basée sur performance réelle

OUTPUT:
  - Liste d'opportunités anticipées pour les 90 prochains jours
  - Jalons objectifs glissants pour le mois courant
  - Recommandations d'actions préventives
══════════════════════════════════════════════════════════════════════════════
"""
import json
import logging
import math
import threading
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

log = logging.getLogger("NAYA.ANTICIPATION")

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "cache" / "anticipation_engine.json"


# ─── Roadmap OODA M1→M36 ──────────────────────────────────────────────────────

ROADMAP_M1_M36: Dict[int, Dict] = {
    # M1-M6 : Observe → Orient
    1:  {"target": 5_000,   "max": 12_000,  "phase": "OBSERVE",   "focus": "Cartographier 50 prospects OT"},
    2:  {"target": 15_000,  "max": 25_000,  "phase": "ORIENT",    "focus": "Qualifier top 10, pitcher Audit Express"},
    3:  {"target": 25_000,  "max": 40_000,  "phase": "DECIDE",    "focus": "3 deals chauds, closing calls"},
    4:  {"target": 35_000,  "max": 50_000,  "phase": "ACT",       "focus": "Convertir one-shot en récurrents"},
    5:  {"target": 45_000,  "max": 60_000,  "phase": "OBSERVE",   "focus": "Partenariats Siemens/ABB + upsell"},
    6:  {"target": 60_000,  "max": 80_000,  "phase": "ORIENT",    "focus": "Lancer SaaS NIS2 MVP + MRR"},
    # M7-M12 : Scale
    7:  {"target": 70_000,  "max": 90_000,  "phase": "DECIDE",    "focus": "3 grands comptes CAC40 OT"},
    8:  {"target": 80_000,  "max": 100_000, "phase": "ACT",       "focus": "MRR 10k€ + deal Premium 80k€"},
    9:  {"target": 85_000,  "max": 110_000, "phase": "OBSERVE",   "focus": "Analyser conversion par secteur"},
    10: {"target": 90_000,  "max": 115_000, "phase": "ORIENT",    "focus": "Upsell 100% clients +30%"},
    11: {"target": 95_000,  "max": 120_000, "phase": "DECIDE",    "focus": "Contrats annuels avant clôture budgets"},
    12: {"target": 100_000, "max": 130_000, "phase": "ACT",       "focus": "2 consultants OT + MRR >20k€"},
    # M13-M18 : Consolidation
    13: {"target": 110_000, "max": 140_000, "phase": "OBSERVE",   "focus": "Audit concurrentiel complet marché OT"},
    14: {"target": 120_000, "max": 150_000, "phase": "ORIENT",    "focus": "Lancer plateforme SaaS IEC 62443 complète"},
    15: {"target": 130_000, "max": 165_000, "phase": "DECIDE",    "focus": "Deal institutionnel OIV 100k+"},
    16: {"target": 140_000, "max": 175_000, "phase": "ACT",       "focus": "MRR 30k€ — 15 clients SaaS"},
    17: {"target": 150_000, "max": 185_000, "phase": "OBSERVE",   "focus": "Explorer marchés Moyen-Orient OT"},
    18: {"target": 160_000, "max": 200_000, "phase": "ORIENT",    "focus": "Partenariat grand intégrateur"},
    # M19-M24 : Expansion géographique
    19: {"target": 170_000, "max": 210_000, "phase": "DECIDE",    "focus": "Premier deal Moyen-Orient (EAU/KSA)"},
    20: {"target": 180_000, "max": 225_000, "phase": "ACT",       "focus": "Office Polynésie → Hub Pacifique"},
    21: {"target": 190_000, "max": 235_000, "phase": "OBSERVE",   "focus": "Veille AI/OT convergence"},
    22: {"target": 200_000, "max": 250_000, "phase": "ORIENT",    "focus": "Produit AI-OT Security lance"},
    23: {"target": 210_000, "max": 265_000, "phase": "DECIDE",    "focus": "3 clients référence internationaux"},
    24: {"target": 225_000, "max": 280_000, "phase": "ACT",       "focus": "Équipe 5 personnes + MRR 50k€"},
    # M25-M30 : Industrialisation
    25: {"target": 240_000, "max": 300_000, "phase": "OBSERVE",   "focus": "Analyse NIS2 wave 2 compliance"},
    26: {"target": 255_000, "max": 315_000, "phase": "ORIENT",    "focus": "Offre compliance-as-a-service"},
    27: {"target": 270_000, "max": 330_000, "phase": "DECIDE",    "focus": "Accord distribution VAR europée"},
    28: {"target": 285_000, "max": 345_000, "phase": "ACT",       "focus": "20 clients SaaS MRR 70k€"},
    29: {"target": 300_000, "max": 365_000, "phase": "OBSERVE",   "focus": "Positionnement acquisition potentielle"},
    30: {"target": 315_000, "max": 385_000, "phase": "ORIENT",    "focus": "Dossier levée ou acquisition M&A"},
    # M31-M36 : Souveraineté totale
    31: {"target": 330_000, "max": 400_000, "phase": "DECIDE",    "focus": "Valorisation 5M€ ou revenue run rate"},
    32: {"target": 345_000, "max": 420_000, "phase": "ACT",       "focus": "Closing levée ou deal M&A"},
    33: {"target": 360_000, "max": 440_000, "phase": "OBSERVE",   "focus": "Expansion Afrique francophone OT"},
    34: {"target": 375_000, "max": 460_000, "phase": "ORIENT",    "focus": "Hub formation OT certifié IEC"},
    35: {"target": 390_000, "max": 480_000, "phase": "DECIDE",    "focus": "Franchise modèle NAYA × 3 pays"},
    36: {"target": 405_000, "max": 500_000, "phase": "ACT",       "focus": "Souveraineté financière totale atteinte"},
}

# Tendances marché macros prédéfinies avec leur cycle temporel
MACRO_TRENDS = [
    {
        "id": "NIS2_DEADLINE",
        "label": "Deadline NIS2 — obligation conformité",
        "category": "regulatory",
        "sectors": ["energie", "transport", "industrie", "ot"],
        "signal_strength": 0.95,
        "opportunity_eur": 40_000,
        "recurrence_months": 12,
        "description": "Chaque fin d'année réglementaire = pic de demande audit OT/NIS2",
    },
    {
        "id": "BUDGET_Q4",
        "label": "Budgets SI/Sécurité — Q4 entreprises",
        "category": "economic",
        "sectors": ["ot", "transport", "energie"],
        "signal_strength": 0.85,
        "opportunity_eur": 25_000,
        "recurrence_months": 12,
        "description": "Q4 (oct-déc) = consommation budgets sécurité avant clôture",
    },
    {
        "id": "IEC62443_RENEWAL",
        "label": "Renouvellements certifications IEC 62443",
        "category": "regulatory",
        "sectors": ["industrie", "ot"],
        "signal_strength": 0.80,
        "opportunity_eur": 20_000,
        "recurrence_months": 36,
        "description": "Cycle 3 ans de renouvellement certification IEC 62443",
    },
    {
        "id": "CYBER_INCIDENT_WAVE",
        "label": "Vague d'incidents cyber industriels",
        "category": "security_event",
        "sectors": ["ot", "energie", "transport", "industrie"],
        "signal_strength": 0.70,
        "opportunity_eur": 35_000,
        "recurrence_months": 6,
        "description": "Post-incident = pic de demande audit préventif",
    },
    {
        "id": "AI_OT_CONVERGENCE",
        "label": "Convergence AI + OT Security",
        "category": "technology",
        "sectors": ["ot", "industrie"],
        "signal_strength": 0.75,
        "opportunity_eur": 50_000,
        "recurrence_months": 18,
        "description": "Adoption AI dans environnements industriels = nouveaux risques",
    },
    {
        "id": "POLYNESIA_LOCAL",
        "label": "Marché local Polynésie — OPT/EDT/Air Tahiti",
        "category": "geographic",
        "sectors": ["transport", "energie"],
        "signal_strength": 0.72,
        "opportunity_eur": 12_000,
        "recurrence_months": 12,
        "description": "Appels d'offres annuels des opérateurs locaux polynésiens",
    },
    {
        "id": "MIDDLE_EAST_OT",
        "label": "Expansion Moyen-Orient — Vision 2030 Saudi",
        "category": "geographic",
        "sectors": ["energie", "ot"],
        "signal_strength": 0.65,
        "opportunity_eur": 80_000,
        "recurrence_months": 24,
        "description": "Projets massifs industriels Vision 2030 — sécurité OT requise",
    },
    {
        "id": "SME_DIGITAL_TRANSITION",
        "label": "PME — Transition numérique + cybersécurité",
        "category": "economic",
        "sectors": ["industrie", "ot"],
        "signal_strength": 0.68,
        "opportunity_eur": 8_000,
        "recurrence_months": 6,
        "description": "Vague de mise à niveau cybersécurité PME industrielles",
    },
]


# ─── Structures de données ────────────────────────────────────────────────────

@dataclass
class AnticipatedOpportunity:
    """Opportunité anticipée avec horizon temporel."""
    id: str
    trend_id: str
    label: str
    sector: str
    horizon_days: int           # Dans combien de jours cette opportunité se matérialise
    opportunity_eur: float
    probability: float          # [0..1]
    expected_value: float       # opportunity_eur × probability
    action_required: str        # Action à préparer maintenant
    priority_score: float       # Score global pour priorisation
    ts: float = field(default_factory=time.time)


@dataclass
class MonthlyMilestone:
    """Jalon mensuel de la roadmap 36 mois."""
    month: int
    target_eur: float
    max_eur: float
    phase: str
    focus: str
    achieved_eur: float = 0.0
    status: str = "pending"     # "pending", "on_track", "achieved", "exceeded", "behind"
    updated_at: float = field(default_factory=time.time)


# ─── Moteur d'anticipation ────────────────────────────────────────────────────

class AnticipationEngine:
    """
    Anticipe les opportunités marché sur 36 mois.
    Se met à jour automatiquement et s'adapte aux performances réelles.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._milestones: Dict[int, MonthlyMilestone] = self._init_milestones()
        self._opportunities: List[AnticipatedOpportunity] = []
        self._system_start: float = time.time()
        self._current_month: int = 1          # Mois courant dans la roadmap
        self._total_revenue: float = 0.0
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        self._load()
        self._refresh_opportunities()
        log.info("[ANTICIPATION] Engine V19 démarré — %d jalons, %d opportunités",
                 len(self._milestones), len(self._opportunities))

    # ── API publique ──────────────────────────────────────────────────────────

    def get_current_milestone(self) -> MonthlyMilestone:
        """Retourne le jalon du mois courant."""
        with self._lock:
            return self._milestones.get(self._current_month,
                                         self._milestones[max(self._milestones)])

    def get_upcoming_opportunities(self, horizon_days: int = 90) -> List[AnticipatedOpportunity]:
        """Retourne les opportunités dans l'horizon indiqué, triées par priorité."""
        with self._lock:
            self._refresh_opportunities()
            return sorted(
                [o for o in self._opportunities if o.horizon_days <= horizon_days],
                key=lambda x: x.priority_score,
                reverse=True,
            )

    def record_revenue(self, amount_eur: float, month: Optional[int] = None) -> None:
        """Enregistre un revenu réel et met à jour le statut du jalon correspondant."""
        with self._lock:
            m = month or self._current_month
            self._total_revenue += amount_eur
            if m in self._milestones:
                self._milestones[m].achieved_eur += amount_eur
                self._milestones[m].updated_at = time.time()
                self._update_milestone_status(m)
        self._save()
        log.info("[ANTICIPATION] Revenue enregistré: %.0f€ — M%d", amount_eur, m)

    def advance_month(self) -> MonthlyMilestone:
        """Avance au mois suivant de la roadmap."""
        with self._lock:
            self._current_month = min(self._current_month + 1, 36)
            milestone = self._milestones[self._current_month]
            self._refresh_opportunities()
        self._save()
        return milestone

    def get_3year_roadmap(self) -> List[Dict]:
        """Retourne la roadmap complète 36 mois avec statuts."""
        with self._lock:
            return [
                {
                    "month": m.month,
                    "target_eur": m.target_eur,
                    "max_eur": m.max_eur,
                    "phase": m.phase,
                    "focus": m.focus,
                    "achieved_eur": m.achieved_eur,
                    "status": m.status,
                    "is_current": m.month == self._current_month,
                }
                for m in sorted(self._milestones.values(), key=lambda x: x.month)
            ]

    def get_stats(self) -> Dict:
        """Résumé complet de l'état du moteur d'anticipation."""
        with self._lock:
            current = self._milestones.get(self._current_month)
            upcoming = self.get_upcoming_opportunities(90)
            achieved = sum(1 for m in self._milestones.values() if m.status in ("achieved", "exceeded"))
            behind = sum(1 for m in self._milestones.values() if m.status == "behind")
            return {
                "current_month": self._current_month,
                "current_target_eur": current.target_eur if current else 0,
                "current_achieved_eur": current.achieved_eur if current else 0,
                "current_status": current.status if current else "unknown",
                "total_revenue": round(self._total_revenue, 2),
                "milestones_achieved": achieved,
                "milestones_behind": behind,
                "milestones_total": len(self._milestones),
                "upcoming_opportunities_90d": len(upcoming),
                "top_opportunity": {
                    "label": upcoming[0].label,
                    "horizon_days": upcoming[0].horizon_days,
                    "expected_value": upcoming[0].expected_value,
                    "action": upcoming[0].action_required,
                } if upcoming else None,
            }

    # ── Logique interne ───────────────────────────────────────────────────────

    def _init_milestones(self) -> Dict[int, MonthlyMilestone]:
        return {
            month: MonthlyMilestone(
                month=month,
                target_eur=data["target"],
                max_eur=data["max"],
                phase=data["phase"],
                focus=data["focus"],
            )
            for month, data in ROADMAP_M1_M36.items()
        }

    def _update_milestone_status(self, month: int) -> None:
        m = self._milestones[month]
        if m.achieved_eur >= m.max_eur:
            m.status = "exceeded"
        elif m.achieved_eur >= m.target_eur:
            m.status = "achieved"
        elif m.achieved_eur >= m.target_eur * 0.5:
            m.status = "on_track"
        elif m.month < self._current_month:
            m.status = "behind"
        else:
            m.status = "pending"

    def _refresh_opportunities(self) -> None:
        """
        Recalcule la liste des opportunités anticipées à partir des tendances macro.
        Les opportunités sont calculées en fonction du mois courant dans la roadmap.
        """
        opportunities: List[AnticipatedOpportunity] = []
        now = datetime.now(timezone.utc)

        for trend in MACRO_TRENDS:
            # Calculer les prochaines occurrences de la tendance
            recurrence = trend["recurrence_months"]
            for multiplier in range(1, 4):  # 3 prochaines occurrences
                horizon_days = int(recurrence * multiplier * 30.4)
                if horizon_days > 365:  # Limiter à 1 an d'horizon pour action concrète
                    break

                # Probabilité décroît avec l'éloignement temporel
                base_prob = trend["signal_strength"]
                time_decay = math.exp(-horizon_days / (recurrence * 30.4))
                probability = base_prob * (0.5 + 0.5 * time_decay)

                expected_value = trend["opportunity_eur"] * probability

                # Score de priorité : valeur attendue × urgence × proximité actuelle
                proximity_score = 1.0 / (1.0 + horizon_days / 30)
                priority_score = expected_value * proximity_score

                action = self._build_action(trend, horizon_days)

                opp = AnticipatedOpportunity(
                    id=f"{trend['id']}_{multiplier}",
                    trend_id=trend["id"],
                    label=f"{trend['label']} (dans {horizon_days}j)",
                    sector=trend["sectors"][0],
                    horizon_days=horizon_days,
                    opportunity_eur=trend["opportunity_eur"],
                    probability=round(probability, 3),
                    expected_value=round(expected_value, 0),
                    action_required=action,
                    priority_score=round(priority_score, 3),
                )
                opportunities.append(opp)

        self._opportunities = sorted(opportunities, key=lambda x: x.priority_score, reverse=True)

    def _build_action(self, trend: Dict, horizon_days: int) -> str:
        """Construit l'action préventive recommandée."""
        days_to_act = max(0, horizon_days - 14)  # Agir 14j avant l'opportunité
        if trend["category"] == "regulatory":
            return f"Préparer pitch NIS2/IEC62443 → envoyer dans {days_to_act}j"
        elif trend["category"] == "economic":
            return f"Contacter 5 prospects secteur {trend['sectors'][0]} dans {days_to_act}j"
        elif trend["category"] == "security_event":
            return f"Activer séquence outreach post-incident → {days_to_act}j"
        elif trend["category"] == "technology":
            return f"Produire contenu AI+OT → pipeline dans {days_to_act}j"
        elif trend["category"] == "geographic":
            return f"Adapter catalogue pour marché {trend['sectors'][0]} → {days_to_act}j"
        return f"Préparer offre {trend['label'][:30]} → {days_to_act}j"

    # ── Persistance ───────────────────────────────────────────────────────────

    def _save(self) -> None:
        try:
            data = {
                "milestones": {str(m): asdict(ms) for m, ms in self._milestones.items()},
                "current_month": self._current_month,
                "total_revenue": self._total_revenue,
                "saved_at": time.time(),
            }
            tmp = DATA_FILE.with_suffix(".tmp")
            tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            tmp.replace(DATA_FILE)
        except Exception as e:
            log.warning("[ANTICIPATION] Save error: %s", e)

    def _load(self) -> None:
        try:
            if not DATA_FILE.exists():
                return
            data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            for m_str, ms_dict in data.get("milestones", {}).items():
                m = int(m_str)
                if m in self._milestones:
                    self._milestones[m] = MonthlyMilestone(**ms_dict)
            self._current_month = data.get("current_month", 1)
            self._total_revenue = data.get("total_revenue", 0.0)
        except Exception as e:
            log.warning("[ANTICIPATION] Load error: %s — starting fresh", e)


# ── Singleton ──────────────────────────────────────────────────────────────────
_engine: Optional[AnticipationEngine] = None


def get_anticipation_engine() -> AnticipationEngine:
    global _engine
    if _engine is None:
        _engine = AnticipationEngine()
    return _engine
