"""
NAYA — Hunter.io Integration (Production)
Vérification et découverte d'emails. Clé: SECRETS/keys/market_data.env → HUNTER_IO_API_KEY
"""
import os, logging
from typing import Dict, List, Optional
from dataclasses import dataclass

log = logging.getLogger("NAYA.HUNTER")

def _gs(key:str, default:str="") -> str:
    try:
        from SECRETS.secrets_loader import get_secret
        return get_secret(key, default) or default
    except Exception:
        return os.environ.get(key, default)

@dataclass
class HunterEmail:
    email:str=""; first_name:str=""; last_name:str=""
    position:str=""; confidence:int=0; department:str=""; verified:bool=False
    @property
    def is_reliable(self) -> bool: return self.confidence>=70 and bool(self.email)

class HunterIntegration:
    BASE = "https://api.hunter.io/v2"

    def __init__(self): self._calls=0

    @property
    def api_key(self) -> str: return _gs("HUNTER_IO_API_KEY")
    @property
    def available(self) -> bool: return bool(self.api_key)

    def _get(self, ep:str, params:Dict) -> Optional[Dict]:
        if not self.available: return None
        try:
            import httpx
            params["api_key"]=self.api_key
            r = httpx.get(f"{self.BASE}/{ep}",params=params,timeout=15)
            self._calls+=1
            return r.json() if r.status_code==200 else None
        except Exception as e: log.warning(f"[HUNTER] {e}"); return None

    def find_emails_by_domain(self, domain:str, limit:int=10) -> List[HunterEmail]:
        data=self._get("domain-search",{"domain":domain,"limit":limit})
        if not data: return []
        return [HunterEmail(email=e.get("value",""),first_name=e.get("first_name",""),
                last_name=e.get("last_name",""),position=e.get("position",""),
                confidence=e.get("confidence",0),department=e.get("department",""))
                for e in data.get("data",{}).get("emails",[])]

    def find_email(self, domain:str, first_name:str, last_name:str) -> Optional[HunterEmail]:
        data=self._get("email-finder",{"domain":domain,"first_name":first_name,"last_name":last_name})
        if not data or not data.get("data",{}).get("email"): return None
        d=data["data"]
        return HunterEmail(email=d.get("email",""),first_name=first_name,
                          last_name=last_name,confidence=d.get("score",0))

    def verify_email(self, email:str) -> bool:
        data=self._get("email-verifier",{"email":email})
        return data.get("data",{}).get("result","") in ("deliverable","risky") if data else False

    def get_stats(self) -> Dict:
        return {"available":self.available,"calls":self._calls,
                "config":"SECRETS/keys/market_data.env → HUNTER_IO_API_KEY"}

_H:Optional[HunterIntegration]=None
def get_hunter() -> HunterIntegration:
    global _H
    if _H is None: _H=HunterIntegration()
    return _H
