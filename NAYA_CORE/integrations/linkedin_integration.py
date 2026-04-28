"""
NAYA — LinkedIn Integration
Publication de posts LinkedIn et monitoring des réponses.
LinkedIn = canal principal de génération d'inbound B2B NAYA.

Modes:
  1. API LinkedIn officielle (nécessite OAuth2)
  2. Publication manuelle assistée (NAYA génère, tu publies)
  3. Webhook inbound pour tracker les réponses
"""
import os
import time
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field

log = logging.getLogger("NAYA.LINKEDIN")

def _gs(key: str, default: str = "") -> str:
    try:
        from SECRETS.secrets_loader import get_secret
        return get_secret(key, default) or default
    except Exception:
        return os.environ.get(key, default)


@dataclass
class LinkedInPost:
    content: str = ""
    url: str = ""
    post_id: str = ""
    published_at: float = 0.0
    likes: int = 0
    comments: int = 0
    impressions: int = 0
    leads_generated: int = 0
    status: str = "draft"       # draft / published / scheduled


class LinkedInIntegration:
    """
    Client LinkedIn pour NAYA.
    Publie des posts de chasse automatiques et track les inbounds.
    """

    API_BASE = "https://api.linkedin.com/v2"
    SHARE_URL = "https://api.linkedin.com/v2/ugcPosts"

    def __init__(self):
        self._post_count = 0
        self._posts = []

    @property
    def access_token(self) -> str: return _gs("LINKEDIN_ACCESS_TOKEN")
    @property
    def profile_urn(self) -> str: return _gs("LINKEDIN_PROFILE_URN")
    @property
    def org_urn(self) -> str: return _gs("LINKEDIN_ORG_URN")

    @property
    def available(self) -> bool:
        return (
            bool(self.access_token)
            and not self.access_token.startswith("METS")
            and bool(self.profile_urn)
            and not self.profile_urn.endswith("METS_TON_ID")
        )

    def publish_post(self, content: str, visibility: str = "PUBLIC") -> LinkedInPost:
        """
        Publie un post LinkedIn.
        Le contenu est généré par StorytellingEngine.
        """
        post = LinkedInPost(content=content, published_at=time.time(), status="draft")

        if not self.available:
            log.info(f"[LINKEDIN] Mode manuel — post prêt à publier:\n{content[:200]}...")
            post.status = "manual_required"
            self._posts.append(post)
            return post

        try:
            import httpx
            author = self.org_urn or self.profile_urn
            payload = {
                "author": author,
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {"text": content},
                        "shareMediaCategory": "NONE",
                    }
                },
                "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": visibility},
            }
            resp = httpx.post(
                self.SHARE_URL,
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                    "X-Restli-Protocol-Version": "2.0.0",
                },
                json=payload,
                timeout=20,
            )
            if resp.status_code in (200, 201):
                post_id = resp.headers.get("x-restli-id", resp.json().get("id", ""))
                post.post_id = post_id
                post.url = f"https://www.linkedin.com/feed/update/{post_id}"
                post.status = "published"
                self._post_count += 1
                log.info(f"[LINKEDIN] ✅ Post publié: {post.url}")
            else:
                log.warning(f"[LINKEDIN] HTTP {resp.status_code}: {resp.text[:200]}")
                post.status = "failed"
        except Exception as e:
            log.warning(f"[LINKEDIN] Erreur publication: {e}")
            post.status = "error"

        self._posts.append(post)
        return post

    def get_post_stats(self, post_id: str) -> Dict:
        """Récupère les stats d'un post (likes, comments, impressions)."""
        if not self.available:
            return {}
        try:
            import httpx
            resp = httpx.get(
                f"{self.API_BASE}/socialActions/{post_id}",
                headers={"Authorization": f"Bearer {self.access_token}"},
                timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "likes": data.get("likesSummary", {}).get("totalLikes", 0),
                    "comments": data.get("commentsSummary", {}).get("totalFirstLevelComments", 0),
                }
        except Exception as e:
            log.warning(f"[LINKEDIN] Stats error: {e}")
        return {}

    def generate_post_text(self, pain: str, solution: str, result: str, sector: str = "") -> str:
        """
        Template de post LinkedIn haute-performance.
        Format: Hook → Problème → Solution → Preuve → CTA
        """
        hook = f"⚠️ {pain.capitalize()} détruit silencieusement la marge de milliers d'entreprises."
        body = (
            f"\n\nBeaucoup de {sector or 'dirigeants'} ne le voient pas — "
            f"jusqu'à ce que les chiffres s'effondrent.\n\n"
            f"Ce qu'on a découvert :\n"
            f"→ {pain}\n"
            f"→ Solution : {solution}\n"
            f"→ Résultat : {result}\n\n"
            f"C'est résolu en 48H.\n\n"
            f"Si vous reconnaissez ce problème dans votre entreprise,\n"
            f"répondez 'OUI' en commentaire ou envoyez-moi un DM.\n\n"
            f"Je vous envoie un diagnostic gratuit."
        )
        hashtags = "\n\n#PME #Gestion #Performance #Rentabilité #Business"
        return hook + body + hashtags

    def get_stats(self) -> Dict:
        return {
            "available": self.available,
            "posts_published": self._post_count,
            "total_posts": len(self._posts),
            "recent_posts": [
                {"status": p.status, "content_preview": p.content[:80], "url": p.url}
                for p in self._posts[-5:]
            ],
        }


_linkedin: Optional[LinkedInIntegration] = None

def get_linkedin() -> LinkedInIntegration:
    global _linkedin
    if _linkedin is None:
        _linkedin = LinkedInIntegration()
    return _linkedin
