"""
NAYA V19 — Prospect Validator
Vérifie qu'un prospect est RÉEL avant de dépenser de l'énergie en outreach.
Élimine les faux positifs du Serper : pages Wikipedia, articles de presse, etc.
"""
import re, logging, time, threading
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse

log = logging.getLogger("NAYA.VALIDATOR")


class ProspectValidator:
    """
    Filtre les prospects non-actionnables AVANT l'enrichissement.
    Un prospect valide a: une entité identifiable + un secteur + une URL de site d'entreprise.
    """

    # Domaines à TOUJOURS rejeter (pas des entreprises)
    BLACKLIST_DOMAINS = {
        "wikipedia.org", "youtube.com", "facebook.com", "twitter.com",
        "instagram.com", "tiktok.com", "reddit.com", "pinterest.com",
        "amazon.com", "amazon.fr", "ebay.com", "ebay.fr",
        "lemonde.fr", "lefigaro.fr", "liberation.fr", "bfmtv.com",
        "francetvinfo.fr", "leparisien.fr", "20minutes.fr",
        "indeed.com", "indeed.fr", "glassdoor.com", "glassdoor.fr",
        "pagesjaunes.fr", "societe.com", "infogreffe.fr",
        "gov.fr", "service-public.fr", "impots.gouv.fr",
        "google.com", "google.fr", "bing.com",
    }

    # Mots-clés dans le titre/snippet qui indiquent un NON-prospect
    REJECT_KEYWORDS = {
        "wikipedia", "actualit", "article", "presse", "journal",
        "emploi", "recrutement", "offre d'emploi", "job", "career",
        "formation gratuite", "mooc", "cours en ligne",
        "avis consommateur", "comparatif", "classement",
        "annuaire", "pages jaunes", "kompass",
    }

    # Mots-clés qui CONFIRMENT un prospect valide
    CONFIRM_KEYWORDS = {
        "entreprise", "société", "sarl", "sas", "eurl", "sa ",
        "cabinet", "agence", "bureau", "atelier", "boutique",
        "restaurant", "hotel", "hôtel", "clinique", "pharmacie",
        "gérant", "directeur", "fondateur", "pdg", "ceo",
        "services", "solutions", "expertise", "conseil",
    }

    def __init__(self):
        self._lock = threading.Lock()
        self._validated = 0
        self._rejected = 0

    def validate(self, prospect: Dict) -> Tuple[bool, str]:
        """
        Valide un prospect. Retourne (is_valid, reason).
        """
        entity = prospect.get("entity", prospect.get("company_name", "")).strip()
        url = prospect.get("url", "").strip()
        description = prospect.get("description", prospect.get("snippet", "")).strip().lower()
        sector = prospect.get("sector", "").strip()

        # Check 1: Entité non vide
        if not entity or len(entity) < 3:
            self._rejected += 1
            return False, "entity_too_short"

        # Check 2: URL blacklistée
        if url:
            domain = self._extract_domain(url)
            if domain in self.BLACKLIST_DOMAINS or any(bl in domain for bl in self.BLACKLIST_DOMAINS):
                self._rejected += 1
                return False, f"blacklisted_domain:{domain}"

        # Check 3: Mots-clés de rejet dans description
        if description:
            for kw in self.REJECT_KEYWORDS:
                if kw in description:
                    self._rejected += 1
                    return False, f"reject_keyword:{kw}"

        # Check 4: Valeur estimée réaliste
        value = prospect.get("estimated_value", 0)
        if isinstance(value, (int, float)) and value < 500:
            self._rejected += 1
            return False, "value_too_low"

        # Check 5: Bonus — mots-clés de confirmation
        has_confirm = any(kw in description or kw in entity.lower()
                          for kw in self.CONFIRM_KEYWORDS)

        # Check 6: L'entité ne doit pas être un titre d'article
        if len(entity) > 120:
            self._rejected += 1
            return False, "entity_looks_like_article_title"

        if entity.startswith('"') or entity.startswith("«"):
            self._rejected += 1
            return False, "entity_is_quoted_text"

        self._validated += 1
        confidence = 0.8 if has_confirm else 0.6
        return True, f"valid:confidence={confidence}"

    def validate_batch(self, prospects: list) -> list:
        """Filtre une liste de prospects, retourne uniquement les valides."""
        valid = []
        for p in prospects:
            is_valid, reason = self.validate(p)
            if is_valid:
                p["validation_status"] = reason
                valid.append(p)
            else:
                log.debug(f"[VALIDATOR] Rejeté: {p.get('entity', '?')[:50]} — {reason}")
        log.info(f"[VALIDATOR] {len(valid)}/{len(prospects)} prospects valides")
        return valid

    def _extract_domain(self, url: str) -> str:
        try:
            parsed = urlparse(url)
            domain = parsed.netloc or parsed.path.split("/")[0]
            domain = domain.lower().replace("www.", "")
            return domain
        except Exception:
            return ""

    def get_stats(self) -> Dict:
        total = self._validated + self._rejected
        return {
            "validated": self._validated,
            "rejected": self._rejected,
            "total": total,
            "validation_rate": round(self._validated / max(total, 1) * 100, 1),
        }


_validator = None
_validator_lock = threading.Lock()

def get_prospect_validator() -> ProspectValidator:
    global _validator
    if _validator is None:
        with _validator_lock:
            if _validator is None:
                _validator = ProspectValidator()
    return _validator
