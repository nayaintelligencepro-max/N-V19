"""
NAYA V21 — NIS2 Checker SaaS
Score conformité NIS2 0-100 via formulaire 20 questions.
Freemium: scan gratuit (score seul), rapport complet = 500 EUR/mois.
"""
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

log = logging.getLogger("NAYA.SAAS_NIS2.CHECKER")

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "saas_nis2"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ── 20 questions NIS2 (Directive EU 2022/2555) ────────────────────────────────
NIS2_QUESTIONS: List[Dict] = [
    # Gouvernance (25 pts)
    {
        "id": "Q01", "category": "Gouvernance", "weight": 5,
        "text": "Avez-vous désigné un responsable de la sécurité des réseaux et de l'information (RSSI ou équivalent) ?",
        "yes_label": "Oui, RSSI désigné", "no_label": "Non",
        "guidance": "Article 20 NIS2 : obligation de gouvernance pour les entités essentielles et importantes.",
    },
    {
        "id": "Q02", "category": "Gouvernance", "weight": 5,
        "text": "La direction générale est-elle formée et tenue responsable de la cybersécurité ?",
        "yes_label": "Oui, formations régulières", "no_label": "Non",
        "guidance": "Article 20 §1 NIS2 : la direction doit approuver les mesures de gestion des risques.",
    },
    {
        "id": "Q03", "category": "Gouvernance", "weight": 5,
        "text": "Disposez-vous d'une politique de sécurité documentée et approuvée par la direction ?",
        "yes_label": "Oui, politique formelle", "no_label": "Non",
        "guidance": "Article 21 §2 NIS2 : politique de sécurité obligatoire.",
    },
    {
        "id": "Q04", "category": "Gouvernance", "weight": 5,
        "text": "Effectuez-vous des audits de sécurité réguliers (au moins annuels) ?",
        "yes_label": "Oui, audit annuel minimum", "no_label": "Non",
        "guidance": "Article 21 §2 NIS2 : évaluation et audits réguliers requis.",
    },
    # Gestion des risques (20 pts)
    {
        "id": "Q05", "category": "Gestion des risques", "weight": 5,
        "text": "Avez-vous une cartographie des actifs critiques et une analyse de risques formelle ?",
        "yes_label": "Oui, inventaire + analyse risques", "no_label": "Non",
        "guidance": "Article 21 §2a NIS2 : gestion des risques formelle obligatoire.",
    },
    {
        "id": "Q06", "category": "Gestion des risques", "weight": 5,
        "text": "Disposez-vous d'un plan de traitement des risques cyber avec priorisation ?",
        "yes_label": "Oui, plan documenté", "no_label": "Non",
        "guidance": "Article 21 §2 NIS2 : mesures proportionnées aux risques identifiés.",
    },
    {
        "id": "Q07", "category": "Gestion des risques", "weight": 5,
        "text": "Évaluez-vous les risques liés à votre chaîne d'approvisionnement (fournisseurs IT/OT) ?",
        "yes_label": "Oui, supply chain risk management", "no_label": "Non",
        "guidance": "Article 21 §2d NIS2 : sécurité de la chaîne d'approvisionnement.",
    },
    {
        "id": "Q08", "category": "Gestion des risques", "weight": 5,
        "text": "Appliquez-vous le principe de moindre privilège pour les accès systèmes ?",
        "yes_label": "Oui, contrôle d'accès strict", "no_label": "Non",
        "guidance": "Article 21 §2i NIS2 : contrôle d'accès et gestion des identités.",
    },
    # Gestion des incidents (20 pts)
    {
        "id": "Q09", "category": "Gestion des incidents", "weight": 5,
        "text": "Avez-vous une procédure formelle de détection et réponse aux incidents cyber ?",
        "yes_label": "Oui, IR plan documenté", "no_label": "Non",
        "guidance": "Article 21 §2b NIS2 : gestion des incidents obligatoire.",
    },
    {
        "id": "Q10", "category": "Gestion des incidents", "weight": 5,
        "text": "Êtes-vous capable de notifier l'ANSSI/CERT-FR dans les 24h en cas d'incident significatif ?",
        "yes_label": "Oui, processus de notification", "no_label": "Non",
        "guidance": "Article 23 NIS2 : notification obligatoire sous 24h (alerte précoce).",
    },
    {
        "id": "Q11", "category": "Gestion des incidents", "weight": 5,
        "text": "Disposez-vous de journaux (logs) de sécurité avec une rétention d'au moins 12 mois ?",
        "yes_label": "Oui, logs centralisés ≥ 12 mois", "no_label": "Non",
        "guidance": "Article 21 §2 NIS2 : traçabilité et surveillance requises.",
    },
    {
        "id": "Q12", "category": "Gestion des incidents", "weight": 5,
        "text": "Effectuez-vous des exercices de simulation d'incidents cyber (red team, tabletop) ?",
        "yes_label": "Oui, exercices réguliers", "no_label": "Non",
        "guidance": "Article 21 §2 NIS2 : tests et simulations pour vérifier la résilience.",
    },
    # Continuité d'activité (15 pts)
    {
        "id": "Q13", "category": "Continuité d'activité", "weight": 5,
        "text": "Disposez-vous d'un Plan de Continuité d'Activité (PCA) et Plan de Reprise (PRA) documentés ?",
        "yes_label": "Oui, PCA/PRA formels testés", "no_label": "Non",
        "guidance": "Article 21 §2c NIS2 : continuité des activités et gestion des crises.",
    },
    {
        "id": "Q14", "category": "Continuité d'activité", "weight": 5,
        "text": "Effectuez-vous des sauvegardes régulières et testez-vous leur restauration ?",
        "yes_label": "Oui, backups + tests restauration", "no_label": "Non",
        "guidance": "Article 21 §2c NIS2 : sauvegardes et reprise après sinistre.",
    },
    {
        "id": "Q15", "category": "Continuité d'activité", "weight": 5,
        "text": "Avez-vous un RTO (Recovery Time Objective) défini pour vos systèmes critiques ?",
        "yes_label": "Oui, RTO/RPO définis", "no_label": "Non",
        "guidance": "Article 21 §2c NIS2 : objectifs de reprise formalisés.",
    },
    # Sécurité technique (20 pts)
    {
        "id": "Q16", "category": "Sécurité technique", "weight": 5,
        "text": "Utilisez-vous la MFA (authentification multi-facteurs) pour les accès critiques ?",
        "yes_label": "Oui, MFA généralisée", "no_label": "Non",
        "guidance": "Article 21 §2i NIS2 : authentification multi-facteurs obligatoire.",
    },
    {
        "id": "Q17", "category": "Sécurité technique", "weight": 5,
        "text": "Chiffrez-vous les données sensibles au repos et en transit ?",
        "yes_label": "Oui, chiffrement bout-en-bout", "no_label": "Non",
        "guidance": "Article 21 §2h NIS2 : chiffrement des données.",
    },
    {
        "id": "Q18", "category": "Sécurité technique", "weight": 5,
        "text": "Appliquez-vous des correctifs de sécurité dans les 30 jours suivant leur publication ?",
        "yes_label": "Oui, patch management < 30j", "no_label": "Non",
        "guidance": "Article 21 §2e NIS2 : sécurité dans l'acquisition et maintenance.",
    },
    {
        "id": "Q19", "category": "Sécurité technique", "weight": 5,
        "text": "Segmentez-vous votre réseau (OT/IT séparés, DMZ, zones de sécurité) ?",
        "yes_label": "Oui, segmentation réseau", "no_label": "Non",
        "guidance": "Article 21 §2 NIS2 : sécurité des réseaux et des systèmes d'information.",
    },
    # Formation (0 pts—bonus)
    {
        "id": "Q20", "category": "Formation & Sensibilisation", "weight": 5,
        "text": "Dispensez-vous des formations cybersécurité à l'ensemble des collaborateurs au moins une fois par an ?",
        "yes_label": "Oui, programme annuel", "no_label": "Non",
        "guidance": "Article 21 §2g NIS2 : formation et sensibilisation à la cybersécurité.",
    },
]


@dataclass
class NIS2Question:
    """Représente une question NIS2."""
    id: str
    category: str
    weight: int
    text: str
    yes_label: str
    no_label: str
    guidance: str
    answer: Optional[bool] = None


@dataclass
class NIS2Assessment:
    """Résultat d'un audit NIS2."""
    assessment_id: str
    company: str
    sector: str
    contact_email: str
    answers: Dict[str, bool]  # {question_id: True/False}
    score: int = 0
    max_score: int = 100
    tier: str = "non-conforme"  # non-conforme|partiel|conforme|avancé
    gaps: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    freemium: bool = True  # True = score seulement, False = rapport complet
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


class NIS2Checker:
    """Moteur de scoring NIS2 — 20 questions, score 0-100."""

    TIER_MAP = [
        (80, "avancé"),
        (60, "conforme"),
        (40, "partiel"),
        (0,  "non-conforme"),
    ]

    def __init__(self):
        self._assessments: Dict[str, NIS2Assessment] = {}
        self._load_data()
        log.info("✅ NIS2Checker initialisé (%d questions)", len(NIS2_QUESTIONS))

    # ── Persistence ───────────────────────────────────────────────────────────
    def _data_path(self) -> Path:
        return DATA_DIR / "assessments.json"

    def _load_data(self) -> None:
        p = self._data_path()
        if p.exists():
            try:
                raw = json.loads(p.read_text())
                for k, v in raw.items():
                    v["gaps"] = v.get("gaps", [])
                    v["recommendations"] = v.get("recommendations", [])
                    self._assessments[k] = NIS2Assessment(**v)
            except Exception as exc:
                log.warning("NIS2 data load error: %s", exc)

    def _save_data(self) -> None:
        p = self._data_path()
        try:
            p.write_text(json.dumps(
                {k: v.to_dict() for k, v in self._assessments.items()},
                ensure_ascii=False, indent=2,
            ))
        except Exception as exc:
            log.warning("NIS2 save error: %s", exc)

    # ── Public API ────────────────────────────────────────────────────────────
    def get_questions(self) -> List[NIS2Question]:
        """Retourne les 20 questions NIS2."""
        return [NIS2Question(**q) for q in NIS2_QUESTIONS]

    def compute_score(self, answers: Dict[str, bool]) -> Tuple[int, str]:
        """Calcule le score 0-100 et le tier de conformité."""
        total_weight = sum(q["weight"] for q in NIS2_QUESTIONS)
        earned = sum(
            q["weight"] for q in NIS2_QUESTIONS
            if answers.get(q["id"], False)
        )
        score = round(earned * 100 / total_weight) if total_weight > 0 else 0
        tier = "non-conforme"
        for threshold, label in self.TIER_MAP:
            if score >= threshold:
                tier = label
                break
        return score, tier

    def identify_gaps(self, answers: Dict[str, bool]) -> List[str]:
        """Identifie les lacunes (questions répondues Non)."""
        return [
            f"[{q['id']}] {q['category']}: {q['text']}"
            for q in NIS2_QUESTIONS
            if not answers.get(q["id"], False)
        ]

    def generate_recommendations(self, answers: Dict[str, bool]) -> List[str]:
        """Génère des recommandations priorisées par poids."""
        failed = [q for q in NIS2_QUESTIONS if not answers.get(q["id"], False)]
        failed.sort(key=lambda q: q["weight"], reverse=True)
        recs = []
        for q in failed[:8]:  # Top 8 priorités
            recs.append(f"PRIORITÉ {q['category']}: {q['guidance']}")
        return recs

    def create_assessment(
        self,
        company: str,
        sector: str,
        contact_email: str,
        answers: Dict[str, bool],
        freemium: bool = True,
    ) -> NIS2Assessment:
        """Crée et enregistre un assessment NIS2."""
        import uuid
        score, tier = self.compute_score(answers)
        gaps = self.identify_gaps(answers)
        recs = self.generate_recommendations(answers) if not freemium else []

        assessment = NIS2Assessment(
            assessment_id=str(uuid.uuid4()),
            company=company,
            sector=sector,
            contact_email=contact_email,
            answers=answers,
            score=score,
            tier=tier,
            gaps=gaps if not freemium else gaps[:3],  # Freemium: 3 gaps seulement
            recommendations=recs,
            freemium=freemium,
        )
        self._assessments[assessment.assessment_id] = assessment
        self._save_data()
        log.info(
            "NIS2 Assessment %s : %s score=%d tier=%s",
            assessment.assessment_id, company, score, tier,
        )
        return assessment

    def get_assessment(self, assessment_id: str) -> Optional[NIS2Assessment]:
        return self._assessments.get(assessment_id)

    def list_assessments(self, limit: int = 20) -> List[NIS2Assessment]:
        lst = sorted(
            self._assessments.values(),
            key=lambda a: a.created_at,
            reverse=True,
        )
        return lst[:limit]

    def get_stats(self) -> Dict:
        total = len(self._assessments)
        if not total:
            return {"total": 0, "avg_score": 0, "tier_distribution": {}}
        scores = [a.score for a in self._assessments.values()]
        tiers: Dict[str, int] = {}
        for a in self._assessments.values():
            tiers[a.tier] = tiers.get(a.tier, 0) + 1
        return {
            "total": total,
            "avg_score": round(sum(scores) / total, 1),
            "tier_distribution": tiers,
            "paid_subscribers": sum(1 for a in self._assessments.values() if not a.freemium),
        }


# ── Singleton ─────────────────────────────────────────────────────────────────
_checker: Optional[NIS2Checker] = None


def get_nis2_checker() -> NIS2Checker:
    global _checker
    if _checker is None:
        _checker = NIS2Checker()
    return _checker
