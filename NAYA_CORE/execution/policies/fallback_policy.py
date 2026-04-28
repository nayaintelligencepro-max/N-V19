"""NAYA V19 - Fallback Policy - Politique de fallback entre providers."""
import logging
from typing import List, Optional

log = logging.getLogger("NAYA.POLICY.FALLBACK")

class FallbackPolicy:
    """Definit l ordre de fallback entre les providers LLM."""

    FALLBACK_CHAIN = [
        "groq",         # Gratuit, ultra-rapide
        "deepseek",     # Quasi-gratuit, tres bon
        "huggingface",  # Gratuit, variable
        "ollama",       # Gratuit, local
        "anthropic",    # Payant, meilleur
        "openai",       # Payant, bon
        "grok",         # Payant, rapide
        "internal",     # Templates internes sans LLM
    ]

    TASK_PREFERENCES = {
        "strategic": ["anthropic", "deepseek", "groq"],
        "creative": ["anthropic", "openai", "deepseek"],
        "fast": ["groq", "deepseek", "ollama"],
        "analysis": ["deepseek", "anthropic", "groq"],
        "outreach": ["groq", "deepseek", "huggingface"],
        "general": FALLBACK_CHAIN[:4],
    }

    def get_chain(self, task_type: str = "general") -> List[str]:
        return self.TASK_PREFERENCES.get(task_type, self.FALLBACK_CHAIN[:4])

    def next_provider(self, current: str, task_type: str = "general") -> Optional[str]:
        chain = self.get_chain(task_type)
        try:
            idx = chain.index(current)
            if idx + 1 < len(chain):
                return chain[idx + 1]
        except ValueError:
            pass
        return "internal"

    def get_stats(self) -> dict:
        return {"chain_length": len(self.FALLBACK_CHAIN), "task_types": list(self.TASK_PREFERENCES.keys())}
