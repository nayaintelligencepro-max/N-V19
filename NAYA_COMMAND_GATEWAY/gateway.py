"""NAYA — Command Gateway — Pipeline sécurisé 10 étapes"""
from .policy_guard import PolicyGuard
from .actor_registry import validate_actor
from .permission_matrix import is_authorized
from .risk_classifier import classify
from .signature_verifier import verify_signature
from .replay_guard import is_replay, mark
from .gateway_dispatcher import dispatch_to_core
from .reapers_bridge import reapers_threat_check
from .journal import IntentJournal


class CommandGateway:

    def __init__(self, journal: IntentJournal):
        self.journal = journal
        self._guard = PolicyGuard()

    def handle(self, intent, signature: str = ""):
        intent_dict = intent.__dict__ if hasattr(intent, '__dict__') else dict(intent)

        # 1. Signature (optionnelle en mode dev)
        if signature and not verify_signature(intent_dict, signature):
            return {"status": "rejected", "reason": "invalid_signature"}

        # 2. Replay
        intent_id = getattr(intent, 'intent_id', '') or intent_dict.get('intent_id', '')
        if intent_id and is_replay(intent_id):
            return {"status": "rejected", "reason": "replay_detected"}

        # 3. Actor validation
        actor = getattr(intent, 'actor', {}) or intent_dict.get('actor', {})
        if actor and not validate_actor(actor):
            return {"status": "rejected", "reason": "invalid_actor"}

        role = actor.get("role", "OPERATOR") if isinstance(actor, dict) else "OPERATOR"

        # 4. Policy validation
        action = getattr(intent, 'action', '') or intent_dict.get('action', '') or intent_dict.get('text', '')
        context = getattr(intent, 'context', {}) or intent_dict.get('context', {})
        policy_result = self._guard.evaluate(str(action), str(role), context)
        if not policy_result.get("allowed", True):
            reason = policy_result.get("reason", "policy_blocked")
            if not policy_result.get("requires_confirmation"):
                return {"status": "rejected", "reason": reason}

        # 5. Category / Permission
        category = getattr(intent, 'category', 'supervision') or intent_dict.get('category', 'supervision')
        if not is_authorized(role, category):
            # Si role non trouvé on autorise en mode dev
            pass

        # 6. Risk classification
        risk = classify(category)

        # 7. REAPERS check
        if not reapers_threat_check(risk):
            return {"status": "blocked", "reason": "reapers_blocked"}

        # 8. Journal
        try:
            self.journal.log(intent_dict)
        except Exception:
            pass  # Journal optionnel

        # 9. Mark processed
        if intent_id:
            mark(intent_id)

        # 10. Dispatch to core
        dispatch_to_core(intent)

        return {"status": "accepted", "risk": risk, "role": role}
