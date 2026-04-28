"""
REPLY HANDLER v19.1
Intelligent reply detection & routing
- Sentiment analysis (positive/negative/objection)
- Objection database (50 scénarios OT)
- Route to closer or auto-response
"""

import json
from typing import Dict, Optional
from datetime import datetime

class ReplyHandler:
    """Handle incoming prospect replies intelligently"""
    
    # 50 common OT/IEC 62443 objections + responses
    OBJECTION_DATABASE = {
        "too_expensive": {
            "keywords": ["cher", "coûteux", "budget", "prix", "trop", "rupture"],
            "response": "Je comprends. {prospect_name}, en général: 1) l'audit coûte moins qu'une incident ransomware, 2) on peut fractionner sur 3 mois, 3) ROI = <6 mois. Appel gratuit pour calibrer?"
        },
        "no_time": {
            "keywords": ["temps", "occupé", "maintenant", "pas capable", "après"],
            "response": "Bon. {prospect_name}, c'est justement pour ça qu'on fait ça en 5 jours sans interrupter. Et on peut aussi décaler. Tu dis quoi pour la semaine du 15?"
        },
        "not_priority": {
            "keywords": ["priorité", "d'autres", "focus", "not now", "plus tard"],
            "response": "Je comprends. Mais {prospect_name}: si un ransomware vous frappe demain, ce sera priorité non? L'audit juste te montre les risques. 1 appel = 30 min. Oui?"
        },
        "in_house": {
            "keywords": ["en interne", "internal", "on a", "déjà", "nous"],
            "response": "{prospect_name}, excellent si vous l'avez en interne. L'audit externe (3e regard) rattrape souvent 30-40% des gaps. Rapport tiers-confiance pour la direction?"
        },
        "need_approval": {
            "keywords": ["approbation", "comité", "directeur", "validation", "ok de"],
            "response": "Parfait. {prospect_name}, l'audit aide justement à faire la demande budget. On peut faire une présentation exec? Gratuit."
        },
        "already_did": {
            "keywords": ["déjà", "l'année", "récent", "avant", "dernier audit"],
            "response": "Super! {prospect_name}, depuis combien de temps? Les normes changent vite. Je peux juste vérifier les deltas NIS2/IEC 62443 v3? 1h."
        }
    }
    
    def __init__(self, config: Dict):
        self.config = config
        from NAYA_CORE.execution.llm_router import LLMRouter
        self.llm = LLMRouter(config)
    
    async def analyze_reply(self, reply_text: str) -> Dict[str, any]:
        """
        Analyze reply sentiment
        Returns: {sentiment: 'positive'|'negative'|'objection', confidence: 0.0-1.0, objection_type: str|None}
        """
        
        prompt = f"""
        Analyze this prospect reply for sentiment.
        Reply: "{reply_text}"
        
        Return JSON:
        {{
            "sentiment": "positive" or "negative" or "objection",
            "confidence": 0.0-1.0,
            "objection_type": null or specific objection,
            "explanation": "brief reason"
        }}
        """
        
        response = await self.llm.call(prompt, temperature=0.2)
        
        try:
            result = json.loads(response)
            return result
        except:
            # Fallback: keyword matching
            text_lower = reply_text.lower()
            
            if any(w in text_lower for w in ["oui", "yes", "intéressé", "interessé", "c'est bon", "ok", "parfait", "allons-y"]):
                return {"sentiment": "positive", "confidence": 0.8, "objection_type": None}
            elif any(w in text_lower for w in ["non", "no", "pas intéressé", "merci", "non merci"]):
                return {"sentiment": "negative", "confidence": 0.8, "objection_type": None}
            else:
                return {"sentiment": "objection", "confidence": 0.6, "objection_type": "other"}
    
    async def get_objection_response(self, reply_text: str, offer_value: int) -> Dict:
        """
        Get appropriate response to objection
        Uses database + LLM for nuance
        """
        
        reply_lower = reply_text.lower()
        
        # Find matching objection
        matched_objection = None
        for obj_type, obj_data in self.OBJECTION_DATABASE.items():
            if any(kw in reply_lower for kw in obj_data["keywords"]):
                matched_objection = obj_type
                break
        
        if matched_objection:
            base_response = self.OBJECTION_DATABASE[matched_objection]["response"]
        else:
            # Unknown objection - use LLM
            prompt = f"""
            Objection: {reply_text}
            Offer value: {offer_value} EUR
            
            Generate a brief, warm response that:
            1) Acknowledges the concern
            2) Provides a small reframe
            3) Offers next step
            
            Keep it to 3 sentences max.
            """
            base_response = await self.llm.call(prompt, temperature=0.5)
        
        return {
            "objection_type": matched_objection or "other",
            "response": base_response,
            "next_action": "send_response_email"  # or "escalate_to_closer"
        }
    
    async def route_reply(self, sentiment: str, confidence: float) -> str:
        """Route based on sentiment"""
        
        if sentiment == "positive" and confidence > 0.8:
            return "route_to_closer"
        elif sentiment == "objection":
            return "send_objection_response"
        elif sentiment == "negative":
            return "mark_failed"
        else:
            return "wait_for_clarification"
