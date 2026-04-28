"""
NAYA SUPREME V19 — Recommendation Engine
Personalized recommendations: quick wins vs long-term, budget estimation, priority scoring.
Production-ready, async, zero placeholders.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

log = logging.getLogger("NAYA.RecommendationEngine")


class RecommendationEngine:
    """
    Generate personalized remediation recommendations based on audit findings.
    Prioritizes quick wins and provides budget estimates.
    """

    # Recommendation templates by category
    RECOMMENDATION_TEMPLATES = {
        "access_control": {
            "quick_wins": [
                {
                    "action": "Change all default passwords on OT devices",
                    "duration_days": 2,
                    "cost_eur": 1000,
                    "impact": "HIGH",
                },
                {
                    "action": "Implement strong password policy (complexity, rotation)",
                    "duration_days": 5,
                    "cost_eur": 2000,
                    "impact": "MEDIUM",
                },
            ],
            "long_term": [
                {
                    "action": "Deploy MFA for all administrative access",
                    "duration_weeks": 4,
                    "cost_eur": 8000,
                    "impact": "HIGH",
                },
                {
                    "action": "Implement RBAC with least privilege principle",
                    "duration_weeks": 8,
                    "cost_eur": 15000,
                    "impact": "HIGH",
                },
            ],
        },
        "network_security": {
            "quick_wins": [
                {
                    "action": "Enable logging on all firewalls and switches",
                    "duration_days": 1,
                    "cost_eur": 500,
                    "impact": "MEDIUM",
                },
                {
                    "action": "Disable unused network ports and services",
                    "duration_days": 3,
                    "cost_eur": 1500,
                    "impact": "MEDIUM",
                },
            ],
            "long_term": [
                {
                    "action": "Implement IT/OT network segmentation (DMZ, VLANs)",
                    "duration_weeks": 12,
                    "cost_eur": 35000,
                    "impact": "CRITICAL",
                },
                {
                    "action": "Deploy industrial IDS/IPS (Nozomi, Claroty, etc.)",
                    "duration_weeks": 8,
                    "cost_eur": 45000,
                    "impact": "HIGH",
                },
            ],
        },
        "patch_management": {
            "quick_wins": [
                {
                    "action": "Inventory all OT assets and firmware versions",
                    "duration_days": 5,
                    "cost_eur": 3000,
                    "impact": "MEDIUM",
                },
            ],
            "long_term": [
                {
                    "action": "Establish patch management process with test environment",
                    "duration_weeks": 16,
                    "cost_eur": 25000,
                    "impact": "HIGH",
                },
                {
                    "action": "Implement automated vulnerability scanning for OT",
                    "duration_weeks": 6,
                    "cost_eur": 18000,
                    "impact": "MEDIUM",
                },
            ],
        },
        "incident_response": {
            "quick_wins": [
                {
                    "action": "Create basic incident response playbook",
                    "duration_days": 10,
                    "cost_eur": 5000,
                    "impact": "HIGH",
                },
            ],
            "long_term": [
                {
                    "action": "Deploy SIEM with OT integration",
                    "duration_weeks": 12,
                    "cost_eur": 50000,
                    "impact": "HIGH",
                },
                {
                    "action": "Establish SOC or contract with MSSP",
                    "duration_weeks": 20,
                    "cost_eur": 80000,
                    "impact": "HIGH",
                },
                {
                    "action": "Conduct quarterly cyber crisis exercises",
                    "duration_weeks": 52,
                    "cost_eur": 12000,
                    "impact": "MEDIUM",
                },
            ],
        },
        "governance": {
            "quick_wins": [
                {
                    "action": "Designate a RSSI/CISO with clear responsibilities",
                    "duration_days": 7,
                    "cost_eur": 2000,
                    "impact": "HIGH",
                },
                {
                    "action": "Document cybersecurity policy (v1.0)",
                    "duration_days": 15,
                    "cost_eur": 8000,
                    "impact": "HIGH",
                },
            ],
            "long_term": [
                {
                    "action": "Establish cybersecurity steering committee",
                    "duration_weeks": 8,
                    "cost_eur": 10000,
                    "impact": "MEDIUM",
                },
                {
                    "action": "Implement GRC platform (Governance, Risk, Compliance)",
                    "duration_weeks": 16,
                    "cost_eur": 40000,
                    "impact": "MEDIUM",
                },
            ],
        },
        "training": {
            "quick_wins": [
                {
                    "action": "Conduct cybersecurity awareness session for all staff",
                    "duration_days": 2,
                    "cost_eur": 3000,
                    "impact": "MEDIUM",
                },
            ],
            "long_term": [
                {
                    "action": "Implement annual cyber training program",
                    "duration_weeks": 12,
                    "cost_eur": 15000,
                    "impact": "MEDIUM",
                },
                {
                    "action": "Launch quarterly phishing simulation campaigns",
                    "duration_weeks": 52,
                    "cost_eur": 8000,
                    "impact": "MEDIUM",
                },
            ],
        },
    }

    async def generate_recommendations(
        self,
        audit_results: Dict[str, Any],
        company_size: str,
        budget_constraint: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Generate personalized recommendations based on audit findings.

        Args:
            audit_results: Complete audit data (IEC62443 or NIS2)
            company_size: Small/Medium/Large/Enterprise
            budget_constraint: Optional budget limit in EUR

        Returns:
            Comprehensive recommendation plan
        """
        log.info(f"Generating recommendations for {audit_results.get('company_name')}")

        try:
            # Identify priority areas from audit
            priority_areas = await self._identify_priority_areas(audit_results)

            # Generate quick wins
            quick_wins = await self._generate_quick_wins(priority_areas, company_size)

            # Generate long-term projects
            long_term = await self._generate_long_term_projects(
                priority_areas, company_size, budget_constraint
            )

            # Calculate ROI
            roi_analysis = self._calculate_roi(quick_wins, long_term)

            # Prioritize recommendations
            prioritized = self._prioritize_recommendations(quick_wins + long_term, audit_results)

            # Build implementation roadmap
            roadmap = await self._build_implementation_roadmap(prioritized, company_size)

            recommendation_plan = {
                "company_name": audit_results.get("company_name"),
                "priority_areas": priority_areas,
                "quick_wins": quick_wins,
                "long_term_projects": long_term,
                "prioritized_recommendations": prioritized,
                "implementation_roadmap": roadmap,
                "roi_analysis": roi_analysis,
                "total_quick_win_cost": sum(qw["cost_eur"] for qw in quick_wins),
                "total_long_term_cost": sum(lt["cost_eur"] for lt in long_term),
                "total_estimated_cost": sum(r["cost_eur"] for r in prioritized),
            }

            log.info(
                f"Recommendations generated: {len(quick_wins)} quick wins, "
                f"{len(long_term)} long-term projects"
            )

            return recommendation_plan

        except Exception as e:
            log.error(f"Recommendation generation failed: {e}", exc_info=True)
            raise

    async def _identify_priority_areas(
        self, audit_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify priority areas from audit findings."""
        await asyncio.sleep(0.05)

        priority_areas = []

        # From vulnerabilities
        vulnerabilities = audit_results.get("vulnerabilities", [])
        critical_vulns = [v for v in vulnerabilities if v.get("severity") == "CRITICAL"]
        high_vulns = [v for v in vulnerabilities if v.get("severity") == "HIGH"]

        if critical_vulns:
            # Categorize by type
            if any("access" in v.get("title", "").lower() or "credential" in v.get("title", "").lower()
                   for v in critical_vulns):
                priority_areas.append({
                    "category": "access_control",
                    "severity": "CRITICAL",
                    "issue_count": len([v for v in critical_vulns if "access" in v.get("title", "").lower()]),
                })

            if any("network" in v.get("title", "").lower() or "segmentation" in v.get("title", "").lower()
                   for v in critical_vulns):
                priority_areas.append({
                    "category": "network_security",
                    "severity": "CRITICAL",
                    "issue_count": len([v for v in critical_vulns if "network" in v.get("title", "").lower()]),
                })

        # From gaps
        gaps = audit_results.get("gaps", [])
        high_priority_gaps = [g for g in gaps if g.get("priority") == "HIGH"]

        for gap in high_priority_gaps:
            domain = gap.get("domain", "")
            if domain and not any(pa["category"] == domain for pa in priority_areas):
                priority_areas.append({
                    "category": domain,
                    "severity": "HIGH",
                    "issue_count": len([g for g in gaps if g.get("domain") == domain]),
                })

        # From compliance score
        overall_score = audit_results.get("overall_compliance_score") or audit_results.get("overall_score", 100)

        if overall_score < 50:
            # Critical situation - add governance
            if not any(pa["category"] == "governance" for pa in priority_areas):
                priority_areas.append({
                    "category": "governance",
                    "severity": "HIGH",
                    "issue_count": 1,
                })

        return priority_areas

    async def _generate_quick_wins(
        self, priority_areas: List[Dict[str, Any]], company_size: str
    ) -> List[Dict[str, Any]]:
        """Generate quick win recommendations."""
        await asyncio.sleep(0.05)

        quick_wins = []

        for area in priority_areas:
            category = area["category"]
            templates = self.RECOMMENDATION_TEMPLATES.get(category, {}).get("quick_wins", [])

            for template in templates:
                # Adjust cost based on company size
                cost_multiplier = {
                    "Small": 0.7,
                    "Medium": 1.0,
                    "Large": 1.3,
                    "Enterprise": 1.6,
                }.get(company_size, 1.0)

                quick_wins.append({
                    "category": category,
                    "type": "quick_win",
                    "action": template["action"],
                    "duration_days": template["duration_days"],
                    "cost_eur": int(template["cost_eur"] * cost_multiplier),
                    "impact": template["impact"],
                    "priority_score": self._calculate_priority_score(
                        area["severity"], template["impact"], template["duration_days"]
                    ),
                })

        return sorted(quick_wins, key=lambda x: x["priority_score"], reverse=True)

    async def _generate_long_term_projects(
        self,
        priority_areas: List[Dict[str, Any]],
        company_size: str,
        budget_constraint: Optional[int],
    ) -> List[Dict[str, Any]]:
        """Generate long-term project recommendations."""
        await asyncio.sleep(0.05)

        long_term = []

        for area in priority_areas:
            category = area["category"]
            templates = self.RECOMMENDATION_TEMPLATES.get(category, {}).get("long_term", [])

            for template in templates:
                # Adjust cost based on company size
                cost_multiplier = {
                    "Small": 0.7,
                    "Medium": 1.0,
                    "Large": 1.3,
                    "Enterprise": 1.6,
                }.get(company_size, 1.0)

                project_cost = int(template["cost_eur"] * cost_multiplier)

                # Filter by budget if specified
                if budget_constraint and project_cost > budget_constraint * 0.5:
                    continue

                long_term.append({
                    "category": category,
                    "type": "long_term",
                    "action": template["action"],
                    "duration_weeks": template["duration_weeks"],
                    "cost_eur": project_cost,
                    "impact": template["impact"],
                    "priority_score": self._calculate_priority_score(
                        area["severity"], template["impact"], template["duration_weeks"] * 7
                    ),
                })

        return sorted(long_term, key=lambda x: x["priority_score"], reverse=True)

    def _calculate_priority_score(
        self, severity: str, impact: str, duration_days: int
    ) -> float:
        """Calculate priority score for a recommendation."""
        severity_weight = {"CRITICAL": 10, "HIGH": 7, "MEDIUM": 4, "LOW": 2}.get(severity, 2)
        impact_weight = {"CRITICAL": 10, "HIGH": 7, "MEDIUM": 4, "LOW": 2}.get(impact, 2)

        # Favor shorter duration
        duration_factor = 1.0 / (1 + duration_days / 30)

        score = (severity_weight + impact_weight) * duration_factor

        return round(score, 2)

    def _prioritize_recommendations(
        self,
        all_recommendations: List[Dict[str, Any]],
        audit_results: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Prioritize all recommendations based on audit context."""
        # Sort by priority score, then by cost (prefer lower cost)
        return sorted(
            all_recommendations,
            key=lambda x: (x["priority_score"], -x["cost_eur"]),
            reverse=True,
        )

    async def _build_implementation_roadmap(
        self,
        prioritized_recommendations: List[Dict[str, Any]],
        company_size: str,
    ) -> List[Dict[str, Any]]:
        """Build phased implementation roadmap."""
        await asyncio.sleep(0.05)

        # Determine max parallel projects based on company size
        max_parallel = {
            "Small": 2,
            "Medium": 3,
            "Large": 4,
            "Enterprise": 6,
        }.get(company_size, 2)

        phases = []
        current_phase = 1
        remaining_recommendations = list(prioritized_recommendations)

        while remaining_recommendations:
            # Take next batch
            batch = remaining_recommendations[:max_parallel]
            remaining_recommendations = remaining_recommendations[max_parallel:]

            # Calculate phase duration (max of parallel projects)
            phase_duration_weeks = max(
                (rec.get("duration_weeks") or rec.get("duration_days", 0) / 7)
                for rec in batch
            )

            phase_cost = sum(rec["cost_eur"] for rec in batch)

            phases.append({
                "phase": f"Phase {current_phase}",
                "duration_weeks": int(phase_duration_weeks),
                "projects": [rec["action"] for rec in batch],
                "project_count": len(batch),
                "total_cost_eur": phase_cost,
            })

            current_phase += 1

        return phases

    def _calculate_roi(
        self,
        quick_wins: List[Dict[str, Any]],
        long_term: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Calculate ROI analysis for recommendations."""
        # Heuristic: estimate cost of incidents prevented
        quick_win_cost = sum(qw["cost_eur"] for qw in quick_wins)
        long_term_cost = sum(lt["cost_eur"] for lt in long_term)
        total_investment = quick_win_cost + long_term_cost

        # Average cost of OT cyber incident: 500k-2M EUR
        # Assume recommendations reduce risk by 70-90%
        potential_loss_prevented = 1_000_000
        risk_reduction_factor = 0.8

        estimated_savings = int(potential_loss_prevented * risk_reduction_factor)

        roi = ((estimated_savings - total_investment) / total_investment * 100) if total_investment > 0 else 0

        return {
            "total_investment_eur": total_investment,
            "estimated_savings_eur": estimated_savings,
            "roi_percentage": round(roi, 1),
            "payback_period_months": int(total_investment / (estimated_savings / 12)) if estimated_savings > 0 else 999,
            "note": "ROI based on industry average incident costs and risk reduction estimates",
        }
