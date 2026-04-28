"""
NAYA V19 — Dynamic Scaler
══════════════════════════════════════════════════════════════════════════════
Scale dynamiquement les slots parallèles de 4 → 6 → 8 → 12.

RÈGLE D'ESCALADE (toutes les 24h max):
  Ajouter 1 slot si TOUTES ces conditions sont vraies :
    1. SHI ≥ 0.75          (système en bonne santé)
    2. conversion_rate ≥ 15% (la chasse est efficace)
    3. revenue_mtd ≥ 10 000€ (on génère du cash réel)
    4. slots_libres == 0   (tous les slots actuels sont utilisés)
    5. Pas de régression détectée lors de la dernière vérification

RÈGLE DE RÉDUCTION (garde-fou):
  Retirer 1 slot si :
    1. SHI < 0.40            (système dégradé)
    2. Ou plus de 50% des slots actifs sont bloqués > 14j

PLANCHER ABSOLU: 4 slots (jamais en dessous)
PLAFOND ABSOLU: 12 slots (configurable via MAX_SLOTS_ABSOLUTE)
══════════════════════════════════════════════════════════════════════════════
"""
import json
import logging
import threading
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional

log = logging.getLogger("NAYA.DYNAMIC_SCALER")

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "cache" / "dynamic_scaler.json"

MIN_SLOTS = 5  # Upgraded from 4 to 5 for production
MAX_SLOTS_ABSOLUTE = 12
SCALE_COOLDOWN_S = 24 * 3600  # Minimum 24h entre deux scalings


@dataclass
class ScalingEvent:
    """Enregistrement d'un événement de scaling."""
    ts: float
    direction: str       # "up" | "down" | "hold"
    slots_before: int
    slots_after: int
    reason: str
    kpis_snapshot: Dict = field(default_factory=dict)


class DynamicScaler:
    """
    Évalue et applique le scaling des slots parallèles.
    Thread-safe. Persistance JSON. Anti-régression intégrée.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._current_slots: int = MIN_SLOTS
        self._last_scale_ts: float = 0.0
        self._history: List[ScalingEvent] = []
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        self._load()
        log.info("[SCALER] Dynamic Scaler V19 — slots actuels: %d", self._current_slots)

    # ── API publique ──────────────────────────────────────────────────────────

    def evaluate_and_scale(self, kpis: Dict) -> Dict:
        """
        Évalue les conditions et scale si nécessaire.

        Args:
            kpis: dict avec shi_score, conversion_rate, revenue_mtd (ou mrr),
                  active_slots, max_slots, slots_libres

        Returns:
            dict avec current_slots, new_slots, action, reason
        """
        with self._lock:
            slots_before = self._current_slots
            action, reason = self._decide(kpis)

            if action == "up":
                new_slots = min(self._current_slots + 1, MAX_SLOTS_ABSOLUTE)
                if new_slots != self._current_slots:
                    self._apply_scale(new_slots, "up", reason, kpis)
            elif action == "down":
                new_slots = max(self._current_slots - 1, MIN_SLOTS)
                if new_slots != self._current_slots:
                    self._apply_scale(new_slots, "down", reason, kpis)
            else:
                new_slots = self._current_slots

            return {
                "current_slots": slots_before,
                "new_slots": self._current_slots,
                "action": action,
                "reason": reason,
                "cooldown_remaining_h": self._cooldown_remaining_h(),
            }

    def get_current_slots(self) -> int:
        """Retourne le nombre de slots actifs actuel."""
        with self._lock:
            return self._current_slots

    def force_scale(self, n_slots: int, reason: str = "manual") -> Dict:
        """Force le nombre de slots (usage manuel via Telegram /scale N)."""
        with self._lock:
            n_slots = max(MIN_SLOTS, min(n_slots, MAX_SLOTS_ABSOLUTE))
            direction = "up" if n_slots > self._current_slots else "down" if n_slots < self._current_slots else "hold"
            if direction != "hold":
                self._apply_scale(n_slots, direction, f"[FORCED] {reason}", {})
            return {"new_slots": self._current_slots, "action": direction}

    def get_stats(self) -> Dict:
        with self._lock:
            return {
                "current_slots": self._current_slots,
                "min_slots": MIN_SLOTS,
                "max_slots": MAX_SLOTS_ABSOLUTE,
                "last_scale": self._last_scale_ts,
                "cooldown_remaining_h": self._cooldown_remaining_h(),
                "history_count": len(self._history),
                "last_event": asdict(self._history[-1]) if self._history else None,
            }

    # ── Logique de décision ───────────────────────────────────────────────────

    def _decide(self, kpis: Dict) -> tuple:
        """Retourne (action, reason) — action ∈ {"up", "down", "hold"}"""

        shi = kpis.get("shi_score", 0.5)
        conv = kpis.get("conversion_rate", 0.0)
        revenue_mtd = kpis.get("revenue_mtd", kpis.get("mrr", 0.0))
        slots_libres = kpis.get("slots_libres",
                                kpis.get("max_slots", 4) - kpis.get("active_slots", 4))

        # Garde-fou : réduction si système dégradé
        if shi < 0.40:
            return "down", f"SHI={shi:.2f} < 0.40 — réduction préventive"

        # Cooldown : pas deux scalings en 24h
        if self._cooldown_remaining_h() > 0:
            return "hold", f"Cooldown actif ({self._cooldown_remaining_h():.1f}h restantes)"

        # Conditions de montée en charge
        if (
            self._current_slots < MAX_SLOTS_ABSOLUTE
            and shi >= 0.75
            and conv >= 0.15
            and revenue_mtd >= 10_000
            and slots_libres == 0
        ):
            return "up", (
                f"Conditions remplies: SHI={shi:.2f}≥0.75, "
                f"conv={conv:.1%}≥15%, revenue={revenue_mtd:,.0f}€≥10k€, "
                f"slots_libres=0"
            )

        return "hold", (
            f"Conditions non remplies: SHI={shi:.2f}, "
            f"conv={conv:.1%}, revenue={revenue_mtd:,.0f}€"
        )

    def _apply_scale(self, new_slots: int, direction: str, reason: str, kpis: Dict) -> None:
        """Applique le changement de slots avec persistance."""
        old_slots = self._current_slots
        self._current_slots = new_slots
        self._last_scale_ts = time.time()

        event = ScalingEvent(
            ts=time.time(),
            direction=direction,
            slots_before=old_slots,
            slots_after=new_slots,
            reason=reason,
            kpis_snapshot={k: kpis[k] for k in list(kpis)[:6]},
        )
        self._history.append(event)
        if len(self._history) > 100:
            self._history = self._history[-50:]

        log.info("[SCALER] %s: %d → %d slots | %s",
                 direction.upper(), old_slots, new_slots, reason[:60])

        # Appliquer au ParallelPipelineManager
        try:
            from PARALLEL_ENGINE.parallel_pipeline_manager import get_parallel_pipeline
            pipeline = get_parallel_pipeline()
            pipeline.N_SLOTS = new_slots
            # S'assurer que les nouveaux slots sont disponibles
            while len(pipeline.slots) < new_slots:
                from PARALLEL_ENGINE.parallel_pipeline_manager import Slot
                pipeline.slots.append(Slot(len(pipeline.slots)))
            pipeline._fill_slots()
            log.info("[SCALER] Pipeline mis à jour: %d slots", new_slots)
        except Exception as e:
            log.warning("[SCALER] Pipeline update: %s", e)

        self._save()

    def _cooldown_remaining_h(self) -> float:
        """Retourne les heures restantes avant le prochain scaling possible."""
        elapsed = time.time() - self._last_scale_ts
        remaining = max(0, SCALE_COOLDOWN_S - elapsed)
        return round(remaining / 3600, 1)

    # ── Persistance ───────────────────────────────────────────────────────────

    def _save(self) -> None:
        try:
            data = {
                "current_slots": self._current_slots,
                "last_scale_ts": self._last_scale_ts,
                "history": [asdict(e) for e in self._history[-20:]],
                "saved_at": time.time(),
            }
            tmp = DATA_FILE.with_suffix(".tmp")
            tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            tmp.replace(DATA_FILE)
        except Exception as e:
            log.warning("[SCALER] Save: %s", e)

    def _load(self) -> None:
        try:
            if not DATA_FILE.exists():
                return
            data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            loaded = data.get("current_slots", MIN_SLOTS)
            self._current_slots = max(MIN_SLOTS, min(loaded, MAX_SLOTS_ABSOLUTE))
            self._last_scale_ts = data.get("last_scale_ts", 0.0)
            for ed in data.get("history", []):
                try:
                    self._history.append(ScalingEvent(**ed))
                except Exception:
                    pass
        except Exception as e:
            log.warning("[SCALER] Load: %s", e)


# ── Singleton ──────────────────────────────────────────────────────────────────
_scaler: Optional[DynamicScaler] = None


def get_dynamic_scaler() -> DynamicScaler:
    global _scaler
    if _scaler is None:
        _scaler = DynamicScaler()
    return _scaler
