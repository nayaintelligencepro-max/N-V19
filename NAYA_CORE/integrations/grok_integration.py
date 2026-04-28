"""
NAYA V19 — Grok/xAI Integration
Cerveau LLM alternatif — actif automatiquement si Anthropic sans crédit.
Clé: SECRETS/keys/grok.json → GROK_API_KEY
"""
import os, logging
from typing import Dict, Optional
log = logging.getLogger("NAYA.GROK")

def _gs(k, d=""):
    try:
        from SECRETS.secrets_loader import get_secret
        return get_secret(k,d) or d
    except: return os.environ.get(k,d)

class GrokIntegration:
    BASE_URL = "https://api.x.ai/v1"
    MODEL = "grok-beta"

    def __init__(self): pass

    @property
    def api_key(self) -> str: return _gs("GROK_API_KEY") or _gs("XAI_API_KEY")
    @property
    def available(self) -> bool: return bool(self.api_key)

    def complete(self, prompt: str, system: str = "", max_tokens: int = 1500,
                 temperature: float = 0.3) -> str:
        if not self.available: return ""
        try:
            import httpx
            messages = []
            if system: messages.append({"role":"system","content":system})
            messages.append({"role":"user","content":prompt})
            r = httpx.post(
                f"{self.BASE_URL}/chat/completions",
                headers={"Authorization":f"Bearer {self.api_key}","Content-Type":"application/json"},
                json={"model":self.MODEL,"messages":messages,
                      "max_tokens":max_tokens,"temperature":temperature},
                timeout=45
            )
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"]
            log.warning(f"[GROK] HTTP {r.status_code}: {r.text[:100]}")
            return ""
        except Exception as e:
            log.warning(f"[GROK] {e}"); return ""

    def get_stats(self) -> Dict:
        return {"available":self.available,"model":self.MODEL,
                "key_prefix":self.api_key[:12]+"..." if self.available else ""}

_g: Optional[GrokIntegration] = None
def get_grok() -> GrokIntegration:
    global _g
    if _g is None: _g = GrokIntegration()
    return _g
