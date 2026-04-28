"""
NAYA — Apollo.io Integration V2 (Production)
Prospection B2B via Apollo.io. Clé: SECRETS/keys/market_data.env → APOLLO_API_KEY
"""
import os, time, logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field

log = logging.getLogger("NAYA.APOLLO")

def _gs(key:str, default:str="") -> str:
    try:
        from SECRETS.secrets_loader import get_secret
        return get_secret(key, default) or default
    except Exception:
        return os.environ.get(key, default)

@dataclass
class ApolloContact:
    id:str=""; first_name:str=""; last_name:str=""; name:str=""; title:str=""
    email:str=""; email_status:str=""; phone:str=""; linkedin_url:str=""
    company_name:str=""; company_domain:str=""; company_industry:str=""
    company_employees:int=0; company_city:str=""; company_country:str="FR"
    seniority:str=""
    @property
    def full_name(self) -> str: return self.name or f"{self.first_name} {self.last_name}".strip()
    @property
    def is_decision_maker(self) -> bool:
        return self.seniority.lower() in {"director","c_suite","vp","partner","founder","owner","president"}
    @property
    def has_verified_email(self) -> bool:
        return self.email_status in ("verified","likely_to_engage") and bool(self.email)
    def to_dict(self) -> Dict:
        return {"id":self.id,"name":self.full_name,"title":self.title,"email":self.email,
                "email_status":self.email_status,"phone":self.phone,"linkedin_url":self.linkedin_url,
                "company":self.company_name,"industry":self.company_industry,"city":self.company_city,
                "country":self.company_country,"employees":self.company_employees,
                "seniority":self.seniority,"decision_maker":self.is_decision_maker,
                "verified_email":self.has_verified_email}

SECTOR_FILTERS = {
    "pme_b2b":{"seniority":["director","manager","c_suite","owner","founder"],"titles":["CEO","CFO","Directeur","Gérant","Fondateur","PDG"],"employees":["11-50","51-200"]},
    "artisan_trades":{"seniority":["owner","founder","manager"],"titles":["Gérant","Artisan","Patron"],"employees":["1-10","11-50"]},
    "restaurant_food":{"seniority":["owner","founder","manager"],"titles":["Chef","Gérant","Propriétaire"],"employees":["1-10","11-50"]},
    "healthcare_wellness":{"seniority":["director","manager","c_suite","owner","founder"],"titles":["Directeur médical","Gérant","Dr"],"employees":["1-10","11-50","51-200"]},
    "ecommerce":{"seniority":["director","c_suite","founder","owner"],"titles":["CEO","Fondateur","Directeur"],"employees":["1-10","11-50","51-200"]},
    "startup_scaleup":{"seniority":["c_suite","vp","director","founder"],"titles":["CEO","CTO","CFO","VP","Head of"],"employees":["11-50","51-200","201-500"]},
    "liberal_professions":{"seniority":["owner","founder","partner","director"],"titles":["Avocat","Expert-comptable","Notaire","Architecte"],"employees":["1-10","11-50"]},
}

class ApolloIntegration:
    BASE = "https://api.apollo.io/v1"
    RATE = 1.0

    def __init__(self):
        self._last=0.0; self._calls=0; self._total=0

    @property
    def api_key(self) -> str: return _gs("APOLLO_API_KEY")
    @property
    def available(self) -> bool: return bool(self.api_key)

    def _wait(self):
        e = time.time()-self._last
        if e < self.RATE: time.sleep(self.RATE-e)
        self._last = time.time()

    def _post(self, ep:str, payload:Dict) -> Optional[Dict]:
        if not self.available: return None
        try:
            import httpx; self._wait()
            r = httpx.post(f"{self.BASE}/{ep}",
                headers={"Content-Type":"application/json","X-Api-Key":self.api_key},
                json=payload, timeout=30)
            self._calls += 1
            if r.status_code==200: return r.json()
            if r.status_code==429: time.sleep(5)
            log.warning(f"[APOLLO] HTTP {r.status_code}")
        except Exception as e: log.warning(f"[APOLLO] {e}")
        return None

    def search_contacts(self, sector:str="pme_b2b", count:int=10, city:str="", country:str="France") -> List[ApolloContact]:
        if not self.available:
            log.info("[APOLLO] Clé manquante — SECRETS/keys/market_data.env → APOLLO_API_KEY"); return []
        f = SECTOR_FILTERS.get(sector, SECTOR_FILTERS["pme_b2b"])
        payload = {
            "per_page":min(count,25),"page":1,
            "person_seniorities":f["seniority"],
            "person_titles":f["titles"],
            "organization_num_employees_ranges":f["employees"],
            "contact_email_status":["verified","likely_to_engage"],
        }
        if country: payload["contact_location_country_codes"]=["FR" if "france" in country.lower() else country[:2].upper()]
        if city: payload["contact_location_city_raw"]=[city]
        data = self._post("mixed_people/search", payload)
        if not data: return []
        contacts=[]
        for p in data.get("people",[])[:count]:
            org=p.get("organization") or {}
            contacts.append(ApolloContact(
                id=p.get("id",""), first_name=p.get("first_name",""), last_name=p.get("last_name",""),
                name=p.get("name",""), title=p.get("title",""), email=p.get("email",""),
                email_status=p.get("email_status",""), phone=p.get("sanitized_phone",""),
                linkedin_url=p.get("linkedin_url",""), company_name=org.get("name",""),
                company_domain=org.get("primary_domain",""), company_industry=org.get("industry",""),
                company_employees=org.get("num_employees",0) or 0,
                company_city=p.get("city",""), company_country=p.get("country","FR"),
                seniority=p.get("seniority",""),
            ))
        self._total += len(contacts)
        log.info(f"[APOLLO] {len(contacts)} contacts — {sector}")
        return contacts

    def get_stats(self) -> Dict:
        return {"available":self.available,"calls":self._calls,"contacts":self._total,
                "config":"SECRETS/keys/market_data.env → APOLLO_API_KEY"}

_A:Optional[ApolloIntegration]=None
def get_apollo() -> ApolloIntegration:
    global _A
    if _A is None: _A=ApolloIntegration()
    return _A
