"""Adaptive Business Hunt Engine — NAYA_PROJECT_ENGINE.

Moteur unifié qui:
1) découvre automatiquement les projets disponibles,
2) adapte stratégie business/chasse à chaque projet,
3) produit une mission J1→J10 orientée revenus,
4) priorise les projets selon un score go-live.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[1]


@dataclass
class ProjectProfile:
    project_id: str
    name: str
    source_path: str
    vertical: str
    monetization_model: str
    hunting_channels: List[str]
    avg_ticket_eur: int
    confidence: float


class AdaptiveBusinessHuntEngine:
    """Moteur adaptatif business/chasse multi-projets."""

    VERTICAL_RULES: List[tuple[str, str, str, int, List[str], float]] = [
        # (regex, vertical, model, avg_ticket, channels, confidence)
        (r"cash|rapid|trade|acquisition|immobili", "Deal Acceleration", "one_shot + upsell", 15000, ["email", "linkedin", "partner_referral"], 0.85),
        (r"xr|tech|data|analytics|transformation", "B2B Tech Enablement", "audit + implementation", 30000, ["email", "webinar", "linkedin"], 0.80),
        (r"botanica|beauty|skin|ecommerce", "D2C Commerce", "product + subscription", 5000, ["ads", "influencer", "crm"], 0.78),
        (r"tiny|house|housing|construction", "Modular Habitat", "project + maintenance", 40000, ["partnership", "rfp", "linkedin"], 0.74),
        (r"paye|pay|fintech|payment|cross_border", "Fintech Payments", "transaction + premium", 25000, ["email", "community", "partnership"], 0.82),
        (r"sustainability|impact|green", "Sustainability Services", "audit + roadmap", 18000, ["email", "events", "linkedin"], 0.72),
    ]

    def __init__(self) -> None:
        self._profiles: Dict[str, ProjectProfile] = {}

    def _discover_project_paths(self) -> List[Path]:
        """Découvre les dossiers projets sous les différentes branches NAYA."""
        candidates: List[Path] = []
        roots = [
            ROOT / "projects",
            ROOT / "first_project_queue",
            ROOT / "business" / "projects",
        ]
        for base in roots:
            if not base.exists():
                continue
            for child in base.iterdir():
                if child.is_dir() and child.name.upper().startswith("PROJECT_"):
                    candidates.append(child)
        # tri déterministe
        return sorted(candidates, key=lambda p: p.name)

    def _extract_project_identity(self, folder: Path) -> tuple[str, str]:
        """Extrait id + nom lisible depuis le dossier projet."""
        pid = folder.name
        name = re.sub(r"^PROJECT_\d+_?", "", folder.name, flags=re.IGNORECASE).replace("_", " ").strip()
        return pid, name.title() if name else pid

    def _classify(self, pid: str, name: str) -> tuple[str, str, int, List[str], float]:
        """Classe un projet vers une verticale et un modèle de monétisation."""
        hay = f"{pid} {name}".lower()
        for pattern, vertical, model, ticket, channels, conf in self.VERTICAL_RULES:
            if re.search(pattern, hay):
                return vertical, model, ticket, channels, conf
        return (
            "General B2B Services",
            "diagnostic + implementation",
            12000,
            ["email", "linkedin"],
            0.70,
        )

    def discover_and_profile(self) -> List[ProjectProfile]:
        """Découvre et profile tous les projets disponibles."""
        profiles: List[ProjectProfile] = []
        for folder in self._discover_project_paths():
            pid, name = self._extract_project_identity(folder)
            vertical, model, ticket, channels, conf = self._classify(pid, name)
            p = ProjectProfile(
                project_id=pid,
                name=name,
                source_path=str(folder.relative_to(ROOT)).replace("\\", "/"),
                vertical=vertical,
                monetization_model=model,
                hunting_channels=channels,
                avg_ticket_eur=ticket,
                confidence=conf,
            )
            profiles.append(p)
            self._profiles[p.project_id] = p
        return profiles

    @staticmethod
    def _go_live_score(profile: ProjectProfile) -> float:
        """Score de priorité lancement (0-100)."""
        channel_bonus = min(15, len(profile.hunting_channels) * 3)
        ticket_bonus = min(35, profile.avg_ticket_eur / 1500)
        conf_bonus = profile.confidence * 40
        return round(min(100.0, channel_bonus + ticket_bonus + conf_bonus), 2)

    def rank_projects(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retourne les projets triés par potentiel go-live immédiat."""
        profiles = self.discover_and_profile()
        ranked = sorted(
            profiles,
            key=lambda p: (self._go_live_score(p), p.avg_ticket_eur),
            reverse=True,
        )
        return [
            {
                **asdict(p),
                "go_live_score": self._go_live_score(p),
            }
            for p in ranked[: max(1, limit)]
        ]

    def build_hunt_playbook(self, project_id: str) -> Dict[str, Any]:
        """Construit le playbook de chasse adapté à un projet."""
        profile = self._profiles.get(project_id)
        if profile is None:
            # refresh automatique
            self.discover_and_profile()
            profile = self._profiles.get(project_id)
        if profile is None:
            raise ValueError(f"Unknown project_id: {project_id}")

        offer_floor = max(1000, int(profile.avg_ticket_eur * 0.3))
        offer_target = profile.avg_ticket_eur
        offer_premium = int(profile.avg_ticket_eur * 2.2)

        return {
            "project_id": profile.project_id,
            "vertical": profile.vertical,
            "hunting_channels": profile.hunting_channels,
            "offers": {
                "floor_eur": offer_floor,
                "target_eur": offer_target,
                "premium_eur": offer_premium,
            },
            "pipeline": {
                "daily_new_leads_target": 20,
                "reply_rate_target_pct": 12,
                "meeting_rate_target_pct": 4,
                "close_rate_target_pct": 18,
            },
            "automation": [
                "lead_scoring_auto",
                "sequence_7_touch_auto",
                "objection_handler_auto",
                "contract_invoice_auto",
            ],
        }

    def build_first_10_days_mission(self, project_id: str) -> Dict[str, Any]:
        """Mission opérationnelle J1→J10 orientée cash et exécution."""
        profile = self._profiles.get(project_id)
        if profile is None:
            self.discover_and_profile()
            profile = self._profiles.get(project_id)
        if profile is None:
            raise ValueError(f"Unknown project_id: {project_id}")

        playbook = self.build_hunt_playbook(project_id)
        target_10d = int(profile.avg_ticket_eur * 1.8)

        days = [
            {"day": 1, "goal": "Positioning + offer stack", "deliverable": "1-pager offre floor/target/premium"},
            {"day": 2, "goal": "ICP + lead list", "deliverable": "100 leads enrichis minimum"},
            {"day": 3, "goal": "Sequence launch", "deliverable": "7-touch active sur 50 leads"},
            {"day": 4, "goal": "A/B hooks", "deliverable": "2 variantes message + tracking"},
            {"day": 5, "goal": "First meetings", "deliverable": "3-5 meetings qualifiés"},
            {"day": 6, "goal": "Proposal day", "deliverable": "2 propositions envoyées"},
            {"day": 7, "goal": "Objection battle", "deliverable": "FAQ objections + scripts closing"},
            {"day": 8, "goal": "Closing sprint", "deliverable": "1 deal signé"},
            {"day": 9, "goal": "Upsell + referral", "deliverable": "1 upsell + 3 intros"},
            {"day": 10, "goal": "Scale loop", "deliverable": "playbook versionné + KPI baseline"},
        ]

        return {
            "project": asdict(profile),
            "target_10_days_eur": target_10d,
            "playbook": playbook,
            "daily_mission": days,
            "success_kpi": {
                "new_leads_total": 120,
                "meetings_total": 10,
                "proposals_total": 5,
                "signed_deals_min": 1,
            },
        }

    def launch_top10_bundle(self) -> Dict[str, Any]:
        """Prépare le bundle mission pour les 10 premiers projets prioritaires."""
        ranked = self.rank_projects(limit=10)
        missions = [self.build_first_10_days_mission(p["project_id"]) for p in ranked]
        return {
            "count": len(missions),
            "projects": [m["project"]["project_id"] for m in missions],
            "portfolio_target_10d_eur": sum(m["target_10_days_eur"] for m in missions),
            "missions": missions,
        }


adaptive_business_hunt_engine = AdaptiveBusinessHuntEngine()
