"""
NAYA — Credibility Guard
Protège et construit la crédibilité pour maximiser les conversions.
"""
from typing import Dict, List
from dataclasses import dataclass, field

@dataclass
class SocialProof:
    type: str  # testimonial, case_study, metric, logo, certification
    content: str; source: str; impact_score: float

class CredibilityGuard:
    """Valide le contenu et construit la crédibilité business."""

    CREDIBILITY_FACTORS = {
        "case_study": 0.35, "testimonial": 0.25, "metric": 0.20,
        "logo": 0.10, "certification": 0.10
    }

    def validate_content(self, content: Dict) -> bool:
        body = content.get("body", "").lower()
        has_specifics = any(c.isdigit() for c in body)
        has_credibility = any(w in body for w in 
            ["résultat", "client", "cas", "exemple", "garanti", "prouvé", "elite"])
        return has_specifics or has_credibility

    def score_credibility(self, proofs: List[SocialProof]) -> float:
        score = 0
        for proof in proofs:
            weight = self.CREDIBILITY_FACTORS.get(proof.type, 0.05)
            score += weight * proof.impact_score
        return min(100, score * 100)

    def generate_credibility_stack(self, results: List[Dict]) -> List[SocialProof]:
        proofs = []
        for r in results:
            if r.get("revenue_increase"):
                proofs.append(SocialProof("metric",
                    f"+{r['revenue_increase']}% de CA en {r.get('days',30)} jours",
                    r.get("company", "Client"), 0.9))
            if r.get("testimonial"):
                proofs.append(SocialProof("testimonial", r["testimonial"],
                    r.get("name", "Directeur"), 0.8))
        return proofs

    def anti_hype_filter(self, content: str) -> str:
        """Remplace le hype par des faits."""
        replacements = {
            "révolutionnaire": "éprouvé", "incroyable": "mesurable",
            "magique": "systématique", "parfait": "optimisé",
            "le meilleur": "adapté à votre secteur"
        }
        for hype, fact in replacements.items():
            content = content.replace(hype, fact)
        return content
