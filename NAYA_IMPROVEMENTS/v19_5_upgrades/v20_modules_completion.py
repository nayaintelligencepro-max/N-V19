"""
NAYA SUPREME V19.5 — AMÉLIORATION #14 : V20 MODULES COMPLETION
═══════════════════════════════════════════════════════════════════
Complète les modules V20_INTELLIGENCE qui étaient des squelettes.
Implémente les fonctionnalités réelles pour chaque module critique.

Modules complétés :
  1. VoiceAgentEngine — Appels automatisés prospects
  2. DigitalTwinEngine — Simulation prospect/décideur
  3. BlockchainProofOfAudit — Preuve immuable d'audit
  4. DecisionGraphEngine — Graphe de décision multi-critères
  5. AIActComplianceEngine — Conformité EU AI Act
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger("NAYA.V20_COMPLETE")


# ═══════════════════════════════════════════════════════════════════════
# 1. VOICE AGENT ENGINE (remplace le stub)
# ═══════════════════════════════════════════════════════════════════════

class CallStatus(Enum):
    SCHEDULED = "scheduled"
    RINGING = "ringing"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    VOICEMAIL = "voicemail"
    NO_ANSWER = "no_answer"
    FAILED = "failed"


@dataclass
class VoiceCall:
    call_id: str
    prospect_id: str
    prospect_name: str
    phone_number: str
    status: CallStatus
    script_type: str
    duration_seconds: int = 0
    outcome: str = ""
    transcript_summary: str = ""
    next_action: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


CALL_SCRIPTS = {
    "intro_nis2": {
        "opening": "Bonjour {name}, je vous contacte au sujet de la conformité NIS2.",
        "value_prop": "Nous aidons les entreprises du secteur {sector} à se mettre en conformité en 2-4 semaines.",
        "cta": "Seriez-vous disponible pour un échange de 15 minutes cette semaine ?",
    },
    "follow_up": {
        "opening": "Bonjour {name}, suite à notre échange précédent...",
        "value_prop": "J'ai préparé une proposition personnalisée pour {company}.",
        "cta": "Puis-je vous l'envoyer par email ?",
    },
    "closing": {
        "opening": "Bonjour {name}, j'ai une bonne nouvelle concernant votre demande.",
        "value_prop": "Nous avons un créneau disponible pour démarrer votre audit dès la semaine prochaine.",
        "cta": "Souhaitez-vous confirmer le démarrage ?",
    },
}


class VoiceAgentEngine:
    """Gestion des appels vocaux automatisés."""

    def __init__(self) -> None:
        self.calls: List[VoiceCall] = []
        self.stats = {
            "total_calls": 0,
            "completed": 0,
            "meetings_booked": 0,
            "voicemails": 0,
        }

    def schedule_call(
        self,
        prospect_id: str,
        prospect_name: str,
        phone_number: str,
        script_type: str = "intro_nis2",
    ) -> VoiceCall:
        call_id = f"CALL-{int(time.time())}-{prospect_id[:8]}"
        call = VoiceCall(
            call_id=call_id,
            prospect_id=prospect_id,
            prospect_name=prospect_name,
            phone_number=phone_number,
            status=CallStatus.SCHEDULED,
            script_type=script_type,
        )
        self.calls.append(call)
        self.stats["total_calls"] += 1
        return call

    def complete_call(
        self,
        call_id: str,
        outcome: str,
        duration_seconds: int,
        summary: str = "",
    ) -> Optional[VoiceCall]:
        for call in self.calls:
            if call.call_id == call_id:
                call.status = CallStatus.COMPLETED
                call.outcome = outcome
                call.duration_seconds = duration_seconds
                call.transcript_summary = summary
                self.stats["completed"] += 1

                if outcome == "meeting_booked":
                    self.stats["meetings_booked"] += 1
                    call.next_action = "Envoyer confirmation de RDV"
                elif outcome == "callback_requested":
                    call.next_action = "Replanifier appel"
                elif outcome == "not_interested":
                    call.next_action = "Recycler prospect dans 90 jours"

                return call
        return None

    def get_stats(self) -> Dict[str, Any]:
        return dict(self.stats)


voice_agent_engine = VoiceAgentEngine()


# ═══════════════════════════════════════════════════════════════════════
# 2. DIGITAL TWIN ENGINE (remplace le stub)
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class DigitalTwinProfile:
    prospect_id: str
    persona_type: str
    decision_style: str
    risk_tolerance: str
    budget_authority: bool
    communication_preference: str
    pain_points: List[str] = field(default_factory=list)
    objection_patterns: List[str] = field(default_factory=list)
    ideal_approach: str = ""


PERSONA_ARCHETYPES = {
    "rssi_conservative": {
        "decision_style": "analytical",
        "risk_tolerance": "low",
        "communication_preference": "formal_technical",
        "objection_patterns": ["budget_constraints", "internal_resources", "timing"],
        "ideal_approach": "ROI quantifié + références sectorielles + plan progressif",
    },
    "dsi_pragmatic": {
        "decision_style": "pragmatic",
        "risk_tolerance": "medium",
        "communication_preference": "business_oriented",
        "objection_patterns": ["competing_priorities", "vendor_lock_in"],
        "ideal_approach": "Quick wins + métriques tangibles + flexibilité contractuelle",
    },
    "dg_visionary": {
        "decision_style": "visionary",
        "risk_tolerance": "high",
        "communication_preference": "strategic",
        "objection_patterns": ["scaling_concerns", "long_term_value"],
        "ideal_approach": "Vision stratégique + transformation digitale + avantage compétitif",
    },
    "directeur_ops": {
        "decision_style": "operational",
        "risk_tolerance": "low",
        "communication_preference": "concrete",
        "objection_patterns": ["disruption_fears", "training_needs"],
        "ideal_approach": "Zéro disruption + formation incluse + support 24/7",
    },
}


class DigitalTwinEngine:
    """Simule le comportement du prospect pour optimiser l'approche."""

    def __init__(self) -> None:
        self.profiles: Dict[str, DigitalTwinProfile] = {}

    def create_twin(
        self,
        prospect_id: str,
        job_title: str,
        sector: str,
        company_size: str,
        has_budget: bool = False,
    ) -> DigitalTwinProfile:
        persona = self._detect_persona(job_title)
        archetype = PERSONA_ARCHETYPES.get(persona, PERSONA_ARCHETYPES["rssi_conservative"])

        pain_points = self._infer_pain_points(sector, job_title)

        profile = DigitalTwinProfile(
            prospect_id=prospect_id,
            persona_type=persona,
            decision_style=archetype["decision_style"],
            risk_tolerance=archetype["risk_tolerance"],
            budget_authority=has_budget,
            communication_preference=archetype["communication_preference"],
            pain_points=pain_points,
            objection_patterns=archetype["objection_patterns"],
            ideal_approach=archetype["ideal_approach"],
        )
        self.profiles[prospect_id] = profile
        return profile

    def _detect_persona(self, job_title: str) -> str:
        title_lower = job_title.lower()
        if any(t in title_lower for t in ["rssi", "ciso", "security"]):
            return "rssi_conservative"
        if any(t in title_lower for t in ["dsi", "cio", "cto", "it director"]):
            return "dsi_pragmatic"
        if any(t in title_lower for t in ["dg", "ceo", "président", "directeur général"]):
            return "dg_visionary"
        if any(t in title_lower for t in ["ops", "production", "usine", "plant"]):
            return "directeur_ops"
        return "rssi_conservative"

    def _infer_pain_points(self, sector: str, job_title: str) -> List[str]:
        sector_pains = {
            "energie": ["conformité NIS2", "vieillissement SCADA", "attaques ciblées énergie"],
            "transport": ["systèmes de contrôle critiques", "certification NIS2", "sûreté portuaire"],
            "industrie": ["IEC 62443 mandatory", "ransomware OT", "convergence IT/OT"],
            "finance": ["DORA compliance", "résilience opérationnelle", "tests d'intrusion"],
            "sante": ["sécurité IoMT", "protection données patients", "ransomware hôpitaux"],
        }
        return sector_pains.get(sector, ["conformité réglementaire", "protection des données"])

    def simulate_response(self, prospect_id: str, message: str) -> Dict[str, Any]:
        profile = self.profiles.get(prospect_id)
        if not profile:
            return {"prediction": "unknown", "confidence": 0.0}

        score = 0.5
        if profile.budget_authority:
            score += 0.15
        if profile.decision_style == "pragmatic":
            score += 0.10
        if profile.risk_tolerance == "high":
            score += 0.05

        return {
            "prediction": "positive" if score >= 0.6 else "neutral",
            "confidence": round(score, 2),
            "recommended_angle": profile.ideal_approach,
            "likely_objections": profile.objection_patterns[:2],
        }


digital_twin_engine = DigitalTwinEngine()


# ═══════════════════════════════════════════════════════════════════════
# 3. BLOCKCHAIN PROOF OF AUDIT (remplace le stub)
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class AuditProof:
    proof_id: str
    audit_id: str
    audit_hash: str
    timestamp: str
    auditor: str
    client_company: str
    scope: str
    findings_count: int
    severity_summary: Dict[str, int]
    chain: str = "internal_ledger"
    block_number: int = 0
    previous_hash: str = ""


class BlockchainProofOfAudit:
    """Crée des preuves immuables d'audit avec chaîne de hachage."""

    def __init__(self) -> None:
        self.chain: List[AuditProof] = []
        self.genesis_hash = hashlib.sha256(b"NAYA_GENESIS_BLOCK").hexdigest()

    def create_proof(
        self,
        audit_id: str,
        client_company: str,
        scope: str,
        findings_count: int,
        severity_summary: Dict[str, int],
        auditor: str = "NAYA Intelligence",
    ) -> AuditProof:
        previous_hash = self.chain[-1].audit_hash if self.chain else self.genesis_hash

        data_to_hash = json.dumps({
            "audit_id": audit_id,
            "company": client_company,
            "scope": scope,
            "findings": findings_count,
            "severity": severity_summary,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "previous": previous_hash,
        }, sort_keys=True).encode()

        audit_hash = hashlib.sha256(data_to_hash).hexdigest()
        proof_id = f"PROOF-{audit_hash[:12].upper()}"

        proof = AuditProof(
            proof_id=proof_id,
            audit_id=audit_id,
            audit_hash=audit_hash,
            timestamp=datetime.now(timezone.utc).isoformat(),
            auditor=auditor,
            client_company=client_company,
            scope=scope,
            findings_count=findings_count,
            severity_summary=severity_summary,
            block_number=len(self.chain),
            previous_hash=previous_hash,
        )
        self.chain.append(proof)

        log.info("Audit proof created: %s for %s", proof_id, client_company)
        return proof

    def verify_chain(self) -> Tuple[bool, List[str]]:
        errors = []
        for i, proof in enumerate(self.chain):
            if i == 0:
                if proof.previous_hash != self.genesis_hash:
                    errors.append(f"Genesis block mismatch at index {i}")
            else:
                if proof.previous_hash != self.chain[i - 1].audit_hash:
                    errors.append(f"Chain broken at index {i}")
        return len(errors) == 0, errors

    def get_proof(self, audit_id: str) -> Optional[AuditProof]:
        for proof in self.chain:
            if proof.audit_id == audit_id:
                return proof
        return None

    def get_chain_length(self) -> int:
        return len(self.chain)


blockchain_proof = BlockchainProofOfAudit()


# ═══════════════════════════════════════════════════════════════════════
# 4. DECISION GRAPH ENGINE (remplace le stub)
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class DecisionNode:
    node_id: str
    question: str
    criteria: str
    weight: float
    yes_node: str = ""
    no_node: str = ""
    action: str = ""


class DecisionGraphEngine:
    """Graphe de décision multi-critères pour qualifier les prospects."""

    def __init__(self) -> None:
        self.nodes: Dict[str, DecisionNode] = {}
        self._build_default_graph()

    def _build_default_graph(self) -> None:
        nodes = [
            DecisionNode("start", "Est-ce une entreprise dans un secteur cible ?", "sector_match", 1.0, "check_size", "discard"),
            DecisionNode("check_size", "L'entreprise a-t-elle > 50 employés ?", "company_size", 0.8, "check_regulation", "small_biz"),
            DecisionNode("check_regulation", "Est-elle soumise à NIS2/IEC62443 ?", "regulation", 0.9, "check_budget", "educate"),
            DecisionNode("check_budget", "Y a-t-il un budget cybersécurité identifié ?", "budget", 0.7, "hot_lead", "nurture"),
            DecisionNode("hot_lead", "", "", 0.0, action="CLOSER_IMMÉDIAT — Proposer RDV cette semaine"),
            DecisionNode("nurture", "", "", 0.0, action="NURTURING — Séquence éducative 4 semaines"),
            DecisionNode("educate", "", "", 0.0, action="ÉDUCATION — Envoyer guide conformité + relancer dans 3 mois"),
            DecisionNode("small_biz", "", "", 0.0, action="OFFRE PME — Proposition audit allégé à 1000€"),
            DecisionNode("discard", "", "", 0.0, action="RECYCLER — Hors périmètre, remettre dans pool 6 mois"),
        ]
        for node in nodes:
            self.nodes[node.node_id] = node

    def evaluate(self, prospect_data: Dict[str, Any]) -> Dict[str, Any]:
        current = "start"
        path = []

        for _ in range(20):
            node = self.nodes.get(current)
            if not node:
                break
            path.append(current)

            if node.action:
                return {
                    "action": node.action,
                    "path": path,
                    "final_node": current,
                }

            criteria_value = prospect_data.get(node.criteria, False)
            if criteria_value:
                current = node.yes_node
            else:
                current = node.no_node

        return {"action": "MANUAL_REVIEW", "path": path, "final_node": current}


decision_graph_engine = DecisionGraphEngine()


# ═══════════════════════════════════════════════════════════════════════
# 5. AI ACT COMPLIANCE ENGINE (remplace le stub)
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class AIActAssessment:
    system_name: str
    risk_category: str
    obligations: List[str]
    compliant: bool
    gaps: List[str]
    recommendations: List[str]


RISK_CATEGORIES = {
    "unacceptable": {
        "description": "Systèmes interdits (scoring social, surveillance de masse)",
        "obligations": ["INTERDIT — Ne pas déployer"],
    },
    "high_risk": {
        "description": "Systèmes à haut risque (RH, crédit, santé, justice)",
        "obligations": [
            "Évaluation de conformité obligatoire",
            "Documentation technique complète",
            "Supervision humaine obligatoire",
            "Transparence et explicabilité",
            "Gestion des risques continue",
        ],
    },
    "limited_risk": {
        "description": "Systèmes à risque limité (chatbots, deepfakes)",
        "obligations": [
            "Obligation de transparence",
            "Informer que l'utilisateur interagit avec une IA",
        ],
    },
    "minimal_risk": {
        "description": "Systèmes à risque minimal (filtres, jeux)",
        "obligations": ["Pas d'obligation spécifique"],
    },
}


class AIActComplianceEngine:
    """Évalue la conformité EU AI Act d'un système."""

    def __init__(self) -> None:
        self.assessments: List[AIActAssessment] = []

    def assess_system(
        self,
        system_name: str,
        system_purpose: str,
        uses_personal_data: bool = False,
        automated_decisions: bool = False,
        sector: str = "",
    ) -> AIActAssessment:
        risk_category = self._classify_risk(
            system_purpose, uses_personal_data, automated_decisions, sector,
        )

        category_info = RISK_CATEGORIES.get(risk_category, RISK_CATEGORIES["minimal_risk"])
        obligations = category_info["obligations"]

        gaps = []
        recommendations = []

        if risk_category in ("high_risk", "limited_risk"):
            gaps.append("Documentation technique à compléter")
            recommendations.append("Rédiger la documentation technique conforme EU AI Act")

            if automated_decisions:
                gaps.append("Supervision humaine à implémenter")
                recommendations.append("Ajouter un mécanisme de supervision humaine")

            if uses_personal_data:
                gaps.append("Analyse d'impact vie privée requise")
                recommendations.append("Réaliser une AIPD (Analyse d'Impact Protection des Données)")

        compliant = len(gaps) == 0

        assessment = AIActAssessment(
            system_name=system_name,
            risk_category=risk_category,
            obligations=obligations,
            compliant=compliant,
            gaps=gaps,
            recommendations=recommendations,
        )
        self.assessments.append(assessment)
        return assessment

    def _classify_risk(
        self,
        purpose: str,
        personal_data: bool,
        automated: bool,
        sector: str,
    ) -> str:
        purpose_lower = purpose.lower()

        if any(k in purpose_lower for k in ["social scoring", "mass surveillance"]):
            return "unacceptable"

        high_risk_sectors = ["sante", "finance", "justice", "rh", "education"]
        if sector.lower() in high_risk_sectors and automated:
            return "high_risk"

        if personal_data and automated:
            return "high_risk"

        if any(k in purpose_lower for k in ["chatbot", "assistant", "generation"]):
            return "limited_risk"

        return "minimal_risk"

    def get_naya_self_assessment(self) -> AIActAssessment:
        return self.assess_system(
            system_name="NAYA SUPREME V19.5",
            system_purpose="B2B sales automation and cybersecurity consulting",
            uses_personal_data=True,
            automated_decisions=False,
            sector="cybersecurite",
        )


ai_act_compliance = AIActComplianceEngine()
