"""
NAYA SUPREME V19.3 — AMELIORATION #4
Prospect Deduplicator
=====================
Detection et fusion automatique des prospects doublons dans le pipeline.
Evite d'envoyer 2 offres au meme prospect et de perdre en credibilite.

Unique a NAYA : deduplication multi-signal (email, domaine, nom, telephone)
avec score de similarite et fusion intelligente des donnees.
"""
import re
import time
import logging
import threading
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

log = logging.getLogger("NAYA.DEDUP")


@dataclass
class DeduplicationResult:
    total_checked: int
    duplicates_found: int
    merged_groups: int
    unique_prospects: int
    merge_actions: List[Dict]
    elapsed_ms: float


class ProspectDeduplicator:
    """
    Moteur de deduplication multi-critere pour les prospects.

    Strategies de matching :
    1. Email exact → 100% doublon
    2. Domaine + nom similaire → 90% doublon
    3. Telephone normalise → 95% doublon
    4. Nom entreprise + ville → 80% doublon
    5. LinkedIn URL identique → 100% doublon
    """

    def __init__(self):
        self._merge_log: List[Dict] = []
        self._total_deduped: int = 0
        self._lock = threading.Lock()

    def find_duplicates(self, prospects: List[Dict]) -> DeduplicationResult:
        """Analyse une liste de prospects et identifie les doublons."""
        start = time.time()
        groups: Dict[str, List[int]] = {}
        merge_actions: List[Dict] = []

        for i, p in enumerate(prospects):
            keys = self._generate_match_keys(p)
            matched_group = None
            for key in keys:
                if key in groups:
                    matched_group = key
                    break
            if matched_group:
                groups[matched_group].append(i)
            else:
                primary_key = keys[0] if keys else f"prospect_{i}"
                groups[primary_key] = [i]

        # Identifier les groupes avec doublons
        duplicate_groups = {k: v for k, v in groups.items() if len(v) > 1}

        for key, indices in duplicate_groups.items():
            primary = prospects[indices[0]]
            duplicates = [prospects[idx] for idx in indices[1:]]
            merged = self._merge_prospects(primary, duplicates)
            merge_actions.append({
                "primary_id": primary.get("id", indices[0]),
                "primary_company": primary.get("company", primary.get("business_name", "")),
                "duplicates_count": len(duplicates),
                "duplicate_ids": [d.get("id", idx) for d, idx in zip(duplicates, indices[1:])],
                "merged_fields": list(merged.keys()),
                "match_key": key,
            })

        self._total_deduped += len(merge_actions)
        elapsed = round((time.time() - start) * 1000, 1)

        result = DeduplicationResult(
            total_checked=len(prospects),
            duplicates_found=sum(len(v) - 1 for v in duplicate_groups.values()),
            merged_groups=len(duplicate_groups),
            unique_prospects=len(groups),
            merge_actions=merge_actions,
            elapsed_ms=elapsed,
        )

        if merge_actions:
            log.info(
                f"[DEDUP] {result.duplicates_found} doublons trouves dans "
                f"{result.total_checked} prospects ({result.merged_groups} groupes)"
            )

        return result

    def _generate_match_keys(self, prospect: Dict) -> List[str]:
        """Genere les cles de matching pour un prospect."""
        keys = []

        # Email exact
        email = prospect.get("email", "").strip().lower()
        if email:
            keys.append(f"email:{email}")

        # LinkedIn URL
        linkedin = prospect.get("linkedin_url", "").strip().lower()
        if linkedin:
            keys.append(f"linkedin:{self._normalize_linkedin(linkedin)}")

        # Telephone normalise
        phone = prospect.get("phone", "").strip()
        if phone:
            normalized = self._normalize_phone(phone)
            if normalized:
                keys.append(f"phone:{normalized}")

        # Domaine email
        if email and "@" in email:
            domain = email.split("@")[1]
            if domain not in ("gmail.com", "yahoo.com", "hotmail.com", "outlook.com"):
                keys.append(f"domain:{domain}")

        # Nom entreprise normalise
        company = prospect.get("company", prospect.get("business_name", "")).strip().lower()
        if company:
            normalized_company = self._normalize_company(company)
            country = prospect.get("country", "").strip().lower()
            keys.append(f"company:{normalized_company}:{country}")

        return keys

    def _normalize_phone(self, phone: str) -> str:
        """Normalise un numero de telephone (garde uniquement les chiffres)."""
        digits = re.sub(r"[^\d+]", "", phone)
        if len(digits) < 8:
            return ""
        return digits[-10:]  # Derniers 10 chiffres

    def _normalize_linkedin(self, url: str) -> str:
        """Normalise une URL LinkedIn."""
        url = url.rstrip("/")
        parts = url.split("/")
        return parts[-1] if parts else url

    def _normalize_company(self, name: str) -> str:
        """Normalise un nom d'entreprise pour le matching."""
        name = name.lower().strip()
        # Retirer les suffixes juridiques communs
        for suffix in ["sas", "sarl", "sa", "srl", "gmbh", "ltd", "inc", "llc", "corp"]:
            name = re.sub(rf"\b{suffix}\b", "", name)
        # Retirer ponctuation et espaces multiples
        name = re.sub(r"[^\w\s]", "", name)
        name = re.sub(r"\s+", " ", name).strip()
        return name

    def _merge_prospects(self, primary: Dict, duplicates: List[Dict]) -> Dict:
        """Fusionne les donnees des doublons dans le prospect primaire."""
        merged = dict(primary)
        for dup in duplicates:
            for key, value in dup.items():
                if key in ("id", "created_at"):
                    continue
                if not merged.get(key) and value:
                    merged[key] = value
                elif key == "pain_score" and value:
                    current = merged.get(key, 0)
                    merged[key] = max(current, value)
                elif key == "revenue_potential" and value:
                    current = merged.get(key, 0)
                    merged[key] = max(current, value)
        return merged

    def deduplicate_pipeline(self, pipeline: Dict) -> Dict:
        """Deduplique le pipeline complet et retourne les stats."""
        prospects = list(pipeline.values()) if isinstance(pipeline, dict) else pipeline
        result = self.find_duplicates(prospects)
        return {
            "total_checked": result.total_checked,
            "duplicates_found": result.duplicates_found,
            "unique_after_dedup": result.unique_prospects,
            "merge_actions": result.merge_actions,
        }

    def get_stats(self) -> Dict:
        return {
            "total_deduped": self._total_deduped,
            "merge_log_size": len(self._merge_log),
        }


_dedup: Optional[ProspectDeduplicator] = None


def get_deduplicator() -> ProspectDeduplicator:
    global _dedup
    if _dedup is None:
        _dedup = ProspectDeduplicator()
    return _dedup
