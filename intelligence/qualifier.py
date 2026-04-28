#!/usr/bin/env python3
"""
NAYA SUPREME V19 — Lead Qualifier
Lead scoring 0-100 based on BANT (Budget, Authority, Need, Timing).
Output: qualified_score + recommendation (pursue/nurture/discard).
"""

import asyncio
import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

log = logging.getLogger("NAYA.Qualifier")


# ── Qualification Models ──────────────────────────────────────────────────────
class Recommendation(str, Enum):
    PURSUE = "pursue"          # Score ≥ 70: immediate action
    NURTURE = "nurture"        # Score 40-69: long-term follow-up
    DISCARD = "discard"        # Score < 40: not worth pursuing


@dataclass
class QualifiedLead:
    """Lead with BANT qualification score."""
    lead_id: str
    company: str
    sector: str
    contact_name: Optional[str]
    contact_email: Optional[str]
    contact_title: Optional[str]

    # BANT Scores (each 0-25)
    budget_score: float
    authority_score: float
    need_score: float
    timing_score: float

    # Overall
    qualified_score: float  # 0-100
    recommendation: Recommendation
    qualified_at: str
    notes: str = ""
    metadata: Dict = None

    def to_dict(self) -> Dict:
        data = asdict(self)
        data["recommendation"] = self.recommendation.value
        return data


# ── Qualifier Engine ──────────────────────────────────────────────────────────
class Qualifier:
    """
    BANT-based lead qualification engine.
    Budget: Can they afford our minimum 1000 EUR?
    Authority: Is contact a decision-maker?
    Need: Do they have a clear pain?
    Timing: Is there urgency?
    """

    MIN_CONTRACT_VALUE = 1000  # EUR

    def __init__(self, storage_path: str = "data/intelligence/qualified_leads.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.qualified_leads: List[QualifiedLead] = []
        self._load_leads()
        log.info("✅ Qualifier initialized")

    # ── Storage ───────────────────────────────────────────────────────────────
    def _load_leads(self) -> None:
        """Load qualified leads from storage."""
        if self.storage_path.exists():
            try:
                data = json.loads(self.storage_path.read_text())
                self.qualified_leads = []
                for item in data:
                    item["recommendation"] = Recommendation(item["recommendation"])
                    self.qualified_leads.append(QualifiedLead(**item))
                log.info("Loaded %d qualified leads", len(self.qualified_leads))
            except Exception as exc:
                log.warning("Failed to load qualified leads: %s", exc)
                self.qualified_leads = []

    def _save_leads(self) -> None:
        """Save qualified leads to storage."""
        try:
            data = [lead.to_dict() for lead in self.qualified_leads]
            self.storage_path.write_text(json.dumps(data, indent=2, default=str))
        except Exception as exc:
            log.warning("Failed to save qualified leads: %s", exc)

    # ── Qualification ─────────────────────────────────────────────────────────
    async def qualify_lead(
        self,
        lead_id: str,
        company: str,
        sector: str,
        prospect_profile: Dict,
        enrichment_data: Dict,
        pain_detected: Optional[Dict] = None,
    ) -> QualifiedLead:
        """
        Qualify a lead using BANT framework.

        Args:
            lead_id: Unique lead identifier
            company: Company name
            sector: Business sector
            prospect_profile: Profile data (title, role, etc)
            enrichment_data: Enrichment data (company size, revenue, etc)
            pain_detected: Detected pain data (optional)

        Returns:
            QualifiedLead with scores and recommendation
        """
        # Calculate BANT scores
        budget_score = self._score_budget(enrichment_data)
        authority_score = self._score_authority(prospect_profile)
        need_score = self._score_need(pain_detected, sector)
        timing_score = self._score_timing(pain_detected, enrichment_data)

        # Overall score (sum of BANT)
        qualified_score = budget_score + authority_score + need_score + timing_score

        # Recommendation
        recommendation = self._determine_recommendation(qualified_score)

        qualified_lead = QualifiedLead(
            lead_id=lead_id,
            company=company,
            sector=sector,
            contact_name=prospect_profile.get("name"),
            contact_email=prospect_profile.get("email"),
            contact_title=prospect_profile.get("title"),
            budget_score=budget_score,
            authority_score=authority_score,
            need_score=need_score,
            timing_score=timing_score,
            qualified_score=qualified_score,
            recommendation=recommendation,
            qualified_at=datetime.now().isoformat(),
            notes=self._generate_notes(budget_score, authority_score, need_score, timing_score),
            metadata={
                "sector": sector,
                "company_size": enrichment_data.get("company_size"),
                "revenue": enrichment_data.get("revenue"),
            },
        )

        # Save
        self.qualified_leads.append(qualified_lead)
        self._save_leads()

        log.info("✅ Qualified lead %s: score=%.1f, recommendation=%s",
                 lead_id, qualified_score, recommendation.value)

        return qualified_lead

    # ── BANT Scoring ──────────────────────────────────────────────────────────
    def _score_budget(self, enrichment_data: Dict) -> float:
        """
        Score budget capacity (0-25).
        Based on company size, revenue, sector.
        """
        score = 0.0

        # Company revenue
        revenue = enrichment_data.get("revenue_eur", 0)
        if revenue >= 100_000_000:  # 100M+ EUR
            score += 15
        elif revenue >= 10_000_000:  # 10M+ EUR
            score += 12
        elif revenue >= 1_000_000:   # 1M+ EUR
            score += 8
        elif revenue >= 100_000:     # 100k+ EUR
            score += 5

        # Company size
        company_size = enrichment_data.get("company_size", "").lower()
        if "enterprise" in company_size or "large" in company_size:
            score += 10
        elif "medium" in company_size or "mid" in company_size:
            score += 7
        elif "small" in company_size or "startup" in company_size:
            score += 3

        return min(score, 25.0)

    def _score_authority(self, prospect_profile: Dict) -> float:
        """
        Score decision-making authority (0-25).
        Based on title, role, seniority.
        """
        score = 0.0

        title = prospect_profile.get("title", "").lower()

        # C-level
        if any(keyword in title for keyword in ["ceo", "cto", "ciso", "cio", "directeur", "director"]):
            score += 25
        # VP / Head
        elif any(keyword in title for keyword in ["vp", "head of", "responsable", "manager"]):
            score += 20
        # Senior role
        elif any(keyword in title for keyword in ["senior", "lead", "principal", "expert"]):
            score += 15
        # Security-specific
        elif any(keyword in title for keyword in ["rssi", "security", "cyber", "risk"]):
            score += 18
        # Technical role (lower authority)
        elif any(keyword in title for keyword in ["engineer", "analyst", "consultant", "ingénieur"]):
            score += 8
        else:
            score += 5

        return min(score, 25.0)

    def _score_need(self, pain_detected: Optional[Dict], sector: str) -> float:
        """
        Score need intensity (0-25).
        Based on pain signal, sector criticality.
        """
        score = 0.0

        if pain_detected:
            pain_score = pain_detected.get("score", 0)
            # Pain score 0-100 → need score 0-20
            score += (pain_score / 100) * 20

            # Pain urgency
            urgency = pain_detected.get("urgency", "low")
            if urgency == "critical":
                score += 5
            elif urgency == "high":
                score += 4
            elif urgency == "medium":
                score += 2
        else:
            # No pain detected = low need
            score += 5

        # Sector bonus (critical sectors have higher intrinsic need)
        if sector in ["energie_utilities", "iec62443"]:
            score += 3
        elif sector in ["transport_logistique", "manufacturing"]:
            score += 2

        return min(score, 25.0)

    def _score_timing(self, pain_detected: Optional[Dict], enrichment_data: Dict) -> float:
        """
        Score timing/urgency (0-25).
        Based on signal recency, regulatory deadlines, budget cycles.
        """
        score = 0.0

        # Pain signal recency
        if pain_detected:
            detected_at = pain_detected.get("detected_at")
            if detected_at:
                try:
                    detected_date = datetime.fromisoformat(detected_at)
                    days_ago = (datetime.now() - detected_date).days
                    if days_ago <= 7:
                        score += 15
                    elif days_ago <= 30:
                        score += 12
                    elif days_ago <= 90:
                        score += 8
                    else:
                        score += 4
                except Exception:
                    score += 5

        # Recent hiring (job posting = immediate need)
        if pain_detected and pain_detected.get("signal_source") == "job_offer":
            score += 10

        # Regulatory deadline proximity
        if pain_detected and pain_detected.get("signal_source") == "regulatory":
            deadline = pain_detected.get("metadata", {}).get("deadline")
            if deadline:
                try:
                    deadline_date = datetime.fromisoformat(deadline)
                    days_until = (deadline_date - datetime.now()).days
                    if 0 < days_until < 90:
                        score += 10
                    elif 90 <= days_until < 180:
                        score += 5
                except Exception:
                    pass

        return min(score, 25.0)

    # ── Recommendation ────────────────────────────────────────────────────────
    def _determine_recommendation(self, score: float) -> Recommendation:
        """Determine action recommendation based on score."""
        if score >= 70:
            return Recommendation.PURSUE
        elif score >= 40:
            return Recommendation.NURTURE
        else:
            return Recommendation.DISCARD

    def _generate_notes(
        self,
        budget_score: float,
        authority_score: float,
        need_score: float,
        timing_score: float,
    ) -> str:
        """Generate qualification notes."""
        notes = []

        if budget_score < 10:
            notes.append("⚠️ Low budget capacity")
        if authority_score < 15:
            notes.append("⚠️ Low authority level - may need approval")
        if need_score < 10:
            notes.append("⚠️ Weak pain signal")
        if timing_score < 10:
            notes.append("⚠️ Low urgency - long sales cycle expected")

        if budget_score >= 20 and authority_score >= 20:
            notes.append("✅ High-value decision maker")
        if need_score >= 20 and timing_score >= 20:
            notes.append("✅ Strong immediate need")

        return " | ".join(notes) if notes else "Standard qualification"

    # ── Query ─────────────────────────────────────────────────────────────────
    async def get_leads_to_pursue(self) -> List[QualifiedLead]:
        """Get leads with PURSUE recommendation."""
        return [lead for lead in self.qualified_leads if lead.recommendation == Recommendation.PURSUE]

    async def get_leads_to_nurture(self) -> List[QualifiedLead]:
        """Get leads with NURTURE recommendation."""
        return [lead for lead in self.qualified_leads if lead.recommendation == Recommendation.NURTURE]

    async def get_leads_by_score(self, min_score: float) -> List[QualifiedLead]:
        """Get leads with score >= min_score."""
        return [lead for lead in self.qualified_leads if lead.qualified_score >= min_score]

    async def get_lead_by_id(self, lead_id: str) -> Optional[QualifiedLead]:
        """Get a specific lead by ID."""
        for lead in self.qualified_leads:
            if lead.lead_id == lead_id:
                return lead
        return None

    def get_stats(self) -> Dict:
        """Get qualification statistics."""
        if not self.qualified_leads:
            return {
                "total": 0,
                "avg_score": 0,
                "by_recommendation": {},
                "avg_bant": {},
            }

        by_recommendation = {}
        for lead in self.qualified_leads:
            rec = lead.recommendation.value
            by_recommendation[rec] = by_recommendation.get(rec, 0) + 1

        avg_bant = {
            "budget": sum(l.budget_score for l in self.qualified_leads) / len(self.qualified_leads),
            "authority": sum(l.authority_score for l in self.qualified_leads) / len(self.qualified_leads),
            "need": sum(l.need_score for l in self.qualified_leads) / len(self.qualified_leads),
            "timing": sum(l.timing_score for l in self.qualified_leads) / len(self.qualified_leads),
        }

        return {
            "total": len(self.qualified_leads),
            "avg_score": sum(l.qualified_score for l in self.qualified_leads) / len(self.qualified_leads),
            "by_recommendation": by_recommendation,
            "avg_bant": avg_bant,
        }


# ── CLI Test ──────────────────────────────────────────────────────────────────
async def main():
    """Test Qualifier."""
    print("🎯 NAYA Lead Qualifier — Test Module\n")

    qualifier = Qualifier()

    # Test leads
    test_leads = [
        {
            "lead_id": "LEAD_001",
            "company": "SNCF",
            "sector": "transport_logistique",
            "prospect_profile": {
                "name": "Jean Dupont",
                "email": "jean.dupont@sncf.fr",
                "title": "RSSI Transport Ferroviaire",
            },
            "enrichment_data": {
                "revenue_eur": 50_000_000,
                "company_size": "large",
            },
            "pain_detected": {
                "score": 85,
                "urgency": "high",
                "signal_source": "job_offer",
                "detected_at": datetime.now().isoformat(),
            },
        },
        {
            "lead_id": "LEAD_002",
            "company": "PME Manufacturing",
            "sector": "manufacturing",
            "prospect_profile": {
                "name": "Marie Martin",
                "email": "marie@pme.fr",
                "title": "Ingénieur IT",
            },
            "enrichment_data": {
                "revenue_eur": 500_000,
                "company_size": "small",
            },
            "pain_detected": {
                "score": 45,
                "urgency": "low",
                "signal_source": "news",
                "detected_at": (datetime.now()).isoformat(),
            },
        },
    ]

    for test_lead in test_leads:
        qualified = await qualifier.qualify_lead(**test_lead)

        print(f"\n📊 Lead: {qualified.company}")
        print(f"   Contact: {qualified.contact_name} ({qualified.contact_title})")
        print(f"   Qualified Score: {qualified.qualified_score:.1f}/100")
        print(f"   Recommendation: {qualified.recommendation.value}")
        print(f"   BANT Breakdown:")
        print(f"     Budget: {qualified.budget_score:.1f}/25")
        print(f"     Authority: {qualified.authority_score:.1f}/25")
        print(f"     Need: {qualified.need_score:.1f}/25")
        print(f"     Timing: {qualified.timing_score:.1f}/25")
        print(f"   Notes: {qualified.notes}")

    # Stats
    stats = qualifier.get_stats()
    print(f"\n📈 Statistics:")
    print(f"   Total leads: {stats['total']}")
    print(f"   Avg score: {stats['avg_score']:.1f}")
    print(f"   By recommendation: {stats['by_recommendation']}")
    print(f"   Avg BANT:")
    for key, value in stats['avg_bant'].items():
        print(f"     {key}: {value:.1f}/25")


if __name__ == "__main__":
    asyncio.run(main())
