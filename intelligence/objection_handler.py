#!/usr/bin/env python3
"""
NAYA SUPREME V19 — Objection Handler
Real-time objection detection from prospect replies.
Auto-response generation with best_response from memory.
Learning: record usage + success rate.
Uses NAYA_CORE/memory/objection_memory.py
"""

import asyncio
import logging
import os
from typing import Dict, List, Optional
from dataclasses import dataclass

# Import NAYA memory
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from NAYA_CORE.memory.objection_memory import objection_memory, ObjectionResponse
from ML_ENGINE.llm_router_v2 import get_llm_router_v2

log = logging.getLogger("NAYA.ObjectionHandler")


# ── Data Models ───────────────────────────────────────────────────────────────
@dataclass
class ObjectionDetection:
    """Detected objection from prospect reply."""
    objection_text: str
    category: str  # prix, timing, besoin, autorité, concurrence
    confidence: float  # 0-1
    best_response: ObjectionResponse
    context: Dict


# ── Objection Handler Engine ─────────────────────────────────────────────────
class ObjectionHandler:
    """
    Real-time objection detection and response generation.

    Features:
    - Detect objections from prospect replies
    - Match with best response from memory
    - Generate custom responses using LLM + RAG
    - Record usage and success rate
    - Learn from wins/losses
    """

    def __init__(self):
        self.memory = objection_memory
        self.llm_router = get_llm_router_v2()
        log.info("✅ ObjectionHandler initialized")

    # ── Objection Detection ───────────────────────────────────────────────────
    async def detect_objection(self, prospect_reply: str) -> Optional[str]:
        """
        Detect if prospect reply contains an objection.

        Args:
            prospect_reply: The prospect's message

        Returns:
            Objection category if detected, None otherwise
        """
        reply_lower = prospect_reply.lower()

        # Simple keyword-based detection (could be enhanced with ML)
        objection_patterns = {
            "prix": [
                "trop cher", "cher", "prix", "coût", "budget", "expensive",
                "combien", "tarif", "gratuit", "pas les moyens"
            ],
            "timing": [
                "plus tard", "pas maintenant", "en ce moment", "actuellement",
                "pas le temps", "mois prochain", "année prochaine", "trop tôt"
            ],
            "besoin": [
                "pas besoin", "déjà", "suffisant", "inutile", "pas nécessaire",
                "avons déjà", "pas convaincu", "pas prioritaire"
            ],
            "autorité": [
                "dois en parler", "pas moi qui décide", "mon chef", "ma hiérarchie",
                "comité", "validation", "autorisation"
            ],
            "concurrence": [
                "concurrent", "travaillons avec", "autre solution", "comparaison",
                "pourquoi vous", "déjà un fournisseur"
            ],
        }

        detected_categories = []
        for category, keywords in objection_patterns.items():
            if any(keyword in reply_lower for keyword in keywords):
                detected_categories.append(category)

        if detected_categories:
            # Return most likely category (first match)
            return detected_categories[0]

        # Check for negative sentiment (simple heuristic)
        negative_keywords = ["non", "pas", "ne", "jamais", "aucun", "impossible"]
        if sum(1 for word in negative_keywords if word in reply_lower) >= 2:
            return "besoin"  # Default to need objection

        return None

    # ── Response Handling ─────────────────────────────────────────────────────
    async def handle_objection(
        self,
        prospect_reply: str,
        sector: str,
        context: Optional[Dict] = None,
    ) -> Dict:
        """
        Handle objection: detect + find best response + generate custom response.

        Args:
            prospect_reply: The prospect's message
            sector: Business sector
            context: Additional context (prospect profile, offer sent, etc)

        Returns:
            Dict with objection detected, response, and metadata
        """
        # Detect objection
        objection_category = await self.detect_objection(prospect_reply)

        if not objection_category:
            return {
                "objection_detected": False,
                "response": None,
                "recommendation": "No objection detected - proceed with normal flow",
            }

        log.info("🛡️ Objection detected: category=%s", objection_category)

        # Find best response from memory
        best_match = await self.memory.find_best_response(prospect_reply, sector)

        if best_match:
            log.info("✅ Best match found: %s (success_rate=%.2f)",
                     best_match.objection_id, best_match.success_rate)

            # Generate custom response using LLM + RAG
            custom_response = await self._generate_custom_response(
                prospect_reply=prospect_reply,
                best_match=best_match,
                sector=sector,
                context=context or {},
            )

            return {
                "objection_detected": True,
                "objection_category": objection_category,
                "objection_id": best_match.objection_id,
                "base_response": best_match.best_response,
                "custom_response": custom_response,
                "success_rate": best_match.success_rate,
                "recommendation": "Send custom response",
            }
        else:
            # No match - generate from scratch
            log.warning("⚠️ No objection match found - generating from scratch")

            custom_response = await self._generate_custom_response(
                prospect_reply=prospect_reply,
                best_match=None,
                sector=sector,
                context=context or {},
            )

            return {
                "objection_detected": True,
                "objection_category": objection_category,
                "objection_id": None,
                "base_response": None,
                "custom_response": custom_response,
                "success_rate": 0.0,
                "recommendation": "Review response before sending (no historical match)",
            }

    # ── Response Generation ───────────────────────────────────────────────────
    async def _generate_custom_response(
        self,
        prospect_reply: str,
        best_match: Optional[ObjectionResponse],
        sector: str,
        context: Dict,
    ) -> str:
        """
        Generate custom objection response using LLM + RAG.

        Args:
            prospect_reply: The prospect's message
            best_match: Best matching objection from memory (if found)
            sector: Business sector
            context: Additional context

        Returns:
            Custom response text
        """
        # Build context for LLM
        llm_context = f"""
Prospect reply: {prospect_reply}

Context:
- Company: {context.get('company', 'N/A')}
- Sector: {sector}
- Contact: {context.get('contact_name', 'N/A')} ({context.get('contact_title', 'N/A')})
- Offer sent: {context.get('offer_value', 'N/A')} EUR
"""

        if best_match:
            llm_context += f"""

Best response from memory (success_rate={best_match.success_rate:.2%}):
{best_match.best_response}

Alternative responses:
{chr(10).join(f'- {alt}' for alt in best_match.alternative_responses[:3])}
"""

        prompt = f"""
Tu es un expert closer B2B OT/IEC62443. Le prospect vient d'émettre une objection.

{llm_context}

Génère une réponse de closing persuasive qui:
1. Valide l'objection (empathie)
2. Reframe avec des faits/chiffres concrets
3. Propose une action claire (call, meeting, demo)

Réponse (3-4 phrases max, ton professionnel mais chaleureux):
"""

        try:
            llm_response = self.llm_router.generate(
                task="closing_negotiation",
                prompt=prompt,
                sector=sector,
            )
            return llm_response.text
        except Exception as exc:
            log.warning("LLM generation failed: %s", exc)
            # Fallback to best match or template
            if best_match:
                return best_match.best_response
            else:
                return self._fallback_response(prospect_reply, sector)

    def _fallback_response(self, prospect_reply: str, sector: str) -> str:
        """Fallback response when LLM fails."""
        return f"""
Je comprends votre préoccupation. Dans le secteur {sector}, nous avons déjà accompagné
des entreprises similaires qui avaient les mêmes interrogations initiales.

Pourriez-vous m'accorder 15 minutes cette semaine pour que je vous montre concrètement
comment nous avons résolu ces challenges ? Je peux adapter la démo à votre contexte spécifique.

Merci,
"""

    # ── Learning ──────────────────────────────────────────────────────────────
    async def record_outcome(
        self,
        objection_id: str,
        won: bool,
    ) -> None:
        """
        Record objection handling outcome for learning.

        Args:
            objection_id: The objection ID from memory
            won: True if the objection was successfully handled (deal progressed)
        """
        if objection_id:
            await self.memory.record_usage(objection_id, won)
            log.info("📊 Recorded outcome for %s: won=%s", objection_id, won)

    # ── Query ─────────────────────────────────────────────────────────────────
    async def get_top_objections(self, category: Optional[str] = None, limit: int = 10) -> List[ObjectionResponse]:
        """Get top objections by usage."""
        return await self.memory.get_top_objections(category, limit)

    async def get_stats(self) -> Dict:
        """Get objection handling statistics."""
        return await self.memory.get_stats()

    # ── Training ──────────────────────────────────────────────────────────────
    async def add_custom_objection(
        self,
        objection_text: str,
        category: str,
        sector: str,
        best_response: str,
        alternative_responses: Optional[List[str]] = None,
    ) -> str:
        """
        Add a custom objection to the memory.

        Args:
            objection_text: The objection text
            category: Objection category
            sector: Business sector
            best_response: Best response to this objection
            alternative_responses: Alternative responses

        Returns:
            Objection ID
        """
        from datetime import datetime
        import hashlib

        objection_id = hashlib.sha256(objection_text.encode()).hexdigest()[:16]

        new_objection = ObjectionResponse(
            objection_id=objection_id,
            objection_text=objection_text,
            category=category,
            sector=sector,
            best_response=best_response,
            alternative_responses=alternative_responses or [],
            success_rate=0.0,
            used_count=0,
            won_count=0,
            created_at=datetime.now().isoformat(),
            last_updated=datetime.now().isoformat(),
        )

        self.memory.objections.append(new_objection)
        self.memory._save_memory()

        log.info("✅ Added custom objection: %s", objection_id)
        return objection_id


# ── CLI Test ──────────────────────────────────────────────────────────────────
async def main():
    """Test Objection Handler."""
    print("🛡️ NAYA Objection Handler — Test Module\n")

    handler = ObjectionHandler()

    # Test objections
    test_cases = [
        {
            "reply": "C'est vraiment trop cher pour nous, nous n'avons pas le budget.",
            "sector": "manufacturing",
            "context": {
                "company": "Test Corp",
                "contact_name": "Jean Dupont",
                "contact_title": "RSSI",
                "offer_value": 15000,
            },
        },
        {
            "reply": "On verra ça plus tard, ce n'est pas notre priorité en ce moment.",
            "sector": "transport_logistique",
            "context": {
                "company": "SNCF",
                "contact_name": "Marie Martin",
                "contact_title": "DSI",
                "offer_value": 40000,
            },
        },
        {
            "reply": "Nous travaillons déjà avec un concurrent, pourquoi changerions-nous ?",
            "sector": "energie_utilities",
            "context": {
                "company": "EDF",
                "contact_name": "Pierre Dubois",
                "contact_title": "Directeur Cybersécurité",
                "offer_value": 80000,
            },
        },
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*70}")
        print(f"Test Case {i}")
        print(f"{'='*70}")
        print(f"Prospect Reply: {test['reply']}")
        print(f"Sector: {test['sector']}")

        result = await handler.handle_objection(
            prospect_reply=test["reply"],
            sector=test["sector"],
            context=test["context"],
        )

        print(f"\n📊 Detection Result:")
        print(f"   Objection detected: {result['objection_detected']}")
        if result['objection_detected']:
            print(f"   Category: {result.get('objection_category')}")
            print(f"   Objection ID: {result.get('objection_id')}")
            print(f"   Success rate: {result.get('success_rate', 0):.1%}")
            print(f"   Recommendation: {result['recommendation']}")
            print(f"\n💬 Custom Response:")
            print(f"   {result['custom_response']}")

    # Stats
    print(f"\n{'='*70}")
    print("Statistics")
    print(f"{'='*70}")
    stats = await handler.get_stats()
    print(f"Total objections in memory: {stats['total_objections']}")
    print(f"Total times used: {stats['total_used']}")
    print(f"Total won: {stats['total_won']}")
    print(f"Global success rate: {stats['global_success_rate']:.1%}")


if __name__ == "__main__":
    asyncio.run(main())
