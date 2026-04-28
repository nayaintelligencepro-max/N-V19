"""
NAYA — Notion Integration
Sync mémoire, opportunités, business plans vers Notion.
Requiert: NOTION_API_KEY + NOTION_DATABASE_ID dans .env
"""
import os
import time
import logging
from typing import Dict, List, Optional

log = logging.getLogger("NAYA.NOTION")

def _gs(key, default=""):
    try:
        from SECRETS.secrets_loader import get_secret
        return get_secret(key, default) or default
    except Exception:
        return __import__("os").environ.get(key, default)



class NotionIntegration:
    """Connecteur Notion pour export et sync des données NAYA."""

    def __init__(self):
        self.api_key = _gs("NOTION_API_KEY")
        self.db_id = _gs("NOTION_DATABASE_ID")
        self.available = bool(self.api_key and self.db_id)
        if not self.available:
            log.debug("Notion non configuré — ajoute NOTION_API_KEY + NOTION_DATABASE_ID dans .env")

    def sync(self, payload: Dict = None) -> Dict:
        payload = payload or {}
        if not self.available:
            return {"status": "not_configured", "hint": "Ajoute NOTION_API_KEY + NOTION_DATABASE_ID dans .env"}
        try:
            import httpx
            pages = self._prepare_pages(payload)
            created = 0
            for page in pages:
                resp = httpx.post(
                    "https://api.notion.com/v1/pages",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Notion-Version": "2022-06-28",
                        "Content-Type": "application/json",
                    },
                    json=page,
                    timeout=10,
                )
                if resp.status_code in (200, 201):
                    created += 1
                else:
                    log.warning(f"Notion page error: {resp.status_code} {resp.text[:200]}")
            return {"status": "synced", "pages_created": created}
        except ImportError:
            return {"status": "error", "error": "httpx non installé — pip install httpx"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _prepare_pages(self, payload: Dict) -> List[Dict]:
        """Prépare les pages Notion depuis le payload."""
        pages = []
        # Sync mémoire NAYA
        if payload.get("sync_memory"):
            try:
                from NAYA_CORE.memory.distributed_memory import get_memory
                entries = get_memory().export_for_notion(limit=payload.get("limit", 50))
                for e in entries:
                    pages.append(self._memory_to_notion_page(e))
            except Exception as ex:
                log.warning(f"Memory export: {ex}")
        # Sync une opportunité spécifique
        elif payload.get("opportunity"):
            opp = payload["opportunity"]
            pages.append(self._opportunity_to_notion_page(opp))
        return pages

    def _memory_to_notion_page(self, entry: Dict) -> Dict:
        return {
            "parent": {"database_id": self.db_id},
            "properties": {
                "Name": {"title": [{"text": {"content": f"[{entry.get('Catégorie','?')}] {entry.get('id','')}"}}]},
                "Date": {"date": {"start": entry.get("Date", "")[:10]}},
                "Catégorie": {"select": {"name": entry.get("Catégorie", "decision")}},
                "Projet": {"rich_text": [{"text": {"content": entry.get("Projet", "global")}}]},
                "Résumé": {"rich_text": [{"text": {"content": (entry.get("Opportunité") or entry.get("Décision", ""))[:2000]}}]},
            }
        }

    def _opportunity_to_notion_page(self, opp: Dict) -> Dict:
        return {
            "parent": {"database_id": self.db_id},
            "properties": {
                "Name": {"title": [{"text": {"content": opp.get("name", "Opportunité NAYA")}}]},
                "Date": {"date": {"start": time.strftime("%Y-%m-%d")}},
                "Catégorie": {"select": {"name": "opportunity"}},
                "Projet": {"rich_text": [{"text": {"content": opp.get("project", "global")}}]},
                "Résumé": {"rich_text": [{"text": {"content": str(opp)[:2000]}}]},
            }
        }

    def push_opportunity(self, opportunity: Dict) -> Dict:
        """Push une opportunité directement dans Notion."""
        return self.sync({"opportunity": opportunity})

    def export_memory(self, limit: int = 100) -> Dict:
        """Exporte la mémoire NAYA vers Notion."""
        return self.sync({"sync_memory": True, "limit": limit})
