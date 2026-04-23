"""
NAYA V20 — Sentiment Radar
══════════════════════════════════════════════════════════════════════════════
Real-time distress scoring on social posts from RSSI/DSI decision-makers.

DOCTRINE:
  A RSSI posting "nuit blanche" + "incident" at 3 AM is a HOT lead with a
  budget that just became unblocked.  We reach them within the hour with a
  tailored OT audit proposal.

SCORING:
  Keyword-weighted distress score 0–100 accumulated per post.
  Score ≥ 80 → immediate Telegram alert + TIER-URGENCE outreach
  Score ≥ 70 → hot lead queue (same-day contact)
  Score < 70 → standard enrichment pipeline

SOURCES (pluggable via ingest_post):
  LinkedIn posts, Twitter/X mentions, Mastodon industry feeds,
  RSS blogs RSSI, Telegram public channels.
══════════════════════════════════════════════════════════════════════════════
"""
import hashlib
import json
import logging
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

log = logging.getLogger("NAYA.SENTIMENT_RADAR")

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_FILE = ROOT / "data" / "cache" / "sentiment_radar.json"

MIN_SCORE_ALERT = 80
MIN_SCORE_HOT = 70

DISTRESS_KEYWORDS: Dict[str, int] = {
    "nuit blanche": 25,
    "incident": 20,
    "attaque": 25,
    "ransomware": 30,
    "SCADA down": 30,
    "production arrêtée": 25,
    "conformité": 15,
    "audit": 15,
    "urgence": 20,
    "deadline": 15,
    "NIS2": 15,
    "vulnérable": 20,
}


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


@dataclass
class SentimentSignal:
    """A scored distress signal from a social post."""

    post_id: str
    author_name: str
    author_role: str
    company: str
    text_snippet: str          # first 200 chars of original post
    platform: str
    distress_score: float      # 0–100
    hot_keywords: List[str]
    is_hot_lead: bool
    posted_at: str


class SentimentRadar:
    """
    Ingests social posts, scores them for OT-security distress and surfaces
    hot leads in real time.

    Thread-safe singleton.  All signals persisted to DATA_FILE.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._data_file = DATA_FILE
        self._signals: List[Dict] = []
        self._seen_ids: set = set()
        self._load()

    # ──────────────────────────────────────────────────────────────────────
    # Persistence
    # ──────────────────────────────────────────────────────────────────────

    def _load(self) -> None:
        if self._data_file.exists():
            try:
                with open(self._data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._signals = data.get("signals", [])
                    self._seen_ids = set(data.get("seen_ids", []))
            except Exception:
                pass

    def _save(self) -> None:
        self._data_file.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            with open(self._data_file, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "signals": self._signals,
                        "seen_ids": list(self._seen_ids),
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    },
                    f,
                    indent=2,
                    ensure_ascii=False,
                )

    # ──────────────────────────────────────────────────────────────────────
    # Scoring
    # ──────────────────────────────────────────────────────────────────────

    def _compute_score(self, text: str) -> tuple:
        """
        Compute distress score and matched keywords for a post.

        Returns:
            Tuple of (score: float, matched_keywords: List[str]).
        """
        text_lower = text.lower()
        score = 0.0
        matched = []
        for keyword, weight in DISTRESS_KEYWORDS.items():
            if keyword.lower() in text_lower:
                score += weight
                matched.append(keyword)
        return min(score, 100.0), matched

    # ──────────────────────────────────────────────────────────────────────
    # Business methods
    # ──────────────────────────────────────────────────────────────────────

    def ingest_post(
        self,
        post_id: str,
        author_name: str,
        author_role: str,
        company: str,
        text: str,
        platform: str,
        posted_at: str,
    ) -> Optional[SentimentSignal]:
        """
        Ingest a social post and score it for OT distress signals.

        Args:
            post_id: Platform-native post identifier.
            author_name: Full name of the author.
            author_role: Job title (e.g. "RSSI", "DSI").
            company: Employer of the author.
            text: Full post text.
            platform: Source platform name (e.g. "linkedin", "twitter").
            posted_at: ISO-8601 timestamp of original post.

        Returns:
            SentimentSignal if post is new and has at least one keyword match,
            None if already seen or no keywords matched.
        """
        if post_id in self._seen_ids:
            return None

        score, keywords = self._compute_score(text)
        if score == 0.0:
            with self._lock:
                self._seen_ids.add(post_id)
            return None

        signal = SentimentSignal(
            post_id=post_id,
            author_name=author_name,
            author_role=author_role,
            company=company,
            text_snippet=text[:200],
            platform=platform,
            distress_score=score,
            hot_keywords=keywords,
            is_hot_lead=score >= MIN_SCORE_HOT,
            posted_at=posted_at,
        )

        with self._lock:
            self._seen_ids.add(post_id)
            self._signals.append(asdict(signal))

        self._save()

        if score >= MIN_SCORE_ALERT:
            self._send_alert(signal)

        return signal

    def get_hot_leads(self, min_score: float = 70) -> List[SentimentSignal]:
        """
        Return signals whose distress_score is at or above min_score.

        Args:
            min_score: Minimum distress score threshold.

        Returns:
            List of SentimentSignal objects sorted by distress_score descending.
        """
        with self._lock:
            raw = [s for s in self._signals if s["distress_score"] >= min_score]
        raw.sort(key=lambda s: s["distress_score"], reverse=True)
        return [SentimentSignal(**s) for s in raw]

    def get_stats(self) -> Dict:
        """
        Return aggregate statistics for the dashboard.

        Returns:
            Dict with total_posts, hot_leads, avg_score.
        """
        with self._lock:
            total = len(self._signals)
            hot = sum(1 for s in self._signals if s["distress_score"] >= MIN_SCORE_HOT)
            avg = (
                sum(s["distress_score"] for s in self._signals) / total
                if total > 0
                else 0.0
            )
        return {"total_posts": total, "hot_leads": hot, "avg_score": round(avg, 2)}

    def _send_alert(self, signal: SentimentSignal) -> None:
        """Send a Telegram alert for high-distress signals."""
        msg = (
            f"🚨 SENTIMENT RADAR — HOT LEAD\n"
            f"├── Auteur : {signal.author_name} ({signal.author_role})\n"
            f"├── Entreprise : {signal.company}\n"
            f"├── Plateforme : {signal.platform}\n"
            f"├── Score détresse : {signal.distress_score}/100\n"
            f"├── Mots-clés : {', '.join(signal.hot_keywords)}\n"
            f"└── Extrait : {signal.text_snippet[:100]}…"
        )
        try:
            from NAYA_CORE.integrations.telegram_notifier import get_notifier
            get_notifier().send(msg)
        except Exception as exc:
            log.warning("SentimentRadar: Telegram alert failed: %s", exc)


# ──────────────────────────────────────────────────────────────────────────────
# Singleton
# ──────────────────────────────────────────────────────────────────────────────

_radar: Optional[SentimentRadar] = None


def get_sentiment_radar() -> SentimentRadar:
    """Return the process-wide singleton SentimentRadar instance."""
    global _radar
    if _radar is None:
        _radar = SentimentRadar()
    return _radar
