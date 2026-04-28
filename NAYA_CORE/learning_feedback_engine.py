"""
NAYA V19 - Learning Feedback Engine
Chaque vente reussie ou ratee alimente un moteur d apprentissage.
Ajuste strategies, messages, prix, secteurs pour devenir plus precis.
"""
import time, logging, threading, json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path

log = logging.getLogger("NAYA.LEARNING")
LEARNING_FILE = Path("data/cache/learning_state.json")

@dataclass
class FeedbackEntry:
    sector: str
    offer_type: str
    price_proposed: float
    outcome: str  # won, lost, no_response, negotiated
    response_time_h: float
    message_template: str
    channel: str
    pain_type: str
    timestamp: float = field(default_factory=time.time)
    notes: str = ""

@dataclass
class SectorInsight:
    sector: str
    win_rate: float = 0.0
    avg_deal_size: float = 0.0
    best_channel: str = ""
    best_offer_type: str = ""
    avg_response_time_h: float = 0.0
    total_attempts: int = 0
    total_wins: int = 0
    total_revenue: float = 0.0
    optimal_price_range: tuple = (1000, 10000)

class LearningFeedbackEngine:
    """Moteur d apprentissage continu - le systeme s ameliore a chaque interaction."""

    def __init__(self):
        self._feedback: List[FeedbackEntry] = []
        self._insights: Dict[str, SectorInsight] = {}
        self._lock = threading.RLock()
        self._channel_scores: Dict[str, Dict[str, float]] = {}
        self._message_scores: Dict[str, List[float]] = {}
        self._load()

    def record_feedback(self, entry: FeedbackEntry) -> None:
        """Enregistre un feedback et met a jour les insights."""
        with self._lock:
            self._feedback.append(entry)
            if len(self._feedback) > 5000:
                self._feedback = self._feedback[-2500:]
            self._update_insights(entry)
        self._save()

    def record_win(self, sector: str, offer_type: str, price: float,
                   channel: str, pain_type: str) -> None:
        self.record_feedback(FeedbackEntry(
            sector=sector, offer_type=offer_type, price_proposed=price,
            outcome="won", response_time_h=0, message_template="",
            channel=channel, pain_type=pain_type
        ))

    def record_loss(self, sector: str, offer_type: str, price: float,
                    reason: str = "") -> None:
        self.record_feedback(FeedbackEntry(
            sector=sector, offer_type=offer_type, price_proposed=price,
            outcome="lost", response_time_h=0, message_template="",
            channel="", pain_type="", notes=reason
        ))

    def _update_insights(self, entry: FeedbackEntry) -> None:
        sector = entry.sector
        if sector not in self._insights:
            self._insights[sector] = SectorInsight(sector=sector)
        ins = self._insights[sector]
        ins.total_attempts += 1

        if entry.outcome == "won":
            ins.total_wins += 1
            ins.total_revenue += entry.price_proposed

        ins.win_rate = ins.total_wins / ins.total_attempts if ins.total_attempts > 0 else 0
        ins.avg_deal_size = ins.total_revenue / ins.total_wins if ins.total_wins > 0 else 0

        # Best channel
        if sector not in self._channel_scores:
            self._channel_scores[sector] = {}
        ch = entry.channel
        if ch:
            if ch not in self._channel_scores[sector]:
                self._channel_scores[sector][ch] = 0
            if entry.outcome == "won":
                self._channel_scores[sector][ch] += 1
            best_ch = max(self._channel_scores[sector], key=self._channel_scores[sector].get)
            ins.best_channel = best_ch

    def get_insight(self, sector: str) -> Optional[SectorInsight]:
        with self._lock:
            return self._insights.get(sector)

    def get_best_sectors(self, n: int = 5) -> List[SectorInsight]:
        with self._lock:
            sectors = sorted(self._insights.values(),
                           key=lambda s: s.win_rate * s.avg_deal_size, reverse=True)
            return sectors[:n]

    def recommend_strategy(self, sector: str, pain_type: str) -> Dict:
        """Recommande la meilleure strategie basee sur l apprentissage."""
        with self._lock:
            ins = self._insights.get(sector)
            if not ins or ins.total_attempts < 3:
                return {
                    "strategy": "explorer",
                    "message": "Pas assez de donnees - tester plusieurs approches",
                    "recommended_channel": "email",
                    "recommended_price_range": (1000, 5000)
                }

            return {
                "strategy": "optimise" if ins.win_rate > 0.3 else "ajuster",
                "win_rate": round(ins.win_rate, 2),
                "avg_deal": round(ins.avg_deal_size, 2),
                "recommended_channel": ins.best_channel or "email",
                "recommended_price_range": (
                    max(1000, ins.avg_deal_size * 0.7),
                    ins.avg_deal_size * 1.3
                ),
                "total_data_points": ins.total_attempts,
                "confidence": min(1.0, ins.total_attempts / 20)
            }

    def _save(self) -> None:
        try:
            LEARNING_FILE.parent.mkdir(parents=True, exist_ok=True)
            with self._lock:
                data = {
                    "insights": {
                        s: {"win_rate": i.win_rate, "avg_deal": i.avg_deal_size,
                            "total_attempts": i.total_attempts, "total_wins": i.total_wins,
                            "total_revenue": i.total_revenue, "best_channel": i.best_channel}
                        for s, i in self._insights.items()
                    },
                    "channels": self._channel_scores
                }
            LEARNING_FILE.write_text(json.dumps(data, indent=2))
        except Exception as e:
            log.debug(f"[LEARNING] Save: {e}")

    def _load(self) -> None:
        try:
            if LEARNING_FILE.exists():
                data = json.loads(LEARNING_FILE.read_text())
                for s, d in data.get("insights", {}).items():
                    self._insights[s] = SectorInsight(
                        sector=s, win_rate=d.get("win_rate", 0),
                        avg_deal_size=d.get("avg_deal", 0),
                        total_attempts=d.get("total_attempts", 0),
                        total_wins=d.get("total_wins", 0),
                        total_revenue=d.get("total_revenue", 0),
                        best_channel=d.get("best_channel", "")
                    )
                self._channel_scores = data.get("channels", {})
                log.info(f"[LEARNING] {len(self._insights)} secteurs charges")
        except Exception as e:
            log.debug(f"[LEARNING] Load: {e}")

    def get_stats(self) -> Dict:
        with self._lock:
            total_wins = sum(i.total_wins for i in self._insights.values())
            total_revenue = sum(i.total_revenue for i in self._insights.values())
            return {
                "sectors_tracked": len(self._insights),
                "total_feedback": len(self._feedback),
                "total_wins": total_wins,
                "total_revenue": total_revenue,
                "best_sectors": [
                    {"sector": s.sector, "win_rate": round(s.win_rate, 2), "revenue": s.total_revenue}
                    for s in sorted(self._insights.values(), key=lambda x: x.total_revenue, reverse=True)[:5]
                ]
            }

_learning = None
_learning_lock = threading.Lock()
def get_learning_engine() -> LearningFeedbackEngine:
    global _learning
    if _learning is None:
        with _learning_lock:
            if _learning is None:
                _learning = LearningFeedbackEngine()
    return _learning
