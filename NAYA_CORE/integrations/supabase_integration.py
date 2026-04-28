"""
NAYA V19 — Supabase Integration
Base de données PostgreSQL cloud — backup et sync du pipeline.
Projet: rndocrhwoncfiopmzhg.supabase.co
"""
import os
import json
import logging
import urllib.request
import urllib.parse
from typing import Dict, List, Optional, Any

log = logging.getLogger("NAYA.SUPABASE")


def _gs(k: str, d: str = "") -> str:
    try:
        from SECRETS.secrets_loader import get_secret
        return get_secret(k, d) or d
    except Exception:
        return os.environ.get(k, d)


class SupabaseIntegration:
    """
    Connecteur Supabase REST API.
    Sync pipeline, prospects, revenus vers PostgreSQL cloud.
    """

    def __init__(self):
        self._url    = _gs("SUPABASE_URL", "https://rndocrhwoncfiopmzhg.supabase.co")
        self._anon   = _gs("SUPABASE_ANON_KEY")
        self._service = _gs("SUPABASE_SERVICE_KEY")
        self.available = bool(self._url and (self._anon or self._service))

        if self.available:
            log.info(f"[SUPABASE] Connecté: {self._url}")
        else:
            log.debug("[SUPABASE] Clés manquantes")

    def _headers(self, use_service: bool = False) -> Dict:
        key = self._service if use_service else self._anon
        return {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    def _request(self, method: str, endpoint: str, data: Any = None,
                 params: Dict = None, use_service: bool = False) -> Optional[Dict]:
        if not self.available:
            return None
        try:
            url = f"{self._url}/rest/v1/{endpoint}"
            if params:
                url += "?" + urllib.parse.urlencode(params)
            payload = json.dumps(data).encode() if data else None
            req = urllib.request.Request(
                url, data=payload,
                headers=self._headers(use_service),
                method=method
            )
            with urllib.request.urlopen(req, timeout=10) as r:
                body = r.read().decode()
                return json.loads(body) if body else {}
        except Exception as e:
            log.warning(f"[SUPABASE] {method} {endpoint}: {e}")
            return None

    def upsert_prospect(self, prospect: Dict) -> bool:
        """Sync un prospect vers Supabase."""
        data = {
            "id":          prospect.get("id", ""),
            "company":     prospect.get("company", prospect.get("company_name", "")),
            "email":       prospect.get("email", ""),
            "sector":      prospect.get("sector", ""),
            "status":      prospect.get("status", "NEW"),
            "offer_price": float(prospect.get("offer_price", 0)),
            "pain":        prospect.get("pain_category", ""),
            "city":        prospect.get("city", ""),
            "created_at":  prospect.get("created_at", ""),
        }
        result = self._request("POST", "naya_pipeline",
                               data=[data],
                               params={"on_conflict": "id"},
                               use_service=True)
        return result is not None

    def get_pipeline(self, limit: int = 100) -> List[Dict]:
        """Récupère le pipeline depuis Supabase."""
        result = self._request("GET", "naya_pipeline",
                               params={"limit": limit, "order": "created_at.desc"})
        return result if isinstance(result, list) else []

    def log_revenue(self, amount: float, company: str, sector: str, method: str = "paypal") -> bool:
        """Enregistre un revenu gagné."""
        data = {
            "amount":     amount,
            "company":    company,
            "sector":     sector,
            "method":     method,
            "created_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        }
        result = self._request("POST", "naya_revenue",
                               data=[data], use_service=True)
        return result is not None

    def sync_pipeline_from_local(self) -> Dict:
        """Sync le pipeline local SQLite → Supabase."""
        if not self.available:
            return {"synced": 0, "reason": "Supabase non configuré"}
        try:
            from NAYA_REVENUE_ENGINE.pipeline_tracker import PipelineTracker
            pt = PipelineTracker()
            entries = pt.all()
            synced = 0
            for entry in entries:
                if self.upsert_prospect(entry):
                    synced += 1
            log.info(f"[SUPABASE] Sync: {synced}/{len(entries)} prospects")
            return {"synced": synced, "total": len(entries)}
        except Exception as e:
            return {"synced": 0, "error": str(e)}

    def get_stats(self) -> Dict:
        return {
            "available": self.available,
            "url": self._url,
            "has_service_key": bool(self._service),
        }


_supa: Optional[SupabaseIntegration] = None
_supa_lock = __import__("threading").Lock()


def get_supabase() -> SupabaseIntegration:
    global _supa
    if _supa is None:
        with _supa_lock:
            if _supa is None:
                _supa = SupabaseIntegration()
    return _supa
